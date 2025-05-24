import asyncio
import typer  # You'll need to add 'typer' to your pyproject.toml dev-dependencies
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust path if your script is outside the main app structure
# This assumes your script can import from 'app'
# If running from project root: python -m scripts.create_superuser
from app.core.config import settings  # To initialize DB if needed
from app.database.session import AsyncSessionFactory, create_db_and_tables  # For session and table creation
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.database.models import User as UserModel, Role as RoleModel  # For checking existing roles

cli_app = typer.Typer()


async def _create_superuser_logic(db: AsyncSession, email: str, username: str, password: str, full_name: Optional[str] = None):
    user_service = UserService(db)
    # First, check by username as it should be unique
    print(f"Checking if user with username '{username}' already exists...")
    user = await user_service.get_user_by_username(username=username)
    if not user:
        # If not found by username, check by email as a fallback or for older records
        print(f"No user with username '{username}' found. Checking by email '{email}'...")
        user = await user_service.get_user_by_email(email=email)

    if user:
        print(f"User found: ID={user.id}, Username='{user.username}', Email='{user.email}'.")
        if not user.is_superuser:
            print(f"User '{user.username or user.email}' exists but is not a superuser. Updating to superuser.")
            user.is_superuser = True
            db.add(user)
        else:
            print(f"User '{user.username or user.email}' already exists and is a superuser.")
    else:
        print(f"Creating superuser {username} ({email})...")
        user_in = UserCreate(
            email=email,
            username=username,
            password=password,
            full_name=full_name if full_name else "Admin User",
            is_superuser=True,
            is_active=True,
            role_ids=[]  # Optionally assign a specific "superuser" role ID here
        )
        user = await user_service.create_user(user_in=user_in)
        print(f"Superuser {user.username} ({user.email}) created successfully.")

    # Example: Ensure a "superuser" or "admin" role exists and assign it
    # admin_role_name = "Administrator" # Or "Superuser"
    # role_query = await db.execute(select(RoleModel).where(RoleModel.name == admin_role_name))
    # admin_role = role_query.scalars().first()
    # if not admin_role:
    #     print(f"Role '{admin_role_name}' not found. Please create it first or adjust script.")
    # elif admin_role not in user.roles:
    #     user.roles.append(admin_role)
    #     db.add(user)
    #     print(f"Assigned '{admin_role_name}' role to {user.email}")

    await db.commit()
    await db.refresh(user) # Ensure all attributes, including username, are loaded
    print(f"Superuser details: ID={user.id}, Email='{user.email}', Username='{user.username}', Is Superuser={user.is_superuser}")


@cli_app.command()
def create_admin(
        username: str = typer.Option(..., "--username", "-u", help="Superuser's username."),
        email: str = typer.Option(..., "--email", "-e", help="Superuser's email address."),
        password: str = typer.Option(
            ...,
            "--password",
            "-p",
            help="Superuser's password (will be prompted if not provided).",
            prompt=True,
            hide_input=True,  # Hides password input
            confirmation_prompt=True,  # Asks for password confirmation
        ),
        full_name: Optional[str] = typer.Option(None, "--name", "-n", help="Superuser's full name."),
):
    """
    Creates an administrative superuser in the database.
    """

    async def main():
        print("Attempting to create database tables if they don't exist (for CLI setup)...")
        # This is for convenience if running the script against a fresh DB
        # In production, migrations should handle table creation.
        # await create_db_and_tables() # Make sure your models are imported for Base.metadata

        async with AsyncSessionFactory() as session:
            await _create_superuser_logic(session, email, username, password, full_name)

    asyncio.run(main())


if __name__ == "__main__":
    cli_app()