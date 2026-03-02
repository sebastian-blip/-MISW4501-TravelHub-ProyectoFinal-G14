import json
import uuid
from datetime import datetime
import asyncpg


class AuditRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def record_solicitud_olvido(self, user_id: uuid.UUID, timestamp: datetime, payload: dict | None = None) -> uuid.UUID:
        row = await self._pool.fetchrow(
            """
            INSERT INTO audit_events (event_type, user_id, consumer_id, timestamp, payload)
            VALUES ('solicitud_olvido', $1, NULL, $2, $3::jsonb)
            RETURNING id
            """,
            user_id,
            timestamp,
            json.dumps(payload or {}),
        )
        return row["id"]

    async def record_completado(self, user_id: uuid.UUID, consumer_id: str, timestamp: datetime) -> None:
        await self._pool.execute(
            """
            INSERT INTO audit_events (event_type, user_id, consumer_id, timestamp, payload)
            VALUES ('completado', $1, $2, $3, '{}')
            """,
            user_id,
            consumer_id,
            timestamp,
        )
