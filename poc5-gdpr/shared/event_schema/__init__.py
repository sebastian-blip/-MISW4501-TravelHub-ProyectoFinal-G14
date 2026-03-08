"""
Shared event schema for PoC-5 derecho al olvido.
User Service publishes UsuarioOlvidado; Reader, Reservations, Analytics consume it.
"""
from .payloads import UsuarioOlvidadoPayload
from .constants import (
    STREAM_USUARIO_OLVIDADO,
    CONSUMER_GROUP_READER,
    CONSUMER_GROUP_RESERVATIONS,
    CONSUMER_GROUP_ANALYTICS,
    EXCHANGE_USUARIO_OLVIDADO,
    QUEUE_READER,
    QUEUE_RESERVATIONS,
    QUEUE_ANALYTICS,
    ROUTING_KEY,
)

__all__ = [
    "UsuarioOlvidadoPayload",
    "STREAM_USUARIO_OLVIDADO",
    "CONSUMER_GROUP_READER",
    "CONSUMER_GROUP_RESERVATIONS",
    "CONSUMER_GROUP_ANALYTICS",
    "EXCHANGE_USUARIO_OLVIDADO",
    "QUEUE_READER",
    "QUEUE_RESERVATIONS",
    "QUEUE_ANALYTICS",
    "ROUTING_KEY",
]
