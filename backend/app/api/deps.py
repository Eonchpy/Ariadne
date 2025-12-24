from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
from redis.asyncio import Redis
import structlog

from app.config import settings
from app.core.cache import redis_dependency
from app.db import get_db_session
from app.repositories.user_repo import UserRepository
from app.schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
logger = structlog.get_logger(__name__)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    redis: Annotated[Redis, Depends(redis_dependency)],
    session=Depends(get_db_session),
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    repo = UserRepository(session)
    user_model = await repo.get(user_id)
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
    )
    return User(
        id=str(user_model.id),
        email=user_model.email,
        name=user_model.name,
        roles=user_model.roles or [],
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if "admin" not in (current_user.roles or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return current_user
