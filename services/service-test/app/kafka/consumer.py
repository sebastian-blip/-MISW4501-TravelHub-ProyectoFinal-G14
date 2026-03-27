import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"
TOPIC_RESULTS  = "user-validation-results"

# Usuarios "registrados" hardcodeados para la prueba
KNOWN_USERS = {"miguelegion@gmail.com"}

# Historial en memoria
results: list[dict] = []

_consumer: AIOKafkaConsumer | None = None
_producer: AIOKafkaProducer | None = None
_task: asyncio.Task | None = None


async def start_consumer(bootstrap_servers: str):
    global _consumer, _producer, _task

    _producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await _producer.start()

    _consumer = AIOKafkaConsumer(
        TOPIC_REQUESTS,
        bootstrap_servers=bootstrap_servers,
        group_id="user-validation-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(f"[service-test Consumer] escuchando topic={TOPIC_REQUESTS}")


async def stop_consumer():
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
    email = payload.get("email", "")
    correlation_id = payload.get("correlation_id", "")
    found = email in KNOWN_USERS

    result = {
        "correlation_id": correlation_id,
        "email": email,
        "exists": found,
        "message": f"Usuario '{email}' {'encontrado ✓' if found else 'NO encontrado ✗'}",
    }

    results.append(result)

    # Publicar respuesta a service-core
    reply = json.dumps(result).encode("utf-8")
    await _producer.send_and_wait(TOPIC_RESULTS, reply)

    if found:
        logging.info(f"[service-test Consumer] ✓ Existe: {email} → respuesta enviada")
    else:
        logging.info(f"[service-test Consumer] ✗ No existe: {email} → respuesta enviada")
