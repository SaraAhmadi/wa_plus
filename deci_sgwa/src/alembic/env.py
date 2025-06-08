import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context  # <<< 'context' is imported from Alembic

# --- Alembic Config object ---
# 'config' IS DEFINED BY ALEMBIC WHEN IT RUNS THIS SCRIPT.
# It's an instance of alembic.config.Config
config = context.config  # This is correct, context is available here.

# Get database credentials directly from environment
POSTGRES_USER = os.getenv("POSTGRES_USER", "waplus_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "waplus_db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "water_accounting_db")

# Construct database URL
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

print(f"========Environment variables:====================")
print(f"  ==========POSTGRES_USER: {POSTGRES_USER}")
print(f"  ==========POSTGRES_SERVER: {POSTGRES_SERVER}")
print(f"  =========POSTGRES_PORT: {POSTGRES_PORT}")
print(f"  =========POSTGRES_DB: {POSTGRES_DB}")
print(f"Constructed DATABASE_URL: {DATABASE_URL}")


# --- Python Logging ---
# Interpret the config file for Python logging.
# This line reads the logging.ini file if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Add project root to Python path for imports ---
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

# --- Import your application's Base model and settings ---
from app.database.models.base_model import Base as TargetBase
from app.core.config import settings

# --- Set the target_metadata for Alembic ---
target_metadata = TargetBase.metadata

# --- Configure sqlalchemy.url for Alembic's offline/generation needs ---
# This is done if not explicitly set in alembic.ini, ensuring env.py can be the source of truth.
if not config.get_main_option("sqlalchemy.url"):
    sync_db_url = str(settings.DATABASE_URL)
    if "+asyncpg" in sync_db_url:
        sync_db_url = sync_db_url.replace("+asyncpg", "+psycopg2")
    elif "postgresql://" in sync_db_url and "+psycopg2" not in sync_db_url:
        sync_db_url = sync_db_url.replace("postgresql://", "postgresql+psycopg2://")

    config.set_main_option("sqlalchemy.url", sync_db_url)
    print(f"Alembic (env.py): Set synchronous sqlalchemy.url for offline/generation: {sync_db_url}")


# This function can be defined globally in env.py or within the run_migrations_ Fns
def include_object(object, name, type_, reflected, compare_to):
    """
    Should you include this table or sequence in the autogenerate pass?
    Return True if you want to include it, False if you want to ignore it.
    """
    if type_ == "table" and name in ["spatial_ref_sys", "geometry_columns", "raster_columns", "raster_overviews"]:
        # Add other PostGIS-specific or extension-managed tables here if needed
        return False
    else:
        return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        # Add include_object to filter out PostGIS tables during autogenerate comparison
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Helper function to run migrations within a transaction for online mode."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # Add include_object to filter out PostGIS tables during autogenerate comparison
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    # Use the DATABASE_URL we constructed from environment variables
    connectable = create_async_engine(
        DATABASE_URL,  # Use this instead of settings.DATABASE_URL
        pool_pre_ping=True,
        poolclass=pool.NullPool
    )
    print(f"Alembic (env.py): Running online migrations with ASYNC URL: {DATABASE_URL}")

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()
    print("Alembic (env.py): Online migrations complete, engine disposed.")



# --- Main execution logic for Alembic ---
# THIS BLOCK MUST COME AFTER 'config = context.config' and other setup
# because 'context.is_offline_mode()' relies on the 'context' object.
if context.is_offline_mode():
    print("Alembic (env.py): Running migrations in OFFLINE mode.")
    run_migrations_offline()
else:
    print("Alembic (env.py): Running migrations in ONLINE mode.")
    asyncio.run(run_migrations_online())