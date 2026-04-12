from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from accommodation_service.queries.accommodation_queries import (
    HotelSummary,
    HotelAvailabilityResult,
    RoomTypeAvailability,
    RoomAmenityInfo,
    CityInfo,
)


class HotelListingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_hotels(
        self,
        city: Optional[str] = None,
        country_id: Optional[UUID] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        min_rating: Optional[Decimal] = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[HotelSummary]:
        """Lista todos los hoteles con filtros opcionales"""
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if active_only:
            conditions.append("h.active = true")
        
        if city:
            conditions.append("LOWER(h.city) = LOWER(:city)")
            params["city"] = city
        
        if country_id:
            conditions.append("h.country_id = :country_id")
            params["country_id"] = country_id
        
        if min_stars is not None:
            conditions.append("h.stars >= :min_stars")
            params["min_stars"] = min_stars
        
        if max_stars is not None:
            conditions.append("h.stars <= :max_stars")
            params["max_stars"] = max_stars
        
        if min_rating is not None:
            conditions.append("h.rating >= :min_rating")
            params["min_rating"] = min_rating
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        sql = text(f"""
            SELECT
                h.id,
                h.name,
                h.description,
                h.address,
                h.city,
                h.stars,
                h.rating,
                h.total_reviews,
                h.active
            FROM hotels h
            {where_clause}
            ORDER BY h.rating DESC NULLS LAST, h.name ASC
            LIMIT :limit
            OFFSET :offset
        """)
        
        result = await self.session.execute(sql, params)
        rows = result.mappings().all()
        
        return [
            HotelSummary(
                id=UUID(str(row["id"])),
                name=row["name"],
                description=row["description"],
                address=row["address"],
                city=row["city"],
                stars=row["stars"],
                rating=Decimal(str(row["rating"])) if row["rating"] else None,
                total_reviews=row["total_reviews"],
                active=row["active"],
            )
            for row in rows
        ]

    async def get_hotel_availability(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int,
    ) -> Optional[HotelAvailabilityResult]:
        """Obtiene disponibilidad de un hotel específico"""
        nights = (check_out - check_in).days
        
        # Primero verificar que el hotel existe
        hotel_sql = text("""
            SELECT
                h.id,
                h.name,
                h.description,
                h.city,
                h.stars,
                h.rating,
                h.check_in_time,
                h.check_out_time
            FROM hotels h
            WHERE h.id = :hotel_id AND h.active = true
        """)
        
        hotel_result = await self.session.execute(hotel_sql, {"hotel_id": hotel_id})
        hotel_row = hotel_result.mappings().first()
        
        if not hotel_row:
            return None
        
        # Buscar disponibilidad de habitaciones
        availability_sql = text("""
            SELECT
                rt.id AS room_type_id,
                rt.name AS room_type_name,
                rt.description AS room_type_description,
                rt.max_capacity,
                rt.bed_type,
                rt.size_sqm,
                ic.currency_code,
                SUM(ic.price_per_night) AS total_price,
                ROUND(SUM(ic.price_per_night) / :nights, 2) AS price_per_night,
                MAX(ic.minimum_stay) AS minimum_stay
            FROM room_types rt
            JOIN inventory_calendar ic
                ON ic.room_type_id = rt.id
                AND ic.date >= :check_in
                AND ic.date < :check_out
                AND ic.available_units > 0
            WHERE rt.hotel_id = :hotel_id
              AND rt.active = true
              AND rt.max_capacity >= :guests
            GROUP BY
                rt.id, rt.name, rt.description, rt.max_capacity,
                rt.bed_type, rt.size_sqm, ic.currency_code
            HAVING
                COUNT(ic.date) = :nights
                AND :nights >= MAX(ic.minimum_stay)
            ORDER BY total_price ASC
        """)
        
        availability_result = await self.session.execute(
            availability_sql,
            {
                "hotel_id": hotel_id,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "nights": nights,
            }
        )
        
        room_rows = availability_result.mappings().all()
        
        # Obtener amenities para cada room_type
        room_type_ids = [str(row["room_type_id"]) for row in room_rows]
        amenities_map = {}
        
        if room_type_ids:
            amenities_sql = text(
                """
                SELECT 
                    room_type_id,
                    name,
                    icon
                FROM room_amenities
                WHERE room_type_id = ANY(:room_type_ids)
                ORDER BY name
            """
            )
            amenities_result = await self.session.execute(
                amenities_sql, {"room_type_ids": room_type_ids}
            )
            
            for amenity_row in amenities_result.mappings().all():
                rt_id = str(amenity_row["room_type_id"])
                if rt_id not in amenities_map:
                    amenities_map[rt_id] = []
                amenities_map[rt_id].append(
                    RoomAmenityInfo(
                        name=amenity_row["name"],
                        icon=amenity_row["icon"],
                    )
                )
        
        available_room_types = [
            RoomTypeAvailability(
                id=UUID(str(row["room_type_id"])),
                name=row["room_type_name"],
                description=row["room_type_description"],
                max_capacity=row["max_capacity"],
                bed_type=row["bed_type"],
                size_sqm=Decimal(str(row["size_sqm"])) if row["size_sqm"] else None,
                price_per_night=Decimal(str(row["price_per_night"])),
                total_price=Decimal(str(row["total_price"])),
                currency_code=row["currency_code"],
                minimum_stay=row["minimum_stay"],
                amenities=amenities_map.get(str(row["room_type_id"]), []),
            )
            for row in room_rows
        ]
        
        return HotelAvailabilityResult(
            hotel_id=UUID(str(hotel_row["id"])),
            hotel_name=hotel_row["name"],
            description=hotel_row["description"],
            city=hotel_row["city"],
            stars=hotel_row["stars"],
            rating=Decimal(str(hotel_row["rating"])) if hotel_row["rating"] else None,
            check_in_time=str(hotel_row["check_in_time"]),
            check_out_time=str(hotel_row["check_out_time"]),
            nights=nights,
            available_room_types=available_room_types,
        )

    async def list_cities(
        self,
        country_id: Optional[UUID] = None,
    ) -> List[CityInfo]:
        """Lista ciudades con hoteles activos"""
        
        conditions = ["h.active = true"]
        params = {}
        
        if country_id:
            conditions.append("h.country_id = :country_id")
            params["country_id"] = country_id
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        sql = text(f"""
            SELECT
                h.city,
                h.country_id,
                COUNT(DISTINCT h.id) AS hotel_count
            FROM hotels h
            {where_clause}
            GROUP BY h.city, h.country_id
            ORDER BY hotel_count DESC, h.city ASC
        """)
        
        result = await self.session.execute(sql, params)
        rows = result.mappings().all()
        
        return [
            CityInfo(
                city=row["city"],
                country_id=UUID(str(row["country_id"])),
                hotel_count=row["hotel_count"],
            )
            for row in rows
        ]
