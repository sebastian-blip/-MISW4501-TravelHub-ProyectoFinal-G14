from tortoise import fields
from tortoise.models import Model


class UserSession(Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField()
    token = fields.CharField(max_length=500, unique=True)
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.TextField(null=True)
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_sessions"
        app = "user_service"

    def __str__(self):
        return f"Session {self.id}"
