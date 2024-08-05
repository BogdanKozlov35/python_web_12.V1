from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas_admin import RoleCreate
from src.auth.models import Role
from src.contacts.models import Contact, Email, Phone


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_exception(self, e):
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_all_contacts(self, limit: int, offset: int):
        try:
            stmt = select(Contact).offset(offset).limit(limit)
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_role(self, role_create: RoleCreate) -> Role:
        new_role = Role(name=role_create.name)
        self.db.add(new_role)
        await self.db.commit()
        await self.db.refresh(new_role)
        return new_role

    async def get_role(self, role_name: str) -> Role:
        result = await self.db.execute(select(Role).where(Role.name == role_name))
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> list[Role]:
        result = await self.db.execute(select(Role))
        return result.scalars().all()
