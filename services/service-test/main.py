from dotenv import load_dotenv
load_dotenv()

import os
import logging
from contextlib import asynccontextmanager
from types import ModuleType

from fastapi import FastAPI

from app.infrastructure.database import init_db
from app.kafka.producer import start_producer, stop_producer
from app.kafka.consumer import start_consumer, stop_consumer
from app.kafka.reservation_consumer import start_reservation_consumer, stop_reservation_consumer
from app.routes.check_router import router as check_router
from app.routes.test_results_router import router as test_results_router

# Configuración de Kafka
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME", "")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "")
KAFKA_CA_PATH = os.getenv("KAFKA_CA_PATH", "/app/certs/ca-cert.pem")

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
            if True:  # Cambiar a True si la lógica indicaba USE_SSL y ya lo removemos como en service-core
                await start_producer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=True,
                    username=KAFKA_USERNAME,
                    password=KAFKA_PASSWORD
                )
                await start_consumer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=True,
                    username=KAFKA_USERNAME,
                    password=KAFKA_PASSWORD
                )
                await start_reservation_consumer(
                    KAFKA_BOOTSTRAP_SERVERS,
                    use_ssl=True,
                    username=KAFKA_USERNAME,
                    password=KAFKA_PASSWORD
                )
            else:
                logging.warning("[Kafka] SSL no está habilitado, no se pueden iniciar los consumidores/productores.")
        except Exception as e:
            logging.warning(f"[Kafka] No disponible: {e}")
    else:
        logging.info("[Kafka] Deshabilitado (KAFKA_ENABLED=false)")

    yield

    if KAFKA_ENABLED:
        await stop_producer()
        await stop_consumer()
        await stop_reservation_consumer()


app = FastAPI(
    title="TravelHub Service Test - Kafka",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/service-test"
)

app.include_router(check_router)
app.include_router(test_results_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "service-test",
        "kafka": {
            "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
            "enabled": KAFKA_ENABLED
        }
    }


@app.get("/config/kafka")
async def get_kafka_config():
    """Endpoint para verificar la configuración actual de Kafka."""
    return {
        "kafka_enabled": KAFKA_ENABLED,
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "auth_configured": bool(KAFKA_USERNAME and KAFKA_PASSWORD)
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server... Kafka AWS: {KAFKA_BOOTSTRAP_SERVERS}")
    uvicorn.run(app, host="0.0.0.0", port=8001)