from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models.user import User

VALID_USER_TYPES = {"traveler", "hotel_admin", "agency", "admin"}


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        statement = select(User).where(User.id == UUID(user_id) if isinstance(user_id, str) else user_id).where(User.active == True)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.first() is not None

    async def create(
        self,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        user_type: str,
        phone: Optional[str] = None,
        country_id: Optional[UUID] = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            phone=phone,
            country_id=country_id,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
