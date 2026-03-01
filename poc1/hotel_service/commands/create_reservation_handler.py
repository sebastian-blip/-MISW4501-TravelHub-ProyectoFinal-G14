from mediatr import mediator
from poc1.hotel_service.commands.reservation_commands import CreateReservationCommand, ReservationCreatedResponse
from poc1.hotel_service.repository.reservation_repository import ReservationRepository

@mediator.handler
async def handle_create_reservation(command: CreateReservationCommand):
    repo = ReservationRepository()

    reserva = await repo.create(
        hotel_id=command.hotel_id,
        room_id=command.room_id,
        user_id=command.user_id,
        check_in=command.check_in,
        check_out=command.check_out,
    )
    return ReservationCreatedResponse(id=reserva.id, status="created")