from django.core.management.base import BaseCommand
from django.db import transaction
from core.user_management.models import User, Role, Permission # Adjust import path as needed

class Command(BaseCommand):
    help = 'Populates the database with initial development data: roles, permissions, and test users.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data population...'))

        # Define permissions
        permissions_data = [
            {'name': 'view_content', 'description': 'Can view content'},
            {'name': 'edit_content', 'description': 'Can edit content'},
            {'name': 'publish_content', 'description': 'Can publish content'},
            {'name': 'manage_users', 'description': 'Can manage users (subset of admin)'},
        ]
        permissions = {}
        for p_data in permissions_data:
            perm, created = Permission.objects.get_or_create(name=p_data['name'], defaults={'description': p_data['description']})
            permissions[p_data['name']] = perm
            if created:
                self.stdout.write(f'Created permission: {perm.name}')

        # Define roles and assign permissions
        roles_data = [
            {'name': 'Admin', 'description': 'Administrator with all standard permissions', 'perms': list(permissions.keys())},
            {'name': 'Editor', 'description': 'Can view, edit, and publish content', 'perms': ['view_content', 'edit_content', 'publish_content']},
            {'name': 'Viewer', 'description': 'Can only view content', 'perms': ['view_content']},
        ]
        roles = {}
        for r_data in roles_data:
            role, created = Role.objects.get_or_create(name=r_data['name'], defaults={'description': r_data['description']})
            roles[r_data['name']] = role
            if created:
                self.stdout.write(f'Created role: {role.name}')

            # Clear existing permissions before adding new ones to ensure consistency
            role.permissions.clear()
            for perm_name in r_data['perms']:
                if perm_name in permissions:
                    role.permissions.add(permissions[perm_name])
            # No need for role.save() if only M2M fields are changed, but good practice if other fields might change.
            # In this case, defaults are set during get_or_create.

        # Define test users and assign roles
        users_data = [
            {'username': 'devadmin', 'email': 'devadmin@example.com', 'password': 'password', 'is_staff': True, 'is_superuser': False, 'full_name': 'Dev Admin', 'roles': ['Admin']},
            {'username': 'editoruser', 'email': 'editor@example.com', 'password': 'password', 'is_staff': False, 'is_superuser': False, 'full_name': 'Editor User', 'roles': ['Editor']},
            {'username': 'vieweruser', 'email': 'viewer@example.com', 'password': 'password', 'is_staff': False, 'is_superuser': False, 'full_name': 'Viewer User', 'roles': ['Viewer']},
        ]

        for u_data in users_data:
            if not User.objects.filter(username=u_data['username']).exists():
                # Prepare data for create_user, excluding custom fields like 'roles'
                user_creation_data = {
                    'email': u_data['email'],
                    'username': u_data['username'],
                    'full_name': u_data.get('full_name', ''),
                    # Pass is_staff and is_superuser directly to create_user if your manager handles them
                    # Otherwise, set them after creation as done below.
                    # Our UserManager.create_user takes **extra_fields, which can include these.
                    'is_staff': u_data.get('is_staff', False),
                    'is_superuser': u_data.get('is_superuser', False)
                }
                user = User.objects.create_user(password=u_data['password'], **user_creation_data)

                # Assign roles
                for role_name in u_data['roles']:
                    if role_name in roles:
                        user.roles.add(roles[role_name])
                self.stdout.write(f'Created user: {user.username} with roles: {u_data["roles"]}')
            else:
                self.stdout.write(self.style.WARNING(f'User {u_data["username"]} already exists. Skipping.'))

        self.stdout.write(self.style.SUCCESS('Data population complete.'))
