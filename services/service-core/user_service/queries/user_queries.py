from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GetUserByIdQuery:
    user_id: UUID


@dataclass
class GetUserByEmailQuery:
    email: str


@dataclass
class UserResponse:
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    country_id: Optional[UUID]
    user_type: str
    email_verified: bool
    mfa_enabled: bool
    active: bool

    @classmethod
    def from_orm(cls, user) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            country_id=user.country_id,
            user_type=user.user_type,
            email_verified=user.email_verified,
            mfa_enabled=user.mfa_enabled,
            active=user.active,
        )
