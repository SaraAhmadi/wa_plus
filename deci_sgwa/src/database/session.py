from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from src.settings.config import settings # Your Pydantic settings instance
from src.database.models.base_model import Base # To ensure Base is known for metadata creation

# Create an asynchronous engine instance.
# The 'echo=settings.DEBUG' will log SQL statements if DEBUG is True.
async_engine = create_async_engine(
    str(settings.DATABASE_URL),     # Ensure DATABASE_URL from settings is a string
    echo=settings.DEBUG,            # Log SQL queries if DEBUG is True
    pool_pre_ping=True,             # Test connections before handing them out
    connect_args={"server_settings": {"timezone": "utc"}} # <<< CRITICAL: Set session timezone to UTC
)

# Create an asynchronous session class factory.
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False, # Keep objects accessible after commit
    autoflush=False,        # Manage flush manually in async code
    autocommit=False        # Manage commit manually
)


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get an asynchronous database session.
    Ensures the session is properly closed after the request.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # Commits should ideally happen within service layers for transactional control.
            # If a service doesn't commit, and you want to commit at the end of a successful request:
            # await session.commit() # But this is usually too broad.
        except Exception:
            await session.rollback() # Rollback in case of any exception
            raise
        finally:
            await session.close() # Ensure session is always closed


async def create_db_and_tables():
    """
    (Optional Utility for Dev/Test) Creates all database tables defined in SQLAlchemy models.
    For production, always use Alembic migrations.
    """
    async with async_engine.begin() as conn:
        # Ensure all your models are imported somewhere (e.g., in models/__init__.py)
        # so that Base.metadata is populated before this call.
        await conn.run_sync(Base.metadata.create_all)
    print("Development: Database tables created/checked via create_db_and_tables().")


async def drop_db_and_tables():
    """
    (Optional Utility - DANGEROUS) Drops all database tables.
    Use with extreme caution, primarily for development/testing.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Development: Database tables dropped via drop_db_and_tables().")

# Example for standalone script execution (not typically run this way for FastAPI)
if __name__ == "__main__":
    import asyncio
    async def _test_setup():
        print(f"Using DATABASE_URL: {settings.DATABASE_URL}")
        await create_db_and_tables()
        # await drop_db_and_tables() # Be careful
    asyncio.run(_test_setup())