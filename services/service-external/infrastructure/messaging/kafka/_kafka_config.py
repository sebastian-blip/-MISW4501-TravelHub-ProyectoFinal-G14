from __future__ import annotations

import os
from typing import Any


def consumer_base_config(bootstrap_servers: str, group_id: str) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "bootstrap_servers": bootstrap_servers,
        "group_id": group_id,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
    }
    user = os.getenv("KAFKA_USERNAME", "")
    password = os.getenv("KAFKA_PASSWORD", "")
    if user and password:
        cfg["sasl_mechanism"] = "SCRAM-SHA-256"
        cfg["security_protocol"] = "SASL_PLAINTEXT"
        cfg["sasl_plain_username"] = user
        cfg["sasl_plain_password"] = password
    return cfg


def producer_base_config(bootstrap_servers: str) -> dict[str, Any]:
    cfg: dict[str, Any] = {"bootstrap_servers": bootstrap_servers}
    user = os.getenv("KAFKA_USERNAME", "")
    password = os.getenv("KAFKA_PASSWORD", "")
    if user and password:
        cfg["sasl_mechanism"] = "SCRAM-SHA-256"
        cfg["security_protocol"] = "SASL_PLAINTEXT"
        cfg["sasl_plain_username"] = user
        cfg["sasl_plain_password"] = password
    return cfg
