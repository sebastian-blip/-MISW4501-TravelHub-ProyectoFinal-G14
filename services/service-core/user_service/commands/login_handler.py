from mediatr import Mediator

from infrastructure.database import async_session_maker
from user_service.commands.user_commands import LoginCommand, LoginResponse
from user_service.repository.user_repository import UserRepository
from user_service.utils.security import verify_password, create_access_token


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

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "user_type": user.user_type,
    })

    return LoginResponse(access_token=token, token_type="bearer")
