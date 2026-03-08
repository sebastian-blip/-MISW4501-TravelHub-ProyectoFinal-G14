from fastapi import APIRouter, Depends
from mediatr import Mediator
from hotel_service.commands.reservation_commands import CreateReservationCommand, ReservationCreatedResponse
import hotel_service.commands.create_reservation_handler

router = APIRouter(prefix="/reservations", tags=["Reservations"])


def get_mediator() -> Mediator:
    return Mediator()


@router.post("", response_model=ReservationCreatedResponse)
async def create_reservation(
    command: CreateReservationCommand,
    mediator: Mediator = Depends(get_mediator),
):
    """Endpoint that uses the CreateReservation command (CQRS write side).

    The handler will validate, persist and publish ReservationCreated to Kafka.
    """
    return await mediator.send(command)
