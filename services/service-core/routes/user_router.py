from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from mediatr import Mediator

from user_service.queries.user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetUserProfileQuery,
    UserResponse,
    UserProfileResponse,
)
from user_service.utils.security import get_current_user


router = APIRouter(prefix="/users", tags=["Users"])


def get_mediator() -> Mediator:
    return Mediator()


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    mediator: Mediator = Depends(get_mediator),
):
    """Obtiene el perfil completo del usuario autenticado con conteo de reservas."""
    try:
        user_id = UUID(current_user["user_id"])
        return await mediator.send(GetUserProfileQuery(user_id=user_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    mediator: Mediator = Depends(get_mediator),
):
    """Obtiene un usuario por ID (CQRS read side)."""
    try:
        return await mediator.send(GetUserByIdQuery(user_id=user_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    mediator: Mediator = Depends(get_mediator),
):
    """Obtiene un usuario por email (CQRS read side)."""
    try:
        return await mediator.send(GetUserByEmailQuery(email=email))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
