from typing import List
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.room_type import RoomType
from domain.models.room_amenity import RoomAmenity
from domain.models.room_image import RoomImage


@dataclass
class RoomTypeWithDetails:
    room_type: RoomType
    amenities: List[RoomAmenity]
    images: List[RoomImage]


class RoomTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_hotel_id(
        self,
        hotel_id: UUID,
        active_only: bool = True,
    ) -> List[RoomTypeWithDetails]:
        """
        Lista los tipos de habitación de un hotel, incluyendo
        amenities e imágenes asociadas.
        """
        filters = [RoomType.hotel_id == hotel_id]
        if active_only:
            filters.append(RoomType.active.is_(True))

        stmt = select(RoomType).where(*filters).order_by(RoomType.name)
        result = await self.session.execute(stmt)
        room_types = result.scalars().all()

        if not room_types:
            return []

        room_type_ids = [rt.id for rt in room_types]

        # Cargar amenities
        amenity_stmt = select(RoomAmenity).where(RoomAmenity.room_type_id.in_(room_type_ids))
        amenity_result = await self.session.execute(amenity_stmt)
        amenities = amenity_result.scalars().all()

        amenities_by_rt: dict = {}
        for a in amenities:
            amenities_by_rt.setdefault(a.room_type_id, []).append(a)

        # Cargar imágenes
        image_stmt = (
            select(RoomImage)
            .where(RoomImage.room_type_id.in_(room_type_ids))
            .order_by(RoomImage.sort_order)
        )
        image_result = await self.session.execute(image_stmt)
        images = image_result.scalars().all()

        images_by_rt: dict = {}
        for i in images:
            images_by_rt.setdefault(i.room_type_id, []).append(i)

        return [
            RoomTypeWithDetails(
                room_type=rt,
                amenities=amenities_by_rt.get(rt.id, []),
                images=images_by_rt.get(rt.id, []),
            )
            for rt in room_types
        ]
