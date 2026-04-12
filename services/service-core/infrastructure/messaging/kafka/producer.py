from __future__ import annotations

import json
import logging
import os
from aiokafka import AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"
TOPIC_STEP_EVENTS = "step-change-events"
TOPIC_RESERVATION_VALIDATE = "reservation-validate-requests"
TOPIC_AWS_TEST = "aws-test-messages"

_producer: AIOKafkaProducer | None = None


async def start_producer(
        bootstrap_servers: str,
        use_ssl: bool = False,
        username: str = "",
        password: str = ""
):
    """Inicia el productor de Kafka con soporte para SASL/SSL en AWS."""
    global _producer

    config = {
        "bootstrap_servers": bootstrap_servers,
    }


    config["sasl_mechanism"] = "SCRAM-SHA-256"
    config["security_protocol"] = "SASL_PLAINTEXT"
    config["sasl_plain_username"] = os.getenv("KAFKA_USERNAME")
    config["sasl_plain_password"] = os.getenv("KAFKA_PASSWORD")


    _producer = AIOKafkaProducer(**config)
    await _producer.start()
    logging.info(f"[service-core Producer] conectado a Kafka en {bootstrap_servers}")


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()


async def publish_user_check(email: str, correlation_id: str):
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")

    payload = json.dumps({"email": email, "correlation_id": correlation_id}).encode("utf-8")
    await _producer.send_and_wait(TOPIC_REQUESTS, payload)
    logging.info(f"[service-core Producer] pregunta enviada → email={email} correlation_id={correlation_id}")


async def publish_step_change(task_id: int, previous_step: int, new_step: int, history: list):
    """Publica un evento cuando cambia el paso de una tarea."""
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")

    payload = json.dumps({
        "event": "step_changed",
        "task_id": task_id,
        "previous_step": previous_step,
        "new_step": new_step,
        "history": history,
        "action_required": "query_users"
    }).encode("utf-8")

    await _producer.send_and_wait(TOPIC_STEP_EVENTS, payload)
    logging.info(f"[service-core Producer] evento de paso enviado → task_id={task_id}, step={new_step}")


async def publish_reservation_validate(
        user_id: str,
        hotel_id: str,
        room_type_id: str,
        check_in: str,
        check_out: str,
        correlation_id: str
):
    """Publica evento para validar si una reserva existe."""
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")

    payload = json.dumps({
        "event": "reservation_validate_request",
        "user_id": user_id,
        "hotel_id": hotel_id,
        "room_type_id": room_type_id,
        "check_in": check_in,
        "check_out": check_out,
        "correlation_id": correlation_id
    }).encode("utf-8")

    await _producer.send_and_wait(TOPIC_RESERVATION_VALIDATE, payload)
    logging.info(f"[service-core Producer] validación reserva enviada → correlation_id={correlation_id}")


async def publish_test_message(
        message: str,
        correlation_id: str,
        priority: str = "normal",
        metadata: dict = None,
        timestamp: str = None
):
    """Publica un mensaje de prueba para validar conectividad en AWS."""
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")

    import socket
    hostname = socket.gethostname()

    payload = json.dumps({
        "event": "aws_test_message",
        "message": message,
        "correlation_id": correlation_id,
        "priority": priority,
        "metadata": metadata or {},
        "timestamp": timestamp,
        "source": {
            "service": "service-core",
            "host": hostname,
            "port": 8000
        }
    }).encode("utf-8")

    await _producer.send_and_wait(TOPIC_AWS_TEST, payload)
    logging.info(
        f"[service-core Producer] mensaje de prueba AWS enviado → correlation_id={correlation_id}, priority={priority}"
    )
