"""
Shared event schema for PoC-5 derecho al olvido.
User Service publishes UsuarioOlvidado; Reader, Reservations, Analytics consume it.
"""
from .payloads import UsuarioOlvidadoPayload
from .constants import (
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
