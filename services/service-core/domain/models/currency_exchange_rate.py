from tortoise import fields
from tortoise.models import Model


class CurrencyExchangeRate(Model):
    id = fields.UUIDField(pk=True)
    from_currency = fields.CharField(max_length=3)
    to_currency = fields.CharField(max_length=3)
    rate = fields.DecimalField(max_digits=15, decimal_places=6)
    fetched_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "currency_exchange_rates"
        app = "reporting_service"
        unique_together = ("from_currency", "to_currency", "fetched_at")

    def __str__(self):
        return f"{self.from_currency} -> {self.to_currency}"
