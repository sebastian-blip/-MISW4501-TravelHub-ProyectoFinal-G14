import uuid
import asyncpg
from apoyo_analytics_consumer.domain.ports import AnalyticsRepositoryPort


class PostgresAnalyticsRepository(AnalyticsRepositoryPort):
    def __init__(self, pool: asyncpg.Pool, anonymous_user_id: str = "00000000-0000-0000-0000-000000000001"):
        self._pool = pool
        self._anonymous_user_id = uuid.UUID(anonymous_user_id)

    async def anonymize_user(self, user_id: uuid.UUID) -> None:
        # Criterio unificado con Reservations: reemplazar user_id por UUID anónimo (no solo flag)
        # para cumplir derecho al olvido GDPR (identificador real no debe quedar rastreable).
        await self._pool.execute(
            """
            UPDATE analytics_user_activity
            SET user_id = $1, anonymized = TRUE
            WHERE user_id = $2 AND (anonymized = FALSE OR anonymized IS NULL)
            """,
            self._anonymous_user_id,
            user_id,
        )
