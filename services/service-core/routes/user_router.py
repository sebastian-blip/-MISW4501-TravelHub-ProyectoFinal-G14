from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from mediatr import Mediator

from user_service.queries.user_queries import GetUserByIdQuery, GetUserByEmailQuery, UserResponse
import user_service.queries.get_user_handler  # registra handlers

router = APIRouter(prefix="/users", tags=["Users"])


def get_mediator() -> Mediator:
    return Mediator()


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
