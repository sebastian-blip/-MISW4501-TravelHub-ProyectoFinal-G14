"""
PLAINTEXT Kafka client config for tests only (e.g. docker-compose local broker).

Do not use in production paths. Production code should use _kafka_config.consumer_base_config /
producer_base_config with KAFKA_USERNAME + KAFKA_PASSWORD when talking to SASL brokers.
"""

from __future__ import annotations

from typing import Any


def testing_consumer_base_config(bootstrap_servers: str, group_id: str) -> dict[str, Any]:
    return {
        "bootstrap_servers": bootstrap_servers,
        "group_id": group_id,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
    }


def testing_producer_base_config(bootstrap_servers: str) -> dict[str, Any]:
    return {"bootstrap_servers": bootstrap_servers}
