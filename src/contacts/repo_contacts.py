from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.contacts.models import Contact, Email, Phone
from src.contacts.schema_contacts import ContactUpdateSchema, ContactCreate


class ContactRepository:
    def __init__(self, db: AsyncSession):
        """
        Initializes the repository with a database session.

        :param db: The database session to use for database operations.
        :type db: AsyncSession
        """
        self.db = db

    async def handle_exception(self, e):
        """
        Handles exceptions by printing the error message, rolling back the transaction, and raising an HTTPException.

        :param e: The exception to handle.
        :type e: Exception
        :raises HTTPException: Always raises an HTTPException with a 500 status code.
        """
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_all_contacts(self, limit: int, offset: int):
        """
        Retrieves all contacts with pagination.

        :param limit: The maximum number of contacts to return.
        :type limit: int
        :param offset: The number of contacts to skip before starting to collect results.
        :type offset: int
        :return: A list of contacts.
        :rtype: list[Contact]
        :raises HTTPException: If an error occurs while retrieving the contacts.
        """
        try:
            stmt = select(Contact).offset(offset).limit(limit)
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)

    async def get_contact(self, contact_id: int, owner_id: int):
        """
        Retrieves a contact by its ID and owner ID.

        :param contact_id: The ID of the contact to retrieve.
        :type contact_id: int
        :param owner_id: The ID of the owner of the contact.
        :type owner_id: int
        :return: The contact with the specified ID and owner ID.
        :rtype: Contact
        :raises HTTPException: If the contact is not found.
        """
        try:
            stmt = select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
            result = await self.db.execute(stmt)
            contact = result.scalar_one_or_none()
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            await self.db.refresh(contact, ['emails', 'phones'])
            return contact
        except Exception as e:
            await self.handle_exception(e)

    async def create_contact(self, body: ContactCreate, owner_id: int):
        """
        Creates a new contact.

        :param body: The contact data to create.
        :type body: ContactCreate
        :param owner_id: The ID of the owner of the contact.
        :type owner_id: int
        :return: The newly created contact.
        :rtype: Contact
        :raises HTTPException: If an error occurs while creating the contact.
        """
        try:
            contact = Contact(
                firstname=body.firstname,
                lastname=body.lastname,
                birthday=body.birthday,
                description=body.description,
                owner_id=owner_id
            )

            self.db.add(contact)
            await self.db.commit()
            await self.db.refresh(contact)

            if body.emails:
                for email_data in body.emails:
                    email = Email(email=email_data.email, contact_id=contact.id)
                    self.db.add(email)

            if body.phones:
                for phone_data in body.phones:
                    phone = Phone(phone=phone_data.phone, contact_id=contact.id)
                    self.db.add(phone)

            await self.db.commit()
            await self.db.refresh(contact, ['emails', 'phones'])
            return contact
        except Exception as e:
            await self.handle_exception(e)

    async def update_contact(self, contact_id: int, body: ContactUpdateSchema, owner_id: int):
        """
        Updates an existing contact.

        :param contact_id: The ID of the contact to update.
        :type contact_id: int
        :param body: The updated contact data.
        :type body: ContactUpdateSchema
        :param owner_id: The ID of the owner of the contact.
        :type owner_id: int
        :return: The updated contact.
        :rtype: Contact
        :raises HTTPException: If the contact is not found or if an error occurs while updating the contact.
        """
        try:
            stmt = select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
            result = await self.db.execute(stmt)
            contact = result.scalar_one_or_none()
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")

            contact.firstname = body.firstname
            contact.lastname = body.lastname
            contact.birthday = body.birthday
            contact.description = body.description

            if body.emails is not None:
                await self.db.execute(delete(Email).where(Email.contact_id == contact_id))
                for email_data in body.emails:
                    email = Email(email=email_data.email, contact_id=contact.id)
                    self.db.add(email)

            if body.phones is not None:
                await self.db.execute(delete(Phone).where(Phone.contact_id == contact_id))
                for phone_data in body.phones:
                    phone = Phone(phone=phone_data.phone, contact_id=contact.id)
                    self.db.add(phone)

            await self.db.commit()
            await self.db.refresh(contact, ['emails', 'phones'])
            return contact
        except Exception as e:
            await self.handle_exception(e)

    async def delete_contact(self, contact_id: int, owner_id: int):
        """
        Deletes a contact by its ID and owner ID.

        :param contact_id: The ID of the contact to delete.
        :type contact_id: int
        :param owner_id: The ID of the owner of the contact.
        :type owner_id: int
        :return: The deleted contact.
        :rtype: Contact
        :raises HTTPException: If the contact is not found or if an error occurs while deleting the contact.
        """
        try:
            stmt = select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
            result = await self.db.execute(stmt)
            contact = result.scalar_one_or_none()
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")

            await self.db.execute(delete(Email).where(Email.contact_id == contact_id))
            await self.db.execute(delete(Phone).where(Phone.contact_id == contact_id))
            await self.db.execute(delete(Contact).where(Contact.id == contact_id))
            await self.db.commit()

            return contact
        except Exception as e:
            await self.handle_exception(e)

    async def get_birthdays(self, limit: int, offset: int, owner_id: int):
        """
        Retrieves contacts with upcoming birthdays within the next week for a specific owner.

        :param limit: The maximum number of contacts to return.
        :type limit: int
        :param offset: The number of contacts to skip before starting to collect results.
        :type offset: int
        :param owner_id: The ID of the owner of the contacts.
        :type owner_id: int
        :return: A list of contacts with upcoming birthdays.
        :rtype: list[Contact]
        :raises HTTPException: If an error occurs while retrieving the contacts.
        """
        try:
            today = datetime.now().date()
            future_date = today + timedelta(days=7)

            stmt = select(Contact).where(Contact.owner_id == owner_id,
                                         Contact.birthday.between(today, future_date)).offset(
                offset).limit(limit)
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)

    async def get_all_birthdays(self, limit: int, offset: int):
        """
        Retrieves all contacts with upcoming birthdays within the next week.

        :param limit: The maximum number of contacts to return.
        :type limit: int
        :param offset: The number of contacts to skip before starting to collect results.
        :type offset: int
        :return: A list of contacts with upcoming birthdays.
        :rtype: list[Contact]
        :raises HTTPException: If an error occurs while retrieving the contacts.
        """
        try:
            today = datetime.now().date()
            future_date = today + timedelta(days=7)

            stmt = select(Contact).where(Contact.birthday.between(today, future_date)).offset(
                offset).limit(limit)
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)

    async def search_contacts(self, query: str, owner_id: int):
        """
        Searches for contacts based on a query string and owner ID.

        :param query: The query string to search for.
        :type query: str
        :param owner_id: The ID of the owner of the contacts.
        :type owner_id: int
        :return: A list of contacts matching the search query.
        :rtype: list[Contact]
        :raises HTTPException: If an error occurs while searching for contacts.
        """
        try:
            stmt = select(Contact).where(Contact.owner_id == owner_id).filter(or_(
                Contact.firstname.ilike(f"%{query}%"),
                Contact.lastname.ilike(f"%{query}%"),
                Contact.emails.any(Email.email.ilike(f"%{query}%")),
                Contact.phones.any(Phone.phone.ilike(f"%{query}%"))
            ))
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)

    async def search_all_contacts(self, query: str):
        """
        Searches for all contacts based on a query string.

        :param query: The query string to search for.
        :type query: str
        :return: A list of contacts matching the search query.
        :rtype: list[Contact]
        :raises HTTPException: If an error occurs while searching for contacts.
        """
        try:
            stmt = select(Contact).filter(or_(
                Contact.firstname.ilike(f"%{query}%"),
                Contact.lastname.ilike(f"%{query}%"),
                Contact.emails.any(Email.email.ilike(f"%{query}%")),
                Contact.phones.any(Phone.phone.ilike(f"%{query}%"))
            ))
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)
