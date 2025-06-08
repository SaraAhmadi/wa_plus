import asyncio
import typer
import os
import sys
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

# Suppress bcrypt version warnings
os.environ['PASSLIB_BCRYPT_NO_WARN'] = '1'
logging.getLogger("passlib").setLevel(logging.ERROR)

# Adjust path to ensure app imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.settings.config import settings
from src.database.session import AsyncSessionFactory
from src.schemas.user import UserCreate
from src.services.user_service import UserService

cli_app = typer.Typer()


async def create_superuser(
        db: AsyncSession,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
) -> None:
    """Core logic to create or update superuser"""
    user_service = UserService(db)

    # Check if user exists by username or email
    user = await user_service.get_user_by_username(username)
    if not user:
        user = await user_service.get_user_by_email(email)

    if user:
        print(f"User found: ID={user.id}, Email={user.email}")
        if not user.is_superuser:
            print("Upgrading user to superuser")
            user.is_superuser = True
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            print("User is already a superuser")
    else:
        print(f"Creating new superuser: {username}")
        user_in = UserCreate(
            email=email,
            username=username,
            password=password,
            full_name=full_name or "Admin User",
            is_superuser=True,
            is_active=True
        )
        user = await user_service.create_user(user_in)
        print(f"Superuser created: ID={user.id}")

    print(f"Superuser details: ID={user.id}, Email={user.email}, Username={user.username}")


@cli_app.command()
def create_admin(
        username: str = typer.Option(..., "--username", "-u", help="Admin username"),
        email: str = typer.Option(..., "--email", "-e", help="Admin email"),
        password: str = typer.Option(
            ...,
            "--password",
            "-p",
            prompt=True,
            hide_input=True,
            confirmation_prompt=True,
            help="Admin password"
        ),
        full_name: Optional[str] = typer.Option(None, "--name", "-n", help="Full name")
) -> None:
    """CLI command to create admin superuser"""

    async def run_async() -> None:
        async with AsyncSessionFactory() as session:
            await create_superuser(
                session,
                email=email,
                username=username,
                password=password,
                full_name=full_name
            )

    asyncio.run(run_async())


if __name__ == "__main__":
    cli_app()