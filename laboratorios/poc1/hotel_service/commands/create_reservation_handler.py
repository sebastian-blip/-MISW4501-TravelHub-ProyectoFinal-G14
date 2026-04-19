from datetime import datetime, timezone
import uuid

from mediatr import Mediator

from hotel_service.commands.reservation_commands import CreateReservationCommand, ReservationCreatedResponse
from hotel_service.repository.reservation_repository import ReservationRepository
from hotel_service.events.reservation_events import ReservationCreatedEvent
from hotel_service.events.publisher import EventPublisher
from hotel_service.metrics import reservations_created_total


@Mediator.handler
async def handle_create_reservation(command: CreateReservationCommand):
    # simple validation
    if command.check_in >= command.check_out:
        raise ValueError("check_in must be before check_out")

    repo = ReservationRepository()

    # persist reservation (write model)
    reserva = await repo.create(
        hotel_id=command.hotel_id,
        room_id=command.room_id,
        user_id=command.user_id,
        check_in=command.check_in,
        check_out=command.check_out,
        total_price=command.total_price,
    )

    # build domain event
    def _ensure_aware(dt: datetime | None) -> datetime:
        if dt is None:
            return datetime.now(tz=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    correlation_id = str(uuid.uuid4())

    event = ReservationCreatedEvent(
        reservation_id=str(reserva.id),
        user_id=str(reserva.user_id),
        hotel_id=str(reserva.hotel_id),
        room_id=str(reserva.room_id),
        created_at=_ensure_aware(reserva.created_at),
        correlation_id=correlation_id,
    )

    # publish event (decoupled publisher)
    publisher = EventPublisher.get()
    # publisher is async-aware
    await publisher.publish(event)

    reservations_created_total.inc()
    return ReservationCreatedResponse(id=reserva.id, status="created")
