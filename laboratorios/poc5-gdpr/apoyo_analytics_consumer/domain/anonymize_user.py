"""
Domain: when a user is forgotten, anonymize all analytics data for that user.
"""
from datetime import datetime
from uuid import UUID
from .ports import AnalyticsRepositoryPort, AuditPort


class AnonymizeUserForAnalytics:
    """Application service: orchestrates anonymization and audit (uses ports)."""

    def __init__(self, analytics_repo: AnalyticsRepositoryPort, audit: AuditPort, consumer_id: str):
        self._analytics_repo = analytics_repo
        self._audit = audit
        self._consumer_id = consumer_id

    async def execute(self, user_id: UUID) -> None:
        await self._analytics_repo.anonymize_user(user_id)
        t = datetime.utcnow()
        await self._audit.record_completado(user_id, self._consumer_id, t)
