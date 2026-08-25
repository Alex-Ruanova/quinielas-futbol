from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine


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
async def client() -> AsyncGenerator[AsyncClient]:
    # Placeholder app until app/main.py (out of this phase's file_scope) wires real routers.
    app = FastAPI()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
