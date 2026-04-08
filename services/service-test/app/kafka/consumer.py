import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"
TOPIC_RESULTS = "user-validation-results"
TOPIC_STEP_EVENTS = "step-change-events"

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
        TOPIC_STEP_EVENTS,  # Escuchar eventos de cambio de paso
        bootstrap_servers=bootstrap_servers,
        group_id="service-test-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(f"[service-test Consumer] escuchando topics={TOPIC_REQUESTS}, {TOPIC_STEP_EVENTS}")


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
            topic = msg.topic
            
            if topic == TOPIC_STEP_EVENTS:
                await _handle_step_event(payload)
            else:
                await _handle_user_validation(payload)
    except asyncio.CancelledError:
        pass


async def _handle_step_event(payload: dict):
    """Maneja eventos de cambio de paso desde service-core."""
    import os
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("POSTGRES_USER", "postgres")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
    os.environ.setdefault("POSTGRES_DB", "travelhub")
    
    task_id = payload.get("task_id")
    previous_step = payload.get("previous_step")
    new_step = payload.get("new_step")
    history = payload.get("history", [])
    
    logging.info(f"[service-test Consumer] Evento de paso recibido: task_id={task_id}, {previous_step} → {new_step}")
    
    # Consultar la base de datos
    try:
        from sqlalchemy import select
        from app.infrastructure.database import async_session_maker
        from app.models.models.user import User
        
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            user_count = len(users)
            user_emails = [u.email for u in users[:3]]  # Primeros 3 emails
            
            logging.info(f"[service-test Consumer] Consulta BD: {user_count} usuarios encontrados")
    except Exception as e:
        user_count = 0
        user_emails = []
        logging.error(f"[service-test Consumer] Error consultando BD: {e}")
    
    # Preparar resultado
    result = {
        "event_type": "step_changed",
        "task_id": task_id,
        "previous_step": previous_step,
        "new_step": new_step,
        "history": history,
        "db_query_result": {
            "total_users": user_count,
            "sample_users": user_emails
        },
        "message": f"Paso cambiado: {previous_step} → {new_step}. Usuarios en BD: {user_count}"
    }
    
    results.append(result)
    
    # Publicar respuesta
    reply = json.dumps(result).encode("utf-8")
    await _producer.send_and_wait(TOPIC_RESULTS, reply)
    
    logging.info(f"[service-test Consumer] ✓ Respuesta enviada con datos de BD: {user_count} usuarios")


async def _handle_user_validation(payload: dict):
    """Maneja validaciones de usuario (funcionalidad original)."""
    email = payload.get("email", "")
    correlation_id = payload.get("correlation_id", "")
    
    # Usuarios "registrados" hardcodeados para la prueba
    KNOWN_USERS = {"miguelegion1@gmail.com"}
    found = email in KNOWN_USERS
    
    result = {
        "correlation_id": correlation_id,
        "email": email,
        "exists": found,
        "message": f"Usuario '{email}' {'encontrado ✓' if found else 'NO encontrado ✗'}",
    }
    
    results.append(result)
    
    reply = json.dumps(result).encode("utf-8")
    await _producer.send_and_wait(TOPIC_RESULTS, reply)
    
    if found:
        logging.info(f"[service-test Consumer] ✓ Usuario existe: {email}")
    else:
        logging.info(f"[service-test Consumer] ✗ Usuario no existe: {email}")
