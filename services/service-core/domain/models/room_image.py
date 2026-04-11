from tortoise import fields
from tortoise.models import Model


class RoomImage(Model):
    id = fields.UUIDField(pk=True)
    room_type_id = fields.UUIDField()
    url = fields.TextField()
    alt_text = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "room_images"
        app = "inventory_service"

    def __str__(self):
        return f"Image {self.id}"
