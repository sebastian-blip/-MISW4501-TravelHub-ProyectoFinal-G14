"""
Router para creación completa de hotel con owner, habitaciones,
amenidades e inventario de calendario (mayo 2026).
No requiere autenticación.
"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_session
from user_service.utils.security import hash_password
from domain.models.user import User
from domain.models.hotel import Hotel
from domain.models.room_type import RoomType
from domain.models.room_amenity import RoomAmenity
from domain.models.inventory_calendar import InventoryCalendar

router = APIRouter(prefix="/hotel-setup", tags=["Hotel Setup"])

VALID_AMENITIES = {
    "pool",
    "wifi",
    "breakfast_included",
    "parking",
    "room_service",
    "gym",
    "pet_friendly",
}


# ---------------------------------------------------------------------------
# Schemas de entrada
# ---------------------------------------------------------------------------
class OwnerCreateRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    country_id: Optional[UUID] = None


class RoomCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: Decimal
    max_capacity: int = 2
    bed_type: Optional[str] = None
    size_sqm: Optional[Decimal] = None
    total_units: int = 1
    amenities: List[str]

    @field_validator("amenities")
    @classmethod
    def validate_amenities(cls, v: List[str]) -> List[str]:
        if len(v) < 3:
            raise ValueError("Cada habitación debe tener al menos 3 amenidades")
        invalid = set(v) - VALID_AMENITIES
        if invalid:
            raise ValueError(f"Amenidades inválidas: {invalid}")
        return v


class HotelCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    city: str
    country_id: UUID
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    stars: int = 3
    check_in_time: time = time(15, 0)
    check_out_time: time = time(11, 0)
    pms_provider: Optional[str] = None
    pms_hotel_code: Optional[str] = None


class HotelSetupRequest(BaseModel):
    hotel: HotelCreateRequest
    owner: OwnerCreateRequest
    rooms: List[RoomCreateRequest]

    @field_validator("rooms")
    @classmethod
    def validate_rooms(cls, v: List[RoomCreateRequest]) -> List[RoomCreateRequest]:
        if len(v) != 3:
            raise ValueError("Debe enviar exactamente 3 habitaciones")
        return v


# ---------------------------------------------------------------------------
# Schemas de salida
# ---------------------------------------------------------------------------
class RoomSetupResponse(BaseModel):
    id: UUID
    name: str
    amenities: List[str]


class HotelSetupResponse(BaseModel):
    hotel_id: UUID
    owner_user_id: UUID
    rooms: List[RoomSetupResponse]
    message: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("", response_model=HotelSetupResponse, status_code=status.HTTP_201_CREATED)
async def create_full_hotel_setup(
    request: HotelSetupRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Crea un hotel completo con:
    - Usuario owner (rol hotel_admin)
    - Hotel vinculado al owner
    - 3 tipos de habitación con amenities
    - Inventario de calendario para mayo 2026 (10 unidades disponibles por día)
    """
    # Validar email único
    existing = await session.execute(select(User).where(User.email == request.owner.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email del owner ya está registrado")

    # Crear owner
    owner = User(
        email=request.owner.email,
        password_hash=hash_password(request.owner.password),
        first_name=request.owner.first_name,
        last_name=request.owner.last_name,
        phone=request.owner.phone,
        country_id=request.owner.country_id,
        user_type="hotel_admin",
        email_verified=True,
        active=True,
    )
    session.add(owner)
    await session.flush()

    # Crear hotel
    hotel_data = request.hotel
    hotel = Hotel(
        name=hotel_data.name,
        description=hotel_data.description,
        address=hotel_data.address,
        city=hotel_data.city,
        country_id=hotel_data.country_id,
        latitude=hotel_data.latitude,
        longitude=hotel_data.longitude,
        phone=hotel_data.phone,
        email=hotel_data.email,
        stars=hotel_data.stars,
        check_in_time=hotel_data.check_in_time,
        check_out_time=hotel_data.check_out_time,
        owner_user_id=owner.id,
        pms_provider=hotel_data.pms_provider,
        pms_hotel_code=hotel_data.pms_hotel_code,
        active=True,
    )
    session.add(hotel)
    await session.flush()

    created_rooms: List[RoomSetupResponse] = []

    for room_req in request.rooms:
        room = RoomType(
            hotel_id=hotel.id,
            name=room_req.name,
            description=room_req.description,
            base_price=room_req.base_price,
            max_capacity=room_req.max_capacity,
            bed_type=room_req.bed_type,
            size_sqm=room_req.size_sqm,
            total_units=room_req.total_units,
            active=True,
        )
        session.add(room)
        await session.flush()

        # Amenities
        for amenity_name in room_req.amenities:
            amenity = RoomAmenity(
                room_type_id=room.id,
                name=amenity_name,
            )
            session.add(amenity)

        # Inventario mayo 2026 (1 .. 31)
        for day in range(1, 32):
            inv = InventoryCalendar(
                room_type_id=room.id,
                date=date(2026, 5, day),
                available_units=10,
                price_per_night=room_req.base_price,
                currency_code="USD",
                minimum_stay=1,
            )
            session.add(inv)

        created_rooms.append(
            RoomSetupResponse(id=room.id, name=room.name, amenities=room_req.amenities)
        )

    await session.commit()

    return HotelSetupResponse(
        hotel_id=hotel.id,
        owner_user_id=owner.id,
        rooms=created_rooms,
        message="Hotel, owner, habitaciones, amenidades e inventario de mayo 2026 creados exitosamente",
    )
