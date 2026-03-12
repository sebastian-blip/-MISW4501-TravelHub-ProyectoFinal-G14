import os
from prometheus_fastapi_instrumentator import Instrumentator
import logging

from contextlib import asynccontextmanager
from types import ModuleType
from fastapi import FastAPI
from tortoise import Tortoise

from infrastructure.database import TORTOISE_ORM, init_db
from routes.health_router import router as health_router
from routes.hotel_router import router as hotel_router
from routes.reservation_routers.queries import router as reservation_query_router
from routes.reservation_routers.commands import router as reservation_command_router
from hotel_service.events.publisher import EventPublisher
from infrastructure.messaging.kafka.producer import KafkaPublisher
from hotel_service.availability import AvailabilityReadModelConsumer
from infrastructure.database import init_db
from test.create_test_hotels import seed_hotels


def _ensure_kafka_vendor_six_moves():
    import sys

    name = "kafka.vendor.six.moves"
    if name not in sys.modules:
        module = ModuleType(name)
        setattr(module, "range", range)
        setattr(module, "__all__", ["range"])
        setattr(module, "__path__", [])
        sys.modules[name] = module


_ensure_kafka_vendor_six_moves()


DEV = True
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

print(f"Starting TravelHub API with Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if DEV:
        await seed_hotels()
    try:
        kafka_pub = KafkaPublisher(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        EventPublisher.set(kafka_pub)
    except Exception:
        pass
    consumer = AvailabilityReadModelConsumer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    try:
        await consumer.start()
    except Exception:
        pass
    yield
    publisher = EventPublisher.get()
    if hasattr(publisher, "stop"):
        try:
            await publisher.stop()
        except Exception:
            pass
    try:
        await consumer.stop()
    except Exception:
        pass
    await Tortoise.close_connections()

app = FastAPI(
    title="TravelHub API",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)
app.include_router(health_router)
app.include_router(hotel_router)
app.include_router(reservation_query_router)
app.include_router(reservation_command_router)
