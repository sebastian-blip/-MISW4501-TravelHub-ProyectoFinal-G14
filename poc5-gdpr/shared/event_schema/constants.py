"""Redis Stream and consumer group names (shared across services). Aligned with architecture: Redis as message broker."""
STREAM_USUARIO_OLVIDADO = "stream:usuario_olvidado"
# Consumer group names (one group per consumer type; each reads from the same stream)
CONSUMER_GROUP_READER = "reader"
CONSUMER_GROUP_RESERVATIONS = "reservations"
CONSUMER_GROUP_ANALYTICS = "analytics"
# Legacy names kept for compatibility where queue name was used as group id
QUEUE_READER = CONSUMER_GROUP_READER
QUEUE_RESERVATIONS = CONSUMER_GROUP_RESERVATIONS
QUEUE_ANALYTICS = CONSUMER_GROUP_ANALYTICS
EXCHANGE_USUARIO_OLVIDADO = "usuario_olvidado"
ROUTING_KEY = "usuario.olvidado"
