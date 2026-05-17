from mediatr import Mediator

from infrastructure.database import async_session_maker
from user_service.queries.user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetUserProfileQuery,
    UserResponse,
    UserProfileResponse,
)
from user_service.queries.user_queries import GetUserByIdQuery, GetUserByEmailQuery, UserResponse, DeactivatedUserQuery
from user_service.repository.user_repository import UserRepository
from reservation_service.repository.reservation_repository import ReservationRepository


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
class GetUserProfileQueryHandler:

    async def handle(self, query: GetUserProfileQuery) -> UserProfileResponse:
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(str(query.user_id))
            if user is None:
                raise ValueError(f"Usuario '{query.user_id}' no encontrado")

            reservation_repo = ReservationRepository(session)
            past_count = await reservation_repo.count_past_by_user(query.user_id)
            pending_count = await reservation_repo.count_pending_by_user(query.user_id)

            return UserProfileResponse.from_user_and_counts(user, past_count, pending_count)

@Mediator.handler
class DeactivatedUserQueryHandler:
    async def handle(self, query: DeactivatedUserQuery) -> dict:
        async with async_session_maker() as session:
            repository = UserRepository(session)
            user = await repository.anonymize_user_data(str(query.user_id))
            if user is None:
                raise ValueError(f"Usuario '{query.user_id}' no encontrado")
            return {'deactivated': True, 'user_id': str(query.user_id)}
