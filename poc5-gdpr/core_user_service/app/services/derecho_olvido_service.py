"""
Derecho al olvido: anonymize user, publish UsuarioOlvidado to Redis Stream, record T0 in audit.
Broker: Redis (Redis Streams), aligned with architecture.
"""
import uuid
from datetime import datetime
import redis
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository

from shared.event_schema import UsuarioOlvidadoPayload, STREAM_USUARIO_OLVIDADO


class DerechoOlvidoService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository, redis_url: str):
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._redis_url = redis_url

    async def execute(self, user_id: uuid.UUID) -> tuple[bool, str | None]:
        user = await self._user_repo.get(user_id)
        if not user:
            return False, "user_not_found"
        if user.get("anonymized"):
            return False, "already_anonymized"

        t0 = datetime.utcnow()
        await self._user_repo.anonymize(user_id)
        await self._audit_repo.record_solicitud_olvido(user_id, t0, {"t0_iso": t0.isoformat() + "Z"})

        payload = UsuarioOlvidadoPayload(user_id=str(user_id), timestamp=t0.isoformat() + "Z")
        self._publish_event(payload)

        return True, t0.isoformat() + "Z"

    def _publish_event(self, payload: UsuarioOlvidadoPayload) -> None:
        r = redis.from_url(self._redis_url, decode_responses=True)
        r.xadd(STREAM_USUARIO_OLVIDADO, {"payload": payload.model_dump_json()}, maxlen=10000)
        r.close()
