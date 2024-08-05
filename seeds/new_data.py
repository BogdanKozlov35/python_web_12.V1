import asyncio
from faker import Faker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.conf.config import config
from src.contacts.models import Contact, Email, Phone, Base


fake = Faker("uk-UA")


async def create_database():
    engine = create_async_engine(config.DB_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def populate_database():
    engine = create_async_engine(config.DB_URL, future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        for _ in range(10):
            contact = Contact(
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                birthday=fake.date_of_birth(minimum_age=18, maximum_age=80),
                description=fake.text(max_nb_chars=250)
            )
            session.add(contact)

            for _ in range(fake.random_int(min=1, max=3)):
                email = Email(
                    email=fake.email(),
                    contact=contact
                )
                session.add(email)

            for _ in range(fake.random_int(min=1, max=3)):
                phone = Phone(
                    phone=fake.phone_number(),
                    contact=contact
                )
                session.add(phone)

        await session.commit()


async def main():
    await create_database()
    await populate_database()


if __name__ == "__main__":
    asyncio.run(main())
