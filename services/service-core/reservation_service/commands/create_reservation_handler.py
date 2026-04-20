import uuid
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import UUID

from mediatr import Mediator
from infrastructure.database import async_session_maker
from reservation_service.commands.reservation_commands import (
    CreateReservationCommand,
    CreateReservationResponse,
    HotelInfo,
    RoomTypeInfo,
    PricingDetails,
)
from reservation_service.repository.reservation_repository import ReservationRepository
from domain.models.reservation_guest import ReservationGuest
from domain.models.payment import Payment
from domain.models.hotel import Hotel
from domain.models.room_type import RoomType
from sqlalchemy import select
from domain.models.inventory_calendar import InventoryCalendar


def generate_confirmation_code() -> str:
    """Genera un código de confirmación único."""
    return f"RES{uuid.uuid4().hex[:8].upper()}"


@Mediator.handler
async def handle_create_reservation(command: CreateReservationCommand) -> CreateReservationResponse:
    """
    Handler para crear una nueva reservación con guest principal y pago.
    """
    async with async_session_maker() as session:
        repo = ReservationRepository(session)
        
        # Generar código de confirmación
        confirmation_code = generate_confirmation_code()
        
        # Verificar que el código no exista (muy raro pero posible)
        while await repo.get_by_confirmation_code(confirmation_code):
            confirmation_code = generate_confirmation_code()
        
        # Obtener información del hotel y tipo de habitación
        hotel_result = await session.execute(
            select(Hotel).where(Hotel.id == command.hotel_id)
        )
        hotel = hotel_result.scalar_one_or_none()
        
        room_result = await session.execute(
            select(RoomType).where(RoomType.id == command.room_type_id)
        )
        room_type = room_result.scalar_one_or_none()
        
        # Calcular número de noches
        nights = (command.check_out - command.check_in).days
        if nights < 1:
            nights = 1
        
        # Calcular precio total si no viene calculado
        total = command.total_price
        if total == Decimal("0.00"):
            total = command.base_price + command.taxes - command.discounts
        
        # Calcular precio por noche
        price_per_night = total / nights if nights > 0 else total
        
        # Calcular noches para inventario
        nights_inventory = max(1, (command.check_out - command.check_in).days)
        dates = [command.check_in + timedelta(days=d) for d in range(nights_inventory)]
        
        # Verificar y descontar inventario noche por noche (con lock)
        for d in dates:
            inv_result = await session.execute(
                select(InventoryCalendar)
                .where(InventoryCalendar.room_type_id == command.room_type_id)
                .where(InventoryCalendar.date == d)
                .with_for_update()
            )
            inv = inv_result.scalar_one_or_none()
            if not inv or inv.available_units < 1:
                raise ValueError(f"No hay disponibilidad para la fecha {d}")
            inv.available_units -= 1
        
        # Crear la reservación
        reservation = await repo.create(
            user_id=command.user_id,
            user_guest_id=command.user_guest_id,
            hotel_id=command.hotel_id,
            room_type_id=command.room_type_id,
            check_in=command.check_in,
            check_out=command.check_out,
            guests=command.guests,
            base_price=command.base_price,
            taxes=command.taxes,
            discounts=command.discounts,
            total_price=total,
            currency_code=command.currency_code,
            cart_id=command.cart_id,
            cancellation_policy=command.cancellation_policy,
            special_requests=command.special_requests,
            confirmation_code=confirmation_code,
        )
        
        # Crear el guest principal (is_primary=True)
        primary_guest = ReservationGuest(
            reservation_id=reservation.id,
            first_name=command.primary_guest.first_name,
            last_name=command.primary_guest.last_name,
            document_type=command.primary_guest.document_type,
            document_number=command.primary_guest.document_number,
            nationality=command.primary_guest.nationality,
            is_primary=True,
        )
        session.add(primary_guest)
        
        # Crear el pago (usar provider_id fijo si no se proporciona)
        provider_id = UUID(command.payment.provider_id) if command.payment.provider_id else UUID("e1000000-0000-0000-0000-000000000001")
        payment = Payment(
            reservation_id=reservation.id,
            provider_id=provider_id,
            amount=Decimal(command.payment.amount),
            currency_code=command.payment.currency_code,
            status="pending",
            payment_token=command.payment.payment_token,
        )
        session.add(payment)
        
        await session.commit()
        await session.refresh(reservation)

    logging.info(f"[Reservation] Creada: {reservation.confirmation_code} para usuario {reservation.user_id}")

    # Construir respuesta enriquecida
    return CreateReservationResponse(
        id=reservation.id,
        user_id=reservation.user_id,
        confirmation_code=reservation.confirmation_code,
        status=reservation.status,
        message=f"Reservación creada exitosamente con código {confirmation_code}",
        hotel=HotelInfo(
            id=hotel.id if hotel else command.hotel_id,
            name=hotel.name if hotel else "Hotel",
            description=hotel.description if hotel else None,
            address=hotel.address if hotel else "",
            city=hotel.city if hotel else "",
            stars=hotel.stars if hotel else 3,
            rating=hotel.rating if hotel else None,
        ),
        room_type=RoomTypeInfo(
            id=room_type.id if room_type else command.room_type_id,
            name=room_type.name if room_type else "Habitación",
            description=room_type.description if room_type else None,
            max_capacity=room_type.max_capacity if room_type else command.guests,
            bed_type=room_type.bed_type if room_type else None,
            size_sqm=room_type.size_sqm if room_type else None,
        ),
        pricing=PricingDetails(
            nights=nights,
            guests=command.guests,
            price_per_night=price_per_night.quantize(Decimal("0.01")),
            subtotal=(price_per_night * nights).quantize(Decimal("0.01")),
            taxes=command.taxes,
            discounts=command.discounts,
            total=total,
            currency_code=command.currency_code,
        ),
        check_in=reservation.check_in,
        check_out=reservation.check_out,
    )
