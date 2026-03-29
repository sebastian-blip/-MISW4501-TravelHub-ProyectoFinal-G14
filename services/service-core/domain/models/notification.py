from tortoise import fields
from tortoise.models import Model


class Notification(Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField()
    type = fields.CharField(max_length=50)
    title = fields.CharField(max_length=255)
    body = fields.TextField()
    related_entity = fields.CharField(max_length=50, null=True)
    entity_id = fields.UUIDField(null=True)
    sent_at = fields.DatetimeField(null=True)
    read_at = fields.DatetimeField(null=True)
    status = fields.CharField(max_length=50, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"
        app = "notification_service"

    def __str__(self):
        return self.title
