import uuid
from datetime import date
from typing import List, Optional
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from mediatr import Mediator
from pydantic import BaseModel, ConfigDict
from session_service.sesion_handler import SessionHandler

from accommodation_service.queries.accommodation_queries import (
    SearchAccommodationsQuery,
    ListHotelsQuery,
    GetHotelAvailabilityQuery,
    ListCitiesQuery,
)
import accommodation_service.queries.search_accommodations_handler  # registra handler
import accommodation_service.queries.hotel_listing_handler  # registra handlers


router = APIRouter(prefix="/accommodations", tags=["Accommodations"])


class RoomAmenityOut(BaseModel):
    """Amenidad de habitación"""
    name: str
    icon: Optional[str]

    model_config = ConfigDict(from_attributes=True)


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
    amenities: List[RoomAmenityOut] = []

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)

class AccommodationSearchFilters(BaseModel):
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    min_stars: Optional[int] = None
    page: int = 1
    page_size: int = 20

def get_mediator() -> Mediator:
    return Mediator()


@router.get("/search")
async def search_accommodations(
    filters:  AccommodationSearchFilters = Depends(),
    amenities: Optional[List[str]] = Query(
        None, description="Lista de amenidades requeridas (repite este parámetro para más de una)"
    ),
    city: str = Query(..., description="Ciudad de destino"),
    check_in: date = Query(..., description="Fecha de check-in (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Fecha de check-out (YYYY-MM-DD)"),
    guests: int = Query(1, ge=1, description="Número de huéspedes"),
    mediator: Mediator = Depends(get_mediator),x_guest_id: str = Header(..., alias="X-Guest-Id")):
    """
    Busca hospedajes disponibles por ciudad y fechas.

    Solo retorna propiedades con disponibilidad real para todas las noches del período.
    """
    try:


        session_handler = SessionHandler()
        ses =await session_handler.get_session(x_guest_id)
        filters_search = filters.model_dump()
        filters_search['city'] = city
        filters_search['check_in'] = check_in
        filters_search['check_out'] = check_out
        filters_search['guests'] = guests
        if amenities:
            filters_search['amenities'] = amenities
        data_results = await mediator.send(
            SearchAccommodationsQuery(**filters_search
            )
        )

        return {
            "user_session": str(ses),
            "page": data_results.page,
            'page_size': data_results.page_size,
            'total': data_results.total,
            "result": [
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
                            amenities=[
                                RoomAmenityOut(name=a.name, icon=a.icon)
                                for a in rt.amenities
                            ],
                        )
                        for rt in r.available_room_types
                    ],
                )
                for r in data_results.items
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# NUEVOS ENDPOINTS: Listado de hoteles, disponibilidad por hotel y ciudades
# ============================================================================

class HotelSummaryOut(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class HotelAvailabilityOut(BaseModel):
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
    available_room_types: List[RoomTypeAvailabilityOut]

    model_config = ConfigDict(from_attributes=True)


class CityInfoOut(BaseModel):
    """Información de una ciudad con hoteles"""
    city: str
    country_id: UUID
    hotel_count: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/hotels", response_model=List[HotelSummaryOut])
async def list_hotels(
    city: Optional[str] = Query(None, description="Filtrar por ciudad"),
    country_id: Optional[UUID] = Query(None, description="Filtrar por país (UUID)"),
    min_stars: Optional[int] = Query(None, ge=1, le=5, description="Estrellas mínimas"),
    max_stars: Optional[int] = Query(None, ge=1, le=5, description="Estrellas máximas"),
    min_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="Rating mínimo"),
    include_inactive: bool = Query(False, description="Incluir hoteles inactivos"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    mediator: Mediator = Depends(get_mediator),
):
    """
    Lista todos los hoteles con filtros opcionales.

    Permite filtrar por ciudad, país, estrellas y rating.
    """
    try:
        results = await mediator.send(
            ListHotelsQuery(
                city=city,
                country_id=country_id,
                min_stars=min_stars,
                max_stars=max_stars,
                min_rating=min_rating,
                active_only=not include_inactive,
                limit=limit,
                offset=offset,
            )
        )
        return [
            HotelSummaryOut(
                id=h.id,
                name=h.name,
                description=h.description,
                address=h.address,
                city=h.city,
                stars=h.stars,
                rating=h.rating,
                total_reviews=h.total_reviews,
                active=h.active,
            )
            for h in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hotels/{hotel_id}/availability", response_model=HotelAvailabilityOut)
async def get_hotel_availability(
    hotel_id: UUID,
    check_in: date = Query(..., description="Fecha de check-in (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Fecha de check-out (YYYY-MM-DD)"),
    guests: int = Query(1, ge=1, description="Número de huéspedes"),
    mediator: Mediator = Depends(get_mediator),
):
    """
    Verifica disponibilidad de un hotel específico por fechas.

    Retorna las habitaciones disponibles con precios para el rango de fechas solicitado.
    """
    try:
        result = await mediator.send(
            GetHotelAvailabilityQuery(
                hotel_id=hotel_id,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
            )
        )
        return HotelAvailabilityOut(
            hotel_id=result.hotel_id,
            hotel_name=result.hotel_name,
            description=result.description,
            city=result.city,
            stars=result.stars,
            rating=result.rating,
            check_in_time=result.check_in_time,
            check_out_time=result.check_out_time,
            nights=result.nights,
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
                    amenities=[
                        RoomAmenityOut(name=a.name, icon=a.icon)
                        for a in rt.amenities
                    ],
                )
                for rt in result.available_room_types
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cities", response_model=List[CityInfoOut])
async def list_cities(
    country_id: Optional[UUID] = Query(None, description="Filtrar por país (UUID)"),
    mediator: Mediator = Depends(get_mediator),
):
    """
    Lista todas las ciudades que tienen hoteles activos.

    Opcionalmente filtra por país.
    """
    try:
        results = await mediator.send(ListCitiesQuery(country_id=country_id))
        return [
            CityInfoOut(
                city=c.city,
                country_id=c.country_id,
                hotel_count=c.hotel_count,
            )
            for c in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
