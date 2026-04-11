from sqlmodel import Field, SQLModel
from decimal import Decimal
import datetime
import uuid


class RevenueReport(SQLModel, table=True):
    __tablename__ = "revenue_reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    period_start: datetime.date
    period_end: datetime.date
    total_revenue: Decimal = Field(max_digits=12, decimal_places=2)
    total_bookings: int = Field(default=0)
    currency_code: str = Field(default="USD", max_length=3)
    generated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Revenue Report {self.hotel_id} - {self.period_start}"
