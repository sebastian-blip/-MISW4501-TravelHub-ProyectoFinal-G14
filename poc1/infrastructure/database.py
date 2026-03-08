from tortoise import Tortoise

TORTOISE_ORM = {
    "connections": {
        "default": "postgres://postgres:postgres@localhost:5432/travelhub"
    },
    "use_tz": True,
    "timezone": "UTC",
    "apps": {
        "hotel_service": {
            "models": [
                "domain.models.hotel",
                "domain.models.hotel_availability",
            ],
            "default_connection": "default",
        },
        "reservation_service": {
            "models": ["domain.models.reservation"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
