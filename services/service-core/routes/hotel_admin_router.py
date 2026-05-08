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
from mediatr import Mediator

from sqlalchemy import select

from infrastructure.database import get_session
from user_service.utils.security import get_current_user
from reservation_service.repository.reservation_repository import ReservationRepository, VALID_STATUSES
from accommodation_service.repository.inventory_calendar_repository import InventoryCalendarRepository
from accommodation_service.repository.room_type_repository import RoomTypeRepository
from domain.models.inventory_calendar import InventoryCalendar
from domain.models.hotel import Hotel
from reservation_service.queries import GetReservationByIdQuery
from user_service.queries.user_queries import GetUserByIdQuery

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
    user_name: Optional[str]
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
    mediator = Mediator()
    for reservation, room_type in rows:
        try:
            id_reservation = reservation.id
            query = GetReservationByIdQuery(reservation_id=id_reservation)
            result = await mediator.send_async(query)
            user_id = result.user_id
            user_data = await mediator.send(GetUserByIdQuery(user_id=user_id))
            user_name = f'{user_data.first_name} {user_data.last_name}'
        except Exception as e:
            user_name = None

        items.append(
            HotelAdminReservationResponse(
                id=reservation.id,
                hotel_id=reservation.hotel_id,
                user_name=user_name,
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


# ---------------------------------------------------------------------------
# Helper para obtener hotel_id a partir de owner_user_id (JWT)
# ---------------------------------------------------------------------------
async def _get_owned_hotel_id(session: AsyncSession, user_id: UUID) -> UUID:
    result = await session.execute(select(Hotel).where(Hotel.owner_user_id == user_id))
    hotel = result.scalar_one_or_none()
    if not hotel:
        raise HTTPException(status_code=403, detail="Usuario no tiene un hotel asociado")
    return hotel.id


# ---------------------------------------------------------------------------
# Schemas para nuevos endpoints de tarifas / inventario
# ---------------------------------------------------------------------------
class RoomSimpleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]


class RoomSimpleListResponse(BaseModel):
    items: List[RoomSimpleResponse]
    total: int


class UpdateInventoryRequest(BaseModel):
    available_units: int
    price_per_night: Decimal


class BulkInventoryRequest(BaseModel):
    room_type_id: UUID
    start_date: date
    end_date: date
    available_units: int
    price_per_night: Decimal
    currency_code: str = "USD"
    minimum_stay: int = 1

    @classmethod
    def model_validate(cls, obj):
        # Ensure end_date >= start_date
        if hasattr(obj, "end_date") and hasattr(obj, "start_date"):
            if obj.end_date < obj.start_date:
                raise ValueError("end_date no puede ser menor que start_date")
        return super().model_validate(obj)


# ---------------------------------------------------------------------------
# Nuevos endpoints (autorización por owner_user_id)
# ---------------------------------------------------------------------------
@router.get("/rooms/simple", response_model=RoomSimpleListResponse)
async def list_rooms_simple(
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Lista los tipos de habitación del hotel del usuario autenticado
    de forma simple (id, nombre, descripción).
    """
    user_id = UUID(current_user.get("user_id"))
    hotel_id = await _get_owned_hotel_id(session, user_id)

    repo = RoomTypeRepository(session)
    rooms = await repo.list_simple_by_hotel_id(hotel_id, active_only=True)

    return RoomSimpleListResponse(
        items=[RoomSimpleResponse.model_validate(r) for r in rooms],
        total=len(rooms),
    )


@router.get("/rooms/{room_id}", response_model=RoomTypeListResponse)
async def get_room_detail(
    room_id: UUID,
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Retorna la información completa de un tipo de habitación por ID,
    validando que pertenezca al hotel del usuario autenticado.
    """
    user_id = UUID(current_user.get("user_id"))
    hotel_id = await _get_owned_hotel_id(session, user_id)

    repo = RoomTypeRepository(session)
    room = await repo.get_by_id(room_id)
    if not room or room.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    # Cargar amenities e imágenes (reutilizamos list_by_hotel_id para obtener detalles)
    rows = await repo.list_by_hotel_id(hotel_id, active_only=False)
    row = next((r for r in rows if r.room_type.id == room_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    rt = row.room_type
    return RoomTypeListResponse(
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
        amenities=[RoomAmenityResponse(id=a.id, name=a.name, icon=a.icon) for a in row.amenities],
        images=[RoomImageResponse(id=i.id, url=i.url, alt_text=i.alt_text, sort_order=i.sort_order) for i in row.images],
    )


@router.get("/rooms/{room_id}/calendar", response_model=InventoryCalendarListResponse)
async def get_room_calendar(
    room_id: UUID,
    start_date: date = Query(..., description="Fecha de inicio del rango"),
    end_date: date = Query(..., description="Fecha de fin del rango"),
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Retorna todo el calendario de inventario de una habitación en un rango de fechas.
    Incluye fechas sin disponibilidad (available_units = 0).
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date no puede ser mayor que end_date")

    user_id = UUID(current_user.get("user_id"))
    hotel_id = await _get_owned_hotel_id(session, user_id)

    # Validar que el room pertenezca al hotel
    repo_room = RoomTypeRepository(session)
    room = await repo_room.get_by_id(room_id)
    if not room or room.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    repo = InventoryCalendarRepository(session)
    items = await repo.list_by_date_range(start_date, end_date, room_type_id=room_id, hotel_id=hotel_id)

    return InventoryCalendarListResponse(
        items=[InventoryCalendarResponse.model_validate(ic) for ic in items],
        total=len(items),
    )


@router.patch("/inventory/{inventory_id}", response_model=InventoryCalendarResponse)
async def update_inventory(
    inventory_id: UUID,
    body: UpdateInventoryRequest,
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Edita la disponibilidad (available_units) y tarifa (price_per_night)
    de una entrada de calendario de inventario.
    """
    user_id = UUID(current_user.get("user_id"))
    hotel_id = await _get_owned_hotel_id(session, user_id)

    repo = InventoryCalendarRepository(session)
    item = await repo.get_by_id(inventory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro de inventario no encontrado")

    # Validar que el room_type pertenezca al hotel del usuario
    repo_room = RoomTypeRepository(session)
    room = await repo_room.get_by_id(item.room_type_id)
    if not room or room.hotel_id != hotel_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para editar este registro")

    updated = await repo.update(
        inventory_id,
        available_units=body.available_units,
        price_per_night=body.price_per_night,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Registro de inventario no encontrado")

    return InventoryCalendarResponse.model_validate(updated)


@router.post("/inventory/bulk", response_model=InventoryCalendarListResponse)
async def create_bulk_inventory(
    body: BulkInventoryRequest,
    current_user: dict = Depends(require_hotel_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Crea o actualiza disponibilidad y tarifas para un rango de fechas
    de un tipo de habitación.
    """
    if body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="end_date no puede ser menor que start_date")

    user_id = UUID(current_user.get("user_id"))
    hotel_id = await _get_owned_hotel_id(session, user_id)

    # Validar que el room_type pertenezca al hotel del usuario
    repo_room = RoomTypeRepository(session)
    room = await repo_room.get_by_id(body.room_type_id)
    if not room or room.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    repo = InventoryCalendarRepository(session)
    items = await repo.create_range(
        room_type_id=body.room_type_id,
        start_date=body.start_date,
        end_date=body.end_date,
        available_units=body.available_units,
        price_per_night=body.price_per_night,
        currency_code=body.currency_code,
        minimum_stay=body.minimum_stay,
    )

    if items is None:
        raise HTTPException(
            status_code=409,
            detail="Ya existen registros de inventario en el rango de fechas indicado. Use PATCH para editarlos.",
        )

    return InventoryCalendarListResponse(
        items=[InventoryCalendarResponse.model_validate(ic) for ic in items],
        total=len(items),
    )
