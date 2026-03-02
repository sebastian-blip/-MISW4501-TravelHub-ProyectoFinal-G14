from abc import ABC, abstractmethod
from uuid import UUID


class AnalyticsRepositoryPort(ABC):
    @abstractmethod
    async def anonymize_user(self, user_id: UUID) -> None:
        """Anonymize or remove PII for user in analytics/reports."""
        pass
