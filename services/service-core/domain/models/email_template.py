from tortoise import fields
from tortoise.models import Model


class EmailTemplate(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    subject = fields.CharField(max_length=255)
    body_html = fields.TextField()
    body_text = fields.TextField(null=True)
    language = fields.CharField(max_length=5, default="es")
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "email_templates"
        app = "notification_service"

    def __str__(self):
        return self.name
