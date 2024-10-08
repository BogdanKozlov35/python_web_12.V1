import pickle
from datetime import timedelta, datetime, timezone
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from src.auth.models import User
from src.auth.schema_auth import TokenData

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.db import get_db
from src.auth.repo_auth import UserRepository
from src.conf.config import config
import logging

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = 300
REFRESH_TOKEN_EXPIRE_DAYS = 7
CONFIG_EMAIL_EXPIRE_DAYS = 1


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        # password=config.REDIS_PASSWORD,
    )

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Creates an access token with a specified expiration time.

        :param data: The data to encode in the token.
        :type data: dict
        :param expires_delta: The expiration time delta. If None, defaults to 300 minutes.
        :type expires_delta: Optional[timedelta]
        :return: The encoded access token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Creates a refresh token with a specified expiration time.

        :param data: The data to encode in the token.
        :type data: dict
        :param expires_delta: The expiration time delta. If None, defaults to 7 days.
        :type expires_delta: Optional[timedelta]
        :return: The encoded refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire, "scope": "refresh_token"})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def decode_access_token(self, token: str) -> Optional[TokenData]:
        """
        Decodes an access token and extracts the token data.

        :param token: The access token to decode.
        :type token: str
        :return: The token data if the token is valid; None otherwise.
        :rtype: Optional[TokenData]
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            logger.info(f"Decoded payload: {payload}")

            if email is None:
                return None
            return TokenData(username=email)
        except JWTError:
            logger.error("Failed to decode access token")
            return None

    def decode_refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Decodes a refresh token and extracts the token data.

        :param refresh_token: The refresh token to decode.
        :type refresh_token: str
        :return: The token data if the token is valid; raises HTTPException otherwise.
        :rtype: Optional[TokenData]
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return TokenData(username=email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
        """
        Retrieves the current user based on the provided token.

        :param token: The token used to retrieve the current user.
        :type token: str
        :param db: The database session dependency.
        :type db: AsyncSession
        :return: The current user.
        :rtype: User
        :raises HTTPException: If the credentials are invalid or the user cannot be found.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] != "access_token":
                logger.error(f"Invalid token scope: {payload.get('scope')}")
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                logger.error("Token does not contain email")
                raise credentials_exception
        except JWTError as e:
            logger.error(f"JWTError during token decoding: {e}")
            raise credentials_exception

        user = await self._get_user_from_cache_or_db(email, db, credentials_exception)
        logger.info(f"Fetched user: {user}, with role: {user.role.name if user.role else 'No role'}")
        return user

    async def _get_user_from_cache_or_db(self, email: str, db: AsyncSession,
                                         credentials_exception: HTTPException) -> User:
        """
        Retrieves a user from the cache or database.

        :param email: The email of the user to retrieve.
        :type email: str
        :param db: The database session dependency.
        :type db: AsyncSession
        :param credentials_exception: The exception to raise if the user cannot be found.
        :type credentials_exception: HTTPException
        :return: The user retrieved from cache or database.
        :rtype: User
        :raises HTTPException: If the user cannot be found in cache or database.
        """
        user_hash = str(email)
        try:
            cached_user = await self.cache.get(user_hash)
            if cached_user:
                logger.info("User fetched from cache")
                user = pickle.loads(cached_user)
            else:
                logger.info("User not in cache, fetching from database")
                user_repo = UserRepository(db)
                user = await user_repo.get_user_by_email(email)
                if user is None:
                    raise credentials_exception
                await self.cache.set(user_hash, pickle.dumps(user))
                await self.cache.expire(user_hash, 300)
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            raise credentials_exception
        return user

    def create_email_token(self, data: dict) -> str:
        """
        Creates an email verification token with a specified expiration time.

        :param data: The data to encode in the token.
        :type data: dict
        :return: The encoded email token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=CONFIG_EMAIL_EXPIRE_DAYS)
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    def get_email_from_token(self, token: str) -> str:
        """
        Extracts the email from an email verification token.

        :param token: The email verification token.
        :type token: str
        :return: The email extracted from the token.
        :rtype: str
        :raises HTTPException: If the token is invalid or the email cannot be extracted.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
            return email
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def test_redis_connection(self):
        """
        Tests the connection to the Redis cache.

        :raises Exception: If the connection to Redis fails.
        """
        try:
            pong = await self.cache.ping()
            if pong:
                logger.info("Redis connection successful")
            else:
                logger.error("Redis connection failed")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")


auth_service = Auth()
