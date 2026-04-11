from fastapi import APIRouter, Depends, HTTPException, status
from mediatr import Mediator

from user_service.commands.user_commands import (
    RegisterUserCommand,
    RegisterUserResponse,
    LoginCommand,
    LoginResponse,
)
import user_service.commands.register_user_handler  # registra handler
import user_service.commands.login_handler           # registra handler

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_mediator() -> Mediator:
    return Mediator()


@router.post("/register", response_model=RegisterUserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    command: RegisterUserCommand,
    mediator: Mediator = Depends(get_mediator),
):
    """Registra un nuevo usuario (CQRS write side)."""
    try:
        return await mediator.send(command)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    command: LoginCommand,
    mediator: Mediator = Depends(get_mediator),
):
    """Autentica un usuario y retorna un JWT (CQRS write side)."""
    try:
        return await mediator.send(command)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
