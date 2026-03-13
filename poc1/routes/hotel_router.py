from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from mediatr import Mediator

from hotel_service.queries.get_hotels_query import GetHotelsQuery, HotelResponse
from hotel_service.availability.queries import SearchAvailableHotelsQuery, AvailableHotelResponse
import hotel_service.queries.get_hotels_handler  # registra el handler
import hotel_service.availability.queries  # registra handler del read model

router = APIRouter(prefix="/hotels", tags=["Hotels"])


def get_mediator() -> Mediator:
    return Mediator()


@router.get("", response_model=List[HotelResponse])
async def get_hotels(
    city: Optional[str] = None,
    mediator: Mediator = Depends(get_mediator),
):
    return await mediator.send(GetHotelsQuery(city=city))


@router.get("/search", response_model=List[AvailableHotelResponse])
async def search_available_hotels(
    city: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    mediator: Mediator = Depends(get_mediator),
):
    result = await mediator.send(
        SearchAvailableHotelsQuery(
            city=city,
            skip=skip,
            limit=limit
        )
    )
    return result.data  # ✅ Retorna solo la lista