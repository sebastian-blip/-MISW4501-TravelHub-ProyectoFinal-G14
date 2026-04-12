"""TravelHub — external integrations service (HTTP + Kafka consumers)."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from types import ModuleType

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from routes import integration_strategies, mount_routes
from infrastructure.messaging.kafka import start_kafka_consumers, stop_kafka_consumers

KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _ensure_kafka_vendor_six_moves() -> None:
    import sys

    name = "kafka.vendor.six.moves"
    if name not in sys.modules:
        module = ModuleType(name)
        setattr(module, "range", range)
        setattr(module, "__path__", [])
        sys.modules[name] = module


_ensure_kafka_vendor_six_moves()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if KAFKA_ENABLED and KAFKA_BOOTSTRAP_SERVERS:
        try:
            logging.info("[service-external] Kafka consumers → %s", KAFKA_BOOTSTRAP_SERVERS)
            await start_kafka_consumers(KAFKA_BOOTSTRAP_SERVERS)
        except Exception as e:
            logging.warning("[service-external] Kafka consumers not started: %s", e)
    else:
        logging.info("[service-external] Kafka disabled or KAFKA_BOOTSTRAP_SERVERS empty")

    yield

    if KAFKA_ENABLED and KAFKA_BOOTSTRAP_SERVERS:
        try:
            await stop_kafka_consumers()
        except Exception as e:
            logging.warning("[service-external] Kafka stop: %s", e)


app = FastAPI(title="TravelHub Service External", version="0.2.0", lifespan=lifespan)
mount_routes(app)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "service-external",
        "kafka_enabled": KAFKA_ENABLED,
        "integrations": integration_strategies(),
    }


@app.get("/ready")
def ready():
    if os.getenv("TH_PAYMENT_SKIP_READY", "").lower() in ("1", "true", "yes"):
        return {"ready": True, "skipped": True}
    return {"ready": True}
