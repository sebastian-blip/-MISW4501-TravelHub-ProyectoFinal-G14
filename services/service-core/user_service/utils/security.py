import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependencia para proteger endpoints con JWT.
    Extrae y valida el token Bearer del header Authorization.
    Retorna el payload del token (incluyendo user_id, email, etc.)
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[dict]:
    """
    Dependencia opcional para JWT.
    Retorna el payload si el token es válido, de lo contrario None.
    """
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("user_id") is None:
            return None
        return payload
    except JWTError:
        return None
