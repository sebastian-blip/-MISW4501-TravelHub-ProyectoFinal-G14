from __future__ import annotations

import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer

TOPIC_RESULTS = "user-validation-results"
TOPIC_RESERVATION_RESULTS = "reservation-validate-results"

# Futures pendientes por correlation_id — el handler espera aquí
_pending: dict[str, asyncio.Future] = {}

_consumer: AIOKafkaConsumer | None = None
_task: asyncio.Task | None = None


async def start_reply_consumer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = ""
):
    """Inicia el consumidor de respuestas con soporte para SASL."""
    global _consumer, _task
    
    config = {
        "bootstrap_servers": bootstrap_servers,
        "group_id": "service-core-reply-group",
        "auto_offset_reset": "latest",
        "enable_auto_commit": True,
    }
    

    config["sasl_mechanism"] = "SCRAM-SHA-256"
    config["security_protocol"] = "SASL_PLAINTEXT"
    config["sasl_plain_username"] = os.getenv("KAFKA_USERNAME", "")
    config["sasl_plain_password"] = os.getenv("KAFKA_PASSWORD", "")
    
    _consumer = AIOKafkaConsumer(
        TOPIC_RESULTS,
        TOPIC_RESERVATION_RESULTS,
        **config
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(
        "[service-core ReplyConsumer] escuchando topics=%s, %s",
        TOPIC_RESULTS,
        TOPIC_RESERVATION_RESULTS,
    )


async def stop_reply_consumer():
    global _consumer, _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    if _consumer:
        await _consumer.stop()


async def wait_for_reply(correlation_id: str, timeout: float = 5.0) -> dict:
    """Bloquea hasta recibir la respuesta con el correlation_id dado."""
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _pending[correlation_id] = future
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Sin respuesta de Kafka para correlation_id={correlation_id}")
    finally:
        _pending.pop(correlation_id, None)


async def _consume():
    try:
        async for msg in _consumer:
            payload = json.loads(msg.value.decode("utf-8"))
            correlation_id = payload.get("correlation_id", "")
            future = _pending.get(correlation_id)
            if future and not future.done():
                future.set_result(payload)
                logging.info(f"[service-core ReplyConsumer] respuesta recibida → correlation_id={correlation_id}, topic={msg.topic}")
    except asyncio.CancelledError:
        pass
