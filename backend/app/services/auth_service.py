from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
import jwt
from jwt import InvalidTokenError
from redis.asyncio import Redis
import structlog

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.schemas.user import User
from app.repositories.user_repo import UserRepository
from app.models.user import User as UserModel

logger = structlog.get_logger(__name__)


class AuthService:
    """Auth service backed by PostgreSQL users and Redis for refresh token revocation."""

    def __init__(self, redis: Redis, user_repo: UserRepository | None):
        self.redis = redis
        self.user_repo = user_repo

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        if not self.user_repo:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth service not ready")
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        user_schema = self._to_schema(user)
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        await self._store_refresh_token(refresh_token, str(user.id))
        return user_schema, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[User, str, str]:
        payload = self._decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        await self._assert_refresh_token_valid(refresh_token, user_id)

        if not self.user_repo:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth service not ready")
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        user_schema = self._to_schema(user)

        access_token = create_access_token(subject=str(user.id))
        new_refresh = create_refresh_token(subject=str(user.id))

        await self._store_refresh_token(new_refresh, str(user.id))
        await self.redis.delete(self._refresh_key(refresh_token))
        return user_schema, access_token, new_refresh

    async def logout(self, refresh_token: str) -> None:
        payload = self._decode_token(refresh_token, expected_type="refresh")
        key = self._refresh_key(refresh_token)
        await self.redis.delete(key)
        logger.info("logout", user_id=payload.get("sub"))

    @staticmethod
    def _to_schema(user: UserModel) -> User:
        return User(
            id=str(user.id),
            email=user.email,
            name=user.name,
            roles=user.roles or [],
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _decode_token(self, token: str, expected_type: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from exc

        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: {token_type}",
            )
        return payload

    async def _store_refresh_token(self, token: str, user_id: str) -> None:
        key = self._refresh_key(token)
        exp = settings.REFRESH_TOKEN_EXPIRE_DAYS
        await self.redis.setex(key, timedelta(days=exp), user_id)

    async def _assert_refresh_token_valid(self, token: str, user_id: str | None) -> None:
        key = self._refresh_key(token)
        stored_user = await self.redis.get(key)
        if stored_user is None or stored_user != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked",
            )

    @staticmethod
    def _refresh_key(token: str) -> str:
        return f"auth:refresh:{token}"
