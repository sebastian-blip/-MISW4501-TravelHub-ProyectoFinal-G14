"""
PoC-5 DB Service: DuckDB-backed HTTP API for all services.
Replaces direct PostgreSQL; Redis remains the message broker.
"""
import asyncio
import json
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import get_connection, close_db
import threading

_db_lock = threading.Lock()


def _run(f):
    """Run blocking DuckDB calls in thread pool; single connection, serialized access."""
    def wrapper(*args, **kwargs):
        with _db_lock:
            conn = get_connection()
            return f(conn, *args, **kwargs)
    return wrapper


# --- Users ---
@_run
def _get_user(conn, user_id: str) -> dict | None:
    row = conn.execute(
        "SELECT id, email, name, anonymized, created_at, updated_at FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "email": row[1],
        "name": row[2],
        "anonymized": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
        "updated_at": row[5].isoformat() if row[5] else None,
    }


@_run
def _anonymize_user(conn, user_id: str) -> bool:
    row = conn.execute(
        """
        UPDATE users
        SET email = 'anon_' || id::varchar || '@deleted.local',
            name = 'DELETED',
            anonymized = TRUE,
            updated_at = current_timestamp
        WHERE id = ? AND anonymized = FALSE
        RETURNING id
        """,
        [user_id],
    ).fetchone()
    return row is not None


# --- Audit ---
@_run
def _record_solicitud_olvido(conn, user_id: str, timestamp: datetime, payload: dict) -> str:
    row = conn.execute(
        """
        INSERT INTO audit_events (event_type, user_id, consumer_id, timestamp, payload)
        VALUES ('solicitud_olvido', ?, NULL, ?, ?)
        RETURNING id
        """,
        [user_id, timestamp, json.dumps(payload or {})],
    ).fetchone()
    return str(row[0]) if row else ""


@_run
def _record_completado(conn, user_id: str, consumer_id: str, timestamp: datetime) -> None:
    conn.execute(
        """
        INSERT INTO audit_events (event_type, user_id, consumer_id, timestamp, payload)
        VALUES ('completado', ?, ?, ?, '{}')
        """,
        [user_id, consumer_id, timestamp],
    )


