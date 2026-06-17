import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "travelhub")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

print(f"Connecting to database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    """
    Initialize DB connection.

    NOTE:
    This project also ships SQL DDL + seed scripts under `schemas/`.
    If you are using those (recommended for local compose), keep
    AUTO_CREATE_SCHEMA=false so SQLModel doesn't create tables with a
    different shape (missing DB defaults, NOT NULL mismatches, etc.).
    """
    auto_create = os.getenv("AUTO_CREATE_SCHEMA", "false").lower() == "true"
    if not auto_create:
        return

    async with engine.begin() as conn:
        # Import models so SQLModel knows them
        import domain.models.user
        import domain.models.hotel
        import domain.models.room_type
        import domain.models.inventory_calendar
        import domain.models.task_order
        import domain.models.reservation
        # Push notifications (TRAVEL-173): tabla device_tokens. Se auto-crea
        # acá; en prod la migración manual `migrations/create_device_tokens.sql`
        # también la crea.
        import domain.models.device_token  # noqa: F401
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
