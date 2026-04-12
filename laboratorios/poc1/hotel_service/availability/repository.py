from typing import List, Optional, Tuple, Any, Union
from decimal import Decimal
from uuid import UUID
from tortoise.exceptions import IntegrityError

from domain.models.hotel_availability import HotelAvailability
from domain.models.hotel import Room


def _coerce_price(price: Optional[Decimal]) -> Optional[Decimal]:
    """Convierte price a Decimal si es necesario"""
    if price is None:
        return None
    return Decimal(str(price)) if not isinstance(price, Decimal) else price


class HotelAvailabilityRepository:

    async def get_available(
            self,
            city: Optional[str] = None,
            skip: int = 0,
            limit: int = 10,
    ) -> Tuple[List[HotelAvailability], int]:
        """
        Obtiene hoteles disponibles con paginación.

        Returns:
            Tuple con (lista de disponibilidades, total de resultados)
        """
        filters: dict[str, Any] = {"available": True}
        if city:
            filters["city"] = city

        # ✅ Obtener total sin paginación
        total = await HotelAvailability.filter(**filters).count()

        # ✅ Obtener datos paginados ordenados
        availabilities = await (
            HotelAvailability.filter(**filters)
            .order_by("hotel_name", "room_id")
            .offset(skip)
            .limit(limit)
            .all()
        )

        return availabilities, total

    async def get(
            self,
            hotel_id: Union[UUID, str],
            room_id: Union[UUID, str],
    ) -> Optional[HotelAvailability]:
        """Obtiene una disponibilidad específica por hotel_id y room_id"""
        return await HotelAvailability.get_or_none(
            hotel_id=str(hotel_id),
            room_id=str(room_id),
        )

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
        """
        Inserta o actualiza una disponibilidad de hotel.
        Maneja race conditions con IntegrityError.
        """
        hotel_id_str = str(hotel_id)
        room_id_str = str(room_id)
        coerced_price = _coerce_price(price_per_night)

        # ✅ Intentar obtener existente
        availability = await self.get(hotel_id_str, room_id_str)

        if availability:
            # ✅ Actualizar existente
            availability.hotel_name = hotel_name
            availability.city = city
            availability.available = available
            availability.room_type = room_type
            availability.price_per_night = coerced_price
            await availability.save()
            return availability

        try:
            # ✅ Crear nuevo
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
            # ✅ Race condition: alguien más lo creó mientras esperábamos
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

    async def mark_reserved(
            self,
            hotel_id: Union[UUID, str],
            room_id: Union[UUID, str],
    ) -> None:
        """Marca una habitación como reservada (no disponible)"""
        availability = await self.get(hotel_id, room_id)
        if availability and availability.available:
            availability.available = False
            await availability.save()

    async def mark_available(
            self,
            hotel_id: Union[UUID, str],
            room_id: Union[UUID, str],
    ) -> None:
        """Marca una habitación como disponible nuevamente"""
        availability = await self.get(hotel_id, room_id)
        if availability and not availability.available:
            availability.available = True
            await availability.save()

    async def seed_from_rooms(self, rooms: Optional[List[Room]] = None) -> None:
        """
        Sincroniza disponibilidades desde las habitaciones.
        Útil para seeding inicial o resincronización.
        """
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

    async def get_by_hotel_id(
            self,
            hotel_id: Union[UUID, str],
            skip: int = 0,
            limit: int = 10,
    ) -> Tuple[List[HotelAvailability], int]:
        """
        Obtiene todas las habitaciones de un hotel con paginación.
        """
        filters = {"hotel_id": str(hotel_id), "available": True}

        total = await HotelAvailability.filter(**filters).count()

        availabilities = await (
            HotelAvailability.filter(**filters)
            .order_by("room_id")
            .offset(skip)
            .limit(limit)
            .all()
        )

        return availabilities, total

    async def get_city_statistics(self) -> dict[str, int]:
        """
        Obtiene estadísticas de disponibilidad por ciudad.
        Útil para dashboards.
        """
        raw_sql = """
        SELECT city, COUNT(*) as count 
        FROM hotel_availability 
        WHERE available = TRUE
        GROUP BY city
        ORDER BY count DESC
        """
        # Usar conexión raw para queries complejas
        from tortoise import connections

        db = connections.get("default")
        result = await db.execute_query_dict(raw_sql)
        return {row["city"]: row["count"] for row in result}