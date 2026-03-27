import os

from tortoise import Tortoise

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "travelhub")

print (f"Connecting to database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

TORTOISE_ORM = {
    "connections": {
        "default": (
            f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
            f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
    },
    "use_tz": True,
    "timezone": "UTC",
    "apps": {
        "user_service": {
            "models": ["domain.models.user"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
