"""
Derecho al olvido: anonymize user, publish UsuarioOlvidado, record T0 in audit.
"""
import uuid
from datetime import datetime
import json
import pika
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository

from shared.event_schema import UsuarioOlvidadoPayload, EXCHANGE_USUARIO_OLVIDADO, ROUTING_KEY


class DerechoOlvidoService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository, rabbitmq_url: str):
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._rabbitmq_url = rabbitmq_url

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
        params = pika.URLParameters(self._rabbitmq_url)
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.exchange_declare(exchange=EXCHANGE_USUARIO_OLVIDADO, exchange_type="topic", durable=True)
        ch.basic_publish(
            exchange=EXCHANGE_USUARIO_OLVIDADO,
            routing_key=ROUTING_KEY,
            body=payload.model_dump_json(),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
