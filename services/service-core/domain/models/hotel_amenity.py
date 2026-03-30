from tortoise import fields
from tortoise.models import Model


class HotelAmenity(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    name = fields.CharField(max_length=100)
    icon = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "hotel_amenities"
        app = "hotel_service"

    def __str__(self):
        return self.name
