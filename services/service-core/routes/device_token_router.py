"""Endpoints para que el cliente registre/borre el token de push de su
dispositivo. Todos JWT-only — el `user_id` se deriva del Bearer; el cliente
nunca lo manda en el body.

Contrato (alineado con el cliente Android `DeviceTokenApi`):

    POST   /users/me/device-tokens
        body: { "token": "...", "platform": "android"|"ios"|"web", "app_version": "0.1.1" }
        201 Created — devuelve el `id` interno y `last_seen_at`.

    DELETE /users/me/device-tokens
        body: { "token": "..." }
        204 No Content — borra solo este token (logout local de este device).
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_session
from user_service.repository.device_token_repository import (
    DeviceTokenRepository,
    VALID_PLATFORMS,
)
from user_service.utils.security import get_current_user


router = APIRouter(prefix="/users/me/device-tokens", tags=["Device Tokens"])


class RegisterDeviceTokenRequest(BaseModel):
    token: str
    platform: str
    app_version: Optional[str] = None


class DeleteDeviceTokenRequest(BaseModel):
    token: str


class DeviceTokenResponse(BaseModel):
    id: UUID
    user_id: UUID
    platform: str
    app_version: Optional[str]
    last_seen_at: str
    created_at: str


@router.post("", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(
    body: RegisterDeviceTokenRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upsert del token. Idempotente: re-registrar el mismo token solo
    refresca `last_seen_at`. El cliente debe llamar este endpoint cada vez
    que FCM/APNs emita un token nuevo (`onNewToken`)."""
    if body.platform not in VALID_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"platform must be one of {sorted(VALID_PLATFORMS)}",
        )
    if not body.token or not body.token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="token must be non-empty",
        )

    user_id = UUID(current_user["user_id"])
    repo = DeviceTokenRepository(session)
    record = await repo.upsert(
        user_id=user_id,
        token=body.token.strip(),
        platform=body.platform,
        app_version=body.app_version,
    )
    return DeviceTokenResponse(
        id=record.id,
        user_id=record.user_id,
        platform=record.platform,
        app_version=record.app_version,
        last_seen_at=record.last_seen_at.isoformat(),
        created_at=record.created_at.isoformat(),
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_token(
    body: DeleteDeviceTokenRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Borra el token de este device para que el backend pare de mandar
    pushes acá. Tolerante a que el token no exista (idempotente)."""
    user_id = UUID(current_user["user_id"])
    repo = DeviceTokenRepository(session)
    await repo.delete(user_id=user_id, token=body.token.strip())
    return None
