from tortoise import fields
from tortoise.models import Model


class Reservation(Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField()
    hotel_id = fields.UUIDField()
    room_type_id = fields.UUIDField()
    cart_id = fields.UUIDField(null=True)
    check_in = fields.DateField()
    check_out = fields.DateField()
    guests = fields.IntField(default=1)
    base_price = fields.DecimalField(max_digits=10, decimal_places=2)
    taxes = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    discounts = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = fields.DecimalField(max_digits=10, decimal_places=2)
    currency_code = fields.CharField(max_length=3, default="USD")
    status = fields.CharField(max_length=50, default="pending")
    cancellation_policy = fields.CharField(max_length=50, null=True)
    special_requests = fields.TextField(null=True)
    confirmation_code = fields.CharField(max_length=20, unique=True, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "reservations"
        app = "reservation_service"

    def __str__(self):
        return f"Reservation {self.confirmation_code or self.id}"
