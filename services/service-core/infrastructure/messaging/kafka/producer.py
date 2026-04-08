import json
import logging
from aiokafka import AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"
TOPIC_STEP_EVENTS = "step-change-events"

_producer: AIOKafkaProducer | None = None


async def start_producer(bootstrap_servers: str):
    global _producer
    _producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
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
