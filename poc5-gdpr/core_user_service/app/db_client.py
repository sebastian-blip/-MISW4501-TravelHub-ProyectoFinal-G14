"""HTTP client for PoC-5 DB Service (DuckDB)."""
import httpx
from .config import DB_API_URL


async def get_user(user_id: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{DB_API_URL}/users/{user_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def anonymize_user(user_id: str) -> bool:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{DB_API_URL}/users/{user_id}/anonymize")
        r.raise_for_status()
        return r.json().get("updated", False)


async def record_solicitud_olvido(user_id: str, timestamp, payload: dict | None) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{DB_API_URL}/audit/solicitud-olvido",
            json={
                "user_id": user_id,
                "timestamp": timestamp.isoformat(),
                "payload": payload or {},
            },
        )
        r.raise_for_status()


async def get_tfo(user_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{DB_API_URL}/audit/tfo/{user_id}")
        r.raise_for_status()
        return r.json()
