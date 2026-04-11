from tortoise import fields
from tortoise.models import Model


class SpecialOffer(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    room_type_id = fields.UUIDField(null=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    discount_pct = fields.DecimalField(max_digits=5, decimal_places=2)
    valid_from = fields.DateField()
    valid_to = fields.DateField()
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "special_offers"
        app = "inventory_service"

    def __str__(self):
        return self.title
