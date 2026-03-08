from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from typing import Optional

from hotel_service.utils.datetime import ensure_utc


@dataclass
class ReservationCreatedEvent:
    reservation_id: str
    user_id: str
    hotel_id: str
    room_id: str
    created_at: datetime
    correlation_id: Optional[str] = None
    hotel_name: Optional[str] = None
    city: Optional[str] = None
    room_type: Optional[str] = None
    price_per_night: Optional[Decimal] = None
    # default topic for Kafka producer
    topic: str = "reservation-created"

    def to_dict(self):
        d = asdict(self)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        if isinstance(d.get("price_per_night"), Decimal):
            d["price_per_night"] = str(d["price_per_night"])
        return d

    @classmethod
    def from_dict(cls, payload: dict) -> "ReservationCreatedEvent":
        created_at = payload.get("created_at")
        if created_at:
            created_at = datetime.fromisoformat(created_at)
        else:
            from hotel_service.utils.datetime import ensure_utc

            created_at = ensure_utc()

        price = payload.get("price_per_night")
        if price is not None:
            price = Decimal(str(price))

        return cls(
            reservation_id=str(payload.get("reservation_id")),
            user_id=str(payload.get("user_id")),
            hotel_id=str(payload.get("hotel_id")),
            room_id=str(payload.get("room_id")),
            created_at=created_at,
            correlation_id=payload.get("correlation_id"),
            hotel_name=payload.get("hotel_name"),
            city=payload.get("city"),
            room_type=payload.get("room_type"),
            price_per_night=price,
        )
