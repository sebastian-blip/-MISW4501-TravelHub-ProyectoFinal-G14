from tortoise import fields
from tortoise.models import Model


class HotelReview(Model):
    id = fields.UUIDField(pk=True)
    hotel_id = fields.UUIDField()
    user_id = fields.UUIDField()
    reservation_id = fields.UUIDField(null=True)
    overall_rating = fields.DecimalField(max_digits=2, decimal_places=1)
    cleanliness_rating = fields.DecimalField(max_digits=2, decimal_places=1, null=True)
    service_rating = fields.DecimalField(max_digits=2, decimal_places=1, null=True)
    location_rating = fields.DecimalField(max_digits=2, decimal_places=1, null=True)
    value_rating = fields.DecimalField(max_digits=2, decimal_places=1, null=True)
    comment = fields.TextField(null=True)
    response = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "hotel_reviews"
        app = "hotel_service"

    def __str__(self):
        return f"Review {self.id} - {self.overall_rating}"
