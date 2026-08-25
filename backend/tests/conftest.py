from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine, get_session
from app.main import app


@pytest.fixture()
def session() -> Generator[Session]:
    connection: Connection = engine.connect()
    transaction = connection.begin()
    db = SessionLocal(bind=connection)
    try:
        yield db
    finally:
        db.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
async def client(session: Session) -> AsyncGenerator[AsyncClient]:
    def _get_session_override() -> Generator[Session]:
        yield session

    app.dependency_overrides[get_session] = _get_session_override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_session, None)
