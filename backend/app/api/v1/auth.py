from typing import Annotated
from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis

from app.api import deps
from app.config import settings
from app.core.cache import redis_dependency
from app.db import get_db_session
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.schemas.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    redis: Annotated[Redis, Depends(redis_dependency)],
    session=Depends(get_db_session),
):
    service = AuthService(redis, UserRepository(session))
    user, access_token, refresh_token = await service.login(body.email, body.password)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    body: RefreshRequest,
    redis: Annotated[Redis, Depends(redis_dependency)],
    session=Depends(get_db_session),
):
    service = AuthService(redis, UserRepository(session))
    user, access_token, refresh_token = await service.refresh(body.refresh_token)
    return RefreshResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    redis: Annotated[Redis, Depends(redis_dependency)],
):
    service = AuthService(redis, user_repo=None)
    await service.logout(body.refresh_token)
    return None
