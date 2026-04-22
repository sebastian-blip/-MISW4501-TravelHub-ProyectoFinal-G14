from __future__ import annotations

import logging
import os

from infrastructure.messaging.kafka.reservation_validate_consumer import (
    start_reservation_validate_consumer,
    stop_reservation_validate_consumer,
)


async def start_kafka_consumers(bootstrap_servers: str) -> None:
    if os.getenv("TH_CONSUME_RESERVATION_VALIDATE", "true").lower() in ("1", "true", "yes"):
        await start_reservation_validate_consumer(bootstrap_servers)
    else:
        logging.info("[service-external] TH_CONSUME_RESERVATION_VALIDATE=false — skipping")


async def stop_kafka_consumers() -> None:
    await stop_reservation_validate_consumer()
