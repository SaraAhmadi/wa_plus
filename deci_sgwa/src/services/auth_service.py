from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User
# from src.schemas.user import UserCreate # Not typically used directly by auth service for creation
from src.security.hashing import Hasher
from .user_service import UserService # Depends on UserService


class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.user_service = UserService(db_session) # Instantiate UserService

    async def authenticate_user(self, login_identifier: str, password: str) -> Optional[User]:
        """
        Authenticates a user by login_identifier (email or username) and password.
        Returns the user object if authentication is successful, None otherwise.
        """
        user: Optional[User] = None
        if "@" in login_identifier:
            user = await self.user_service.get_user_by_email(email=login_identifier)
        
        if not user: # If not found by email, or if login_identifier was not an email
            user = await self.user_service.get_user_by_username(username=login_identifier)

        if not user:
            return None # User not found by either email or username
        
        if not Hasher.verify_password(password, user.hashed_password):
            return None # Incorrect password
        
        if not user.is_active:
            # Optionally, you might raise a specific exception here or return None
            # For simplicity, returning None indicates auth failure for any reason (like inactive)
            return None # User is inactive
            
        return user

    # Password reset logic could go here in the future
    # async def request_password_reset(self, email: str) -> bool: ...
    # async def reset_password(self, token: str, new_password: str) -> bool: ...
