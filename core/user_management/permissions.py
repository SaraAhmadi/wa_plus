from rest_framework import permissions

class HasPermission(permissions.BasePermission):
    message = 'You do not have the required permissions.'

    def __init__(self, required_permissions=None):
        # Ensure required_permissions is always a set of strings
        if required_permissions is None:
            self.required_permissions = set()
        elif isinstance(required_permissions, str):
            self.required_permissions = {required_permissions}
        else:
            self.required_permissions = set(required_permissions)
        super().__init__()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True # Superuser bypasses specific permission checks

        if not self.required_permissions:
            # If the permission class was instantiated with no specific permissions,
            # and user is authenticated (checked above), allow access.
            # This case might mean "any authenticated user" if no perms are specified.
            # However, for clarity, it's better to use IsAuthenticated directly in such cases.
            # Let's assume if HasPermission is used, it implies some permission might be checked.
            # If self.required_permissions is empty, it means "no specific permission required beyond authentication".
            return True

        user_permissions = set()
        # Ensure request.user.roles exists and is a manager
        if hasattr(request.user, 'roles') and request.user.roles.exists():
            for role in request.user.roles.all():
                # Ensure role.permissions exists and is a manager
                if hasattr(role, 'permissions') and role.permissions.exists():
                    for perm in role.permissions.all():
                        user_permissions.add(perm.name)

        return self.required_permissions.issubset(user_permissions)

class IsOwnerOrAdmin(permissions.BasePermission):
    message = 'You must be the owner or an admin to perform this action.'

    def has_object_permission(self, request, view, obj):
        # request.user.is_staff is a common way to check for admin-like privileges
        # request.user.is_superuser is for the absolute superuser
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        # Check if the object has a 'user' attribute or if the object itself is the user
        if hasattr(obj, 'user'): # For objects that have a 'user' foreign key
            return obj.user == request.user
        return obj == request.user # For objects that are user instances themselves
