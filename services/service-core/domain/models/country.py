from tortoise import fields
from tortoise.models import Model


class Country(Model):
    id = fields.UUIDField(pk=True)
    code = fields.CharField(max_length=3, unique=True)
    name = fields.CharField(max_length=100)
    currency_code = fields.CharField(max_length=3)
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "countries"
        app = "user_service"

    def __str__(self):
        return self.name
