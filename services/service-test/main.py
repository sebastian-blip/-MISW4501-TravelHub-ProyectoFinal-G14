import os
import logging
from contextlib import asynccontextmanager
from types import ModuleType

from fastapi import FastAPI

from app.kafka.producer import start_producer, stop_producer
from app.kafka.consumer import start_consumer, stop_consumer
from app.routes.check_router import router as check_router

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def _ensure_kafka_vendor_six_moves():
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
    logging.info(f"Conectando a Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    await start_producer(KAFKA_BOOTSTRAP_SERVERS)
    await start_consumer(KAFKA_BOOTSTRAP_SERVERS)
    yield
    await stop_producer()
    await stop_consumer()


app = FastAPI(
    title="TravelHub Service Test - Kafka Demo",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(check_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "service-test", "kafka": KAFKA_BOOTSTRAP_SERVERS}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)