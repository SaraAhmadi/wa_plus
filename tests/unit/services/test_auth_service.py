import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth_service import AuthService
from app.services.user_service import UserService # To mock this dependency
from app.database.models.user import User as UserModel # SQLAlchemy model
from app.security.hashing import Hasher # To mock Hasher.verify_password

# pytestmark = pytest.mark.asyncio # Apply to all tests in this module

@pytest.fixture
def mock_user_service() -> AsyncMock:
    """Fixture to create a mock UserService."""
    service = AsyncMock(spec=UserService)
    service.get_user_by_email = AsyncMock()
    service.get_user_by_username = AsyncMock()
    return service

@pytest.fixture
def auth_service(mock_user_service: AsyncMock) -> AuthService:
    """Fixture to create an AuthService instance with a mock UserService."""
    # AuthService typically takes a db_session, but its methods use self.user_service.
    # If AuthService directly used db_session for other things, we'd mock db_session too.
    # For this setup, we directly inject the mocked user_service.
    
    # Create a mock db_session just to instantiate AuthService
    mock_db_session = AsyncMock() 
    
    auth_service_instance = AuthService(db_session=mock_db_session)
    # Replace the internally created UserService with our mock
    auth_service_instance.user_service = mock_user_service 
    return auth_service_instance

@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_with_email_success(
    mock_verify_password: MagicMock,
    auth_service: AuthService, 
    mock_user_service: AsyncMock
):
    # Arrange
    test_email = "test@example.com"
    test_password = "correct_password"
    mock_user = UserModel(id=1, email=test_email, username="testuser", hashed_password="hashed_pw", is_active=True)
    
    mock_user_service.get_user_by_email.return_value = mock_user
    mock_user_service.get_user_by_username.return_value = None # Should not be called
    mock_verify_password.return_value = True

    # Act
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_email, password=test_password)

    # Assert
    mock_user_service.get_user_by_email.assert_called_once_with(email=test_email)
    mock_user_service.get_user_by_username.assert_not_called()
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password)
    assert authenticated_user is not None
    assert authenticated_user == mock_user

@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_with_username_success(
    mock_verify_password: MagicMock,
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    test_username = "testuser"
    test_password = "correct_password"
    mock_user = UserModel(id=1, email="test@example.com", username=test_username, hashed_password="hashed_pw", is_active=True)

    # Logic in auth_service: if "@" in login_identifier, try email. Otherwise, skip email.
    # For test_username = "testuser", email check is skipped.
    mock_user_service.get_user_by_email.return_value = None 
    mock_user_service.get_user_by_username.return_value = mock_user
    mock_verify_password.return_value = True
    
    # Act
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_username, password=test_password)

    # Assert
    mock_user_service.get_user_by_email.assert_not_called() # Because "testuser" does not contain "@"
    mock_user_service.get_user_by_username.assert_called_once_with(username=test_username)
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password)
    assert authenticated_user is not None
    assert authenticated_user == mock_user

@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_with_username_if_email_fails(
    mock_verify_password: MagicMock,
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    # This tests the case where login_identifier looks like an email, but no user is found by email
    test_login_identifier_like_email = "user_not_by_email@example.com"
    test_username_fallback = "user_not_by_email" # assume this is the username of the user
    test_password = "correct_password"
    mock_user = UserModel(id=1, email=test_login_identifier_like_email, username=test_username_fallback, hashed_password="hashed_pw", is_active=True)

    mock_user_service.get_user_by_email.return_value = None # Email lookup fails
    mock_user_service.get_user_by_username.return_value = mock_user # Username lookup succeeds
    mock_verify_password.return_value = True
    
    # Act
    # The auth_service will try email, fail, then try username with the same identifier.
    # This specific test setup might be slightly off if the username is different from the email identifier.
    # The logic is: if user not found by email, it uses the *same* login_identifier for username.
    # So, this test is more about "login_identifier contains @, email fails, then try username with login_identifier"
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_login_identifier_like_email, password=test_password)

    # Assert
    mock_user_service.get_user_by_email.assert_called_once_with(email=test_login_identifier_like_email)
    # The same identifier is used for username lookup
    mock_user_service.get_user_by_username.assert_called_once_with(username=test_login_identifier_like_email)
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password)
    assert authenticated_user is not None
    assert authenticated_user == mock_user


