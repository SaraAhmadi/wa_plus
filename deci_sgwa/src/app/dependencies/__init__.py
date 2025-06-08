from .get_db_session import get_db
# Import the new user dependency functions and the OAuth2 scheme
from .get_current_user import (
    get_current_user_from_core,
    get_current_active_user,
    get_current_active_superuser, # Added new dependency
    oauth2_scheme, # Expose oauth2_scheme if it needs to be accessed directly by some auth flows
    UserModel, # Expose UserModel for type hinting in endpoints
    RoleModel, # Expose RoleModel for type hinting if needed
    PermissionModel # Expose PermissionModel for type hinting if needed
)
from .rbac import CheckPermissions, get_rbac_results, RBACResults # Assuming RBAC will be updated to use UserModel

__all__ = [
    "get_db",
    # New user dependencies
    "get_current_user_from_core",
    "get_current_active_user",
    "get_current_active_superuser", # Added new dependency to __all__
    "oauth2_scheme", # Make scheme available for routers that might need it directly
    "UserModel", # Make the user model available for type hints
    "RoleModel",
    "PermissionModel",
    # RBAC - to be reviewed/updated for UserModel
    "CheckPermissions",
    "get_rbac_results",
    "RBACResults",
]
