from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.roles import RoleChecker
from src.auth.schema_auth import RoleEnum
from src.contacts.repo_contacts import ContactRepository
from src.contacts.schema_contacts import ContactResponse
from src.database.db import get_db
from src.admin.schemas_admin import RoleCreate, RoleResponse
from src.admin.repo_admin import RoleRepository

router = APIRouter(prefix='/api', tags=['admin'])


@router.post('/create_role', response_model=RoleResponse, status_code=201,
             dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))])
async def create_role(role_create: RoleCreate, db: AsyncSession = Depends(get_db)):
    role_repo = RoleRepository(db)
    existing_role = await role_repo.get_role(role_create.name)
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    new_role = await role_repo.create_role(role_create)
    return new_role


@router.get('/get_all_roles', response_model=list[RoleResponse], dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))])
async def get_all_roles(db: AsyncSession = Depends(get_db)):
    role_repo = RoleRepository(db)
    roles = await role_repo.get_all_roles()
    return roles


@router.get("/get_all_contacts", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))])
async def get_all_contacts(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db)):
    contacts = await ContactRepository.get_all_contacts(limit, offset, db)
    for contact in contacts:
        contact.birthday = contact.birthday.strftime("%d-%m-%Y")
    return contacts


@router.get("/get_all_birthdays", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))])
async def get_all_birthdays(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                            db: AsyncSession = Depends(get_db)):
    contacts = await ContactRepository.get_all_birthdays(limit, offset, db)
    for contact in contacts:
        if isinstance(contact.birthday, (datetime, date)):
            contact.birthday = contact.birthday.strftime("%d-%m-%Y")
    return contacts


@router.get("/search_all", response_model=list[ContactResponse], dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))])
async def search_all_contacts(query: str = Query(None), db: AsyncSession = Depends(get_db)):
    contacts = await ContactRepository.search_all_contacts(query, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contacts
