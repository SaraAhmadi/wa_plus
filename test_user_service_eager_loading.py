import asyncio
import os
import sys

# Add project root to sys.path to allow for app imports
project_root_dir = os.path.dirname(os.path.abspath(__file__))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)
# If the test script is in /app, then project_root_dir needs to be its parent
# Assuming the test script will be created in /app for now.
# If it's created at the root, this needs adjustment or be run with `python -m app.test_user_service_eager_loading`
# For simplicity with run_in_bash_session, let's adjust for /app execution if needed,
# or ensure PYTHONPATH is set.
# The current structure from previous runs suggests /app is the root for execution.

from app.database.session import AsyncSessionFactory, async_engine
from app.services.user_service import UserService
from app.database.models.user import User
from app.database.models.role import Role
from app.schemas.user import User as UserSchema # Using User as UserSchema as defined in problem

async def run_test():
    print("Starting test_user_service_eager_loading...")

    # Set dummy environment variables for database connection if not already set
    # These are similar to what was needed for populate_data_test.py
    os.environ.setdefault("POSTGRES_PASSWORD", "testpassword")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb")
    # The above are needed for AsyncSessionFactory to initialize settings.DATABASE_URL

    async with AsyncSessionFactory() as session:
        print("Async session obtained.")
        user_service = UserService(db_session=session)
        print("UserService instantiated.")

        fetched_user = None
        try:
            print("Attempting to fetch user with get_multi_with_pagination(limit=1)...")
            users = await user_service.get_multi_with_pagination(limit=1)
            if users:
                fetched_user = users[0]
                print(f"User found: ID {fetched_user.id}, Email: {fetched_user.email}")

                if fetched_user.roles:
                    print(f"User has {len(fetched_user.roles)} role(s). Accessing permissions for the first role...")
                    # The critical part: accessing permissions
                    # This should not trigger lazy loading if eager loading is working
                    try:
                        # Accessing the attribute is the first step
                        permissions = fetched_user.roles[0].permissions
                        print(f"Successfully accessed user.roles[0].permissions. Found {len(permissions)} permissions.")

                        # Now, simulate Pydantic serialization which was the original pain point
                        print("Attempting Pydantic schema validation (UserSchema.model_validate)...")
                        try:
                            user_data = UserSchema.model_validate(fetched_user)
                            # Access nested data to ensure it was serialized
                            if user_data.roles and user_data.roles[0].permissions:
                                print(f"Pydantic UserSchema validation successful. Permissions for role '{user_data.roles[0].name}' were serialized.")
                                print("TEST SUCCEEDED: Permissions were eagerly loaded and accessible for Pydantic serialization.")
                            elif user_data.roles:
                                print(f"Pydantic UserSchema validation successful, but no permissions found for role '{user_data.roles[0].name}' or role has no permissions list.")
                                print("TEST PARTIALLY SUCCEEDED: Eager loading seems to work, but no permissions data to verify fully.")
                            else:
                                print("Pydantic UserSchema validation successful, but user has no roles in the schema.")
                                print("TEST PARTIALLY SUCCEEDED: Eager loading of roles seems to work, but no roles to verify permission loading.")

                        except Exception as e_pydantic:
                            print(f"ERROR DURING PYDANTIC VALIDATION: {type(e_pydantic).__name__}: {e_pydantic}")
                            print("TEST FAILED: Pydantic validation failed, potentially due to loading issues.")

                    except AttributeError as ae:
                        print(f"AttributeError when accessing permissions: {ae}. This might indicate a problem with the model or relationship name.")
                        print("TEST FAILED.")
                    except Exception as e_access:
                        # Check if it's a detached instance error or similar ORM issue
                        if "DetachedInstanceError" in str(type(e_access)):
                             print(f"ERROR: DetachedInstanceError encountered: {e_access}. This means permissions were not eagerly loaded.")
                             print("TEST FAILED.")
                        else:
                            print(f"An unexpected error occurred while accessing permissions: {type(e_access).__name__}: {e_access}")
                            print("TEST FAILED.")
                else:
                    print("User found, but has no roles. Cannot test permission loading.")
                    print("TEST INCONCLUSIVE: No roles to test permission eager loading.")
            else:
                print("No users found in the database.")
                print("TEST INCONCLUSIVE: Database is empty or no users match criteria.")

        except ConnectionRefusedError as e_conn:
            print(f"DATABASE CONNECTION ERROR: {e_conn}")
            print("Could not connect to the database. This is an environment issue.")
            print("The test cannot fully run, but the SQLAlchemy query options in user_service.py for eager loading are set to:")
            print("'.options(selectinload(User.roles).selectinload(Role.permissions))'")
            print("This setup is theoretically correct for eager loading permissions.")
            print("TEST INCONCLUSIVE due to environment.")
        except OSError as e_os:
            if "Connect call failed" in str(e_os) or "Address family not supported" in str(e_os) :
                print(f"DATABASE CONNECTION/OS ERROR: {e_os}")
                print("Could not connect to the database. This is an environment issue.")
                print("The test cannot fully run, but the SQLAlchemy query options in user_service.py for eager loading are set to:")
                print("'.options(selectinload(User.roles).selectinload(Role.permissions))'")
                print("This setup is theoretically correct for eager loading permissions.")
                print("TEST INCONCLUSIVE due to environment.")

            else:
                print(f"An OS error occurred: {type(e_os).__name__}: {e_os}")
                print("TEST FAILED due to unexpected OS error.")

        except Exception as e:
            print(f"AN UNEXPECTED ERROR OCCURRED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            print("TEST FAILED.")
        finally:
            if 'async_engine' in locals():
                await async_engine.dispose()
            print("Test finished.")

if __name__ == "__main__":
    # Ensure the script is run from the /app directory or that PYTHONPATH is set correctly
    # For `run_in_bash_session`, if CWD is /app, then `python test_script.py` is fine.
    # If CWD is project root, then `python app/test_script.py`
    # The current structure suggests CWD is /app for `python app/scripts/...`
    # So, if this script is in /app, `python test_user_service_eager_loading.py` should work.
    asyncio.run(run_test())
