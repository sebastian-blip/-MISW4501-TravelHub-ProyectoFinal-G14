from dotenv import load_dotenv
load_dotenv()

import os
import logging
from contextlib import asynccontextmanager
from types import ModuleType

from fastapi import FastAPI

from infrastructure.database import init_db
from infrastructure.messaging.kafka.producer import start_producer, stop_producer
from infrastructure.messaging.kafka.reply_consumer import start_reply_consumer, stop_reply_consumer
from routes.health_router import router as health_router
from routes.auth_router import router as auth_router
from routes.user_router import router as user_router
from routes.accommodation_router import router as accommodation_router
from routes.state_machine_router import router as state_machine_router
from routes.reservation_router import router as reservation_router

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"

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
    await init_db()

    if KAFKA_ENABLED:
        try:
            await start_producer(KAFKA_BOOTSTRAP_SERVERS)
            await start_reply_consumer(KAFKA_BOOTSTRAP_SERVERS)
        except Exception as e:
            logging.warning(f"Kafka no disponible, registro funcionará solo con DB local: {e}")
    else:
        logging.info("Kafka deshabilitado (KAFKA_ENABLED=false)")

    yield

    if KAFKA_ENABLED:
        await stop_producer()
        await stop_reply_consumer()


app = FastAPI(
    title="TravelHub User Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(accommodation_router)
app.include_router(state_machine_router)
app.include_router(reservation_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
