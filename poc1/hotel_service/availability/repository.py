from decimal import Decimal
from typing import Any, List, Optional, Union
from uuid import UUID

from tortoise.exceptions import IntegrityError

from domain.models.hotel import Room
from domain.models.hotel_availability import HotelAvailability


def _coerce_price(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (ValueError, ArithmeticError):
        return None


class HotelAvailabilityRepository:

    async def get_available(self, city: Optional[str] = None) -> List[HotelAvailability]:
        filters: dict[str, Any] = {"available": True}
        if city:
            filters["city"] = city
        return await HotelAvailability.filter(**filters).order_by("hotel_name", "room_id")

    async def get(self, hotel_id: Union[UUID, str], room_id: Union[UUID, str]) -> Optional[HotelAvailability]:
        return await HotelAvailability.get_or_none(hotel_id=str(hotel_id), room_id=str(room_id))

    async def upsert(
        self,
        hotel_id: Union[UUID, str],
        room_id: Union[UUID, str],
        hotel_name: str,
        city: str,
        available: bool = True,
        room_type: Optional[str] = None,
        price_per_night: Optional[Decimal] = None,
    ) -> HotelAvailability:
        hotel_id_str = str(hotel_id)
        room_id_str = str(room_id)
        availability = await self.get(hotel_id_str, room_id_str)
        coerced_price = _coerce_price(price_per_night)
        if availability:
            availability.hotel_name = hotel_name
            availability.city = city
            availability.available = available
            availability.room_type = room_type
            availability.price_per_night = coerced_price
            await availability.save()
            return availability

        try:
            return await HotelAvailability.create(
                id=room_id_str,
                hotel_id=hotel_id_str,
                room_id=room_id_str,
                hotel_name=hotel_name,
                city=city,
                available=available,
                room_type=room_type,
                price_per_night=coerced_price,
            )
        except IntegrityError:
            availability = await self.get(hotel_id_str, room_id_str)
            if availability:
                availability.available = available
                availability.hotel_name = hotel_name
                availability.city = city
                availability.room_type = room_type
                availability.price_per_night = coerced_price
                await availability.save()
                return availability
            raise

    async def mark_reserved(self, hotel_id: Union[UUID, str], room_id: Union[UUID, str]) -> None:
        availability = await self.get(hotel_id, room_id)
        if availability and availability.available:
            availability.available = False
            await availability.save()

    async def seed_from_rooms(self, rooms: Optional[List[Room]] = None) -> None:
        rooms = rooms or await Room.all().prefetch_related("hotel")
        for room in rooms:
            hotel = await room.hotel
            await self.upsert(
                hotel_id=hotel.id,
                room_id=room.id,
                hotel_name=hotel.name,
                city=hotel.city,
                available=room.available,
                room_type=room.room_type,
                price_per_night=room.price_per_night,
            )
