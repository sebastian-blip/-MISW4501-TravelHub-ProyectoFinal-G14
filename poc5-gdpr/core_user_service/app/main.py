from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db, close_db, get_pool
from .routes import derecho_olvido


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="PoC-5 User Service (derecho al olvido)",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(derecho_olvido.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/audit/tfo/{user_id}")
async def get_tfo(user_id: str, pool=Depends(get_pool)):
    """Compute TFO for a user: max(completado timestamps) - T0. For reporting."""
    from uuid import UUID
    uid = UUID(user_id)
    row = await pool.fetchrow(
        """
        SELECT timestamp as t0 FROM audit_events
        WHERE user_id = $1 AND event_type = 'solicitud_olvido'
        ORDER BY timestamp DESC LIMIT 1
        """,
        uid,
    )
    if not row:
        return {"user_id": user_id, "t0": None, "completados": [], "tfo_seconds": None}
    t0 = row["t0"]
    rows = await pool.fetch(
        "SELECT consumer_id, timestamp FROM audit_events WHERE user_id = $1 AND event_type = 'completado'",
        uid,
    )
    completados = [{"consumer_id": r["consumer_id"], "timestamp": r["timestamp"].isoformat()} for r in rows]
    if not completados:
        return {"user_id": user_id, "t0": t0.isoformat(), "completados": [], "tfo_seconds": None}
    max_ts = max(r["timestamp"] for r in rows)
    tfo_seconds = (max_ts - t0).total_seconds()
    return {
        "user_id": user_id,
        "t0": t0.isoformat(),
        "completados": completados,
        "tfo_seconds": round(tfo_seconds, 2),
        "tfo_under_3_min": tfo_seconds < 180,
    }
