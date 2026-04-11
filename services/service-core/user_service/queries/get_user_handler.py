from mediatr import Mediator

from user_service.queries.user_queries import GetUserByIdQuery, GetUserByEmailQuery, UserResponse
from user_service.repository.user_repository import UserRepository


@Mediator.handler
class GetUserByIdQueryHandler:

    def __init__(self):
        self.repository = UserRepository()

    async def handle(self, query: GetUserByIdQuery) -> UserResponse:
        user = await self.repository.get_by_id(str(query.user_id))
        if user is None:
            raise ValueError(f"Usuario '{query.user_id}' no encontrado")
        return UserResponse.from_orm(user)


@Mediator.handler
class GetUserByEmailQueryHandler:

    def __init__(self):
        self.repository = UserRepository()

    async def handle(self, query: GetUserByEmailQuery) -> UserResponse:
        user = await self.repository.get_by_email(query.email)
        if user is None:
            raise ValueError(f"Usuario '{query.email}' no encontrado")
        return UserResponse.from_orm(user)
