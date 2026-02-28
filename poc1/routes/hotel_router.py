from typing import Optional, List
from fastapi import APIRouter, Depends
from mediatr import Mediator

from poc1.hotel_service.queries.get_hotels_query import GetHotelsQuery, HotelResponse
import poc1.hotel_service.queries.get_hotels_handler  # registra el handler

router = APIRouter(prefix="/hotels", tags=["Hotels"])


def get_mediator() -> Mediator:
    return Mediator()


@router.get("", response_model=List[HotelResponse])
async def get_hotels(
    city: Optional[str] = None,
    mediator: Mediator = Depends(get_mediator),
):
    return await mediator.send(GetHotelsQuery(city=city))