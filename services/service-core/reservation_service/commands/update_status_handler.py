import logging
from datetime import timedelta

from mediatr import Mediator
from sqlalchemy import select
from infrastructure.database import async_session_maker
from reservation_service.commands.reservation_commands import (
    UpdateReservationStatusCommand,
    UpdateReservationStatusResponse,
)
from reservation_service.repository.reservation_repository import ReservationRepository
from domain.models.inventory_calendar import InventoryCalendar


@Mediator.handler
async def handle_update_status(command: UpdateReservationStatusCommand) -> UpdateReservationStatusResponse:
    """
    Handler para actualizar el estado de una reservación.
    """
    async with async_session_maker() as session:
        repo = ReservationRepository(session)
        
        # Obtener reservación actual
        reservation = await repo.get_by_id(command.reservation_id)
        if not reservation:
            raise ValueError(f"Reservación '{command.reservation_id}' no encontrada")
        
        previous_status = reservation.status
        
        # Actualizar estado
        updated = await repo.update_status(command.reservation_id, command.status)
        if not updated:
            raise ValueError(f"No se pudo actualizar la reservación '{command.reservation_id}'")
        
        # Restaurar inventario si se cancela
        if command.status == "cancelled" and previous_status != "cancelled":
            nights = max(1, (reservation.check_out - reservation.check_in).days)
            dates = [reservation.check_in + timedelta(days=d) for d in range(nights)]
            for d in dates:
                inv_result = await session.execute(
                    select(InventoryCalendar)
                    .where(InventoryCalendar.room_type_id == reservation.room_type_id)
                    .where(InventoryCalendar.date == d)
                    .with_for_update()
                )
                inv = inv_result.scalar_one_or_none()
                if inv:
                    inv.available_units += 1
        
        await session.commit()

    logging.info(f"[Reservation] Estado actualizado: {command.reservation_id} | {previous_status} → {command.status}")

    return UpdateReservationStatusResponse(
        id=command.reservation_id,
        previous_status=previous_status,
        new_status=command.status,
        message=f"Estado actualizado de '{previous_status}' a '{command.status}'",
    )
