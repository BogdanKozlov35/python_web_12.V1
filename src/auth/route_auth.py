from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.schema_auth import Token, UserResponse, UserCreate
from src.auth.password_utils import verify_password
from src.database.db import get_db
from src.auth.repo_auth import UserRepository

from src.auth.utils import create_access_token, create_refresh_token, decode_access_token

router = APIRouter(prefix='/auth', tags=['authentication'])


@router.post('/register', response_model=UserResponse)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user_repo = UserRepository(db)
        existing_user = await user_repo.get_user(user_create.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        new_user = await user_repo.create_user(user_create)
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username})
    refresh_token = create_refresh_token(
        data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    token_data = decode_access_token(refresh_token)
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
    access_token = create_access_token(
        data={"sub": user.username})
    refresh_token = create_refresh_token(
        data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
