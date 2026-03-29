from tortoise import fields
from tortoise.models import Model


class OccupancyReport(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    report_date = fields.DateField()
    total_rooms = fields.IntField()
    occupied_rooms = fields.IntField(default=0)
    occupancy_rate = fields.DecimalField(max_digits=5, decimal_places=2, default=0)
    generated_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "occupancy_reports"
        app = "reporting_service"
        unique_together = ("hotel_id", "report_date")

    def __str__(self):
        return f"Occupancy Report {self.hotel_id} - {self.report_date}"
