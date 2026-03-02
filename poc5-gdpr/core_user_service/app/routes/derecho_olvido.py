from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import uuid
from ..services.derecho_olvido_service import DerechoOlvidoService
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository
from ..config import DATABASE_URL, RABBITMQ_URL
from ..db import get_pool

router = APIRouter(prefix="/users", tags=["users"])


class DerechoOlvidoResponse(BaseModel):
    ok: bool
    message: str
    t0: str | None = None


async def get_derecho_olvido_service(
    pool=Depends(get_pool),
) -> DerechoOlvidoService:
    return DerechoOlvidoService(
        UserRepository(pool),
        AuditRepository(pool),
        RABBITMQ_URL,
    )


@router.post("/{user_id}/derecho-olvido", response_model=DerechoOlvidoResponse)
async def derecho_olvido(
    user_id: uuid.UUID,
    service: DerechoOlvidoService = Depends(get_derecho_olvido_service),
):
    ok, data = await service.execute(user_id)
    if not ok:
        if data == "user_not_found":
            raise HTTPException(status_code=404, detail="User not found")
        if data == "already_anonymized":
            raise HTTPException(status_code=400, detail="User already anonymized")
        raise HTTPException(status_code=400, detail=data or "Bad request")
    return DerechoOlvidoResponse(ok=True, message="Derecho al olvido aceptado. Propagación en curso.", t0=data)
