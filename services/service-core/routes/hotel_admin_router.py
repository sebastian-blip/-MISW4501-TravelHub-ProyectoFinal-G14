"""
Router para administradores de hotel.
Endpoints protegidos con JWT y validación de rol hotel_admin/admin.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_session
from user_service.utils.security import get_current_user
from reservation_service.repository.reservation_repository import ReservationRepository, VALID_STATUSES
from accommodation_service.repository.inventory_calendar_repository import InventoryCalendarRepository
from domain.models.inventory_calendar import InventoryCalendar

router = APIRouter(prefix="/hotel-admin", tags=["Hotel Admin"])


class RoomTypeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    base_price: Decimal
    max_capacity: int
    bed_type: Optional[str]
    size_sqm: Optional[Decimal]


class HotelAdminReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hotel_id: UUID
    room_type_id: UUID
    cart_id: Optional[UUID]
    check_in: date
    check_out: date
    guests: int
    base_price: Decimal
    taxes: Decimal
    discounts: Decimal
    total_price: Decimal
    currency_code: str
    status: str
    cancellation_policy: Optional[str]
    special_requests: Optional[str]
    confirmation_code: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    room_type: RoomTypeDetailResponse


class HotelAdminReservationListResponse(BaseModel):
    items: List[HotelAdminReservationResponse]
    total: int


class InventoryCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_type_id: UUID
    date: date
    available_units: int
    price_per_night: float
    currency_code: str
    minimum_stay: int


class InventoryCalendarListResponse(BaseModel):
    items: List[InventoryCalendarResponse]
    total: int


# Dependencia local para validar rol de hotel_admin
def require_hotel_admin(current_user: dict = Depends(get_current_user)) -> dict:
    user_type = current_user.get("user_type")
    if user_type not in ("hotel_admin", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: se requiere rol de administrador de hotel",
        )
    return current_user


@router.get("/reservations", response_model=HotelAdminReservationListResponse)
async def get_reservations(
    start_date: date = Query(..., description="Fecha de inicio del rango"),
    end_date: date = Query(..., description="Fecha de fin del rango"),
    status: Optional[str] = Query(None, description="Filtrar por estado de la reserva"),
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Lista las reservas cuyo período de estadía se solapa con el rango
    de fechas indicado, incluyendo información de la habitación.
    Opcionalmente filtra por estado.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date no puede ser mayor que end_date")

    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Use: {VALID_STATUSES}",
        )

    repo = ReservationRepository(session)
    rows = await repo.list_by_date_range_with_room_type(start_date, end_date, status)

    items = []
    for reservation, room_type in rows:
        items.append(
            HotelAdminReservationResponse(
                id=reservation.id,
                hotel_id=reservation.hotel_id,
                room_type_id=reservation.room_type_id,
                cart_id=reservation.cart_id,
                check_in=reservation.check_in,
                check_out=reservation.check_out,
                guests=reservation.guests,
                base_price=reservation.base_price,
                taxes=reservation.taxes,
                discounts=reservation.discounts,
                total_price=reservation.total_price,
                currency_code=reservation.currency_code,
                status=reservation.status,
                cancellation_policy=reservation.cancellation_policy,
                special_requests=reservation.special_requests,
                confirmation_code=reservation.confirmation_code,
                created_at=reservation.created_at,
                updated_at=reservation.updated_at,
                room_type=RoomTypeDetailResponse(
                    id=room_type.id,
                    name=room_type.name,
                    description=room_type.description,
                    base_price=room_type.base_price,
                    max_capacity=room_type.max_capacity,
                    bed_type=room_type.bed_type,
                    size_sqm=room_type.size_sqm,
                ),
            )
        )

    return HotelAdminReservationListResponse(items=items, total=len(items))


@router.get("/inventory-calendar", response_model=InventoryCalendarListResponse)
async def list_inventory_calendar(
    start_date: date = Query(..., description="Fecha de inicio del rango"),
    end_date: date = Query(..., description="Fecha de fin del rango"),
    room_type_id: Optional[UUID] = Query(None, description="Filtrar por tipo de habitación"),
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Lista las entradas del calendario de inventario disponibles
    (available_units > 0) dentro del rango de fechas indicado.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date no puede ser mayor que end_date")

    repo = InventoryCalendarRepository(session)
    items = await repo.list_available_by_date_range(start_date, end_date, room_type_id)

    return InventoryCalendarListResponse(
        items=[InventoryCalendarResponse.model_validate(ic) for ic in items],
        total=len(items),
    )