@_run
def _get_tfo(conn, user_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT timestamp FROM audit_events
        WHERE user_id = ? AND event_type = 'solicitud_olvido'
        ORDER BY timestamp DESC LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if not row:
        return None
    t0 = row[0]
    rows = conn.execute(
        "SELECT consumer_id, timestamp FROM audit_events WHERE user_id = ? AND event_type = 'completado'",
        [user_id],
    ).fetchall()
    completados = [{"consumer_id": r[0], "timestamp": r[1].isoformat() if r[1] else None} for r in rows]
    if not completados:
        return {"t0": t0, "completados": []}
    max_ts = max(r[1] for r in rows)
    tfo_seconds = (max_ts - t0).total_seconds()
    return {
        "t0": t0,
        "completados": completados,
        "tfo_seconds": round(tfo_seconds, 2),
        "tfo_under_3_min": tfo_seconds < 180,
    }


# --- Read model ---
@_run
def _anonymize_read_model(conn, user_id: str) -> bool:
    row = conn.execute(
        """
        UPDATE user_read_model
        SET email = 'anon_' || id::varchar || '@deleted.local',
            name = 'DELETED',
            anonymized = TRUE,
            updated_at = current_timestamp
        WHERE id = ? AND (anonymized = FALSE OR anonymized IS NULL)
        RETURNING id
        """,
        [user_id],
    ).fetchone()
    return row is not None


# --- Reservations ---
@_run
def _anonymize_reservations(conn, user_id: str, anonymous_user_id: str) -> int:
    rows = conn.execute(
        """
        UPDATE reservations
        SET user_id = ?, updated_at = current_timestamp
        WHERE user_id = ?
        RETURNING id
        """,
        [anonymous_user_id, user_id],
    ).fetchall()
    return len(rows)


# --- Analytics ---
@_run
def _anonymize_analytics(conn, user_id: str, anonymous_user_id: str) -> None:
    conn.execute(
        """
        UPDATE analytics_user_activity
        SET user_id = ?, anonymized = TRUE
        WHERE user_id = ? AND (anonymized = FALSE OR anonymized IS NULL)
        """,
        [anonymous_user_id, user_id],
    )


# --- Raw audit_events for reporting (e.g. docker exec equivalent) ---
@_run
def _list_audit_events(conn) -> list:
    rows = conn.execute(
        "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp"
    ).fetchall()
    return [
        {"event_type": r[0], "user_id": str(r[1]), "consumer_id": r[2], "timestamp": r[3].isoformat() if r[3] else None}
        for r in rows
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_connection()  # init on startup
    yield
    close_db()


app = FastAPI(title="PoC-5 DB Service (DuckDB)", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "db": "duckdb"}


# --- Users ---
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    row = await asyncio.to_thread(_get_user, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


@app.post("/users/{user_id}/anonymize")
async def anonymize_user(user_id: str):
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    updated = await asyncio.to_thread(_anonymize_user, user_id)
    return {"updated": updated}


# --- Audit ---
class SolicitudOlvidoBody(BaseModel):
    user_id: str
    timestamp: datetime
    payload: dict | None = None


@app.post("/audit/solicitud-olvido")
async def record_solicitud_olvido(body: SolicitudOlvidoBody):
    await asyncio.to_thread(_record_solicitud_olvido, body.user_id, body.timestamp, body.payload or {})
    return {"ok": True}


class CompletadoBody(BaseModel):
    user_id: str
    consumer_id: str
    timestamp: datetime


@app.post("/audit/completado")
async def record_completado(body: CompletadoBody):
    await asyncio.to_thread(_record_completado, body.user_id, body.consumer_id, body.timestamp)
    return {"ok": True}


@app.get("/audit/tfo/{user_id}")
async def get_tfo(user_id: str):
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    data = await asyncio.to_thread(_get_tfo, user_id)
    if not data:
        return {"user_id": user_id, "t0": None, "completados": [], "tfo_seconds": None}
    return {
        "user_id": user_id,
        "t0": data["t0"].isoformat(),
        "completados": data["completados"],
        "tfo_seconds": data.get("tfo_seconds"),
        "tfo_under_3_min": data.get("tfo_under_3_min"),
    }


# --- Read model ---
@app.post("/read-model/{user_id}/anonymize")
async def anonymize_read_model(user_id: str):
    updated = await asyncio.to_thread(_anonymize_read_model, user_id)
    return {"updated": updated}


# --- Reservations ---
class ReservationsAnonymizeBody(BaseModel):
    user_id: str
    anonymous_user_id: str


@app.post("/reservations/anonymize")
async def anonymize_reservations(body: ReservationsAnonymizeBody):
    count = await asyncio.to_thread(
        _anonymize_reservations, body.user_id, body.anonymous_user_id
    )
    return {"updated": count}


# --- Analytics ---
class AnalyticsAnonymizeBody(BaseModel):
    user_id: str
    anonymous_user_id: str


@app.post("/analytics/anonymize")
async def anonymize_analytics(body: AnalyticsAnonymizeBody):
    await asyncio.to_thread(_anonymize_analytics, body.user_id, body.anonymous_user_id)
    return {"ok": True}


# --- Debug / evidence: list audit_events (replaces docker exec psql audit_events) ---
@app.get("/audit/events")
async def list_audit_events():
    events = await asyncio.to_thread(_list_audit_events)
    return {"events": events}


@_run
def _list_users(conn) -> list:
    rows = conn.execute("SELECT id, email, name, anonymized FROM users").fetchall()
    return [{"id": str(r[0]), "email": r[1], "name": r[2], "anonymized": r[3]} for r in rows]


@_run
def _list_read_model(conn) -> list:
    rows = conn.execute("SELECT id, email, name, anonymized FROM user_read_model").fetchall()
    return [{"id": str(r[0]), "email": r[1], "name": r[2], "anonymized": r[3]} for r in rows]


@_run
def _list_reservations(conn, limit: int = 5) -> list:
    rows = conn.execute("SELECT id, user_id FROM reservations LIMIT ?", [limit]).fetchall()
    return [{"id": str(r[0]), "user_id": str(r[1])} for r in rows]


@_run
def _list_analytics(conn, limit: int = 5) -> list:
    rows = conn.execute("SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT ?", [limit]).fetchall()
    return [{"id": str(r[0]), "user_id": str(r[1]), "anonymized": r[2]} for r in rows]


@app.get("/evidence/users")
async def evidence_users():
    data = await asyncio.to_thread(_list_users)
    return {"rows": data}


@app.get("/evidence/read-model")
async def evidence_read_model():
    data = await asyncio.to_thread(_list_read_model)
    return {"rows": data}


@app.get("/evidence/reservations")
async def evidence_reservations(limit: int = 5):
    data = await asyncio.to_thread(_list_reservations, limit)
    return {"rows": data}


@app.get("/evidence/analytics")
async def evidence_analytics(limit: int = 5):
    data = await asyncio.to_thread(_list_analytics, limit)
    return {"rows": data}
