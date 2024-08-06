
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
async def register(user_create: UserCreate, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
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
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
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
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except Exception as e:
        logger.error(f"Error during refresh token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
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


@router.get("/me/",
            response_model=UserResponse,
            dependencies=[Depends(RateLimiter(times=1, seconds=20))], )
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    return user


@router.patch("/avatar",
              response_model=UserResponse,
              dependencies=[Depends(RateLimiter(times=1, seconds=20))],
              )
async def create_avatar(
        file: UploadFile = File(...),
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
):
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
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(body.email)

    if user.is_active:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


