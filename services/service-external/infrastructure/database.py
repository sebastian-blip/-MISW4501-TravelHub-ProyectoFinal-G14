import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "travelhub")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

_echo = os.getenv("SQL_ECHO", "").lower() in ("1", "true", "yes")
_ssl = os.getenv("POSTGRES_SSL", "require").lower()
_connect_args: dict = {}
if _ssl not in ("0", "false", "disable", "off", "no"):
    _connect_args["ssl"] = True

_engine_kwargs: dict = {"echo": _echo}
if _connect_args:
    _engine_kwargs["connect_args"] = _connect_args
engine = create_async_engine(DATABASE_URL, **_engine_kwargs)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
