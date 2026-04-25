import os
from dotenv import load_dotenv, find_dotenv

# Prefer local overrides without breaking Docker/Compose-provided env vars.
# Order:
# - If ENV_FILE is set, load that file.
# - Else load .env.local (if present), then .env as fallback.
# Never override already-defined environment variables.
_env_file = os.getenv("ENV_FILE")
if _env_file:
    load_dotenv(find_dotenv(_env_file, usecwd=True), override=False)
else:
    load_dotenv(find_dotenv(".env.local", usecwd=True), override=False)
    load_dotenv(find_dotenv(".env", usecwd=True), override=False)
import logging
from contextlib import asynccontextmanager
from types import ModuleType

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from routes.hotel_admin_router import router as hotel_admin_router
from infrastructure.messaging.kafka.producer import publish_prueba
from infrastructure.messaging.kafka.reply_consumer import wait_for_reply

# Configuración de Kafka
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME", "")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "")
KAFKA_LOCAL = os.getenv("KAFKA_LOCAL", "false").lower() == "true"

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
            # NOTE: producer/reply_consumer decide SASL/PLAINTEXT using KAFKA_LOCAL + username/password env vars.
            # Keep start_* params for backward compat, but local mode must not force SSL.
            await start_producer(
                KAFKA_BOOTSTRAP_SERVERS,
                use_ssl=not KAFKA_LOCAL,
                username=KAFKA_USERNAME,
                password=KAFKA_PASSWORD,
            )
            await start_reply_consumer(
                KAFKA_BOOTSTRAP_SERVERS,
                use_ssl=not KAFKA_LOCAL,
                username=KAFKA_USERNAME,
                password=KAFKA_PASSWORD,
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

# Configuración CORS - permitir cualquier origen en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",  # Permite cualquier origen incluso con envío de credenciales
    allow_credentials=True,    # Permite el envío de cookies/tokens de autorización
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(accommodation_router)
app.include_router(reservation_router)
app.include_router(reservation_flow_router)
app.include_router(test_router)
app.include_router(hotel_admin_router)


@app.get("/config/kafka")
async def get_kafka_config():
    """Endpoint para verificar la configuración actual de Kafka."""
    return {
        "kafka_enabled": KAFKA_ENABLED,
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "auth_configured": bool(KAFKA_USERNAME and KAFKA_PASSWORD)
    }

from pydantic import BaseModel

class PruebaRequest(BaseModel):
    mensaje: str

@app.post("/prueba/mensaje")
async def enviar_prueba(request: PruebaRequest):
    cid = await publish_prueba(mensaje=request.mensaje)
    reply = await wait_for_reply(cid, timeout=5.0)
    return reply

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server... Kafka AWS: {KAFKA_BOOTSTRAP_SERVERS}")
    uvicorn.run(app, host="0.0.0.0", port=8000)