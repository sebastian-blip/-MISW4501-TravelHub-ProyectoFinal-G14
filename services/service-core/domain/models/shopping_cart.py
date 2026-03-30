from tortoise import fields
from tortoise.models import Model


class ShoppingCart(Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField()
    room_type_id = fields.UUIDField()
    check_in = fields.DateField()
    check_out = fields.DateField()
    guests = fields.IntField(default=1)
    hold_expires_at = fields.DatetimeField()
    status = fields.CharField(max_length=50, default="active")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "shopping_carts"
        app = "reservation_service"

    def __str__(self):
        return f"Cart {self.id}"
