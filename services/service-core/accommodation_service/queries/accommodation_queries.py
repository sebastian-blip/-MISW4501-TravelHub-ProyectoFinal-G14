from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID


@dataclass
class SearchAccommodationsQuery:
    city: str
    check_in: date
    check_out: date
    guests: int = 1


@dataclass
class RoomTypeAvailability:
    id: UUID
    name: str
    description: Optional[str]
    max_capacity: int
    bed_type: Optional[str]
    size_sqm: Optional[Decimal]
    price_per_night: Decimal
    total_price: Decimal
    currency_code: str
    minimum_stay: int


@dataclass
class AccommodationSearchResult:
    hotel_id: UUID
    hotel_name: str
    description: Optional[str]
    address: str
    city: str
    stars: int
    rating: Optional[Decimal]
    check_in_time: str
    check_out_time: str
    available_room_types: List[RoomTypeAvailability] = field(default_factory=list)
