from datetime import datetime
import uuid
from ..db_client import record_solicitud_olvido as _record


class AuditRepository:
    """Uses DB API (DuckDB service)."""

    async def record_solicitud_olvido(
        self, user_id: uuid.UUID, timestamp: datetime, payload: dict | None = None
    ) -> uuid.UUID:
        await _record(str(user_id), timestamp, payload)
        return uuid.uuid4()
