from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.db import get_db
from src.auth.models import User
from src.auth.auth import auth_service

from src.auth.schema_auth import RoleEnum

import logging

logger = logging.getLogger(__name__)

class RoleChecker:
    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

    async def __call__(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
        user = await auth_service.get_current_user(token, db)
        logger.info(f"User role: {user.role.name}, Allowed roles: {[role.name for role in self.allowed_roles]}")
        if user.role.name not in [role.name for role in self.allowed_roles]:
            logger.warning("Permission denied")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return user


