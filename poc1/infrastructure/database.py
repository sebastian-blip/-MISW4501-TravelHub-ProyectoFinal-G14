TORTOISE_ORM = {
    "connections": {
        "default": "postgres://postgres:postgres@localhost:5432/travelhub"
    },
    "apps": {
        "hotel_service": {
            "models": ["poc1.domain.models.hotel"],
            "default_connection": "default",
        },
        "reservation_service": {
            "models": ["poc1.domain.models.reservation"],
            "default_connection": "default",
        },
    },
}