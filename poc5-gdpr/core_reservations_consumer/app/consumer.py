"""
Reservations consumer: read from Redis Stream UsuarioOlvidado, anonymize user_id in reservations, record completado.
Broker: Redis (Redis Streams). DB: DuckDB via HTTP API.
"""
import asyncio
import uuid
from datetime import datetime
import redis
import httpx
from .config import DB_API_URL, REDIS_URL, CONSUMER_ID, ANONYMOUS_USER_ID

from shared.event_schema import STREAM_USUARIO_OLVIDADO, QUEUE_RESERVATIONS, UsuarioOlvidadoPayload


def run_consumer():
    print("Connecting to Redis...", flush=True)
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        r.xgroup_create(STREAM_USUARIO_OLVIDADO, QUEUE_RESERVATIONS, id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
    print(f"Subscribed to stream {STREAM_USUARIO_OLVIDADO} group {QUEUE_RESERVATIONS}", flush=True)

    consumer_name = f"{QUEUE_RESERVATIONS}-1"
    while True:
        msgs = r.xreadgroup(QUEUE_RESERVATIONS, consumer_name, {STREAM_USUARIO_OLVIDADO: ">"}, count=1, block=5000)
        if not msgs:
            continue
        for _stream_name, stream_msgs in msgs:
            for msg_id, fields in stream_msgs:
                body = fields.get("payload")
                try:
                    payload = UsuarioOlvidadoPayload.model_validate_json(body)
                    user_id = uuid.UUID(payload.user_id)
                except Exception:
                    r.xack(STREAM_USUARIO_OLVIDADO, QUEUE_RESERVATIONS, msg_id)
                    continue
                print(f"Received UsuarioOlvidado user_id={user_id}", flush=True)
                asyncio.run(_process(r, msg_id, user_id))


async def _process(r, msg_id: str, user_id: uuid.UUID):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{DB_API_URL}/reservations/anonymize",
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
            print("Updated reservations with anonymous user_id; recorded completado in audit_events", flush=True)
            r.xack(STREAM_USUARIO_OLVIDADO, QUEUE_RESERVATIONS, msg_id)
        except Exception:
            pass


if __name__ == "__main__":
    run_consumer()
