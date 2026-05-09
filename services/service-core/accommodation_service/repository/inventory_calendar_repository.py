from datetime import date, datetime, timezone, timedelta
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

    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        room_type_id: Optional[UUID] = None,
        hotel_id: Optional[UUID] = None,
    ) -> List[InventoryCalendar]:
        """Lista todas las entradas del calendario (incluyendo sin disponibilidad)."""
        filters = [
            InventoryCalendar.date >= start_date,
            InventoryCalendar.date <= end_date,
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
                        RoomType.hotel_id == hotel_id,
                    )
                )
                .order_by(InventoryCalendar.date)
            )
            if room_type_id is not None:
                statement = statement.where(InventoryCalendar.room_type_id == room_type_id)

        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_id(self, inventory_id: UUID) -> Optional[InventoryCalendar]:
        result = await self.session.execute(
            select(InventoryCalendar).where(InventoryCalendar.id == inventory_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        inventory_id: UUID,
        available_units: Optional[int] = None,
        price_per_night: Optional["Decimal"] = None,
    ) -> Optional[InventoryCalendar]:
        item = await self.get_by_id(inventory_id)
        if not item:
            return None
        if available_units is not None:
            item.available_units = available_units
        if price_per_night is not None:
            item.price_per_night = price_per_night
        item.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def create_range(
        self,
        room_type_id: UUID,
        start_date: date,
        end_date: date,
        available_units: int,
        price_per_night: "Decimal",
        currency_code: str = "USD",
        minimum_stay: int = 1,
    ) -> Optional[List[InventoryCalendar]]:
        """
        Crea entradas de calendario para un rango de fechas.
        Retorna None si ya existe al menos una fecha en el rango.
        """
        # Verificar si ya existe alguna fecha en el rango
        check_stmt = select(InventoryCalendar).where(
            and_(
                InventoryCalendar.room_type_id == room_type_id,
                InventoryCalendar.date >= start_date,
                InventoryCalendar.date <= end_date,
            )
        )
        result = await self.session.execute(check_stmt)
        existing = result.scalars().first()
        if existing:
            return None

        items: List[InventoryCalendar] = []
        current = start_date
        delta = timedelta(days=1)

        while current <= end_date:
            new_item = InventoryCalendar(
                room_type_id=room_type_id,
                date=current,
                available_units=available_units,
                price_per_night=price_per_night,
                currency_code=currency_code,
                minimum_stay=minimum_stay,
            )
            self.session.add(new_item)
            items.append(new_item)
            current += delta

        await self.session.commit()
        for item in items:
            await self.session.refresh(item)
        return items
