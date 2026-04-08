import uuid
import logging
from datetime import datetime
from decimal import Decimal

from mediatr import Mediator
from infrastructure.database import async_session_maker
from reservation_service.commands.reservation_commands import (
    CreateReservationCommand,
    CreateReservationResponse,
)
from reservation_service.repository.reservation_repository import ReservationRepository


def generate_confirmation_code() -> str:
    """Genera un código de confirmación único."""
    return f"RES{uuid.uuid4().hex[:8].upper()}"


@Mediator.handler
async def handle_create_reservation(command: CreateReservationCommand) -> CreateReservationResponse:
    """
    Handler para crear una nueva reservación.
    """
    async with async_session_maker() as session:
        repo = ReservationRepository(session)
        
        # Generar código de confirmación
        confirmation_code = generate_confirmation_code()
        
        # Verificar que el código no exista (muy raro pero posible)
        while await repo.get_by_confirmation_code(confirmation_code):
            confirmation_code = generate_confirmation_code()
        
        # Calcular precio total si no viene calculado
        total = command.total_price
        if total == Decimal("0.00"):
            total = command.base_price + command.taxes - command.discounts
        
        # Crear la reservación
        reservation = await repo.create(
            user_id=command.user_id,
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

    logging.info(f"[Reservation] Creada: {reservation.confirmation_code} para usuario {reservation.user_id}")

    return CreateReservationResponse(
        id=reservation.id,
        user_id=reservation.user_id,
        hotel_id=reservation.hotel_id,
        confirmation_code=reservation.confirmation_code,
        status=reservation.status,
        total_price=reservation.total_price,
        currency_code=reservation.currency_code,
        message=f"Reservación creada exitosamente con código {confirmation_code}",
    )
