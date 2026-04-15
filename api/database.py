import os
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    dsn = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://clickstream:clickstream@postgres:5432/clickstream"
    )
    dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    assert _pool is not None, "DB pool not initialized"
    async with _pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    global _pool
    _pool = await create_pool()
    yield
    await _pool.close()
