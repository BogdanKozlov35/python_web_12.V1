import asyncio

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from src.auth.models import Role, User
from src.auth.password_utils import get_password_hash
from src.auth.schema_auth import RoleEnum
from src.conf.config import config
from main import app
from src.contacts.models import Contact
from src.database.db import get_db, Base
from src.auth.auth import auth_service

engine = create_async_engine(config.DB_TEST_URL, echo=True, future=True)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    expire_on_commit=False,
    autoflush=False,
)

test_user_data = {"username": "testuser", "email": "testuser@example.com", "password": "123456"}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop to be used in tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture(scope="function")
def override_get_db():
    async def _get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def user_password(faker):
    return await faker.password()

@pytest.fixture(scope="function")
async def user_role(db_session):
    role = Role(id=1, name=RoleEnum.USER.value)
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role
    # except Exception as e:
    #     await db_session.rollback()
    #     raise e


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession, faker, user_password, user_role):
    async with db_session.begin():
        hashed_password = get_password_hash(user_password)
        new_user = User(
            username=await faker.user_name(),
            email=await faker.email(),
            is_active=True,
            hashed_password=hashed_password,
            role_id=user_role.id,
        )
        db_session.add(new_user)
        await db_session.commit()
        await db_session.refresh(new_user)
        return new_user

@pytest.fixture(scope="function")
async def test_user_contact(db_session, test_user: User, faker) -> Contact:
    async with db_session.begin():
        contact = Contact(
            firstname=await faker.first_name(),
            lastname=await faker.last_name(),
            emails=[{"email": await faker.email()}],
            phones=[{"phone": await faker.phone_number()}],
            owner_id=test_user.id,
            birthday=await faker.date_of_birth(),
            description=await faker.text(),
        )
        db_session.add(contact)
        await db_session.commit()
        await db_session.refresh(contact)
        return contact

@pytest.fixture(scope="function")
async def auth_headers(test_user):
    access_token = auth_service.create_access_token(data={"sub": test_user.username})
    refresh_token = auth_service.create_refresh_token(data={"sub": test_user.username})
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Refresh-Token": refresh_token,
        "Content-Type": "application/json",
    }
    return headers
