import httpx # For making requests to deci_core
import os # For CORE_API_URL (though better to import from get_current_user)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# AsyncSession and get_db might not be needed if AuthService is removed
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.dependencies import get_db

from app.schemas.token import Token # Token schema for response
# Remove AuthService and local token utils if login is fully delegated
# from app.services.auth_service import AuthService
# from app.security.token_utils import create_access_token
# from datetime import timedelta # No longer needed for local token expiry
# from app.core.config import settings # No longer needed for local token expiry

# Import new dependencies and CORE_API_BASE_URL from where it's defined
from app.dependencies import get_current_active_user, UserModel
from app.dependencies.get_current_user import CORE_API_BASE_URL # Import configured URL

router = APIRouter()

# Construct the target URL for deci_core login
CORE_LOGIN_URL = f"{CORE_API_BASE_URL}/api/v1/auth/login/" # Ensure this path is correct for deci_core

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
    # db: AsyncSession = Depends(get_db) # No longer needed for this endpoint
):
    """
    OAuth2 compatible token login.
    This endpoint now delegates authentication to deci_core.
    The 'username' field in form_data can be email or username.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                CORE_LOGIN_URL,
                data={"username": form_data.username, "password": form_data.password}
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: Could not connect to authentication service. {exc}",
            )

        if response.status_code == status.HTTP_200_OK:
            core_tokens = response.json()
            # deci_core returns {"access": "...", "refresh": "..."}
            # deci_sgwa's Token schema expects {"access_token": "...", "token_type": "bearer"}
            # We only pass through the access token for now.
            if "access" not in core_tokens:
                 raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication service returned unexpected token format.",
                )
            return {"access_token": core_tokens["access"], "token_type": "bearer"}

        elif response.status_code == status.HTTP_400_BAD_REQUEST or \
             response.status_code == status.HTTP_401_UNAUTHORIZED:
            # Assuming deci_core returns 400 or 401 for invalid credentials
            # Parse detail from core's response if available and meaningful, else generic message
            error_detail = "Incorrect username or password."
            try:
                core_error = response.json()
                if isinstance(core_error, dict) and "detail" in core_error:
                    error_detail = core_error["detail"]
                elif isinstance(core_error, dict) and "non_field_errors" in core_error : # Django Rest Framework common error key
                    error_detail = core_error["non_field_errors"][0]

            except Exception:
                pass # Stick to generic error_detail

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, # Standardize to 401 for client
                detail=error_detail,
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            # Handle other unexpected status codes from the auth service
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Authentication service returned an unexpected status: {response.status_code}. "
                    f"Response: {response.text[:200]}"
                ),
            )

@router.get("/me", response_model=UserModel) # Use UserModel from dependencies
async def read_users_me(
    current_user: UserModel = Depends(get_current_active_user) # Use new dependency
):
    """
    Get current authenticated user's details from the token.
    The user information is fetched from deci_core via the get_current_active_user dependency.
    """
    # current_user is now the Pydantic UserModel from app.dependencies.get_current_user
    return current_user


# Example of a test route for authenticated users
@router.post("/token/test/", response_model=UserModel) # Use UserModel from dependencies
async def test_token(current_user: UserModel = Depends(get_current_active_user)): # Use new dependency
    """
    Test endpoint to verify token authentication.
    Returns the current user if the token is valid.
    """
    return current_user

# Potential future endpoints:
# - Password Recovery Request
# - Password Reset
# - Token Refresh (if implementing refresh tokens)
