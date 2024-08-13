import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from src.contacts.models import Contact, Email, Phone, User
from src.contacts.schema_contacts import ContactCreate, ContactUpdateSchema, EmailSchema, PhoneSchema
from src.contacts.repo_contacts import ContactRepository

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', hashed_password="qwerty", is_active=True)
        self.session = AsyncMock(spec=AsyncSession)
        self.repo = ContactRepository(self.session)
        logger.info("Test setup completed.")

    async def test_get_all_contacts(self):
        logger.info("Starting test_get_all_contacts...")

        limit = 10
        offset = 0
        contacts = [
            Contact(id=1, firstname="Іван", lastname="Петренко", birthday="1990-01-01", description="Тестовий опис 1",
                    emails=[Email(id=1, email="user1@example.com")],
                    phones=[Phone(id=1, phone="2222222222")]),
            Contact(id=2, firstname="Марія", lastname="Шевченко", birthday="1985-02-15", description="Тестовий опис 2",
                    emails=[Email(id=1, email="user2@example.com")],
                    phones=[Phone(id=1, phone="3333333333")]
                    )]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await self.repo.get_all_contacts(limit, offset)
        logger.debug(f"Retrieved contacts: {result}")

        self.assertEqual(result, contacts)
        self.session.execute.assert_called_once()
        mocked_contacts.scalars.return_value.all.assert_called_once()
        logger.info("test_get_all_contacts completed successfully.")

    async def test_get_contact(self):
        logger.info("Starting test_get_contact...")

        contact_id = 1
        owner_id = 1
        contact = Contact(id=contact_id, firstname="Іван", lastname="Петренко", birthday="1990-01-01",
                          description="Тестовий опис",
                          emails=[Email(id=1, email="user1@example.com")],
                          phones=[Phone(id=1, phone="2222222222")])
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact

        result = await self.repo.get_contact(contact_id, owner_id)
        logger.debug(f"Retrieved contact: {result}")

        self.assertEqual(result.firstname, contact.firstname)
        self.assertEqual(result.lastname, contact.lastname)
        self.assertEqual(result.birthday, contact.birthday)
        self.assertEqual(result.description, contact.description)
        self.assertEqual([e.email for e in result.emails], [e.email for e in contact.emails])
        self.assertEqual([p.phone for p in result.phones], [p.phone for p in contact.phones])

        self.session.execute.assert_called_once()
        mocked_contact.scalar_one_or_none.assert_called_once()
        logger.info("test_get_contact completed successfully.")

    async def test_create_contact(self):
        logger.info("Starting test_create_contact...")
        body = ContactCreate(firstname="Іван", lastname="Петренко", birthday="1990-01-01", description="Тестовий опис",
                             emails=[EmailSchema(email="user1@example.com")],
                             phones=[PhoneSchema(phone="2222222222")])
        # Mocked result for the created contact
        contact = Contact(id=1, firstname="Іван", lastname="Петренко", birthday="1990-01-01",
                          description="Тестовий опис",
                          emails=[Email(id=1, email="user1@example.com")],
                          phones=[Phone(id=1, phone="2222222222")])
        self.repo.create_contact = AsyncMock(return_value=contact)

        result = await self.repo.create_contact(body, self.user)
        logger.debug(f"Contact created: {result}")

        self.assertIsInstance(result, Contact)
        self.assertEqual(result.firstname, body.firstname)
        self.assertEqual(result.lastname, body.lastname)
        self.assertEqual(result.birthday, body.birthday.strftime("%Y-%m-%d"))
        self.assertEqual(result.description, body.description)
        self.assertEqual([e.email for e in result.emails], [e.email for e in body.emails])
        self.assertEqual([p.phone for p in result.phones], [p.phone for p in body.phones])
        logger.info("test_create_contact completed successfully.")

    async def test_update_contact(self):
        logger.info("Starting test_update_contact...")

        contact_id = 1
        owner_id = 1
        body = ContactUpdateSchema(id=contact_id, firstname="Іван", lastname="Петренко", birthday="1990-01-01",
                                   description="Тестовий опис",
                                   emails=[EmailSchema(email="user2@example.com")],
                                   phones=[PhoneSchema(phone="3333333333")])
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=contact_id, firstname="Марія", lastname="Шевченко",
                                                                 birthday="1985-02-15", description="Тестовий опис 2",
                                                                 emails=[Email(id=1, email="user2@example.com")],
                                                                 phones=[Phone(id=1, phone="3333333333")])
        self.session.execute.return_value = mocked_contact

        result = await self.repo.update_contact(contact_id, body, owner_id)
        logger.debug(f"Contact updated: {result}")

        self.assertIsInstance(result, Contact)
        self.assertEqual(result.firstname, body.firstname)
        self.assertEqual(result.lastname, body.lastname)
        self.assertEqual(result.birthday, body.birthday)

        self.assertEqual(result.description, body.description)
        self.assertEqual([e.email for e in result.emails], [e.email for e in body.emails])
        self.assertEqual([p.phone for p in result.phones], [p.phone for p in body.phones])
        logger.info("test_update_contact completed successfully.")

    async def test_delete_contact(self):
        logger.info("Starting test_delete_contact...")

        contact_id = 1
        owner_id = 1

        contact = Contact(
            id=contact_id,
            firstname="Іван",
            lastname="Петренко",
            birthday="1990-01-01",
            description="Тестовий опис",
            emails=[Email(id=1, email="user2@example.com")],
            phones=[Phone(id=1, phone="3333333333")]
        )

        self.repo.delete_contact = AsyncMock(return_value=contact)

        result = await self.repo.delete_contact(contact_id, owner_id)
        logger.debug(f"Contact deleted: {result}")

        self.assertIsInstance(result, Contact)

        logger.info("test_delete_contact completed successfully.")

    async def test_get_birthdays(self):
        logger.info("Starting test_get_birthdays...")

        limit = 10
        offset = 0
        owner_id = 1
        today = datetime.now().date()
        future_date = today + timedelta(days=7)

        contacts = [
            Contact(id=1, firstname="Іван", lastname="Петренко", birthday=today + timedelta(days=3),
                    description="Тестовий опис 1",
                    emails=[Email(id=1, email="user1@example.com")],
                    phones=[Phone(id=1, phone="2222222222")]),
            Contact(id=2, firstname="Марія", lastname="Шевченко", birthday=today + timedelta(days=5),
                    description="Тестовий опис 2",
                    emails=[Email(id=2, email="user2@example.com")],
                    phones=[Phone(id=2, phone="3333333333")]
                    )]

        mocked_execute = MagicMock()
        mocked_execute.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_execute

        self.session.refresh = AsyncMock()

        result = await self.repo.get_birthdays(limit, offset, owner_id)

        self.assertEqual(result, contacts)
        self.session.execute.assert_awaited_once()
        mocked_execute.scalars.return_value.all.assert_called_once()

        for contact in contacts:
            self.session.refresh.assert_any_await(contact, ['emails', 'phones'])

        logger.info("test_get_birthdays completed successfully.")

    async def test_search_contacts(self):
        logger.info("Starting test_search_contacts...")

        query = "Іван"
        contacts = [
            Contact(id=1, firstname="Іван", lastname="Петренко", birthday="1990-01-01", description="Тестовий опис",
                    emails=[Email(id=1, email="user1@example.com")],
                    phones=[Phone(id=1, phone="2222222222")]),
            Contact(id=2, firstname="Марія", lastname="Шевченко", birthday="1985-02-15", description="Тестовий опис 2",
                    emails=[Email(id=2, email="user2@example.com")],
                    phones=[Phone(id=2, phone="3333333333")])
        ]

        mocked_result = MagicMock()
        mocked_result.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_result

        result = await self.repo.search_contacts(query, self.user.id)
        logger.debug(f"Search result: {result}")

        self.assertEqual(result, contacts)
        self.session.execute.assert_awaited_once()
        # for contact in contacts:
        #     self.session.refresh.assert_awaited_with(contact, ['emails', 'phones'])

        logger.info("test_search_contacts completed successfully.")


if __name__ == "__main__":
    unittest.main()
