from tortoise import fields
from tortoise.models import Model


class Reservation(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    room_id = fields.UUIDField()
    user_id = fields.UUIDField()
    check_in = fields.DateField()
    check_out = fields.DateField()
    total_price = fields.DecimalField(max_digits=10, decimal_places=2)
    status = fields.CharField(max_length=50, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "reservations"
        app = "reservation_service"