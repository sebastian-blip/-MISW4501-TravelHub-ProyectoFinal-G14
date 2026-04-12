from datetime import date
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from accommodation_service.queries.accommodation_queries import (
    AccommodationSearchResult,
    RoomTypeAvailability,
    RoomAmenityInfo,
)


class AccommodationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        city: str,
        check_in: date,
        check_out: date,
        guests: int,
    ) -> List[AccommodationSearchResult]:
        nights = (check_out - check_in).days

        # Query principal para buscar disponibilidad
        sql = text(
            """
            SELECT
                h.id            AS hotel_id,
                h.name          AS hotel_name,
                h.description   AS hotel_description,
                h.address,
                h.city,
                h.stars,
                h.rating,
                h.check_in_time,
                h.check_out_time,
                rt.id           AS room_type_id,
                rt.name         AS room_type_name,
                rt.description  AS room_type_description,
                rt.max_capacity,
                rt.bed_type,
                rt.size_sqm,
                ic.currency_code,
                SUM(ic.price_per_night)          AS total_price,
                ROUND(SUM(ic.price_per_night) / :nights, 2) AS price_per_night,
                MAX(ic.minimum_stay)             AS minimum_stay
            FROM hotels h
            JOIN room_types rt
                ON rt.hotel_id = h.id
                AND rt.active = true
                AND rt.max_capacity >= :guests
            JOIN inventory_calendar ic
                ON ic.room_type_id = rt.id
                AND ic.date >= :check_in
                AND ic.date < :check_out
                AND ic.available_units > 0
            WHERE LOWER(h.city) = LOWER(:city)
              AND h.active = true
            GROUP BY
                h.id, h.name, h.description, h.address, h.city,
                h.stars, h.rating, h.check_in_time, h.check_out_time,
                rt.id, rt.name, rt.description, rt.max_capacity,
                rt.bed_type, rt.size_sqm, ic.currency_code
            HAVING
                COUNT(ic.date) = :nights
                AND :nights >= MAX(ic.minimum_stay)
            ORDER BY h.rating DESC NULLS LAST, total_price ASC
        """
        )

        result = await self.session.execute(
            sql,
            {
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "city": city,
                "nights": nights,
            },
        )

        rows = result.mappings().all()

        # Obtener amenities para cada room_type
        room_type_ids = [str(row["room_type_id"]) for row in rows]
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

        return self._build_results(rows, amenities_map)

    def _build_results(self, rows: list, amenities_map: dict) -> List[AccommodationSearchResult]:
        hotels: dict[str, AccommodationSearchResult] = {}

        for row in rows:
            hotel_id = str(row["hotel_id"])
            room_type_id = str(row["room_type_id"])

            if hotel_id not in hotels:
                hotels[hotel_id] = AccommodationSearchResult(
                    hotel_id=UUID(hotel_id),
                    hotel_name=row["hotel_name"],
                    description=row["hotel_description"],
                    address=row["address"],
                    city=row["city"],
                    stars=row["stars"],
                    rating=Decimal(str(row["rating"])) if row["rating"] else None,
                    check_in_time=str(row["check_in_time"]),
                    check_out_time=str(row["check_out_time"]),
                )

            hotels[hotel_id].available_room_types.append(
                RoomTypeAvailability(
                    id=UUID(room_type_id),
                    name=row["room_type_name"],
                    description=row["room_type_description"],
                    max_capacity=row["max_capacity"],
                    bed_type=row["bed_type"],
                    size_sqm=Decimal(str(row["size_sqm"])) if row["size_sqm"] else None,
                    price_per_night=Decimal(str(row["price_per_night"])),
                    total_price=Decimal(str(row["total_price"])),
                    currency_code=row["currency_code"],
                    minimum_stay=row["minimum_stay"],
                    amenities=amenities_map.get(room_type_id, []),
                )
            )

        return list(hotels.values())
