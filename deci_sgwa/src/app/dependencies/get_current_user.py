import os
from typing import List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, EmailStr

# --- Configuration ---
CORE_API_BASE_URL = os.getenv("CORE_API_URL", "http://core_django:8000").rstrip("/")
USERS_ME_ENDPOINT = f"{CORE_API_BASE_URL}/api/v1/users/me/"

# OAuth2PasswordBearer uses the tokenUrl for documentation and OpenAPI schema.
# The actual token generation is handled by deci_core. This path can be a placeholder.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token") # Example relative path

# --- Pydantic Models ---
# These models should ideally match the UserSerializer structure from deci_core.

class PermissionModel(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class RoleModel(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionModel] = Field(default_factory=list)

class UserModel(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool = False # Added is_superuser field
    roles: List[RoleModel] = Field(default_factory=list)

# --- Dependency Functions ---

async def get_current_user_from_core(token: str = Depends(oauth2_scheme)) -> UserModel:
    """
    Dependency to get the current user by validating the token against the deci_core API.
    """
    if not token: # Should be caught by OAuth2PasswordBearer, but as an extra check.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                USERS_ME_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"}
            )
        except httpx.RequestError as exc:
            # Network errors, DNS failures, etc.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: Could not connect to authentication service. {exc}",
            )

        if response.status_code == status.HTTP_200_OK:
            try:
                user_data = response.json()
                return UserModel(**user_data)
            except Exception as e: # Includes JSONDecodeError and Pydantic ValidationError
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing user data from authentication service: {e}",
                )
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: Token is invalid or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            # This might indicate a valid token but insufficient permissions for /users/me/,
            # but for a /users/me/ endpoint, it usually implies an issue treated as unauthorized.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # Or map to 401 as per security policy
                detail="Not authorized to access this resource.",
                headers={"WWW-Authenticate": "Bearer"}, # Consider if Bearer is appropriate for 403
            )
        else:
            # Handle other unexpected status codes from the auth service
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Authentication service returned an unexpected status: {response.status_code}. "
                    f"Response: {response.text[:200]}" # Limit response text in error
                ),
            )

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user_from_core)
) -> UserModel:
    """
    Dependency to get the current active user.
    Relies on `get_current_user_from_core` to fetch the user first.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_active_superuser(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
    """
    Dependency to get the current active user and verify they are a superuser.
    Relies on `get_current_active_user` to fetch and activate the user.
    """
    if not getattr(current_user, 'is_superuser', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have superuser privileges"
        )
    return current_user

# Example of how you might want to expose a "user with permission"
# async def require_permission(permission_codename: str):
#     """
#     Factory for a dependency that checks if the current user has a specific permission.
#     """
#     async def _has_permission(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
#         for role in current_user.roles:
#             for perm in role.permissions:
#                 if perm.name == permission_codename: # Assuming 'name' is the codename
#                     return current_user
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=f"User does not have the required permission: {permission_codename}"
#         )
#     return _has_permission

