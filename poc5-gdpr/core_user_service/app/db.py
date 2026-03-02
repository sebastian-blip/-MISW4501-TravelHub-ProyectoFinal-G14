import asyncpg
from .config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_db() -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, command_timeout=60)
    return _pool


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return _pool
