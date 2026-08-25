from httpx import AsyncClient


async def _register(
    client: AsyncClient, email: str = "alice@example.com"
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "display_name": "Alice",
        },
    )
    return {"status_code": response.status_code, "body": response.json()}


async def test_register_then_duplicate_conflicts(client: AsyncClient) -> None:
    first = await _register(client)
    assert first["status_code"] == 201

    second = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "anotherpass1",
            "display_name": "Alice Two",
        },
    )
    assert second.status_code == 409


async def test_login_and_me_flow(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "password": "correctpass1",
            "display_name": "Bob",
        },
    )

    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrongpass"},
    )
    assert bad_login.status_code == 401

    no_token = await client.get("/api/v1/users/me")
    assert no_token.status_code == 401

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "correctpass1"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "bob@example.com"
    assert "password_hash" not in body


async def test_password_hash_never_leaks(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "carol@example.com",
            "password": "carolpass123",
            "display_name": "Carol",
        },
    )
    assert "password_hash" not in register_response.json()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "carolpass123"},
    )
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert "password_hash" not in me_response.json()


async def test_non_admin_gets_403_from_require_admin(client: AsyncClient) -> None:
    from typing import Annotated

    from fastapi import APIRouter, Depends

    from app.core.security import require_admin
    from app.main import app

    probe_router = APIRouter()

    @probe_router.get("/__probe/admin-only")
    def _admin_only(_: Annotated[object, Depends(require_admin)]) -> dict[str, bool]:
        return {"ok": True}

    app.include_router(probe_router)

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dave@example.com",
            "password": "davepass123",
            "display_name": "Dave",
        },
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "davepass123"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/__probe/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
