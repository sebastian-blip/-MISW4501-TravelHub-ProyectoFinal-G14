"""
Reader consumer: subscribe to UsuarioOlvidado, anonymize read model, record completado.
"""
import asyncio
import json
import uuid
from datetime import datetime
import pika
import asyncpg
from .config import DATABASE_URL, RABBITMQ_URL, CONSUMER_ID
from .repositories.read_model_repository import ReadModelRepository
from .repositories.audit_repository import AuditRepository

from shared.event_schema import (
    EXCHANGE_USUARIO_OLVIDADO,
    QUEUE_READER,
    ROUTING_KEY,
    UsuarioOlvidadoPayload,
)


def run_consumer():
    print("Connecting to RabbitMQ...", flush=True)
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_USUARIO_OLVIDADO, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE_READER, durable=True)
    channel.queue_bind(queue=QUEUE_READER, exchange=EXCHANGE_USUARIO_OLVIDADO, routing_key=ROUTING_KEY)
    print(f"Subscribed to queue {QUEUE_READER}", flush=True)

    async def on_message(ch, method, properties, body):
        try:
            payload = UsuarioOlvidadoPayload.model_validate_json(body)
            user_id = uuid.UUID(payload.user_id)
        except Exception:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        print(f"Received UsuarioOlvidado user_id={user_id}", flush=True)
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)
        try:
            read_repo = ReadModelRepository(pool)
            audit_repo = AuditRepository(pool)
            await read_repo.anonymize_user(user_id)
            await audit_repo.record_completado(user_id, CONSUMER_ID, datetime.utcnow())
            print("Anonymized user in read model; recorded completado in audit_events", flush=True)
        finally:
            await pool.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def callback(ch, method, properties, body):
        asyncio.run(on_message(ch, method, properties, body))

    channel.basic_consume(queue=QUEUE_READER, on_message_callback=callback)
    channel.start_consuming()


if __name__ == "__main__":
    run_consumer()
