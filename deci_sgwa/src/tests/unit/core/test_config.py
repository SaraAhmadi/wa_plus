import unittest
import os
from unittest.mock import patch
from pydantic import PostgresDsn

# Apply a patch at the module level immediately.
# This is to ensure that when deci_sgwa.src.app.core.config is imported (and instantiates a global Settings),
# the required environment variables are already set.
IMMEDIATE_ENV_PATCHER = patch.dict(os.environ, {
    "POSTGRES_PASSWORD": "immediate_test_password",
    "SECRET_KEY": "immediate_test_secret"
    # Add other required env vars for Settings model if any
})
IMMEDIATE_ENV_PATCHER.start()

# Now import the application modules
from deci_sgwa.src.app.core.config import Settings, SettingsConfigDict

# Ensure model_config is explicitly set for tests if not already applied globally
# This is to avoid issues if Settings is imported before model_config is set in the main app flow
# However, in this specific case, Settings already defines model_config.
# If it didn't, we might need something like:
# Settings.model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', case_sensitive=True, extra='ignore')

def tearDownModule():
    """Clean up environment variables after all tests in this module have run."""
    IMMEDIATE_ENV_PATCHER.stop()

class TestConfigAssembleDbConnection(unittest.TestCase):

    def test_assemble_db_connection_default_port(self):
        """
        Test that the default port (5432) is used and is an integer
        when POSTGRES_PORT environment variable is not set.
        """
        env_vars = {
            "POSTGRES_USER": "test_user",
            "POSTGRES_USER": "test_user", # Explicitly set user for this test
            "POSTGRES_PASSWORD": "test_password_default_port", # Different from class/import mock
            "POSTGRES_SERVER": "localhost",
            "POSTGRES_DB": "test_db",
            # POSTGRES_PORT is intentionally not set
        }
        # clear=True ensures that only env_vars are present for this specific test's Settings() instantiation
        with patch.dict(os.environ, env_vars, clear=True):
            current_settings = Settings()
            db_url = current_settings.DATABASE_URL

            self.assertIsNotNone(db_url)
            self.assertIsInstance(db_url, PostgresDsn)
            # Access port via the ._url.hosts()[0]['port']
            self.assertTrue(db_url._url.hosts()) # Ensure hosts list is not empty
            self.assertEqual(db_url._url.hosts()[0]['port'], 5432)
            self.assertIsInstance(db_url._url.hosts()[0]['port'], int)

    def test_assemble_db_connection_custom_port(self):
        """
        Test that a custom port is used and correctly converted to an integer
        when POSTGRES_PORT environment variable is set.
        """
        custom_port = "5433"
        env_vars = {
            "POSTGRES_USER": "test_user",
            "POSTGRES_USER": "test_user", # Explicitly set user
            "POSTGRES_PASSWORD": "test_password_custom_port", # Different password
            "POSTGRES_SERVER": "localhost",
            "POSTGRES_DB": "test_db",
            "POSTGRES_PORT": custom_port,
        }
        with patch.dict(os.environ, env_vars, clear=True):
            current_settings = Settings()
            db_url = current_settings.DATABASE_URL

            self.assertIsNotNone(db_url)
            self.assertIsInstance(db_url, PostgresDsn)
            self.assertTrue(db_url._url.hosts())
            self.assertEqual(db_url._url.hosts()[0]['port'], int(custom_port))
            self.assertIsInstance(db_url._url.hosts()[0]['port'], int)

    def test_assemble_db_connection_with_database_url(self):
        """
        Test that DATABASE_URL environment variable, when set,
        overrides other individual PostgreSQL environment variables.
        """
        direct_db_url_str = "postgresql+asyncpg://direct_user:direct_password@direct_host:1234/direct_db"
        env_vars = {
            "DATABASE_URL": direct_db_url_str,
            "POSTGRES_USER": "ignored_user",
            "POSTGRES_USER": "ignored_user", # Ensure this is set if needed by Settings construction
            "POSTGRES_PASSWORD": "ignored_password",
            "POSTGRES_SERVER": "ignored_host",
            "POSTGRES_DB": "ignored_db",
            "POSTGRES_PORT": "9999", # Should be ignored
        }
        with patch.dict(os.environ, env_vars, clear=True):
            current_settings = Settings()
            db_url = current_settings.DATABASE_URL

            self.assertIsNotNone(db_url)
            self.assertIsInstance(db_url, PostgresDsn)
            # Pydantic's PostgresDsn will parse the string.
            # We compare the string representation for simplicity here,
            # though comparing individual components (user, password, host, port, path) would be more robust.
            self.assertEqual(str(db_url), direct_db_url_str)
            # Specifically check the port from the DATABASE_URL
            self.assertTrue(db_url._url.hosts())
            self.assertEqual(db_url._url.hosts()[0]['port'], 1234)
            self.assertIsInstance(db_url._url.hosts()[0]['port'], int)


if __name__ == '__main__':
    unittest.main()
