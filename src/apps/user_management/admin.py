from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission

# We need a custom UserAdmin to handle the custom User model
# For now, we can start with a simple one and customize later if needed.
# If your User model has custom fields that should be displayed in the admin,
# they would be added to fieldsets, list_display, etc. here.


class UserAdmin(BaseUserAdmin):
    # Add or override UserAdmin settings here if necessary
    # For example, if you have custom fields in your User model like 'full_name'
    # you might want to add them to list_display or fieldsets.
    list_display = ('email', 'full_name', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'roles')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    filter_horizontal = ('roles', 'groups', 'user_permissions',)

    # If your User model doesn't use the standard 'username' field prominently,
    # or if 'email' is the USERNAME_FIELD, ensure fieldsets reflect this.
    # The default UserAdmin fieldsets might assume 'username'.
    # Here's an example adapting default fieldsets:
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'username')}), # 'username' is present but nullable
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Roles', {'fields': ('roles',)}),
    )
    readonly_fields = ('last_login', 'created_at', 'updated_at')


admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(Permission)
