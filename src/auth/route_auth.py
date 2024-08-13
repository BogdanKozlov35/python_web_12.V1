import pickle

from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

import cloudinary
import cloudinary.uploader

from src.admin.emails import send_email
from src.auth.models import User
from src.auth.schema_auth import Token, UserResponse, UserCreate, RequestEmail
from src.auth.password_utils import verify_password
from src.database.db import get_db
from src.auth.repo_auth import UserRepository
from src.auth.auth import auth_service
from src.conf.config import config
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['authentication'])

cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)


@router.post('/register', response_model=UserCreate, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)) -> UserCreate:
    """
    Registers a new user.

    :param user_create: The user creation data.
    :type user_create: UserCreate
    :param bt: Background tasks to be executed.
    :type bt: BackgroundTasks
    :param request: The incoming HTTP request.
    :type request: Request
    :param db: Database session dependency.
    :type db: AsyncSession
    :return: The created user.
    :rtype: UserCreate
    :raises HTTPException: If the username is already registered or if an internal server error occurs.
    """
    try:
        user_repo = UserRepository(db)
        existing_user = await user_repo.get_user(user_create.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        new_user = await user_repo.create_user(user_create)
        bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
        return new_user
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> Token:
    """
    Authenticates a user and returns access and refresh tokens.

    :param form_data: The form data containing username and password.
    :type form_data: OAuth2PasswordRequestForm
    :param db: Database session dependency.
    :type db: AsyncSession
    :return: A dictionary containing access token, refresh token, and token type.
    :rtype: Token
    :raises HTTPException: If the username or password is incorrect or if an internal server error occurs.
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_user(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = auth_service.create_access_token(data={"sub": user.email})
        refresh_token = auth_service.create_refresh_token(data={"sub": user.email})
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Refreshes access and refresh tokens using a valid refresh token.

    :param refresh_token: The refresh token.
    :type refresh_token: str
    :param db: Database session dependency.
    :type db: AsyncSession
    :return: A dictionary containing new access token, refresh token, and token type.
    :rtype: Token
    :raises HTTPException: If the refresh token is invalid or if an internal server error occurs.
    """
    try:
        token_data = auth_service.decode_refresh_token(refresh_token)
        logger.info(f"Token data: {token_data}")
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_repo = UserRepository(db)
        user = await user_repo.get_user(token_data.username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = auth_service.create_access_token(data={"sub": user.email})
        refresh_token = auth_service.create_refresh_token(data={"sub": user.email})
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
    except Exception as e:
        logger.error(f"Error during refresh token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Confirms a user's email using a token.

    :param token: The token sent to the user's email for confirmation.
    :type token: str
    :param db: Database session dependency.
    :type db: AsyncSession
    :return: A message indicating the confirmation status.
    :rtype: dict
    :raises HTTPException: If the token is invalid, the user is not found, or if an internal server error occurs.
    """
    try:
        logger.info(f"Received token for confirmation: {token}")
        email = auth_service.get_email_from_token(token)
        logger.info(f"Decoded email from token: {email}")
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_email(email)
        if user is None:
            logger.error(f"User not found for email: {email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
        if user.is_active:
            logger.info(f"Email already confirmed for user: {user.email}")
            return {"message": "Your email is already confirmed"}
        await user_repo.confirmed_email(email)
        logger.info(f"Email confirmed for user: {user.email}")
        return {"message": "Email confirmed"}
    except Exception as e:
        logger.error(f"Error during email confirmation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_current_user(user: User = Depends(auth_service.get_current_user)) -> UserResponse:
    """
    Gets the currently authenticated user.

    :param user: The currently authenticated user.
    :type user: User
    :return: The current user's data.
    :rtype: UserResponse
    """
    return user


@router.patch("/avatar", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def create_avatar(
        file: UploadFile = File(...),
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Uploads and updates the user's avatar.

    :param file: The uploaded avatar file.
    :type file: UploadFile
    :param user: The currently authenticated user.
    :type user: User
    :param db: Database session dependency.
    :type db: AsyncSession
    :return: The user data with the updated avatar URL.
    :rtype: UserResponse
    :raises HTTPException: If an error occurs during avatar creation.
    """
    try:
        public_id = f"CM API/{user.email}"
        user_repo = UserRepository(db)
        res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        res_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=res.get("version")
        )
        user = await user_repo.create_avatar_url(user.email, res_url)
        auth_service.cache.set(user.email, pickle.dumps(user))
        auth_service.cache.expire(user.email, 300)
        return user
    except Exception as e:
        logger.error(f"Error during avatar creation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post('/request_email')
async def request_email(
        body: RequestEmail,
        background_tasks: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Requests an email confirmation.

    :param body: The request body containing the user's email.
    :type body: RequestEmail
    :param background_tasks: Background tasks to be executed.
    :type background_tasks: BackgroundTasks
    :param request: The incoming HTTP request.
    :type request: Request
    :param db: Database session dependency.
    :type db: AsyncSession
    :return: A message indicating the status of the email confirmation request.
    :rtype: dict
    :raises HTTPException: If an internal server error occurs.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(body.email)

    if user.is_active:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}
