"""
Reader consumer: read from Redis Stream UsuarioOlvidado, anonymize read model, record completado.
Broker: Redis (Redis Streams). DB: DuckDB via HTTP API.
"""
import asyncio
import uuid
from datetime import datetime
import redis
import httpx
from .config import DB_API_URL, REDIS_URL, CONSUMER_ID

from shared.event_schema import STREAM_USUARIO_OLVIDADO, QUEUE_READER, UsuarioOlvidadoPayload


def run_consumer():
    print("Connecting to Redis...", flush=True)
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        r.xgroup_create(STREAM_USUARIO_OLVIDADO, QUEUE_READER, id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
    print(f"Subscribed to stream {STREAM_USUARIO_OLVIDADO} group {QUEUE_READER}", flush=True)

    consumer_name = f"{QUEUE_READER}-1"
    while True:
        msgs = r.xreadgroup(QUEUE_READER, consumer_name, {STREAM_USUARIO_OLVIDADO: ">"}, count=1, block=5000)
        if not msgs:
            continue
        for stream_name, stream_msgs in msgs:
            for msg_id, fields in stream_msgs:
                body = fields.get("payload") or fields.get(b"payload")
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                try:
                    payload = UsuarioOlvidadoPayload.model_validate_json(body)
                    user_id = uuid.UUID(payload.user_id)
                except Exception:
                    r.xack(STREAM_USUARIO_OLVIDADO, QUEUE_READER, msg_id)
                    continue
                print(f"Received UsuarioOlvidado user_id={user_id}", flush=True)
                asyncio.run(_process(r, QUEUE_READER, msg_id, user_id))


async def _process(r, group: str, msg_id: str, user_id: uuid.UUID):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{DB_API_URL}/read-model/{user_id}/anonymize")
            await client.post(
                f"{DB_API_URL}/audit/completado",
                json={
                    "user_id": str(user_id),
                    "consumer_id": CONSUMER_ID,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            print("Anonymized user in read model; recorded completado in audit_events", flush=True)
            r.xack(STREAM_USUARIO_OLVIDADO, group, msg_id)
        except Exception:
            pass


if __name__ == "__main__":
    run_consumer()
