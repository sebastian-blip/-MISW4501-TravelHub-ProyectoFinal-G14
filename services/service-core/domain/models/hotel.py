from tortoise import fields
from tortoise.models import Model


class Hotel(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    address = fields.TextField()
    city = fields.CharField(max_length=100)
    country_id = fields.UUIDField()
    latitude = fields.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitude = fields.DecimalField(max_digits=11, decimal_places=8, null=True)
    phone = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=255, null=True)
    stars = fields.IntField(default=3)
    rating = fields.DecimalField(max_digits=2, decimal_places=1, null=True)
    total_reviews = fields.IntField(default=0)
    check_in_time = fields.TimeField(default="15:00:00")
    check_out_time = fields.TimeField(default="11:00:00")
    owner_user_id = fields.UUIDField(null=True)
    pms_provider = fields.CharField(max_length=100, null=True)
    pms_hotel_code = fields.CharField(max_length=100, null=True)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "hotels"
        app = "hotel_service"

    def __str__(self):
        return self.name
