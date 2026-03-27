from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    phone = fields.CharField(max_length=20, null=True)
    country_id = fields.UUIDField(null=True)
    user_type = fields.CharField(max_length=50)  # 'traveler', 'hotel_admin', 'agency', 'admin'
    email_verified = fields.BooleanField(default=False)
    mfa_enabled = fields.BooleanField(default=False)
    active = fields.BooleanField(default=True)

    class Meta:
        table = "users"
        app = "user_service"

    def __str__(self):
        return self.email
