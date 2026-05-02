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
    amenities: Optional[List[str]] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    min_stars: Optional[int] = None
    page: int = 1
    page_size: int = 20


@dataclass
class ListHotelsQuery:
    """Query para listar todos los hoteles con filtros opcionales"""
    city: Optional[str] = None
    country_id: Optional[UUID] = None
    min_stars: Optional[int] = None
    max_stars: Optional[int] = None
    min_rating: Optional[Decimal] = None
    active_only: bool = True
    limit: int = 50
    offset: int = 0


@dataclass
class GetHotelAvailabilityQuery:
    """Query para ver disponibilidad de un hotel específico"""
    hotel_id: UUID
    check_in: date
    check_out: date
    guests: int = 1


@dataclass
class ListCitiesQuery:
    """Query para listar ciudades con hoteles"""
    country_id: Optional[UUID] = None


@dataclass
class RoomAmenityInfo:
    """Información de amenidad de habitación"""
    name: str
    icon: Optional[str]


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
    amenities: List[RoomAmenityInfo] = field(default_factory=list)


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


@dataclass
class ListHotelsResult:
    total: int
    items: List[AccommodationSearchResult] = field(default_factory=list)
    page: int = 1
    page_size: int = 20


@dataclass
class HotelSummary:
    """Resumen de hotel para listados"""
    id: UUID
    name: str
    description: Optional[str]
    address: str
    city: str
    stars: int
    rating: Optional[Decimal]
    total_reviews: int
    active: bool


@dataclass
class HotelAvailabilityResult:
    """Resultado de disponibilidad para un hotel específico"""
    hotel_id: UUID
    hotel_name: str
    description: Optional[str]
    city: str
    stars: int
    rating: Optional[Decimal]
    check_in_time: str
    check_out_time: str
    nights: int
    available_room_types: List[RoomTypeAvailability] = field(default_factory=list)


@dataclass
class CityInfo:
    """Información de una ciudad con hoteles"""
    city: str
    country_id: UUID
    hotel_count: int
