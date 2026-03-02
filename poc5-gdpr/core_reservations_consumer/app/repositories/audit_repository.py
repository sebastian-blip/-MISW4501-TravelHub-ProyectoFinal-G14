import json
import uuid
from datetime import datetime
import asyncpg


class AuditRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def record_completado(self, user_id: uuid.UUID, consumer_id: str, timestamp: datetime) -> None:
        await self._pool.execute(
            """
            INSERT INTO audit_events (event_type, user_id, consumer_id, timestamp, payload)
            VALUES ('completado', $1, $2, $3, $4::jsonb)
            """,
            user_id,
            consumer_id,
            timestamp,
            json.dumps({}),
        )
