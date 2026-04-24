from uuid import UUID

from mediatr import Mediator
from sqlmodel import select

from infrastructure.database import async_session_maker
from user_service.commands.user_commands import LoginCommand, LoginResponse
from user_service.repository.user_repository import UserRepository
from user_service.utils.security import verify_password, create_access_token
from domain.models.hotel import Hotel


@Mediator.handler
async def handle_login(command: LoginCommand) -> LoginResponse:
    async with async_session_maker() as session:
        repo = UserRepository(session)

        user = await repo.get_by_email(command.email)
        #if user is None or not verify_password(command.password, user.password_hash):
        if user is None or  (command.password != user.password_hash) is True:
            raise ValueError("Credenciales inválidas")

        if not user.active:
            raise ValueError("Usuario inactivo")

        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "user_type": user.user_type,
        }

        if user.user_type == "hotel_admin":
            statement = select(Hotel).where(Hotel.owner_user_id == user.id)
            result = await session.execute(statement)
            hotel = result.scalar_one_or_none()
            if hotel:
                payload["hotel_id"] = str(hotel.id)

    token = create_access_token(payload)

    return LoginResponse(access_token=token, token_type="bearer", user_type=user.user_type)
