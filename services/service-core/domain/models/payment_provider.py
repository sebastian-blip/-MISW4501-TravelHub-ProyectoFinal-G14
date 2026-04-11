from tortoise import fields
from tortoise.models import Model


class PaymentProvider(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=100)
    country_id = fields.UUIDField(null=True)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "payment_providers"
        app = "payment_service"

    def __str__(self):
        return self.name
