from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from sqlalchemy.orm import selectinload
from src.auth.schema_auth import UserCreate, RoleEnum
from src.auth.password_utils import get_password_hash
from src.auth.models import User, Role
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        """
        Initializes the UserRepository with a database session.

        :param db: The database session.
        :type db: AsyncSession
        """
        self.db = db

    async def handle_exception(self, e: Exception):
        """
        Handles exceptions by rolling back the transaction and raising an HTTPException.

        :param e: The exception to handle.
        :type e: Exception
        :raises HTTPException: Always raises a 500 Internal Server Error.
        """
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_role_by_name(self, rolename: RoleEnum) -> Optional[Role]:
        """
        Retrieves a role by its name.

        :param rolename: The name of the role.
        :type rolename: RoleEnum
        :return: The Role object if found, otherwise None.
        :rtype: Optional[Role]
        :raises HTTPException: If there is an error during the query.
        """
        try:
            query = select(Role).where(Role.name == rolename)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            await self.handle_exception(e)

    async def create_user(self, body: UserCreate) -> User:
        """
        Creates a new user in the database.

        :param body: The user creation data.
        :type body: UserCreate
        :return: The created User object.
        :rtype: User
        :raises HTTPException: If there is an error during user creation.
        """
        try:
            hashed_password = get_password_hash(body.password)
            new_user = User(
                username=body.username,
                email=body.email,
                hashed_password=hashed_password,
                is_active=False
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except Exception as e:
            await self.handle_exception(e)

    async def get_user(self, username: str) -> Optional[User]:
        """
        Retrieves a user by their username.

        :param username: The username of the user.
        :type username: str
        :return: The User object if found, otherwise None.
        :rtype: Optional[User]
        :raises HTTPException: If there is an error during the query.
        """
        try:
            stmt = select(User).where(User.username == username)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error repo get_user: {e}")
            await self.handle_exception(e)

    async def get_email(self, username: str) -> Optional[str]:
        """
        Retrieves the email of a user by their username.

        :param username: The username of the user.
        :type username: str
        :return: The email of the user if found, otherwise None.
        :rtype: Optional[str]
        :raises HTTPException: If there is an error during the query.
        """
        try:
            stmt = select(User.email).where(User.username == username)
            result = await self.db.execute(stmt)
            return result.first()
        except Exception as e:
            logger.error(f"Error repo get_email: {e}")
            await self.handle_exception(e)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieves a user by their email.

        :param email: The email of the user.
        :type email: str
        :return: The User object if found, otherwise None.
        :rtype: Optional[User]
        :raises HTTPException: If there is an error during the query.
        """
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                logger.info(f"Fetched user from database: {user}")
            return user
        except Exception as e:
            logger.error(f"Error during database query: {e}")
            return None

    async def update_token(self, user: User, token: Optional[str]):
        """
        Updates the refresh token of a user.

        :param user: The user whose token is to be updated.
        :type user: User
        :param token: The new refresh token.
        :type token: Optional[str]
        :raises HTTPException: If there is an error during the update.
        """
        try:
            user.refresh_token = token
            await self.db.commit()
        except Exception as e:
            await self.handle_exception(e)

    async def confirmed_email(self, email: str) -> None:
        """
        Confirms the email of a user.

        :param email: The email of the user to confirm.
        :type email: str
        :raises HTTPException: If the user is not found or if there is an error during the update.
        """
        try:
            user = await self.get_user_by_email(email)
            if user:
                user.is_active = True
                await self.db.commit()
            else:
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.error(f"Error during email confirmation: {e}")
            await self.handle_exception(e)

    async def create_avatar_url(self, email: str, url: Optional[str]) -> User:
        """
        Updates the avatar URL of a user.

        :param email: The email of the user whose avatar URL is to be updated.
        :type email: str
        :param url: The new avatar URL.
        :type url: Optional[str]
        :return: The user with the updated avatar URL.
        :rtype: User
        :raises HTTPException: If the user is not found or if there is an error during the update.
        """
        try:
            user = await self.get_user_by_email(email)
            if user:
                user.avatar = url
                await self.db.commit()
                await self.db.refresh(user)
                return user
            else:
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            await self.handle_exception(e)
