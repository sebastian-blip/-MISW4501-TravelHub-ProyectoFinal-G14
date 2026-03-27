from dotenv import load_dotenv
load_dotenv()  # carga services/service-core/.env antes de leer os.getenv()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from infrastructure.database import init_db
from routes.health_router import router as health_router
from routes.auth_router import router as auth_router
from routes.user_router import router as user_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await Tortoise.close_connections()


app = FastAPI(
    title="TravelHub User Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
