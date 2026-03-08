"""
Analytics consumer: read from Redis Stream UsuarioOlvidado, anonymize analytics, record completado.
Broker: Redis (Redis Streams). DB: DuckDB via HTTP API.
"""
import asyncio
import time
import uuid
from datetime import datetime
import redis
import httpx

from shared.event_schema import STREAM_USUARIO_OLVIDADO, QUEUE_ANALYTICS, UsuarioOlvidadoPayload

from apoyo_analytics_consumer.app.config import DB_API_URL, REDIS_URL, CONSUMER_ID, ANONYMOUS_USER_ID, DELAY_ANALYTICS_SEC


def run_consumer():
    print("Connecting to Redis...", flush=True)
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        r.xgroup_create(STREAM_USUARIO_OLVIDADO, QUEUE_ANALYTICS, id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
    print(f"Subscribed to stream {STREAM_USUARIO_OLVIDADO} group {QUEUE_ANALYTICS}", flush=True)

    consumer_name = f"{QUEUE_ANALYTICS}-1"
    while True:
        msgs = r.xreadgroup(QUEUE_ANALYTICS, consumer_name, {STREAM_USUARIO_OLVIDADO: ">"}, count=1, block=5000)
        if not msgs:
            continue
        for _stream_name, stream_msgs in msgs:
            for msg_id, fields in stream_msgs:
                body = fields.get("payload")
                try:
                    payload = UsuarioOlvidadoPayload.model_validate_json(body)
                    user_id = uuid.UUID(payload.user_id)
                except Exception:
                    r.xack(STREAM_USUARIO_OLVIDADO, QUEUE_ANALYTICS, msg_id)
                    continue
                print(f"Received UsuarioOlvidado user_id={user_id}", flush=True)
                if DELAY_ANALYTICS_SEC > 0:
                    print(f"Simulating slow consumer: sleeping {DELAY_ANALYTICS_SEC}s...", flush=True)
                    time.sleep(DELAY_ANALYTICS_SEC)
                asyncio.run(_process(r, msg_id, user_id))


async def _process(r, msg_id: str, user_id: uuid.UUID):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{DB_API_URL}/analytics/anonymize",
                json={"user_id": str(user_id), "anonymous_user_id": ANONYMOUS_USER_ID},
            )
            await client.post(
                f"{DB_API_URL}/audit/completado",
                json={
                    "user_id": str(user_id),
                    "consumer_id": CONSUMER_ID,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            print("Anonymized analytics_user_activity; recorded completado in audit_events", flush=True)
            r.xack(STREAM_USUARIO_OLVIDADO, QUEUE_ANALYTICS, msg_id)
        except Exception:
            pass


if __name__ == "__main__":
    run_consumer()
