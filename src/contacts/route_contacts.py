from datetime import datetime, date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schema_auth import RoleEnum
from src.auth.utils import RoleChecker, get_current_user
from src.database.db import get_db
from src.contacts import repo_contacts as repositories_contacts
from src.contacts.schema_contacts import ContactSchema, ContactUpdateSchema, ContactResponse

router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get("/", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_contacts(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                       db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    contacts = await repositories_contacts.get_contacts(limit, offset, current_user.id, db)
    for contact in contacts:
        contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contacts


@router.get("/all", response_model=list[ContactResponse], dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))],
            tags=['admin'])
async def get_all_contacts(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db)):
    contacts = await repositories_contacts.get_all_contacts(limit, offset, db)
    for contact in contacts:
        contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    contact = await repositories_contacts.get_contact(contact_id, current_user.id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    contact = await repositories_contacts.create_contact(body, current_user.id, db)
    contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    contact = await repositories_contacts.update_contact(contact_id, body, current_user.id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    contact = await repositories_contacts.delete_contact(contact_id, current_user.id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return None


@router.get("/birthdays/", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_birthdays(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                        db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    contacts = await repositories_contacts.get_birthdays(limit, offset, current_user.id, db)
    for contact in contacts:
        if isinstance(contact.birthday, (datetime, date)):
            contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contacts


@router.get("/birthdays/", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))],
            tags=['admin'])
async def get_all_birthdays(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                            db: AsyncSession = Depends(get_db)):
    contacts = await repositories_contacts.get_all_birthdays(limit, offset, db)
    for contact in contacts:
        if isinstance(contact.birthday, (datetime, date)):
            contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contacts


@router.get("/search/", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def search_contacts(query: str = Query(None), db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    contacts = await repositories_contacts.search_contacts(query, current_user.id, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contacts


@router.get("/search/all", response_model=list[ContactResponse], dependencies=[Depends(RoleChecker([RoleEnum.ADMIN]))],
            tags=['admin'])
async def search_all_contacts(query: str = Query(None), db: AsyncSession = Depends(get_db)):
    contacts = await repositories_contacts.search_all_contacts(query, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contacts
