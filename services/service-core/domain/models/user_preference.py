from tortoise import fields
from tortoise.models import Model


class UserPreference(Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField(unique=True)
    preferred_currency = fields.CharField(max_length=3, default="USD")
    preferred_language = fields.CharField(max_length=5, default="es")
    notifications_email = fields.BooleanField(default=True)
    notifications_push = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_preferences"
        app = "user_service"

    def __str__(self):
        return f"Preferences for user {self.user_id}"
