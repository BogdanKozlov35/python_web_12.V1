from pydantic import BaseModel, EmailStr
from enum import Enum


class UserSchema(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserSchema):
    password: str


class UserResponse(UserSchema):
    id: int
    is_active: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class RoleEnum(str, Enum):
    USER = "User"
    ADMIN = "Admin"
    MODERATOR = "Moderator"

class RoleBase(BaseModel):
    id: int
    name: RoleEnum
