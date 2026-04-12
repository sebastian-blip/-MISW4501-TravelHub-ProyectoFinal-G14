"""
Consumes reservation-validate-requests (same contract as service-core / service-test).
Replies on reservation-validate-results with randomized `exists`.
No external reservation/PMS service calls; no database in this consumer.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from infrastructure.messaging.kafka._kafka_config import consumer_base_config, producer_base_config
from infrastructure.messaging.kafka.topics import TOPIC_RESERVATION_RESULTS, TOPIC_RESERVATION_VALIDATE

_consumer: AIOKafkaConsumer | None = None
_producer: AIOKafkaProducer | None = None
_task: asyncio.Task | None = None

_EXISTS_RATE = float(os.getenv("TH_MOCK_RESERVATION_EXISTS_RATE", "0.25"))


async def start_reservation_validate_consumer(bootstrap_servers: str) -> None:
    global _consumer, _producer, _task
    if _consumer is not None:
        return

    pcfg = producer_base_config(bootstrap_servers)
    _producer = AIOKafkaProducer(**pcfg)
    await _producer.start()

    ccfg = consumer_base_config(bootstrap_servers, "service-external-reservation-group")
    _consumer = AIOKafkaConsumer(TOPIC_RESERVATION_VALIDATE, **ccfg)
    await _consumer.start()
    _task = asyncio.create_task(_consume_loop())
    logging.info(
        "[service-external] reservation validate consumer on %s (exists_rate=%s, no DB)",
        TOPIC_RESERVATION_VALIDATE,
        _EXISTS_RATE,
    )


async def stop_reservation_validate_consumer() -> None:
    global _consumer, _producer, _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    if _consumer:
        await _consumer.stop()
        _consumer = None
    if _producer:
        await _producer.stop()
        _producer = None


async def _consume_loop() -> None:
    assert _consumer is not None
    try:
        async for msg in _consumer:
            payload = json.loads(msg.value.decode("utf-8"))
            await _handle(payload)
    except asyncio.CancelledError:
        pass


async def _handle(payload: dict) -> None:
    assert _producer is not None
    correlation_id = payload.get("correlation_id", "")

    simulate_exists = random.random() < _EXISTS_RATE
    logging.info(
        "[service-external] validate correlation=%s simulate_exists=%s",
        correlation_id[:8] if correlation_id else "",
        simulate_exists,
    )

    if simulate_exists:
        reply = {
            "correlation_id": correlation_id,
            "exists": True,
            "confirmation_code": f"RES{uuid4().hex[:8].upper()}",
            "message": "Reserva existe (mock, sin BD)",
        }
    else:
        reply = {
            "correlation_id": correlation_id,
            "exists": False,
            "message": "Reserva no existe (mock, sin BD)",
        }

    await _producer.send_and_wait(TOPIC_RESERVATION_RESULTS, json.dumps(reply).encode("utf-8"))
