import os
from django.core.management.base import BaseCommand, CommandError
from core.user_management.models import User # Assuming User is in core.user_management.models
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Creates a superuser from environment variables (DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD)'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([username, email, password]):
            raise CommandError('Please set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD environment variables.')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superuser with username "{username}" already exists. Skipping.'))
            return

        if User.objects.filter(email=email).exists():
            # Check if the existing user with this email is the same as the one with the username
            # This is a bit more nuanced: if username also matches, it's the same user, covered by above.
            # If username is different, then it's a conflict on email.
            existing_user_by_email = User.objects.get(email=email)
            if existing_user_by_email.username != username:
                self.stdout.write(self.style.WARNING(f'A user with email "{email}" but different username ("{existing_user_by_email.username}") already exists. Skipping superuser creation for "{username}".'))
                return
            # If it's the same user (username and email match), the first check for username would have caught it.

        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"'))
        except IntegrityError as e:
            # This might still occur if, despite checks, there's a race condition or other constraint violation
            raise CommandError(f'Error creating superuser: {e}. Does a user with that username or email already exist?')
        except Exception as e:
            raise CommandError(f'An unexpected error occurred: {e}')
