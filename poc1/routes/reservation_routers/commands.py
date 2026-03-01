from fastapi import APIRouter, Depends
from mediatr import Mediator
from poc1.hotel_service.commands.reservation_commands import CreateReservationCommand, ReservationCreatedResponse
import poc1.hotel_service.commands.create_reservation_handler
router = APIRouter(prefix="/reservations", tags=["Reservations"])

def get_mediator() -> Mediator:
    return Mediator()

@router.post("", response_model=ReservationCreatedResponse)
async def create_reservation(
    command: CreateReservationCommand,
    mediator: Mediator = Depends(get_mediator)
):
    return await mediator.send(command)