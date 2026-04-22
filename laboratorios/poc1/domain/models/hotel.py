from tortoise import fields
from tortoise.models import Model


class Hotel(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    city = fields.CharField(max_length=100)
    country = fields.CharField(max_length=3)
    address = fields.TextField()
    stars = fields.IntField(default=3)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "hotels"
        app = "hotel_service"

    def __str__(self):
        return self.name


class Room(Model):
    id = fields.UUIDField(pk=True)
    hotel = fields.ForeignKeyField("hotel_service.Hotel", related_name="rooms")
    room_type = fields.CharField(max_length=50)
    price_per_night = fields.DecimalField(max_digits=10, decimal_places=2)
    capacity = fields.IntField(default=2)
    available = fields.BooleanField(default=True)

    class Meta:
        table = "rooms"
        app = "hotel_service"