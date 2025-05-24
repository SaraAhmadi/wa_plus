from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError # Already imported in token_utils but good to have context

from app.core.config import settings
from app.schemas.token import TokenData
from app.database.models.user import User # Your SQLAlchemy User model
# We'll need a service to fetch the user from the DB by email/ID
# For now, let's assume a placeholder or direct query, will be refined with services
# from app.services.user_service import UserService # Ideal
from app.security.token_utils import decode_access_token
from .get_db_session import get_db # Using the re-exported version

# This defines the scheme for how the token is expected in the request (Authorization: Bearer <token>)
# tokenUrl should point to your login endpoint where tokens are issued.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Decodes the JWT token, retrieves the user from the database.
    Raises HTTPException if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data: Optional[TokenData] = decode_access_token(token)

    if token_data is None or token_data.email is None:
        # This case covers expired tokens or tokens without a subject (email)
        raise credentials_exception

    # In a real application, you'd use a service layer here.
    # user_service = UserService(db)
    # user = await user_service.get_user_by_email(email=token_data.email)

    # Placeholder for direct DB query until user_service is implemented:
    from sqlalchemy import select # Local import for this placeholder
    user_query = select(User).where(User.email == token_data.email)
    result = await db.execute(user_query)
    user: Optional[User] = result.scalars().first()
    # End placeholder

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current authenticated user, ensuring they are a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


# Optional: Dependency to get a user that might or might not be authenticated
# Useful for routes that behave differently for anonymous vs logged-in users
async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme) if settings.API_V1_STR else None, # HACK: tokenUrl is required
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get an optional current user.
    If no token is provided or token is invalid, returns None.
    Otherwise, returns the user.
    """
    if not token:
        return None
    try:
        token_data: Optional[TokenData] = decode_access_token(token)
        if token_data is None or token_data.email is None:
            return None

        # Placeholder for direct DB query (replace with service)
        from sqlalchemy import select
        user_query = select(User).where(User.email == token_data.email)
        result = await db.execute(user_query)
        user: Optional[User] = result.scalars().first()
        # End placeholder

        if user and user.is_active:
            return user
        return None
    except HTTPException: # e.g., if token is present but truly invalid and raises 401
        return None
    except Exception: # Catch any other unexpected error during optional user fetch
        return None

# Note: The hack for `oauth2_scheme` in `get_optional_current_user` is because
# `OAuth2PasswordBearer` requires `tokenUrl`. If you make it truly optional,
# you might need to manually extract the token from the `Authorization` header
# if `Depends(oauth2_scheme)` fails due to missing token.
# A more robust way for optional auth is to handle the header directly:
# from fastapi import Request
# async def get_optional_current_user_robust(request: Request, db: AsyncSession = Depends(get_db)):
#     auth_header = request.headers.get("Authorization")
#     if auth_header:
#         parts = auth_header.split()
#         if len(parts) == 2 and parts[0].lower() == "bearer":
#             token = parts[1]
#             # ... rest of the logic from get_optional_current_user ...
#     return None
