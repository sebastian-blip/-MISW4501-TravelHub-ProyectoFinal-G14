from tortoise import fields
from tortoise.models import Model


class AuditLog(Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField(null=True)
    action = fields.CharField(max_length=100)
    entity_type = fields.CharField(max_length=50, null=True)
    entity_id = fields.UUIDField(null=True)
    ip_address = fields.CharField(max_length=45, null=True)
    details = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
        app = "user_service"

    def __str__(self):
        return f"{self.action} - {self.entity_type}"
