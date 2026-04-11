from tortoise import fields
from tortoise.models import Model


class RevenueReport(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    period_start = fields.DateField()
    period_end = fields.DateField()
    total_revenue = fields.DecimalField(max_digits=12, decimal_places=2)
    total_bookings = fields.IntField(default=0)
    currency_code = fields.CharField(max_length=3, default="USD")
    generated_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "revenue_reports"
        app = "reporting_service"

    def __str__(self):
        return f"Revenue Report {self.hotel_id} - {self.period_start}"
