from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from accommodation_service.queries.accommodation_queries import (
    AccommodationSearchResult,
    RoomTypeAvailability,
    RoomAmenityInfo,
    ListHotelsResult
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
            amenities: Optional[List[str]] = None,
            price_min: Optional[float] = None,
            price_max: Optional[float] = None,
            min_stars: Optional[int] = None,
            page: int = 1,
            page_size: int = 20,
    ) -> ListHotelsResult:

        nights = (check_out - check_in).days

        filters = [
            "LOWER(h.city) = LOWER(:city)",
            "h.active = true",
        ]
        if min_stars:
            filters.append("h.stars >= :min_stars")
        where_clause = "\n  AND ".join(filters)

        having_clauses = [
            "COUNT(ic.date) = :nights",
            ":nights >= MAX(ic.minimum_stay)"
        ]
        if price_min is not None:
            having_clauses.append("SUM(ic.price_per_night) >= :price_min")
        if price_max is not None:
            having_clauses.append("SUM(ic.price_per_night) <= :price_max")

        # Amenities subquery para ambos queries
        if amenities:
            amenities_subquery = """
                AND (
                    SELECT COUNT(DISTINCT ra.name)
                    FROM room_amenities ra
                    WHERE ra.room_type_id = rt.id
                      AND ra.name = ANY(:amenities)
                ) = :num_amenities
            """
        else:
            amenities_subquery = ""

        hotels_sql = text(f"""
            SELECT h.id
            FROM hotels h
            WHERE
              LOWER(h.city) = LOWER(:city)
              AND h.active = true
              {"AND h.stars >= :min_stars" if min_stars else ""}
              AND EXISTS (
                SELECT 1 FROM room_types rt
                WHERE rt.hotel_id = h.id
                  AND rt.active = true
                  AND rt.max_capacity >= :guests
                  AND EXISTS (
                    SELECT 1 FROM inventory_calendar ic
                    WHERE ic.room_type_id = rt.id
                      AND ic.date >= :check_in
                      AND ic.date < :check_out
                      AND ic.available_units > 0
                  )
                  {amenities_subquery}
              )
            ORDER BY h.rating DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """)
        params = {
            "nights": nights,
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        if price_min is not None:
            params["price_min"] = price_min
        if price_max is not None:
            params["price_max"] = price_max
        if min_stars:
            params["min_stars"] = min_stars
        if amenities:
            params["amenities"] = amenities
            params["num_amenities"] = len(amenities)

        result = await self.session.execute(hotels_sql, params)
        hotel_ids = [row["id"] for row in result.mappings().all()]

        items = []
        if hotel_ids:
            placeholders = ", ".join([f":hotel_id_{i}" for i in range(len(hotel_ids))])
            hotel_id_params = {f"hotel_id_{i}": str(hid) for i, hid in enumerate(hotel_ids)}
            all_params = {**params, **hotel_id_params}

            having_sql = "HAVING " + " AND ".join(having_clauses) if having_clauses else ""

            details_sql = text(f"""
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
                WHERE h.id IN ({placeholders})
                {amenities_subquery}
                GROUP BY
                    h.id, h.name, h.description, h.address, h.city,
                    h.stars, h.rating, h.check_in_time, h.check_out_time,
                    rt.id, rt.name, rt.description, rt.max_capacity,
                    rt.bed_type, rt.size_sqm, ic.currency_code
                {having_sql}
                ORDER BY h.rating DESC NULLS LAST, total_price ASC
            """)

            result_details = await self.session.execute(details_sql, all_params)
            rows = result_details.mappings().all()

            # OBTENER AMENITIES para cada room_type
            room_type_ids = [str(row["room_type_id"]) for row in rows]
            amenities_map = {}
            if room_type_ids:
                amenities_sql = text(
                    """
                    SELECT room_type_id,
                           name,
                           icon
                    FROM room_amenities
                    WHERE room_type_id = ANY (:room_type_ids)
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
            items = self._build_results(rows, amenities_map)
        else:
            items = []

        total = await self.search_count(params.copy(), where_clause, having_clauses.copy(), amenities)

        result_search = ListHotelsResult(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
        return result_search

    async def search_count(self, params: dict, where_clause, having_clauses, amenities) -> int:
        # Prepara filtro amenities igual que en el query de search
        if amenities:
            amenities_subquery = """
                AND (
                    SELECT COUNT(DISTINCT ra.name)
                    FROM room_amenities ra
                    WHERE ra.room_type_id = rt.id
                      AND ra.name = ANY(:amenities)
                ) = :num_amenities
            """
            params["amenities"] = amenities
            params["num_amenities"] = len(amenities)
        else:
            amenities_subquery = ""

        having_sql = "HAVING " + " AND ".join(having_clauses) if having_clauses else ""

        count_sql = text(f"""
            SELECT COUNT(DISTINCT hotel_id) AS total
            FROM (
                SELECT h.id AS hotel_id
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
                WHERE {where_clause}
                {amenities_subquery}
                GROUP BY h.id, rt.id
                {having_sql}
            ) AS subq
        """)

        count_result = await self.session.execute(count_sql, params)
        total = count_result.scalar_one()
        return total

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
