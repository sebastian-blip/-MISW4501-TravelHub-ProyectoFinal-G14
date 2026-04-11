from tortoise import fields
from tortoise.models import Model


class InventoryCalendar(Model):
    id = fields.UUIDField(pk=True)
    room_type_id = fields.UUIDField()
    date = fields.DateField()
    available_units = fields.IntField(default=0)
    price_per_night = fields.DecimalField(max_digits=10, decimal_places=2)
    currency_code = fields.CharField(max_length=3, default="USD")
    minimum_stay = fields.IntField(default=1)
    last_synced_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "inventory_calendar"
        app = "inventory_service"
        unique_together = ("room_type_id", "date")

    def __str__(self):
        return f"{self.room_type_id} - {self.date}"
