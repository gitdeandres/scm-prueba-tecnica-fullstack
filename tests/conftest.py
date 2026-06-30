from collections.abc import AsyncIterator
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import create_access_token
from app.database import Base, get_session
from app.main import app
from app.models import Item


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with Session() as s:
        s.add_all(
            [
                Item(sku="A1", status="pending", warehouse_id=1, created_at=datetime(2025, 1, 1)),
                Item(sku="A2", status="done", warehouse_id=1, created_at=datetime(2025, 1, 2)),
                Item(sku="B1", status="pending", warehouse_id=2, created_at=datetime(2025, 1, 3)),
            ]
        )
        await s.commit()
        yield s

    await test_engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    token = create_access_token("admin")
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c
    app.dependency_overrides.clear()
