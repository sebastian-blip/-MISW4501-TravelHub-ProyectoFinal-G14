import uuid
import asyncpg


class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get(self, user_id: uuid.UUID) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, email, name, anonymized, created_at, updated_at FROM users WHERE id = $1",
            user_id,
        )
        if not row:
            return None
        return dict(row)

    async def anonymize(self, user_id: uuid.UUID) -> bool:
        result = await self._pool.execute(
            """
            UPDATE users
            SET email = 'anon_' || id::text || '@deleted.local',
                name = 'DELETED',
                anonymized = TRUE,
                updated_at = NOW()
            WHERE id = $1 AND anonymized = FALSE
            """,
            user_id,
        )
        return result == "UPDATE 1"
