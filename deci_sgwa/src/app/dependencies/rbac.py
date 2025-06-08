from typing import List, Set
from fastapi import Depends, HTTPException, status

# Import new Pydantic models and the updated user dependency
from .get_current_user import (
    get_current_active_user,
    UserModel,
    RoleModel as PydanticRoleModel, # Alias to avoid confusion if SQLAlchemy models are used elsewhere
    PermissionModel as PydanticPermissionModel
)
# SQLAlchemy models are no longer directly used by this RBAC logic with the new UserModel
# from app.database.models.user import User
# from app.database.models.role import Role
# from app.database.models.permission import Permission


# A simple data class to bundle user, roles, and permissions
class RBACResults:
    """Holds results of RBAC checks for easier access in dependencies/routes."""
    # user type hint updated to new Pydantic UserModel
    # roles type hint updated to new Pydantic RoleModel
    def __init__(self, user: UserModel, roles: List[PydanticRoleModel], permissions: Set[str]):
        self.user = user
        self.roles = roles
        self.permissions = permissions


async def get_rbac_results(current_user: UserModel = Depends(get_current_active_user)) -> RBACResults:
    """
    Gathers all roles and permissions for the current user using the Pydantic UserModel.
    The UserModel from get_current_active_user is expected to have roles and permissions populated.
    """
    # current_user is now a Pydantic UserModel
    # current_user.roles is List[PydanticRoleModel]
    # role.permissions is List[PydanticPermissionModel]

    user_roles: List[PydanticRoleModel] = current_user.roles
    user_permissions_set: Set[str] = set()

    for role in user_roles:
        if role.permissions: # This is List[PydanticPermissionModel]
             for perm in role.permissions:
                user_permissions_set.add(perm.name) # perm.name is str

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
