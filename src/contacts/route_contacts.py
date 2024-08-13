from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schema_auth import RoleEnum
from src.admin.roles import RoleChecker
from src.auth.auth import auth_service

from src.database.db import get_db
from src.contacts.repo_contacts import ContactRepository
from src.contacts.schema_contacts import ContactUpdateSchema, ContactResponse, ContactCreate

router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get("/", response_model=list[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                          Depends(RateLimiter(times=5, seconds=60))])
async def get_contacts(
        limit: int = Query(10, ge=1, le=500),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a paginated list of contacts for the current user.

    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param offset: The number of contacts to skip before starting to collect results.
    :type offset: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: A list of contacts.
    :rtype: list[ContactResponse]
    :raises HTTPException: If an error occurs while retrieving the contacts.
    """
    repo = ContactRepository(db)
    contacts = await repo.get_contacts(limit, offset, current_user.id)
    for contact in contacts:
        contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                          Depends(RateLimiter(times=5, seconds=60))])
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a specific contact by its ID for the current user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The contact with the specified ID.
    :rtype: ContactResponse
    :raises HTTPException: If the contact is not found.
    """
    repo = ContactRepository(db)
    contact = await repo.get_contact(contact_id, current_user.id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact.birthday = contact.birthday.strftime("%Y-%m-%d") if contact.birthday else None
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                           Depends(RateLimiter(times=5, seconds=60))])
async def create_contact(body: ContactCreate, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Creates a new contact for the current user.

    :param body: The contact data to create.
    :type body: ContactCreate
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The newly created contact.
    :rtype: ContactResponse
    :raises HTTPException: If an error occurs while creating the contact.
    """
    repo = ContactRepository(db)
    contact = await repo.create_contact(body, current_user.id)
    contact.birthday = contact.birthday.strftime("%Y-%m-%d") if contact.birthday else None
    return contact


@router.put("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                          Depends(RateLimiter(times=5, seconds=60))])
async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Updates an existing contact for the current user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated contact data.
    :type body: ContactUpdateSchema
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The updated contact.
    :rtype: ContactResponse
    :raises HTTPException: If the contact is not found.
    """
    repo = ContactRepository(db)
    contact = await repo.update_contact(contact_id, body, current_user.id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact.birthday = contact.birthday.strftime("%Y-%m-%d") if contact.birthday else None
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                             Depends(RateLimiter(times=5, seconds=60))])
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Deletes a contact by its ID for the current user.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: No content if the contact is successfully deleted.
    :rtype: None
    :raises HTTPException: If the contact is not found.
    """
    repo = ContactRepository(db)
    contact = await repo.delete_contact(contact_id, current_user.id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return None


@router.get("/birthdays/", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                          Depends(RateLimiter(times=5, seconds=60))])
async def get_birthdays(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves contacts with upcoming birthdays within the next week for the current user.

    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param offset: The number of contacts to skip before starting to collect results.
    :type offset: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: A list of contacts with upcoming birthdays.
    :rtype: list[ContactResponse]
    :raises HTTPException: If an error occurs while retrieving the contacts.
    """
    repo = ContactRepository(db)
    contacts = await repo.get_birthdays(limit, offset, current_user.id)
    for contact in contacts:
        if isinstance(contact.birthday, (datetime, date)):
            contact.birthday = contact.birthday.strftime("%Y-%m-%d")
    return contacts


@router.get("/search/", response_model=list[ContactResponse],
            dependencies=[Depends(RoleChecker([RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.MODERATOR])),
                          Depends(RateLimiter(times=5, seconds=60))])
async def search_contacts(query: str = Query(None), db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(auth_service.get_current_user)):
    """
    Searches for contacts based on a query string for the current user.

    :param query: The query string to search for.
    :type query: str
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: A list of contacts matching the search query.
    :rtype: list[ContactResponse]
    :raises HTTPException: If no contacts are found matching the query.
    """
    repo = ContactRepository(db)
    contacts = await repo.search_contacts(query, current_user.id)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contacts
