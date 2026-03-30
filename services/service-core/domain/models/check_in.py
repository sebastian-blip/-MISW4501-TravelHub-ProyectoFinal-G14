from tortoise import fields
from tortoise.models import Model


class CheckIn(Model):
    id = fields.UUIDField(pk=True)
    reservation_id = fields.UUIDField(unique=True)
    qr_code = fields.CharField(max_length=255, unique=True)
    room_number = fields.CharField(max_length=20, null=True)
    checked_in_at = fields.DatetimeField(null=True)
    checked_out_at = fields.DatetimeField(null=True)
    status = fields.CharField(max_length=50, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "check_ins"
        app = "reservation_service"

    def __str__(self):
        return f"CheckIn {self.id}"
