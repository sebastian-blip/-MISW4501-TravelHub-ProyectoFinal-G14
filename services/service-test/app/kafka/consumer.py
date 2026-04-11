import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"
TOPIC_RESULTS = "user-validation-results"
TOPIC_STEP_EVENTS = "step-change-events"
TOPIC_AWS_TEST = "aws-test-messages"

# Historial en memoria
results: list[dict] = []

_consumer: AIOKafkaConsumer | None = None
_producer: AIOKafkaProducer | None = None
_task: asyncio.Task | None = None


async def start_consumer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = ""
):
    """Inicia el consumidor de Kafka con soporte para SASL."""
    global _consumer, _producer, _task
    
    # Configuración base
    producer_config = {"bootstrap_servers": bootstrap_servers}
    consumer_config = {
        "bootstrap_servers": bootstrap_servers,
        "group_id": "service-test-group",
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
        TOPIC_REQUESTS,
        TOPIC_STEP_EVENTS,
        TOPIC_AWS_TEST,
        **consumer_config
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(f"[service-test Consumer] escuchando topics={TOPIC_REQUESTS}, {TOPIC_STEP_EVENTS}, {TOPIC_AWS_TEST}")


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
            elif topic == TOPIC_AWS_TEST:
                await _handle_aws_test_message(payload)
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
            user_emails = [u.email for u in users[:3]]
            
            logging.info(f"[service-test Consumer] Consulta BD: {user_count} usuarios encontrados")
    except Exception as e:
        user_count = 0
        user_emails = []
        logging.error(f"[service-test Consumer] Error consultando BD: {e}")
    
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
    
    reply = json.dumps(result).encode("utf-8")
    await _producer.send_and_wait(TOPIC_RESULTS, reply)
    
    logging.info(f"[service-test Consumer] ✓ Respuesta enviada con datos de BD: {user_count} usuarios")


async def _handle_user_validation(payload: dict):
    """Maneja validaciones de usuario."""
    email = payload.get("email", "")
    correlation_id = payload.get("correlation_id", "")
    
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


async def _handle_aws_test_message(payload: dict):
    """Maneja mensajes de prueba de AWS."""
    import socket
    from datetime import datetime
    
    message = payload.get("message", "")
    correlation_id = payload.get("correlation_id", "")
    priority = payload.get("priority", "normal")
    metadata = payload.get("metadata", {})
    source = payload.get("source", {})
    sent_timestamp = payload.get("timestamp", "")
    
    received_timestamp = datetime.utcnow().isoformat()
    hostname = socket.gethostname()
    
    logging.info(f"[service-test Consumer] 📨 Mensaje AWS recibido: correlation_id={correlation_id}, priority={priority}")
    logging.info(f"[service-test Consumer]    Mensaje: '{message}'")
    logging.info(f"[service-test Consumer]    Origen: {source.get('service', 'unknown')} @ {source.get('host', 'unknown')}")
    
    result = {
        "event_type": "aws_test_response",
        "correlation_id": correlation_id,
        "status": "received",
        "original_message": message,
        "priority": priority,
        "timestamps": {
            "sent": sent_timestamp,
            "received": received_timestamp
        },
        "source": source,
        "destination": {
            "service": "service-test",
            "host": hostname,
            "port": 8001
        },
        "metadata_received": metadata,
        "message": f"✓ Mensaje recibido en service-test: '{message[:50]}...'" if len(message) > 50 else f"✓ Mensaje recibido en service-test: '{message}'"
    }
    
    results.append(result)
    
    reply = json.dumps(result).encode("utf-8")
    await _producer.send_and_wait(TOPIC_RESULTS, reply)
    
    logging.info(f"[service-test Consumer] ✓ Respuesta AWS enviada: correlation_id={correlation_id}")
