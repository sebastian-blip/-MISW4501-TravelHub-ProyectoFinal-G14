from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import derecho_olvido
from .db_client import get_tfo

app = FastAPI(
    title="PoC-5 User Service (derecho al olvido)",
    version="0.1.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(derecho_olvido.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/audit/tfo/{user_id}")
async def audit_tfo(user_id: str):
    """Compute TFO for a user; delegates to DB service."""
    data = await get_tfo(user_id)
    return data

