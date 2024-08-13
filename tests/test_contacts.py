import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from datetime import datetime, timedelta

from src.contacts.models import Contact, Email, Phone
from src.contacts.schema_contacts import ContactUpdateSchema, ContactCreate
from src.contacts.repo_contacts import ContactRepository
from tests.confi_test import override_get_db, test_user, auth_headers, db_session, test_user_contact, user_password, user_role



@pytest.fixture
def contact_repository(db_session: AsyncSession):

    return ContactRepository(db=db_session)



async def test_get_all_contacts(contact_repository, db_session, test_user, test_user_contact, override_get_db):

    contacts = await contact_repository.get_all_contacts(limit=10, offset=0)
    assert len(contacts) > 0
    assert contacts[0].owner_id == test_user.id



async def test_get_contact(contact_repository, db_session, test_user, test_user_contact, override_get_db):

    contact = await contact_repository.get_contact(contact_id=test_user_contact.id, owner_id=test_user.id)
    assert contact.id == test_user_contact.id
    assert contact.owner_id == test_user.id



async def test_create_contact(contact_repository, db_session, test_user, override_get_db):

    contact_data = ContactCreate(
        firstname="John",
        lastname="Doe",
        birthday=datetime.now().date(),
        description="Test contact",
        emails=[{"email": "johndoe@example.com"}],
        phones=[{"phone": "123456789"}]
    )
    contact = await contact_repository.create_contact(body=contact_data, owner_id=test_user.id)
    assert contact.firstname == contact_data.firstname
    assert contact.lastname == contact_data.lastname
    assert contact.emails[0].email == "johndoe@example.com"
    assert contact.phones[0].phone == "123456789"



async def test_update_contact(contact_repository, db_session, test_user, test_user_contact, override_get_db):

    update_data = ContactUpdateSchema(
        firstname="Jane",
        lastname="Doe",
        birthday=test_user_contact.birthday,
        description="Updated contact",
        emails=[{"email": "janedoe@example.com"}],
        phones=[{"phone": "987654321"}]
    )
    updated_contact = await contact_repository.update_contact(contact_id=test_user_contact.id, body=update_data, owner_id=test_user.id)
    assert updated_contact.firstname == "Jane"
    assert updated_contact.lastname == "Doe"
    assert updated_contact.emails[0].email == "janedoe@example.com"
    assert updated_contact.phones[0].phone == "987654321"



async def test_delete_contact(contact_repository, db_session, test_user, test_user_contact, override_get_db):

    deleted_contact = await contact_repository.delete_contact(contact_id=test_user_contact.id, owner_id=test_user.id)
    assert deleted_contact.id == test_user_contact.id


    with pytest.raises(HTTPException):
        await contact_repository.get_contact(contact_id=test_user_contact.id, owner_id=test_user.id)



async def test_get_birthdays(contact_repository, db_session, test_user, test_user_contact, override_get_db):
    assert hasattr(test_user, 'id')
    assert hasattr(test_user_contact, 'id')

    contacts = await contact_repository.get_birthdays(limit=10, offset=0, owner_id=test_user.id)
    assert len(contacts) > 0
    for contact in contacts:
        assert contact.owner_id == test_user.id
        assert contact.birthday >= datetime.now().date()
        assert contact.birthday <= datetime.now().date() + timedelta(days=7)



async def test_search_contacts(contact_repository, db_session, test_user, test_user_contact, override_get_db):

    contacts = await contact_repository.search_contacts(query="John", owner_id=test_user.id)
    assert len(contacts) > 0
    for contact in contacts:
        assert contact.owner_id == test_user.id
        assert "John" in contact.firstname or "John" in contact.lastname
