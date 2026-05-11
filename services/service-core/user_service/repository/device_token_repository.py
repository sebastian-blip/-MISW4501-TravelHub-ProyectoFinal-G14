"""Repositorio para `device_tokens`. Operaciones esperadas por el router:

- `upsert(user_id, token, platform, app_version)` — idempotente. Si el par
  (user_id, token) existe, actualiza `last_seen_at` (y `app_version` si
  cambió). Si no existe, crea la fila.
- `delete(user_id, token)` — borra el registro al hacer logout en ese
  device, para que el backend no le siga mandando pushes.
- `list_for_user(user_id)` — lo usa el adaptador FCM en service-external
  (vía endpoint interno, fuera del scope de esta entrega) para resolver
  destinos a partir de un user_id.
"""
import datetime
import uuid
from typing import List, Optional

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.device_token import DeviceToken


VALID_PLATFORMS = {"android", "ios", "web"}


class DeviceTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID, token: str) -> Optional[DeviceToken]:
        stmt = select(DeviceToken).where(
            DeviceToken.user_id == user_id,
            DeviceToken.token == token,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> List[DeviceToken]:
        stmt = (
            select(DeviceToken)
            .where(DeviceToken.user_id == user_id)
            .order_by(DeviceToken.last_seen_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        user_id: uuid.UUID,
        token: str,
        platform: str,
        app_version: Optional[str] = None,
    ) -> DeviceToken:
        if platform not in VALID_PLATFORMS:
            raise ValueError(f"platform must be one of {VALID_PLATFORMS}, got {platform!r}")
        if not token or not token.strip():
            raise ValueError("token must be non-empty")

        existing = await self.get(user_id, token)
        # Naive UTC — `device_tokens.last_seen_at` es `TIMESTAMP WITHOUT TIME
        # ZONE`. Si pasamos tz-aware, asyncpg lanza "can't subtract offset-
        # naive and offset-aware datetimes" al codificar el parámetro.
        now = datetime.datetime.utcnow()
        if existing is not None:
            existing.last_seen_at = now
            if app_version is not None:
                existing.app_version = app_version
            existing.platform = platform
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        record = DeviceToken(
            user_id=user_id,
            token=token,
            platform=platform,
            app_version=app_version,
            last_seen_at=now,
            created_at=now,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete(self, user_id: uuid.UUID, token: str) -> bool:
        record = await self.get(user_id, token)
        if record is None:
            return False
        await self.session.delete(record)
        await self.session.commit()
        return True

    async def delete_all_for_user(self, user_id: uuid.UUID) -> int:
        """Borra todos los tokens de un usuario (logout global). Devuelve
        el número de filas afectadas para que el caller pueda loggear."""
        rows = await self.list_for_user(user_id)
        for row in rows:
            await self.session.delete(row)
        await self.session.commit()
        return len(rows)
