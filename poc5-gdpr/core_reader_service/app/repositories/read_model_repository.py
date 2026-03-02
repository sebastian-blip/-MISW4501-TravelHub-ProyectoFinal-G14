import uuid
from datetime import datetime
import asyncpg


class ReadModelRepository:
    """CQRS read model: user_read_model table."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def anonymize_user(self, user_id: uuid.UUID) -> bool:
        result = await self._pool.execute(
            """
            UPDATE user_read_model
            SET email = 'anon_' || id::text || '@deleted.local',
                name = 'DELETED',
                anonymized = TRUE,
                updated_at = NOW()
            WHERE id = $1 AND (anonymized = FALSE OR anonymized IS NULL)
            """,
            user_id,
        )
        return result == "UPDATE 1"
