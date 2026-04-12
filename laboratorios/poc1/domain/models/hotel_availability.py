from tortoise import fields
from tortoise.models import Model
from hotel_service.utils.datetime import ensure_utc


class HotelAvailability(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField(index=True)
    room_id = fields.UUIDField(index=True)  # ✅ Agregar índice
    hotel_name = fields.CharField(max_length=255)
    city = fields.CharField(max_length=100, index=True)  # ✅ CRÍTICO - Índice en city
    available = fields.BooleanField(default=True, index=True)  # ✅ Índice en available
    room_type = fields.CharField(max_length=50, null=True)
    price_per_night = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "hotel_availability"
        app = "hotel_service"
        unique_together = ("hotel_id", "room_id")
        indexes = [
            ("city", "available")
        ]

    def __str__(self):
        return f"{self.hotel_name} - {self.room_id} ({'available' if self.available else 'reserved'})"