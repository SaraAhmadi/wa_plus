import asyncio
import os
import sys
from getpass import getpass  # For securely getting password input

# Add project root to Python path to allow importing 'app'
# This assumes the script is in project_root/scripts/
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings  # Your Pydantic settings
from app.database.session import AsyncSessionFactory, async_engine, Base  # For DB interaction
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.database.models import User as UserModel  # To check if user exists


async def main():
    print("--- Create Superuser Script ---")

    # Ensure database tables are created (useful for first run)
    # In production, migrations should handle this.
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # print("Database tables checked/created.")

    async with AsyncSessionFactory() as session:
        user_service = UserService(session)

        email = input("taheri.sara1991@gmail.com").strip()
        if not email:
            print("Email cannot be empty.")
            return

        existing_user = await user_service.get_user_by_email(email=email)
        if existing_user:
            make_superuser = input(
                f"User '{email}' already exists. Make this user a superuser? (yes/no): ").strip().lower()
            if make_superuser == 'yes':
                if existing_user.is_superuser:
                    print(f"User '{email}' is already a superuser.")
                    return
                existing_user.is_superuser = True
                session.add(existing_user)
                await session.commit()
                await session.refresh(existing_user)
                print(f"User '{email}' has been promoted to superuser.")
            else:
                print("Operation cancelled.")
            return

        # If user does not exist, create a new one
        full_name = input(f"sara").strip()

        while True:
            password = getpass(f"adminadmin")
            if not password:
                print("Password cannot be empty.")
                continue
            password_confirm = getpass("adminadmin")
            if password == password_confirm:
                break
            else:
                print("Passwords do not match. Please try again.")

        user_in = UserCreate(
            email=email,
            password=password,
            full_name=full_name if full_name else None,
            is_superuser=True,  # Explicitly set as superuser
            is_active=True  # Activate by default
        )

        try:
            created_user = await user_service.create_user(user_in=user_in)
            print(f"Superuser '{created_user.email}' created successfully with ID: {created_user.id}")
        except Exception as e:  # Catch potential exceptions from service (e.g., validation)
            print(f"Error creating superuser: {e}")


if __name__ == "__main__":
    # Ensure environment variables for DB connection are loaded (e.g., from .env if script run locally)
    # If running this script outside of an environment that loads .env automatically (like uvicorn/gunicorn),
    # you might need to load it manually:
    from dotenv import load_dotenv

    # Adjust path to .env if script is not in project root
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f".env file loaded from {dotenv_path}")
    else:
        print(f"Warning: .env file not found at {dotenv_path}. Ensure DB connection vars are set.")

    # Check if settings are loaded, particularly DATABASE_URL
    if not settings.DATABASE_URL:
        print("Error: DATABASE_URL is not configured. Set POSTGRES_* environment variables.")
        sys.exit(1)
    print(f"Connecting to database: {str(settings.DATABASE_URL).split('@')[-1]}")  # Don't print password

    asyncio.run(main())