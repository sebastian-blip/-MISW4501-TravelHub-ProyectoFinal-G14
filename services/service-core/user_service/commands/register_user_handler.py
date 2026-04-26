import uuid
import logging
from mediatr import Mediator
import httpx
import os

from infrastructure.database import async_session_maker
from user_service.commands.user_commands import RegisterUserCommand, RegisterUserResponse
from user_service.repository.user_repository import UserRepository, VALID_USER_TYPES
from user_service.utils.security import hash_password
from infrastructure.messaging.kafka.producer import publish_user_check
from infrastructure.messaging.kafka.reply_consumer import wait_for_reply

url_mail=os.getenv("MAILER")
token_mailer = os.getenv("TOKEN_SOPORT_SERVICES")

@Mediator.handler
async def handle_register_user(command: RegisterUserCommand) -> RegisterUserResponse:
    if command.user_type not in VALID_USER_TYPES:
        raise ValueError(f"user_type inválido. Valores permitidos: {VALID_USER_TYPES}")


    correlation_id = str(uuid.uuid4())
    #await publish_user_check(email=command.email, correlation_id=correlation_id)

    # try:
    #     reply = await wait_for_reply(correlation_id, timeout=5.0)
    #     if reply.get("exists"):
    #         logging.warning(f"[Register] Kafka reporta que '{command.email}' ya existe en service-test")
    #         raise ValueError(f"El email '{command.email}' ya está registrado en el sistema")
    # except TimeoutError:
    #
    #     logging.warning("[Register] Sin respuesta de Kafka, validando solo en DB local")

    async with async_session_maker() as session:
        repo = UserRepository(session)
        if await repo.email_exists(command.email):
            raise ValueError(f"El email '{command.email}' ya est registrado")

        user = await repo.create(
            email=command.email,
            password_hash=hash_password(command.password),
            first_name=command.first_name,
            last_name=command.last_name,
            user_type=command.user_type,
            phone=command.phone,
            country_id=command.country_id,
        )

    async with httpx.AsyncClient() as client:

        headers = {
            "Authorization": f"Bearer {token_mailer}",
            "Content-Type": "application/json",

        }
        response = await client.post(url_mail, json={
         "email": command.email,
        "message": f"tu contrasena es {command.password}"
        }, headers=headers)
        print(response.json())



    return RegisterUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user.user_type,
    )
