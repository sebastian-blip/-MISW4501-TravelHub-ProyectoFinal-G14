import logging
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from mediatr import Mediator
from sqlalchemy import select

from infrastructure.database import async_session_maker
from fastapi.responses import JSONResponse
from user_service.utils.security import get_current_user_optional
from domain.models.reservation import Reservation
from domain.models.reservation_guest import ReservationGuest
from user_service.commands.user_commands import (
    RegisterUserCommand,
    RegisterUserResponse,
    LoginCommand,
    LoginResponse,
)

from reservation_service.queries import (
    GetActivatedReservationsByUserQuery
)

from user_service.queries import DeactivatedUserQuery
import user_service.commands.register_user_handler  # registra handler
import user_service.commands.login_handler           # registra handler

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_mediator() -> Mediator:
    return Mediator()


async def _link_guest_reservations(user_id: UUID, email: str) -> None:
    """
    Busca reservas creadas como invitado cuyo guest principal tenga
    el mismo email del usuario recién registrado y las vincula.
    """
    async with async_session_maker() as session:
        stmt = (
            select(Reservation)
            .join(ReservationGuest, Reservation.id == ReservationGuest.reservation_id)
            .where(Reservation.user_guest_id.isnot(None))
            .where(ReservationGuest.is_primary == True)
            .where(ReservationGuest.email == email)
        )
        result = await session.execute(stmt)
        reservations = result.scalars().all()

        for reservation in reservations:
            reservation.user_id = user_id
            reservation.user_guest_id = None

        if reservations:
            await session.commit()


@router.post("/register", response_model=RegisterUserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    command: RegisterUserCommand,
    mediator: Mediator = Depends(get_mediator),
):
    """Registra un nuevo usuario (CQRS write side)."""
    try:
        response = await mediator.send(command)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    try:
        await _link_guest_reservations(response.id, response.email)
    except Exception:
        logging.exception("[Auth] Error sincronizando reservas de invitado")

    return response


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


@router.post('/deactivated', status_code=status.HTTP_204_NO_CONTENT)
async def deactivated(
        current_user: Optional[dict] = Depends(get_current_user_optional)
):
    jwt_user_id = current_user.get("user_id") if current_user else None

    if jwt_user_id:
        user_id = jwt_user_id
    else:
        return HTTPException(
            status_code=401,
            detail="Se requiere autenticación (Bearer token)"
        )
    try:
        mediator = get_mediator()
        query = GetActivatedReservationsByUserQuery(user_id=user_id)
        result = await mediator.send_async(query)
        if len(result.items) > 0:
            message = {
                  "error": "conflict",
                  "message": "No se puede desactivar el usuario porque tiene reservas confirmadas activas.",
                  "code": "USER_HAS_ACTIVE_RESERVATIONS",
                  "details": {
                    "active_reservations_count": len(result.items)
                  }
                }
            return JSONResponse(status_code=403, content=message)

        else:
            query = DeactivatedUserQuery(user_id=user_id)
            result = await mediator.send_async(query)
            return JSONResponse(status_code=200, content={'details': f'Usuario con id {result.get('user_id')} desactivado'})

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=None)

