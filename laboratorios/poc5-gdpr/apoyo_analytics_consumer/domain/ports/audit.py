from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class AuditPort(ABC):
    @abstractmethod
    async def record_completado(self, user_id: UUID, consumer_id: str, timestamp: datetime) -> None:
        """Record that this consumer finished anonymization (for TFO)."""
        pass
