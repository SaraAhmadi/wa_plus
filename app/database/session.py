from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings
from app.database.models.base_model import Base # To ensure Base is known for metadata creation

# Create an asynchronous engine instance.
# The 'echo=True' argument will log all SQL statements issued to the database,
# which is useful for debugging during development. Set to False in production.
async_engine = create_async_engine(
    str(settings.DATABASE_URL),  # Ensure DATABASE_URL is a string
    echo=settings.DEBUG,         # Log SQL queries if DEBUG is True
    pool_pre_ping=True,          # Test connections before handing them out from the pool
    # Adjust pool size based on expected concurrency and database limits
    # pool_size=10,
    # max_overflow=20,
)

# Create an asynchronous session class.
# - expire_on_commit=False: Prevents SQLAlchemy from expiring attributes on instances
#   after a commit. This can be useful in async contexts or if you need to access
#   attributes of an object after it has been committed and the session is closed.
# - class_=AsyncSession: Specifies that we are creating an asynchronous session.
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False, # Recommended to manage flush manually in async code
    autocommit=False # Recommended to manage commit manually
)


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get an asynchronous database session.
    This will be injected into API route handlers.
    It ensures the session is properly closed after the request is handled.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # If no exceptions, and if your service layer doesn't explicitly commit,
            # you might consider a commit here, but typically services handle commits.
            # await session.commit() # Generally, commit within service logic for transactional control
        except Exception:
            await session.rollback() # Rollback in case of any exception during the request handling
            raise
        finally:
            await session.close() # Ensure session is closed


async def create_db_and_tables():
    """
    (Optional Utility) Creates all database tables defined in SQLAlchemy models.
    This is typically run once when setting up the application or during migrations.
    For production, Alembic is preferred for managing schema migrations.
    """
    async with async_engine.begin() as conn:
        # For creating all tables based on Base.metadata
        # Make sure all your models are imported somewhere so Base.metadata knows about them.
        # Often, importing them in models/__init__.py is sufficient.
        await conn.run_sync(Base.metadata.create_all)
    # print("Database tables created (if they didn't exist).")


async def drop_db_and_tables():
    """
    (Optional Utility - DANGEROUS) Drops all database tables.
    Use with extreme caution, primarily for development/testing.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # print("Database tables dropped.")


if __name__ == "__main__":
    # Example of how to use create_db_and_tables (run this script directly)
    # Ensure your .env file is set up for DATABASE_URL
    import asyncio

    async def main():
        print(f"Attempting to connect to DB: {settings.DATABASE_URL}")
        # You might want to create tables using Alembic instead for a real project
        await create_db_and_tables()
        # await drop_db_and_tables() # Uncomment with caution to drop tables

    # For Python 3.7+
    # asyncio.run(main())

    # For older Pythons or specific event loop needs:
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    pass # Keep the if __name__ block minimal or for simple tests
