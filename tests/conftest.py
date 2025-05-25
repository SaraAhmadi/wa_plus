import asyncio
import pytest
from typing import AsyncGenerator, Generator, Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app  # Your FastAPI application instance
from app.core.config import settings
from app.database.models.base_model import Base as SQLAlchemyBase  # All your models inherit from this
from app.dependencies import get_db  # The dependency we want to override

# --- Test Database Setup ---
# Use a separate test database (e.g., waplus_db_test)
# Ensure this database exists or can be created.
TEST_DATABASE_URL = str(settings.DATABASE_URL).replace(
    settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_test"
)
if settings.POSTGRES_DB + "_test" not in TEST_DATABASE_URL:  # Basic check
    # If POSTGRES_DB was not in the original URL (e.g. full DSN provided)
    # this replacement might not work as expected. Adjust logic if needed.
    # For now, assume simple DB name replacement is okay.
    # A more robust way is to parse DATABASE_URL and rebuild it.
    print(f"Warning: Could not reliably create TEST_DATABASE_URL from {settings.DATABASE_URL}")
    # Fallback or raise error
    TEST_DATABASE_URL = "postgresql+asyncpg://testuser:testpass@localhost:5433/test_db"  # Example fallback

test_async_engine = create_async_engine(TEST_DATABASE_URL, echo=False)  # Echo off for tests

TestingAsyncSessionFactory = sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override FastAPI dependency for test database session."""
    async with TestingAsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()  # Commit at the end of a successful test "transaction"
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Apply the override to the FastAPI app instance for all tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """
    Create and drop test database tables for the test session.
    `autouse=True` makes this fixture run automatically for the session.
    """
    async with test_async_engine.begin() as conn:
        await conn.run_sync(SQLAlchemyBase.metadata.drop_all)  # Drop first to ensure clean state
        await conn.run_sync(SQLAlchemyBase.metadata.create_all)
    print(f"Test database tables created at {TEST_DATABASE_URL}")
    yield
    async with test_async_engine.begin() as conn:
        await conn.run_sync(SQLAlchemyBase.metadata.drop_all)
    print(f"Test database tables dropped from {TEST_DATABASE_URL}")
    await test_async_engine.dispose()  # Dispose of the engine connections


@pytest.fixture(scope="function")  # function scope for db session to ensure isolation
async def db_session(setup_test_database: None) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean database session for each test function.
    Relies on setup_test_database to ensure tables exist.
    """
    async with TestingAsyncSessionFactory() as session:
        try:
            yield session
            # Transactions are typically handled by the override_get_db or test logic itself
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def test_client(setup_test_database: None) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an HTTPX AsyncClient for making requests to the FastAPI app.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # The app.dependency_overrides[get_db] = override_get_db is already set globally
        yield client


# --- Authentication Fixtures (Example) ---
from app.security.token_utils import create_access_token
from app.database.models import User, Role
from app.schemas.user import UserCreate
from app.services.user_service import UserService  # For creating test users


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Creates a standard test user."""
    user_service = UserService(db_session)
    user_in = UserCreate(
        email="testuser@example.com",
        password="SecurePassword123!",
        full_name="Test User"
        # role_ids=[] # Assign roles if needed
    )
    user = await user_service.create_user(user_in=user_in)
    return user


@pytest.fixture(scope="function")
async def superuser_token_headers(db_session: AsyncSession) -> Dict[str, str]:
    """Returns headers for an authenticated superuser."""
    user_service = UserService(db_session)
    # Ensure a superuser role exists or create one
    # For simplicity, creating a superuser directly
    superuser_in = UserCreate(
        email="superuser@example.com",
        password="SuperSecurePassword123!",
        full_name="Super User",
        is_superuser=True  # Set this flag
    )
    superuser = await user_service.get_user_by_email(superuser_in.email)
    if not superuser:
        superuser = await user_service.create_user(user_in=superuser_in)

    token = create_access_token(subject=superuser.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def normal_user_token_headers(test_user: User) -> Dict[str, str]:
    """Returns headers for an authenticated normal user (created by test_user fixture)."""
    token = create_access_token(subject=test_user.email)
    return {"Authorization": f"Bearer {token}"}

# Add more fixtures as needed (e.g., for creating specific test data for models)
