from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class RegisterUserCommand:
    email: str
    password: str
    first_name: str
    last_name: str
    user_type: str  # 'traveler', 'hotel_admin', 'agency', 'admin'
    phone: Optional[str] = None
    country_id: Optional[UUID] = None


@dataclass
class LoginCommand:
    email: str
    password: str


@dataclass
class RegisterUserResponse:
    id: UUID
    email: str
    first_name: str
    last_name: str
    user_type: str


@dataclass
class LoginResponse:
    access_token: str
    token_type: str
    user_type: str