@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_with_username_wrong_password(
    mock_verify_password: MagicMock,
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    test_username = "testuser"
    test_password = "wrong_password"
    mock_user = UserModel(id=1, email="test@example.com", username=test_username, hashed_password="hashed_pw", is_active=True)

    mock_user_service.get_user_by_email.return_value = None
    mock_user_service.get_user_by_username.return_value = mock_user
    mock_verify_password.return_value = False # Simulate wrong password

    # Act
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_username, password=test_password)

    # Assert
    mock_user_service.get_user_by_username.assert_called_once_with(username=test_username)
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password)
    assert authenticated_user is None

@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_with_email_wrong_password(
    mock_verify_password: MagicMock,
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    test_email = "test@example.com"
    test_password = "wrong_password"
    mock_user = UserModel(id=1, email=test_email, username="testuser", hashed_password="hashed_pw", is_active=True)

    mock_user_service.get_user_by_email.return_value = mock_user
    mock_verify_password.return_value = False # Simulate wrong password

    # Act
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_email, password=test_password)

    # Assert
    mock_user_service.get_user_by_email.assert_called_once_with(email=test_email)
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password)
    assert authenticated_user is None

@pytest.mark.asyncio
async def test_authenticate_user_not_found(
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    test_identifier_email_format = "nonexistent@example.com"
    test_identifier_plain = "nonexistentuser"
    test_password = "any_password"

    # Case 1: Identifier is in email format
    mock_user_service.get_user_by_email.return_value = None
    mock_user_service.get_user_by_username.return_value = None # Fallback also returns None
    
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_identifier_email_format, password=test_password)
    
    mock_user_service.get_user_by_email.assert_called_once_with(email=test_identifier_email_format)
    mock_user_service.get_user_by_username.assert_called_once_with(username=test_identifier_email_format) # Called with same identifier
    assert authenticated_user is None

    # Reset mocks for Case 2
    mock_user_service.get_user_by_email.reset_mock()
    mock_user_service.get_user_by_username.reset_mock()

    # Case 2: Identifier is plain (no "@")
    mock_user_service.get_user_by_email.return_value = None # Should not be called
    mock_user_service.get_user_by_username.return_value = None
    
    authenticated_user_plain = await auth_service.authenticate_user(login_identifier=test_identifier_plain, password=test_password)
    
    mock_user_service.get_user_by_email.assert_not_called()
    mock_user_service.get_user_by_username.assert_called_once_with(username=test_identifier_plain)
    assert authenticated_user_plain is None


@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_inactive_with_username(
    mock_verify_password: MagicMock,
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    test_username = "inactiveuser"
    test_password = "correct_password" 
    mock_user = UserModel(id=1, email="inactive@example.com", username=test_username, hashed_password="hashed_pw", is_active=False)

    mock_user_service.get_user_by_email.return_value = None
    mock_user_service.get_user_by_username.return_value = mock_user
    mock_verify_password.return_value = True # Assume password would be correct

    # Act
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_username, password=test_password)

    # Assert
    mock_user_service.get_user_by_username.assert_called_once_with(username=test_username)
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password) # Password verified before active check
    assert authenticated_user is None

@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.verify_password")
async def test_authenticate_user_inactive_with_email(
    mock_verify_password: MagicMock,
    auth_service: AuthService,
    mock_user_service: AsyncMock
):
    # Arrange
    test_email = "inactive@example.com"
    test_password = "correct_password"
    mock_user = UserModel(id=1, email=test_email, username="inactiveuser", hashed_password="hashed_pw", is_active=False)
    
    mock_user_service.get_user_by_email.return_value = mock_user
    mock_user_service.get_user_by_username.return_value = None # Should not be called
    mock_verify_password.return_value = True # Assume password would be correct

    # Act
    authenticated_user = await auth_service.authenticate_user(login_identifier=test_email, password=test_password)

    # Assert
    mock_user_service.get_user_by_email.assert_called_once_with(email=test_email)
    mock_user_service.get_user_by_username.assert_not_called()
    mock_verify_password.assert_called_once_with(test_password, mock_user.hashed_password) # Password verified before active check
    assert authenticated_user is None
