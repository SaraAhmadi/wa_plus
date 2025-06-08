from typing import List, Set
from fastapi import Depends, HTTPException, status

from src.database.models.user import User
from src.database.models.role import Role
from src.database.models.permission import Permission
from .get_current_user import get_current_user


# A simple data class to bundle user, roles, and permissions, making it easier to pass around or use in
# route logic if needed beyond just the permission check
class RBACResults:
    """Holds results of RBAC checks for easier access in dependencies/routes."""
    def __init__(self, user: User, roles: List[Role], permissions: Set[str]):
        self.user = user
        self.roles = roles
        self.permissions = permissions


async def get_rbac_results(current_user: User = Depends(get_current_user)) -> RBACResults:
    """
    Gathers all roles and permissions for the current user.
    This assumes that user.roles are eagerly loaded or can be awaited if loaded lazily.
    If roles/permissions are lazily loaded and you are in an async context,
    you might need to explicitly await them if your ORM setup requires it.
    With SQLAlchemy's async sessions and relationships, they should often be
    accessible, but fetching them explicitly might be needed if not preloaded.

    Note: Accessing `current_user.roles` and `role.permissions` directly works if
    they are configured for eager loading (e.g., with `selectinload` in the query
    that loads the user in `get_current_user`) or if your async session setup
    handles transparent await for lazy loads (less common for complex structures).

    For simplicity here, we assume direct access works.
    A more robust way might involve a service call: `await user_service.get_user_permissions(user_id)`
    """
    user_roles = current_user.roles # This should be a list of Role objects
    user_permissions_set: Set[str] = set()

    for role in user_roles:
        # role.permissions should be a list of Permission objects
        # Ensure permissions are loaded. If lazy, this might require an await
        # or specific loading strategy in the ORM query for user.
        # For example, in get_current_user, the user query could be:
        # select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(...)
        if role.permissions: # Check if permissions list is not None
             for perm in role.permissions:
                user_permissions_set.add(perm.name)

    return RBACResults(user=current_user, roles=user_roles, permissions=user_permissions_set)


class CheckPermissions:
    """
    Dependency class to check if the current user has all required permissions.
    Usage in an endpoint:
    @router.get("/some_resource", dependencies=[Depends(CheckPermissions(["resource:read", "another:action"]))])
    async def get_some_resource():
        # ...
    """
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = set(required_permissions)

    async def __call__(self, rbac_results: RBACResults = Depends(get_rbac_results)):
        user_permissions = rbac_results.permissions

        if not self.required_permissions.issubset(user_permissions):
            # For better error messages, you can find out which permissions are missing:
            # missing_perms = self.required_permissions - user_permissions
            # detail = f"Missing required permissions: {', '.join(missing_perms)}"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires: {', '.join(self.required_permissions)}"
            )
        # If all checks pass, the request proceeds.
