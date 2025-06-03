from django.test import TestCase
from django.db.utils import IntegrityError
from core.user_management.models import User, Role, Permission

class ModelTests(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(email='test@example.com', username='testuser', password='password123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(email='admin@example.com', username='adminuser', password='password123')
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    def test_create_role(self):
        role = Role.objects.create(name='Editor', description='Can edit content.')
        self.assertEqual(role.name, 'Editor')

    def test_create_permission(self):
        permission = Permission.objects.create(name='edit_article', description='Can edit articles.')
        self.assertEqual(permission.name, 'edit_article')

    def test_role_permission_assignment(self):
        role = Role.objects.create(name='Viewer')
        permission = Permission.objects.create(name='view_article')
        role.permissions.add(permission)
        self.assertIn(permission, role.permissions.all())

    def test_user_role_assignment(self):
        user = User.objects.create_user(email='user@example.com', username='user', password='password')
        role = Role.objects.create(name='Member')
        user.roles.add(role)
        self.assertIn(role, user.roles.all())

    def test_unique_email_constraint(self):
        User.objects.create_user(email='unique@example.com', username='user1', password='password')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email='unique@example.com', username='user2', password='password')