# For testing this dependency directly (optional)
if __name__ == "__main__":
    # This part is for local testing and won't run when imported by FastAPI normally.
    # You would need to mock httpx.AsyncClient and provide a dummy token.
    import asyncio
    from unittest.mock import patch # Ensure patch is imported for the __main__ block

    async def mock_client_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = str(json_data)

            def json(self):
                return self.json_data

        headers = kwargs.get("headers", {})
        token = headers.get("Authorization", "").replace("Bearer ", "")

        if token == "valid_active_token": # Non-superuser
            return MockResponse({
                "id": 1, "email": "active@example.com", "username": "activeuser",
                "full_name": "Active User", "is_active": True, "is_superuser": False,
                "roles": [{"id": 1, "name": "user", "description": "Regular user",
                           "permissions": [{"id":1, "name": "read", "description": "Read access"}]
                          }]
            }, 200)
        elif token == "valid_superuser_token": # Superuser
            return MockResponse({
                "id": 3, "email": "superuser@example.com", "username": "superadmin",
                "full_name": "Super Admin", "is_active": True, "is_superuser": True,
                "roles": [{"id": 2, "name": "admin", "description": "Admin role",
                           "permissions": [{"id":1, "name": "read", "description": "Read access"}, {"id":2, "name": "write", "description": "Write access"}]
                          }]
            }, 200)
        elif token == "valid_inactive_token": # Inactive non-superuser
            return MockResponse({
                "id": 2, "email": "inactive@example.com", "username": "inactiveuser",
                "full_name": "Inactive User", "is_active": False, "is_superuser": False,
                "roles": [{"id": 1, "name": "user", "description": "Regular user",
                           "permissions": [{"id":1, "name": "read", "description": "Read access"}]
                          }]
            }, 200)
        elif token == "invalid_token":
            return MockResponse({"detail": "Invalid token"}, 401)
        elif token == "service_unavailable_token":
            raise httpx.ConnectError("Connection refused")
        else:
            return MockResponse({"detail": "Unknown test token"}, 500)

    async def main():
        # --- Test get_current_user_from_core ---
        print("--- Testing get_current_user_from_core ---")
        # Valid active user
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                user = await get_current_user_from_core(token="valid_active_token")
                print(f"Active user fetched: {user.username}, is_active: {user.is_active}")
                assert user.is_active
                assert user.roles[0].permissions[0].name == "read"
            except HTTPException as e:
                print(f"Error fetching active user: {e.detail} (status: {e.status_code})")

        # Valid inactive user
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                user_in = await get_current_user_from_core(token="valid_inactive_token")
                print(f"Inactive user fetched: {user_in.username}, is_active: {user_in.is_active}")
                assert not user_in.is_active
            except HTTPException as e:
                print(f"Error fetching inactive user: {e.detail} (status: {e.status_code})")

        # Invalid token
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                await get_current_user_from_core(token="invalid_token")
            except HTTPException as e:
                print(f"Correctly handled invalid token: {e.detail} (status: {e.status_code})")
                assert e.status_code == 401

        # Service unavailable
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                await get_current_user_from_core(token="service_unavailable_token")
            except HTTPException as e:
                print(f"Correctly handled service unavailable: {e.detail} (status: {e.status_code})")
                assert e.status_code == 503


        # --- Test get_current_active_user ---
        print("\n--- Testing get_current_active_user ---")
        # Active user
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                user_obj = await get_current_user_from_core(token="valid_active_token")
                active_user = await get_current_active_user(current_user=user_obj)
                print(f"Active user passed through: {active_user.username}")
                assert active_user.is_active
            except HTTPException as e:
                print(f"Error getting active user for active user test: {e.detail} (status: {e.status_code})")

        # Inactive user
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                user_obj_inactive = await get_current_user_from_core(token="valid_inactive_token")
                await get_current_active_user(current_user=user_obj_inactive)
            except HTTPException as e:
                print(f"Correctly handled inactive user for active user test: {e.detail} (status: {e.status_code})")
                assert e.status_code == 400

        # --- Test get_current_active_superuser ---
        print("\n--- Testing get_current_active_superuser ---")
        # Superuser
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                user_obj_super = await get_current_user_from_core(token="valid_superuser_token")
                active_super_user = await get_current_active_user(current_user=user_obj_super) # First ensure active
                super_user = await get_current_active_superuser(current_user=active_super_user)
                print(f"Superuser passed through: {super_user.username}")
                assert super_user.is_superuser
            except HTTPException as e:
                print(f"Error getting superuser for superuser test: {e.detail} (status: {e.status_code})")

        # Non-superuser
        with patch("httpx.AsyncClient.get", mock_client_get):
            try:
                user_obj_active = await get_current_user_from_core(token="valid_active_token")
                active_user_non_super = await get_current_active_user(current_user=user_obj_active)
                await get_current_active_superuser(current_user=active_user_non_super)
            except HTTPException as e:
                print(f"Correctly handled non-superuser for superuser test: {e.detail} (status: {e.status_code})")
                assert e.status_code == 403

        # Inactive superuser (should be caught by get_current_active_user first)
        # For this, we need a mock that returns an inactive superuser
        # Let's assume 'valid_inactive_token' is now an inactive superuser for this test case
        # by modifying mock_client_get slightly or adding a new token type.
        # For simplicity, we'll rely on the active check in get_current_active_superuser's dependency.
        # If an inactive user (superuser or not) is passed to get_current_active_superuser,
        # it assumes get_current_active_user already filtered it.
        # If we were to call get_current_active_superuser with a user from get_current_user_from_core that
        # happens to be inactive but also a superuser, the active check in get_current_active_user (the dependency)
        # would raise the 400 error first.

    if __name__ == "__main__":
        asyncio.run(main())
