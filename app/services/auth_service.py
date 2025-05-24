from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.schemas.user import UserCreate # Not typically used directly by auth service for creation
from app.security.hashing import Hasher
from .user_service import UserService # Depends on UserService


class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.user_service = UserService(db_session) # Instantiate UserService

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticates a user by email and password.
        Returns the user object if authentication is successful, None otherwise.
        """
        user = await self.user_service.get_user_by_email(email=email)
        if not user:
            return None
        if not Hasher.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            # Optionally, you might raise a specific exception here or return None
            # For simplicity, returning None indicates auth failure for any reason
            return None
        return user

    # Password reset logic could go here in the future
    # async def request_password_reset(self, email: str) -> bool: ...
    # async def reset_password(self, token: str, new_password: str) -> bool: ...
