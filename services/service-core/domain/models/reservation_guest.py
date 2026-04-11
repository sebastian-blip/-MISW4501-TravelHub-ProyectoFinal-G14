from tortoise import fields
from tortoise.models import Model


class ReservationGuest(Model):
    id = fields.UUIDField(pk=True)
    reservation_id = fields.UUIDField()
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    document_type = fields.CharField(max_length=50, null=True)
    document_number = fields.CharField(max_length=50, null=True)
    nationality = fields.CharField(max_length=3, null=True)
    is_primary = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "reservation_guests"
        app = "reservation_service"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
