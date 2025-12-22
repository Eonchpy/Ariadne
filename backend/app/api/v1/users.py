from typing import Annotated
from fastapi import APIRouter, Depends

from app.api import deps
from app.schemas.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
async def get_me(current_user: Annotated[User, Depends(deps.get_current_user)]) -> User:
    return current_user
