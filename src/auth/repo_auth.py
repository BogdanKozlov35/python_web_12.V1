from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from src.auth.schema_auth import UserCreate, RoleEnum
from src.auth.password_utils import get_password_hash
from src.auth.models import User, Role

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_exception(self, e):
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_role_by_name(self, rolename: RoleEnum) -> Role:
        try:
            query = select(Role).where(Role.name == rolename)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            await self.handle_exception(e)

    async def create_user(self, body: UserCreate) -> User:
        try:
            hashed_password = get_password_hash(body.password)
            user_role = await self.get_role_by_name(RoleEnum.USER)

            if user_role is None:
                raise HTTPException(status_code=400, detail="Role not found")

            new_user = User(
                username=body.username,
                email=body.email,
                hashed_password=hashed_password,
                role_id=user_role.id,
                is_active=True
            )

            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)

            return new_user
        except Exception as e:
            await self.handle_exception(e)

    async def get_user(self, username: str) -> User:
        try:
            stmt = select(User).where(User.username == username)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await self.handle_exception(e)
