from tortoise import fields
from tortoise.models import Model


class Tour(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    country_id = fields.UUIDField()
    city = fields.CharField(max_length=100, null=True)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    currency_code = fields.CharField(max_length=3, default="USD")
    duration_hrs = fields.IntField(null=True)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tours"
        app = "tour_service"

    def __str__(self):
        return self.name
