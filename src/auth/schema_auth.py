from typing import Optional

from pydantic import BaseModel, EmailStr
from enum import Enum

from src.admin.schemas_admin import RoleResponse


class UserSchema(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserSchema):
    password: str


class UserResponse(UserSchema):
    id: int
    is_active: bool
    username: str
    email: str
    avatar: Optional[str] = None
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class RoleEnum(str, Enum):
    USER = "User"
    ADMIN = "Admin"
    MODERATOR = "Moderator"


class RoleBase(BaseModel):
    id: int
    name: RoleEnum


class RequestEmail(BaseModel):
    email: EmailStr