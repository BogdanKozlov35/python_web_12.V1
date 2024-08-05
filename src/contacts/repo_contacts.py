from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.contacts.models import Contact, Email, Phone
from src.contacts.schema_contacts import ContactUpdateSchema, ContactCreate


class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle_exception(self, e):
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_contacts(self, limit: int, offset: int, owner_id: int):
        try:
            stmt = select(Contact).where(Contact.owner_id == owner_id).offset(offset).limit(limit)
            result = await self.db.execute(stmt)
            contacts = result.scalars().all()
            for contact in contacts:
                await self.db.refresh(contact, ['emails', 'phones'])
            return contacts
        except Exception as e:
            await self.handle_exception(e)

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

    async def get_contact(self, contact_id: int, owner_id: int):
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
