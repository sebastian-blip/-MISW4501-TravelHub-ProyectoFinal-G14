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
from routes.reservation_router import router as reservation_router
from routes.reservation_state_machine_router import router as reservation_flow_router
from routes.test_router import router as test_router

# Configuración de Kafka
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME", "")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "")

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
            logging.info(f"[Kafka] Conectando a AWS: {KAFKA_BOOTSTRAP_SERVERS}")
            if True:  # Cambiado a True ya que USE_SSL no está definido
                await start_producer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=True,
                    username=KAFKA_USERNAME,
                    password=KAFKA_PASSWORD
                )
                await start_reply_consumer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=True,
                    username=KAFKA_USERNAME,
                    password=KAFKA_PASSWORD
                )
            else:
                await start_producer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=False
                )
                await start_reply_consumer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=False
                )
        except Exception as e:
            logging.warning(f"[Kafka] No disponible: {e}")
    else:
        logging.info("[Kafka] Deshabilitado (KAFKA_ENABLED=false)")

    yield

    if KAFKA_ENABLED:
        await stop_producer()
        await stop_reply_consumer()


app = FastAPI(
    title="TravelHub User Service",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/service-core"
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(accommodation_router)
app.include_router(reservation_router)
app.include_router(reservation_flow_router)
app.include_router(test_router)


@app.get("/config/kafka")
async def get_kafka_config():
    """Endpoint para verificar la configuración actual de Kafka."""
    return {
        "kafka_enabled": KAFKA_ENABLED,
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "auth_configured": bool(KAFKA_USERNAME and KAFKA_PASSWORD)
    }


# if __name__ == "__main__":
#     import uvicorn
#     print(f"Starting server... Kafka AWS: {KAFKA_BOOTSTRAP_SERVERS}")
#     uvicorn.run(app, host="0.0.0.0", port=8000)