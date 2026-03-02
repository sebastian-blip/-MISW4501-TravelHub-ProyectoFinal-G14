import uuid
import asyncpg
from apoyo_analytics_consumer.domain.ports import AnalyticsRepositoryPort


class PostgresAnalyticsRepository(AnalyticsRepositoryPort):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def anonymize_user(self, user_id: uuid.UUID) -> None:
        await self._pool.execute(
            """
            UPDATE analytics_user_activity
            SET anonymized = TRUE
            WHERE user_id = $1 AND (anonymized = FALSE OR anonymized IS NULL)
            """,
            user_id,
        )
