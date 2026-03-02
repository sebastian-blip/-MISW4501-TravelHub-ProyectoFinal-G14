"""
Re-export from shared.event_schema (backward compatibility).
Todo el código usa shared.event_schema; este módulo solo reexporta.
"""
from shared.event_schema import (
    UsuarioOlvidadoPayload,
    EXCHANGE_USUARIO_OLVIDADO,
    QUEUE_READER,
    QUEUE_RESERVATIONS,
    QUEUE_ANALYTICS,
    ROUTING_KEY,
)

__all__ = [
    "UsuarioOlvidadoPayload",
    "EXCHANGE_USUARIO_OLVIDADO",
    "QUEUE_READER",
    "QUEUE_RESERVATIONS",
    "QUEUE_ANALYTICS",
    "ROUTING_KEY",
]
