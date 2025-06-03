from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from core.user_management.models import User, Role, Permission

class ViewTests(APITestCase):

    def setUp(self):
        # URLs for UserViewSet related actions
        self.register_url = reverse('user-list') # POST to user-list for registration
        self.user_me_url = reverse('user-get-current-user-details') # Custom action 'me'

        # URL for token authentication
        self.login_url = reverse('token_obtain_pair')

        self.user_data_for_registration = {
            'email': 'viewtest@example.com',
            'username': 'viewtestuser',
            'password': 'password123',
            'full_name': 'View Test User'
        }

        # Create a regular user for testing authenticated (non-admin) access
        self.regular_user_email = 'reguser@example.com'
        self.regular_user_username = 'reguser'
        self.regular_user_password = 'password123'
        self.regular_user = User.objects.create_user(
            email=self.regular_user_email,
            username=self.regular_user_username,
            password=self.regular_user_password
        )

        # Create an admin user
        self.admin_user_email = 'admintest@example.com'
        self.admin_user_username = 'admintest'
        self.admin_user_password = 'password123'
        self.admin_user = User.objects.create_superuser(
            email=self.admin_user_email,
            username=self.admin_user_username,
            password=self.admin_user_password
        )

    def test_user_registration_public(self):
        response = self.client.post(self.register_url, self.user_data_for_registration, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # Count should be initial 2 users + 1 newly registered
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(User.objects.filter(email=self.user_data_for_registration['email']).exists())

    def test_user_login(self):
        # Using the regular_user created in setUp for login
        login_data = {'email': self.regular_user_email, 'password': self.regular_user_password}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_get_current_user_details_me(self):
        login_data = {'email': self.regular_user_email, 'password': self.regular_user_password}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data) # Ensure login is OK
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response_me = self.client.get(self.user_me_url)
        self.assertEqual(response_me.status_code, status.HTTP_200_OK, response_me.data)
        self.assertEqual(response_me.data['email'], self.regular_user_email)

    def test_list_users_as_admin(self):
        login_data = {'email': self.admin_user_email, 'password': self.admin_user_password}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        list_users_url = reverse('user-list') # GET to user-list for listing
        response_list = self.client.get(list_users_url)
        self.assertEqual(response_list.status_code, status.HTTP_200_OK, response_list.data)
        # Response data is a list of users. Check if its length is at least 2 (admin and regular user).
        # Depending on pagination, it might be response_list.data['results']
        # Assuming no pagination for simplicity or default pagination includes these.
        data_to_check = response_list.data
        if 'results' in response_list.data and isinstance(response_list.data, dict): # Handle paginated response
            data_to_check = response_list.data['results']
        self.assertTrue(len(data_to_check) >= 2)

    def test_list_users_as_regular_user_forbidden(self):
        login_data = {'email': self.regular_user_email, 'password': self.regular_user_password}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        list_users_url = reverse('user-list')
        response_list = self.client.get(list_users_url)
        self.assertEqual(response_list.status_code, status.HTTP_403_FORBIDDEN, response_list.data)

    # Add more tests for RoleViewSet, PermissionViewSet, other UserViewSet actions and permissions
