from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.schemas.token import Token
from app.schemas.user import User as UserSchema # Pydantic schema for response
from app.services.auth_service import AuthService
from app.services.user_service import UserService # For the /me endpoint
from app.dependencies import get_db, get_current_user
from app.security.token_utils import create_access_token
from app.core.config import settings

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Corresponds to SSR 8.5.6 POST /api/v1/auth/token
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        login_identifier=form_data.username, # OAuth2PasswordRequestForm uses 'username' for the first field
        password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email,  # Use user.email or user.id as the token subject
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: UserSchema = Depends(get_current_user) # UserSchema is SQLAlchemy model User
                                                        # The dependency returns SQLAlchemy model
                                                        # FastAPI will convert it to UserSchema (Pydantic)
):
    """
    Get current authenticated user's details.
    Corresponds to SSR 8.5.6 GET /api/v1/auth/me

    The `get_current_user` dependency already fetches the User (SQLAlchemy model).
    FastAPI handles the conversion to the `UserSchema` (Pydantic model) for the response
    because of `response_model=UserSchema`.
    The type hint for `current_user` can be `app.database.models.user.User` to be more precise
    about what `get_current_user` returns.
    """
    # `current_user` is already the SQLAlchemy User model instance from the dependency.
    # No further database interaction is typically needed here unless you want to
    # refresh or load more data not already handled by get_current_user.
    return current_user


# Example of a test route for authenticated users
@router.post("/token/test", response_model=UserSchema)
async def test_token(current_user: UserSchema = Depends(get_current_user)):
    """
    Test endpoint to verify token authentication.
    Returns the current user if the token is valid.
    """
    return current_user

# Potential future endpoints:
# - Password Recovery Request
# - Password Reset
# - Token Refresh (if implementing refresh tokens)
