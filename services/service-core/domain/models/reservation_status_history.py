from tortoise import fields
from tortoise.models import Model


class ReservationStatusHistory(Model):
    id = fields.UUIDField(pk=True)
    reservation_id = fields.UUIDField()
    previous_status = fields.CharField(max_length=50, null=True)
    new_status = fields.CharField(max_length=50)
    changed_by = fields.UUIDField(null=True)
    reason = fields.TextField(null=True)
    ip_address = fields.CharField(max_length=45, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "reservation_status_history"
        app = "reservation_service"

    def __str__(self):
        return f"{self.previous_status} -> {self.new_status}"
