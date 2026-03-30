from typing import Optional
from uuid import UUID

from domain.models.user import User

VALID_USER_TYPES = {"traveler", "hotel_admin", "agency", "admin"}


class UserRepository:

    async def get_by_email(self, email: str) -> Optional[User]:
        return await User.get_or_none(email=email)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return await User.get_or_none(id=user_id, active=True)

    async def email_exists(self, email: str) -> bool:
        return await User.filter(email=email).exists()

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
        return await User.create(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            phone=phone,
            country_id=country_id,
        )
