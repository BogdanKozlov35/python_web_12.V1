
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from sqlalchemy.orm import selectinload

from src.auth.schema_auth import UserCreate, RoleEnum
from src.auth.password_utils import get_password_hash
from src.auth.models import User, Role
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_exception(self, e):
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_role_by_name(self, rolename: RoleEnum) -> Optional[Role]:
        try:
            query = select(Role).where(Role.name == rolename)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            await self.handle_exception(e)

    async def create_user(self, body: UserCreate) -> User:
        try:
            hashed_password = get_password_hash(body.password)
            new_user = User(
                username=body.username,
                email=body.email,
                hashed_password=hashed_password,
                is_active=False
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except Exception as e:
            await self.handle_exception(e)

    async def get_user(self, username: str) -> Optional[User]:
        try:
            stmt = select(User).where(User.username == username)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error repo get_user: {e}")
            await self.handle_exception(e)

    async def get_email(self, username: str) -> Optional[User]:
        try:
            stmt = select(User.email).where(User.username == username)
            result = await self.db.execute(stmt)
            return result.first()
        except Exception as e:
            logger.error(f"Error repo get_user: {e}")
            await self.handle_exception(e)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                logger.info(f"Fetched user from database: {user}")
            return user
        except Exception as e:
            logger.error(f"Error during database query: {e}")
            return None

    async def update_token(self, user: User, token: Optional[str]):
        try:
            user.refresh_token = token
            await self.db.commit()
        except Exception as e:
            await self.handle_exception(e)

    async def confirmed_email(self, email: str) -> None:
        try:
            user = await self.get_user_by_email(email)
            if user:
                user.is_active = True
                await self.db.commit()
            else:
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.error(f"Error during email confirmation: {e}")
            await self.handle_exception(e)

    async def create_avatar_url(self, email: str, url: Optional[str]) -> User:
        try:
            user = await self.get_user_by_email(email)
            if user:
                user.avatar = url
                await self.db.commit()
                await self.db.refresh(user)
                return user
            else:
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            await self.handle_exception(e)
