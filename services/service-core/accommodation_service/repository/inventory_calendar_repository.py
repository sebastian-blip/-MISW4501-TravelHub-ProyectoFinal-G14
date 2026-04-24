from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.inventory_calendar import InventoryCalendar
from domain.models.room_type import RoomType


class InventoryCalendarRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_available_by_date_range(
        self,
        start_date: date,
        end_date: date,
        room_type_id: Optional[UUID] = None,
        hotel_id: Optional[UUID] = None,
    ) -> List[InventoryCalendar]:
        filters = [
            InventoryCalendar.date >= start_date,
            InventoryCalendar.date <= end_date,
            InventoryCalendar.available_units > 0,
        ]
        if room_type_id is not None:
            filters.append(InventoryCalendar.room_type_id == room_type_id)

        statement = (
            select(InventoryCalendar)
            .where(and_(*filters))
            .order_by(InventoryCalendar.date)
        )

        if hotel_id is not None:
            statement = (
                select(InventoryCalendar)
                .join(RoomType, InventoryCalendar.room_type_id == RoomType.id)
                .where(
                    and_(
                        InventoryCalendar.date >= start_date,
                        InventoryCalendar.date <= end_date,
                        InventoryCalendar.available_units > 0,
                        RoomType.hotel_id == hotel_id,
                    )
                )
                .order_by(InventoryCalendar.date)
            )
            if room_type_id is not None:
                statement = statement.where(InventoryCalendar.room_type_id == room_type_id)

        result = await self.session.execute(statement)
        return result.scalars().all()
