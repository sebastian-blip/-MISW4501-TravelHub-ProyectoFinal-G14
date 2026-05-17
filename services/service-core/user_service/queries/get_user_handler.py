from mediatr import Mediator

from infrastructure.database import async_session_maker
from user_service.queries.user_queries import GetUserByIdQuery, GetUserByEmailQuery, UserResponse, DeactivatedUserQuery
from user_service.repository.user_repository import UserRepository


@Mediator.handler
class GetUserByIdQueryHandler:

    async def handle(self, query: GetUserByIdQuery) -> UserResponse:
        async with async_session_maker() as session:
            repository = UserRepository(session)
            user = await repository.get_by_id(str(query.user_id))
            if user is None:
                raise ValueError(f"Usuario '{query.user_id}' no encontrado")
            return UserResponse.from_orm(user)


@Mediator.handler
class GetUserByEmailQueryHandler:

    async def handle(self, query: GetUserByEmailQuery) -> UserResponse:
        async with async_session_maker() as session:
            repository = UserRepository(session)
            user = await repository.get_by_email(query.email)
            if user is None:
                raise ValueError(f"Usuario '{query.email}' no encontrado")
            return UserResponse.from_orm(user)

@Mediator.handler
class DeactivatedUserQueryHandler:
    async def handle(self, query: DeactivatedUserQuery) -> dict:
        async with async_session_maker() as session:
            repository = UserRepository(session)
            user = await repository.anonymize_user_data(str(query.user_id))
            if user is None:
                raise ValueError(f"Usuario '{query.user_id}' no encontrado")
            return {'deactivated': True, 'user_id': str(query.user_id)}
