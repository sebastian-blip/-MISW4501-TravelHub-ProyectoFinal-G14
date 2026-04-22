from sqlmodel import Field, SQLModel
from decimal import Decimal
from typing import Optional
import datetime
import uuid


class OccupancyReport(SQLModel, table=True):
    __tablename__ = "occupancy_reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    report_date: datetime.date
    total_rooms: int
    occupied_rooms: int = Field(default=0)
    occupancy_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    generated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Occupancy Report {self.hotel_id} - {self.report_date}"
