"""
prueba_consumer.py — Consumer para mensajes de prueba desde service-core.
Recibe un mensaje, lo modifica y devuelve la respuesta.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

TOPIC_PRUEBA = "prueba-requests"
TOPIC_PRUEBA_RESULTS = "prueba-results"

_consumer: AIOKafkaConsumer | None = None
_producer: AIOKafkaProducer | None = None
_task: asyncio.Task | None = None


async def start_prueba_consumer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = ""
):
    global _consumer, _producer, _task

    kafka_local = os.getenv("KAFKA_LOCAL", "false").lower() == "true"

    producer_config = {"bootstrap_servers": bootstrap_servers}
    consumer_config = {
        "bootstrap_servers": bootstrap_servers,
        "group_id": "service-test-prueba-group",
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
    }

    if not kafka_local:
        sasl_config = {
            "sasl_mechanism": "SCRAM-SHA-256",
            "security_protocol": "SASL_PLAINTEXT",
            "sasl_plain_username": os.getenv("KAFKA_USERNAME", ""),
            "sasl_plain_password": os.getenv("KAFKA_PASSWORD", ""),
        }
        producer_config.update(sasl_config)
        consumer_config.update(sasl_config)
    else:
        plaintext_config = {"security_protocol": "PLAINTEXT"}
        producer_config.update(plaintext_config)
        consumer_config.update(plaintext_config)

    _producer = AIOKafkaProducer(**producer_config)
    await _producer.start()

    _consumer = AIOKafkaConsumer(TOPIC_PRUEBA, **consumer_config)
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(f"[service-test PruebaConsumer] escuchando topic={TOPIC_PRUEBA}")


async def stop_prueba_consumer():
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
            await _handle(payload)
    except asyncio.CancelledError:
        pass


async def _handle(payload: dict):
    correlation_id = payload.get("correlation_id", "")
    mensaje = payload.get("mensaje", "")
    metadata = payload.get("metadata", {})
    timestamp_sent = payload.get("timestamp", "")

    logging.info(f"[service-test PruebaConsumer] Recibido → mensaje='{mensaje}'")

    # Modificar el mensaje
    mensaje_modificado = f"{mensaje} [procesado por service-test @ {datetime.utcnow().strftime('%H:%M:%S')}]"

    reply = {
        "correlation_id": correlation_id,
        "mensaje_original": mensaje,
        "mensaje_modificado": mensaje_modificado,
        "metadata": metadata,
        "timestamps": {
            "sent": timestamp_sent,
            "received": datetime.utcnow().isoformat(),
        },
        "status": "ok"
    }

    await _producer.send_and_wait(
        TOPIC_PRUEBA_RESULTS,
        json.dumps(reply).encode("utf-8")
    )
    logging.info(f"[service-test PruebaConsumer] Respuesta enviada → correlation_id={correlation_id[:8]}...")