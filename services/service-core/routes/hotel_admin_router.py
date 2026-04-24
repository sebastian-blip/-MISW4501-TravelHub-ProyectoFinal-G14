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
from accommodation_service.repository.room_type_repository import RoomTypeRepository
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


class RoomAmenityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    icon: Optional[str]


class RoomImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    alt_text: Optional[str]
    sort_order: int


class RoomTypeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hotel_id: UUID
    name: str
    description: Optional[str]
    base_price: Decimal
    max_capacity: int
    bed_type: Optional[str]
    size_sqm: Optional[Decimal]
    total_units: int
    active: bool
    created_at: datetime
    updated_at: datetime
    amenities: List[RoomAmenityResponse]
    images: List[RoomImageResponse]


class RoomTypeListResult(BaseModel):
    items: List[RoomTypeListResponse]
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
    Opcionalmente filtra por estado. Filtra automáticamente por el hotel_id
    asociado al usuario autenticado.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date no puede ser mayor que end_date")

    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Use: {VALID_STATUSES}",
        )

    hotel_id_str = current_user.get("hotel_id")
    if not hotel_id_str:
        raise HTTPException(status_code=403, detail="Usuario no tiene un hotel asociado")
    hotel_id = UUID(hotel_id_str)

    repo = ReservationRepository(session)
    rows = await repo.list_by_date_range_with_room_type(start_date, end_date, status, hotel_id)

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
    Filtra automáticamente por el hotel_id asociado al usuario autenticado.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date no puede ser mayor que end_date")

    hotel_id_str = current_user.get("hotel_id")
    if not hotel_id_str:
        raise HTTPException(status_code=403, detail="Usuario no tiene un hotel asociado")
    hotel_id = UUID(hotel_id_str)

    repo = InventoryCalendarRepository(session)
    items = await repo.list_available_by_date_range(start_date, end_date, room_type_id, hotel_id)

    return InventoryCalendarListResponse(
        items=[InventoryCalendarResponse.model_validate(ic) for ic in items],
        total=len(items),
    )


@router.get("/room-types", response_model=RoomTypeListResult)
async def list_room_types_by_hotel(
    include_inactive: bool = Query(False, description="Incluir tipos de habitación inactivos"),
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Lista los tipos de habitación disponibles para el hotel asociado
    al usuario autenticado, incluyendo amenities e imágenes asociadas.
    """
    hotel_id_str = current_user.get("hotel_id")
    if not hotel_id_str:
        raise HTTPException(status_code=403, detail="Usuario no tiene un hotel asociado")
    hotel_id = UUID(hotel_id_str)

    repo = RoomTypeRepository(session)
    rows = await repo.list_by_hotel_id(hotel_id, active_only=not include_inactive)

    items = []
    for row in rows:
        rt = row.room_type
        items.append(
            RoomTypeListResponse(
                id=rt.id,
                hotel_id=rt.hotel_id,
                name=rt.name,
                description=rt.description,
                base_price=rt.base_price,
                max_capacity=rt.max_capacity,
                bed_type=rt.bed_type,
                size_sqm=rt.size_sqm,
                total_units=rt.total_units,
                active=rt.active,
                created_at=rt.created_at,
                updated_at=rt.updated_at,
                amenities=[
                    RoomAmenityResponse(id=a.id, name=a.name, icon=a.icon)
                    for a in row.amenities
                ],
                images=[
                    RoomImageResponse(id=i.id, url=i.url, alt_text=i.alt_text, sort_order=i.sort_order)
                    for i in row.images
                ],
            )
        )

    return RoomTypeListResult(items=items, total=len(items))
