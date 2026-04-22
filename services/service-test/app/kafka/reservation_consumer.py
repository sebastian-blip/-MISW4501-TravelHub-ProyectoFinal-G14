"""
Consumer para eventos de validación de reservas desde service-core.
Simula con true/false y crea el registro en BD si es true.
"""
import asyncio
import json
import logging
import os
from uuid import uuid4, UUID
from datetime import date
from decimal import Decimal
from sqlmodel import Session, select, and_, or_
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.infrastructure.database import async_session_maker
from sqlalchemy import select
from app.models.models.reservation import Reservation
from app.models.models.inventory_calendar import InventoryCalendar
from app.models.models.room_type import RoomType
from sqlalchemy import func

TOPIC_RESERVATION_VALIDATE = "reservation-validate-requests"
TOPIC_RESERVATION_RESULTS = "reservation-validate-results"

SIMULATE_EXISTS = False

_consumer: AIOKafkaConsumer | None = None
_producer: AIOKafkaProducer | None = None
_task: asyncio.Task | None = None


async def start_reservation_consumer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = ""
):
    """Inicia el consumidor de reservas con soporte para SASL."""
    global _consumer, _producer, _task
    
    # Configuración base
    producer_config = {"bootstrap_servers": bootstrap_servers}
    consumer_config = {
        "bootstrap_servers": bootstrap_servers,
        "group_id": "service-test-reservation-group",
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
    }
    
    # Configuración SASL para AWS
    if use_ssl and username and password:
        sasl_config = {
            "sasl_mechanism": "SCRAM-SHA-256",
            "security_protocol": "SASL_PLAINTEXT",
            "sasl_plain_username": username,
            "sasl_plain_password": password,
        }
        
        producer_config.update(sasl_config)
        consumer_config.update(sasl_config)
    
    _producer = AIOKafkaProducer(**producer_config)
    await _producer.start()
    
    _consumer = AIOKafkaConsumer(
        TOPIC_RESERVATION_VALIDATE,
        **consumer_config
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(f"[service-test ReservationConsumer] escuchando topic={TOPIC_RESERVATION_VALIDATE}")


async def stop_reservation_consumer():
    global _consumer, _producer, _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    if _consumer:
        await _consumer.stop()
    if _producer:
        await _producer.stop()


async def _consume():
    try:
        async for msg in _consumer:
            payload = json.loads(msg.value.decode("utf-8"))
            await _handle_validate_request(payload)
    except asyncio.CancelledError:
        pass


async def _handle_validate_request(payload: dict):

    correlation_id = payload.get("correlation_id", "")
    user_id = payload.get("user_id", "")
    hotel_id = payload.get("hotel_id", "")
    room_type_id = payload.get("room_type_id", "")
    check_in = payload.get("check_in", "")
    check_out = payload.get("check_out", "")

    reply ={}
    try:
        async with async_session_maker() as session:

            # query = select(Reservation).where(and_(
            #     Reservation.user_id == user_id,
            #     Reservation.hotel_id == hotel_id,
            #     Reservation.room_type_id == room_type_id,
            #     Reservation.check_in == date.fromisoformat(check_in),
            #     Reservation.check_out == date.fromisoformat(check_out)
            # ))
            # resultado = await session.execute(query)  # ← await
            # reservations = resultado.scalars().all()

            check_in = date.fromisoformat(check_in)
            check_out = date.fromisoformat(check_out)

            nights = (check_out - check_in).days
            query = (
                select(
                    RoomType.id,  # <-- explícito
                    RoomType.name.label("room_type_name"),
                    func.min(InventoryCalendar.available_units).label("min_available"),
                    func.count(InventoryCalendar.date).label("nights_covered"),
                )
                .join(InventoryCalendar, InventoryCalendar.room_type_id == RoomType.id)
                .where(
                    InventoryCalendar.date >= check_in,
                    InventoryCalendar.date < check_out,
                    InventoryCalendar.available_units > 0,
                    InventoryCalendar.room_type_id == room_type_id,
                )
                .group_by(RoomType.id, RoomType.name)
                .having(func.count(InventoryCalendar.date) == nights)
            )

            result = await session.execute(query)
            row = result.first()

            if row is not None :

                ## agenda disponible
                reply = {
                    "correlation_id": correlation_id,
                    "exists": False,
                    "confirmation_code": "0",
                    "message": ""
                }
            else :

                ## sin agenda disponible
                reply = {
                    "correlation_id": correlation_id,
                    "exists": True,
                    "confirmation_code": "1",
                }


                
    except Exception as e:
            logging.error(f"[service-test] Error creando reserva: {e}")
            reply = {
                "correlation_id": correlation_id,
                "exists": False,
                "error": str(e),
                "message": "Error al crear reserva"
            }

    await _producer.send_and_wait(
        TOPIC_RESERVATION_RESULTS,
        json.dumps(reply).encode("utf-8")
    )
    logging.info(f"[service-test] Respuesta enviada: exists={reply.get('exists')}")
