from tortoise import fields
from tortoise.models import Model


class RatePlan(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    name = fields.CharField(max_length=100)
    discount_pct = fields.DecimalField(max_digits=5, decimal_places=2, default=0)
    valid_from = fields.DateField(null=True)
    valid_to = fields.DateField(null=True)
    minimum_stay = fields.IntField(default=1)
    refundable = fields.BooleanField(default=True)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "rate_plans"
        app = "inventory_service"

    def __str__(self):
        return self.name
