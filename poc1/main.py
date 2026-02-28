from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from poc1.infrastructure.database import TORTOISE_ORM
from poc1.routes.health_router import router as health_router
from poc1.routes.hotel_router import router as hotel_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    await Tortoise.close_connections()

app = FastAPI(
    title="TravelHub API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(hotel_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("poc1.main:app", host="0.0.0.0", port=8000, reload=True)