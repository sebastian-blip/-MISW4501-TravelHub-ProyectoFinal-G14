from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import date

from sqlalchemy import select, desc, or_, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from domain.models.reservation import Reservation
from domain.models.room_type import RoomType


VALID_STATUSES = {"pending", "confirmed", "cancelled", "completed"}


class ReservationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _with_relations(self, statement):
        return statement.options(
            selectinload(Reservation.user),
            selectinload(Reservation.reservation_guests),
        )

    async def get_by_id(self, reservation_id: UUID) -> Optional[Reservation]:
        statement = self._with_relations(
            select(Reservation).where(Reservation.id == reservation_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_confirmation_code(self, code: str) -> Optional[Reservation]:
        statement = self._with_relations(
            select(Reservation).where(Reservation.confirmation_code == code)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[Reservation]:
        statement = self._with_relations(
            select(Reservation)
            .where(Reservation.user_id == user_id)
            .order_by(desc(Reservation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_by_user_or_guest(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[Reservation]:
        statement = self._with_relations(
            select(Reservation)
            .where(or_(Reservation.user_id == user_id, Reservation.user_guest_id == user_id))
            .order_by(desc(Reservation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_activated_by_user_or_guest(self, user_id: UUID) -> List[Reservation]:
        statement = self._with_relations(
            select(Reservation)
            .where(
                or_(
                    Reservation.user_id == user_id,
                    Reservation.user_guest_id == user_id
                )
            )
            .where(Reservation.status.in_(["confirmed", "Confirmed", "Pending", "pending"]))
            .order_by(desc(Reservation.created_at))
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_all(self, limit: int = 10, offset: int = 0) -> List[Reservation]:
        statement = self._with_relations(
            select(Reservation)
            .order_by(desc(Reservation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(
        self,
        hotel_id: UUID,
        room_type_id: UUID,
        check_in: date,
        check_out: date,
        guests: int,
        base_price: Decimal,
        taxes: Decimal,
        discounts: Decimal,
        total_price: Decimal,
        currency_code: str = "USD",
        cart_id: Optional[UUID] = None,
        cancellation_policy: Optional[str] = None,
        special_requests: Optional[str] = None,
        confirmation_code: Optional[str] = None,
        user_guest_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Reservation:
        reservation = Reservation(
            user_id=user_id,
            user_guest_id=user_guest_id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            cart_id=cart_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            base_price=base_price,
            taxes=taxes,
            discounts=discounts,
            total_price=total_price,
            currency_code=currency_code,
            cancellation_policy=cancellation_policy,
            special_requests=special_requests,
            confirmation_code=confirmation_code,
        )
        self.session.add(reservation)
        await self.session.flush()
        return reservation

    async def count_by_date_range(self, start_date: date, end_date: date) -> int:
        statement = (
            select(func.count(Reservation.id))
            .where(Reservation.check_in <= end_date)
            .where(Reservation.check_out >= start_date)
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_by_date_range_with_room_type(
        self,
        start_date: date,
        end_date: date,
        status: Optional[str] = None,
        hotel_id: Optional[UUID] = None,
    ) -> List[Tuple[Reservation, RoomType]]:
        filters = [
            Reservation.check_in <= end_date,
            Reservation.check_out >= start_date,
        ]
        if status:
            filters.append(Reservation.status == status)
        if hotel_id is not None:
            filters.append(Reservation.hotel_id == hotel_id)

        statement = (
            select(Reservation, RoomType)
            .join(RoomType, Reservation.room_type_id == RoomType.id)
            .where(and_(*filters))
            .order_by(Reservation.check_in)
        )
        result = await self.session.execute(statement)
        return result.all()

    async def update_status(self, reservation_id: UUID, status: str) -> Optional[Reservation]:
        if status not in VALID_STATUSES:
            raise ValueError(f"Status '{status}' inválido. Use: {VALID_STATUSES}")
        
        reservation = await self.get_by_id(reservation_id)
        if reservation:
            reservation.status = status
            from datetime import datetime
            reservation.updated_at = datetime.utcnow()
        return reservation
