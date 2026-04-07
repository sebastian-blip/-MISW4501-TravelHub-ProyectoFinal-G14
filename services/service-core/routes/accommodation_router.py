from datetime import date
from typing import List, Optional
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from mediatr import Mediator
from pydantic import BaseModel

from accommodation_service.queries.accommodation_queries import SearchAccommodationsQuery
import accommodation_service.queries.search_accommodations_handler  # registra handler

router = APIRouter(prefix="/accommodations", tags=["Accommodations"])


class RoomTypeAvailabilityOut(BaseModel):
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

    class Config:
        from_attributes = True


class AccommodationSearchResultOut(BaseModel):
    hotel_id: UUID
    hotel_name: str
    description: Optional[str]
    address: str
    city: str
    stars: int
    rating: Optional[Decimal]
    check_in_time: str
    check_out_time: str
    available_room_types: List[RoomTypeAvailabilityOut]

    class Config:
        from_attributes = True


def get_mediator() -> Mediator:
    return Mediator()


@router.get("/search", response_model=List[AccommodationSearchResultOut])
async def search_accommodations(
    city: str = Query(..., description="Ciudad de destino"),
    check_in: date = Query(..., description="Fecha de check-in (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Fecha de check-out (YYYY-MM-DD)"),
    guests: int = Query(1, ge=1, description="Número de huéspedes"),
    mediator: Mediator = Depends(get_mediator),
):
    """
    Busca hospedajes disponibles por ciudad y fechas.

    Solo retorna propiedades con disponibilidad real para todas las noches del período.
    """
    try:
        results = await mediator.send(
            SearchAccommodationsQuery(
                city=city,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
            )
        )
        return [
            AccommodationSearchResultOut(
                hotel_id=r.hotel_id,
                hotel_name=r.hotel_name,
                description=r.description,
                address=r.address,
                city=r.city,
                stars=r.stars,
                rating=r.rating,
                check_in_time=r.check_in_time,
                check_out_time=r.check_out_time,
                available_room_types=[
                    RoomTypeAvailabilityOut(
                        id=rt.id,
                        name=rt.name,
                        description=rt.description,
                        max_capacity=rt.max_capacity,
                        bed_type=rt.bed_type,
                        size_sqm=rt.size_sqm,
                        price_per_night=rt.price_per_night,
                        total_price=rt.total_price,
                        currency_code=rt.currency_code,
                        minimum_stay=rt.minimum_stay,
                    )
                    for rt in r.available_room_types
                ],
            )
            for r in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
