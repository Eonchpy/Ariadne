from datetime import datetime
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    roles: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
