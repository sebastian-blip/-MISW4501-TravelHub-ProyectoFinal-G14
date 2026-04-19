import uuid
import asyncpg


class ReservationRepository:
    def __init__(self, pool: asyncpg.Pool, anonymous_user_id: uuid.UUID):
        self._pool = pool
        self._anonymous_user_id = anonymous_user_id

    async def anonymize_user_in_reservations(self, user_id: uuid.UUID) -> int:
        result = await self._pool.execute(
            """
            UPDATE reservations
            SET user_id = $1, updated_at = NOW()
            WHERE user_id = $2
            """,
            self._anonymous_user_id,
            user_id,
        )
        # UPDATE N -> return N
        if result.startswith("UPDATE "):
            return int(result.split()[-1])
        return 0
