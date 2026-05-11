"""SQLModel para los tokens de notificación push de cada dispositivo del usuario.

Cada usuario puede tener N tokens activos (un dispositivo Android, otro iOS,
una pestaña de navegador, etc.). El cliente registra el token al iniciar
sesión y lo refresca cuando FCM/APNs lo rota. Lo borramos al hacer logout
explícito desde ese mismo dispositivo.

Diseño:

- `(user_id, token)` es UNIQUE: la combinación es la identidad del registro,
  no usamos el `id` para upserts. Permite que el mismo dispositivo pertenezca
  a varios usuarios si se loguean en serie.
- `last_seen_at` se actualiza en cada upsert para poder podar tokens
  inactivos por una tarea de mantenimiento (>30d).
- `platform` es un enum simple: por ahora solo `android`, pero `ios` y `web`
  ya están reservados para no migrar el schema cuando se sumen.
"""
from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class DeviceToken(SQLModel, table=True):
    __tablename__ = "device_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    token: str = Field(max_length=512)
    platform: str = Field(max_length=16)  # 'android' | 'ios' | 'web'
    app_version: Optional[str] = Field(default=None, max_length=32)
    # `TIMESTAMP WITHOUT TIME ZONE` en la columna → guardamos naive UTC para
    # ser consistentes con el resto de tablas de service-core (que usan el
    # mismo tipo). El cliente que consuma esto puede asumir UTC.
    last_seen_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.utcnow()
    )
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.utcnow()
    )

    def __str__(self) -> str:
        return f"DeviceToken<{self.platform}:{self.token[:8]}…>"
