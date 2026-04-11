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

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.infrastructure.database import async_session_maker
from sqlalchemy import select
from app.models.models.reservation import Reservation

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
    """
    Maneja la solicitud de validación de service-core.
    SIMULA con true/false.
    """
    correlation_id = payload.get("correlation_id", "")
    user_id = payload.get("user_id", "")
    hotel_id = payload.get("hotel_id", "")
    room_type_id = payload.get("room_type_id", "")
    check_in = payload.get("check_in", "")
    check_out = payload.get("check_out", "")
    
    logging.info(f"[service-test] Validación recibida: correlation_id={correlation_id[:8]}...")
    logging.info(f"[service-test] SIMULATE_EXISTS={SIMULATE_EXISTS}")
    
    if SIMULATE_EXISTS:
        logging.info(f"[service-test] Simulando EXISTE → Creando reserva en BD...")
        
        try:
            async with async_session_maker() as session:
                reservation = Reservation(
                    id=uuid4(),
                    user_id=UUID(user_id),
                    hotel_id=UUID(hotel_id),
                    room_type_id=UUID(room_type_id),
                    check_in=date.fromisoformat(check_in),
                    check_out=date.fromisoformat(check_out),
                    guests=2,
                    base_price=Decimal("500.00"),
                    taxes=Decimal("50.00"),
                    discounts=Decimal("0.00"),
                    total_price=Decimal("550.00"),
                    currency_code="USD",
                    status="pending",
                    confirmation_code=f"RES{uuid4().hex[:8].upper()}"
                )
                
                session.add(reservation)
                await session.commit()
                
                logging.info(f"[service-test] Reserva creada: {reservation.confirmation_code}")
                
                reply = {
                    "correlation_id": correlation_id,
                    "exists": True,
                    "confirmation_code": reservation.confirmation_code,
                    "message": "Reserva existe (simulada)"
                }
                
        except Exception as e:
            logging.error(f"[service-test] Error creando reserva: {e}")
            reply = {
                "correlation_id": correlation_id,
                "exists": False,
                "error": str(e),
                "message": "Error al crear reserva"
            }
    else:
        logging.info(f"[service-test] Simulando NO EXISTE")
        reply = {
            "correlation_id": correlation_id,
            "exists": False,
            "message": "Reserva no existe (simulada)"
        }
    
    await _producer.send_and_wait(
        TOPIC_RESERVATION_RESULTS,
        json.dumps(reply).encode("utf-8")
    )
    logging.info(f"[service-test] Respuesta enviada: exists={reply.get('exists')}")
