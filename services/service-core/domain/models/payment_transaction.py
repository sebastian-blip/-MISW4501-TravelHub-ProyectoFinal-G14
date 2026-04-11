from tortoise import fields
from tortoise.models import Model


class PaymentTransaction(Model):
    id = fields.UUIDField(pk=True)
    payment_id = fields.UUIDField()
    type = fields.CharField(max_length=50)
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    status = fields.CharField(max_length=50)
    provider_tx_id = fields.CharField(max_length=255, null=True)
    fraud_score = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    three_ds_verified = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "payment_transactions"
        app = "payment_service"

    def __str__(self):
        return f"Transaction {self.id}"
