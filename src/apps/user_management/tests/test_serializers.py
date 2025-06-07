from django.test import TestCase
from core.user_management.serializers import UserSerializer, RoleSerializer, PermissionSerializer
from core.user_management.models import User, Role, Permission

class SerializerTests(TestCase):

    def setUp(self):
        self.permission1 = Permission.objects.create(name='perm1', description='Perm1 desc')
        self.role1 = Role.objects.create(name='Role1', description='Role1 desc')
        self.role1.permissions.add(self.permission1)

        self.user_data = {
            'email': 'testserializer@example.com',
            'username': 'testserializer',
            'password': 'password123',
            'full_name': 'Test Serializer User'
        }
        # Corrected: create_user expects email and password as positional or keyword.
        # For the representation test, create a user instance first.
        self.user_instance_for_repr = User.objects.create_user(
            email='repruser@example.com',
            username='repruser',
            password='password123',
            full_name='Repr User'
        )
        self.user_instance_for_repr.roles.add(self.role1)


        self.role_data = {'name': 'New Role', 'description': 'A new role'}
        self.permission_data = {'name': 'new_perm', 'description': 'A new permission'}

    def test_user_serializer_create(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_user_serializer_representation(self):
        # User instance for representation is self.user_instance_for_repr
        serializer = UserSerializer(instance=self.user_instance_for_repr)
        data = serializer.data
        self.assertEqual(data['email'], self.user_instance_for_repr.email)
        self.assertNotIn('password', data) # Password should not be in representation
        self.assertTrue(len(data['roles']) == 1)
        self.assertEqual(data['roles'][0]['name'], self.role1.name)

    def test_role_serializer_create_with_permissions(self):
        data = {**self.role_data, 'permission_ids': [self.permission1.id]}
        serializer = RoleSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        role = serializer.save()
        self.assertEqual(role.name, self.role_data['name'])
        self.assertIn(self.permission1, role.permissions.all())

    def test_permission_serializer(self):
        serializer = PermissionSerializer(data=self.permission_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        permission = serializer.save()
        self.assertEqual(permission.name, self.permission_data['name'])
