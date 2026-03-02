"""
Analytics consumer: subscribe to UsuarioOlvidado, run domain service (hexagonal), record completado.
"""
import asyncio
import os
import time
import uuid
from datetime import datetime
import pika
import asyncpg

from shared.event_schema import (
    EXCHANGE_USUARIO_OLVIDADO,
    QUEUE_ANALYTICS,
    ROUTING_KEY,
    UsuarioOlvidadoPayload,
)

# Apoyo - hexagonal: domain + adapters (PYTHONPATH=/app)
from apoyo_analytics_consumer.domain.anonymize_user import AnonymizeUserForAnalytics
from apoyo_analytics_consumer.adapters.postgres_analytics_repository import PostgresAnalyticsRepository
from apoyo_analytics_consumer.adapters.postgres_audit_adapter import PostgresAuditAdapter
from apoyo_analytics_consumer.app.config import DATABASE_URL, RABBITMQ_URL, CONSUMER_ID


def run_consumer():
    print("Connecting to RabbitMQ...", flush=True)
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_USUARIO_OLVIDADO, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE_ANALYTICS, durable=True)
    channel.queue_bind(queue=QUEUE_ANALYTICS, exchange=EXCHANGE_USUARIO_OLVIDADO, routing_key=ROUTING_KEY)
    print(f"Subscribed to queue {QUEUE_ANALYTICS}", flush=True)

    async def on_message(ch, method, properties, body):
        try:
            payload = UsuarioOlvidadoPayload.model_validate_json(body)
            user_id = uuid.UUID(payload.user_id)
        except Exception:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        print(f"Received UsuarioOlvidado user_id={user_id}", flush=True)
        delay_sec = int(os.environ.get("DELAY_ANALYTICS_SEC", "0"))
        if delay_sec > 0:
            print(f"Simulating slow consumer: sleeping {delay_sec}s...", flush=True)
            time.sleep(delay_sec)
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)
        try:
            analytics_repo = PostgresAnalyticsRepository(pool)
            audit = PostgresAuditAdapter(pool)
            use_case = AnonymizeUserForAnalytics(analytics_repo, audit, CONSUMER_ID)
            await use_case.execute(user_id)
            print("Anonymized analytics_user_activity; recorded completado in audit_events", flush=True)
        finally:
            await pool.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def callback(ch, method, properties, body):
        asyncio.run(on_message(ch, method, properties, body))

    channel.basic_consume(queue=QUEUE_ANALYTICS, on_message_callback=callback)
    channel.start_consuming()


if __name__ == "__main__":
    run_consumer()
