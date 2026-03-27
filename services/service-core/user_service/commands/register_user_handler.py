from mediatr import Mediator

from user_service.commands.user_commands import RegisterUserCommand, RegisterUserResponse
from user_service.repository.user_repository import UserRepository, VALID_USER_TYPES
from user_service.utils.security import hash_password


@Mediator.handler
async def handle_register_user(command: RegisterUserCommand) -> RegisterUserResponse:
    if command.user_type not in VALID_USER_TYPES:
        raise ValueError(f"user_type inválido. Valores permitidos: {VALID_USER_TYPES}")

    repo = UserRepository()

    if await repo.email_exists(command.email):
        raise ValueError(f"El email '{command.email}' ya está registrado")

    user = await repo.create(
        email=command.email,
        password_hash=hash_password(command.password),
        first_name=command.first_name,
        last_name=command.last_name,
        user_type=command.user_type,
        phone=command.phone,
        country_id=command.country_id,
    )

    return RegisterUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user.user_type,
    )
