from tortoise import fields
from tortoise.models import Model


class RoomType(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    base_price = fields.DecimalField(max_digits=10, decimal_places=2)
    max_capacity = fields.IntField(default=2)
    bed_type = fields.CharField(max_length=50, null=True)
    size_sqm = fields.DecimalField(max_digits=5, decimal_places=1, null=True)
    total_units = fields.IntField(default=1)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "room_types"
        app = "inventory_service"

    def __str__(self):
        return self.name
