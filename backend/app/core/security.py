from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    to_encode: dict[str, Any] = {"sub": subject, "type": token_type, "iat": now}
    expire = now + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    return create_token(subject, timedelta(minutes=minutes), token_type="access")


def create_refresh_token(subject: str, expires_days: Optional[int] = None) -> str:
    days = expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
    return create_token(subject, timedelta(days=days), token_type="refresh")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
