from tortoise import fields
from tortoise.models import Model


class Payment(Model):
    id = fields.UUIDField(pk=True)
    reservation_id = fields.UUIDField()
    provider_id = fields.UUIDField()
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    currency_code = fields.CharField(max_length=3, default="USD")
    status = fields.CharField(max_length=50, default="pending")
    payment_token = fields.CharField(max_length=255, null=True)
    provider_payment_id = fields.CharField(max_length=255, null=True)
    failure_reason = fields.TextField(null=True)
    refund_amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    refunded_at = fields.DatetimeField(null=True)
    processed_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "payments"
        app = "payment_service"

    def __str__(self):
        return f"Payment {self.id}"
