from tortoise import fields
from tortoise.models import Model


class HotelImage(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    url = fields.TextField()
    alt_text = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(default=0)
    image_type = fields.CharField(max_length=50, default="gallery")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "hotel_images"
        app = "hotel_service"

    def __str__(self):
        return f"Image {self.id}"
