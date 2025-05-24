import pytest
from unittest.mock import AsyncMock, MagicMock, patch  # AsyncMock for async methods

from sqlalchemy.ext.asyncio import AsyncSession  # For type hinting

from app.services.user_service import UserService
from app.database.models.user import User as UserModel  # SQLAlchemy model
from app.database.models.role import Role as RoleModel  # SQLAlchemy model
from app.schemas.user import UserCreate, UserUpdate
from app.security.hashing import Hasher  # We'll mock its methods too


# pytestmark = pytest.mark.asyncio # Apply to all tests in this module

@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()  # Mock the execute method specifically
    # Mock nested calls like result.scalars().first()
    mock_scalar_result = MagicMock()
    mock_scalar_result.first = MagicMock()
    mock_scalar_result.all = MagicMock()
    mock_scalar_result.one_or_none = MagicMock()

    mock_execute_result = MagicMock()
    mock_execute_result.scalars = MagicMock(return_value=mock_scalar_result)
    mock_execute_result.scalar_one_or_none = MagicMock()  # For count

    session.execute.return_value = mock_execute_result
    return session


@pytest.fixture
def user_service(mock_db_session: AsyncMock) -> UserService:
    """Fixture to create a UserService instance with a mock session."""
    return UserService(db_session=mock_db_session)


@pytest.mark.asyncio
async def test_get_user_by_email_found(user_service: UserService, mock_db_session: AsyncMock):
    # Arrange
    test_email = "test@example.com"
    mock_user = UserModel(id=1, email=test_email, hashed_password="hashed_pw", is_active=True, roles=[])

    # Configure the mock for db_session.execute().scalars().first()
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_user

    # Act
    found_user = await user_service.get_user_by_email(email=test_email)

    # Assert
    mock_db_session.execute.assert_called_once()  # Check that execute was called
    # You could add more specific assertions about the SQL query if needed,
    # but for unit tests, checking the interaction pattern is often enough.
    assert found_user is not None
    assert found_user.email == test_email
    assert found_user == mock_user


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_service: UserService, mock_db_session: AsyncMock):
    # Arrange
    test_email = "nonexistent@example.com"
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None

    # Act
    found_user = await user_service.get_user_by_email(email=test_email)

    # Assert
    mock_db_session.execute.assert_called_once()
    assert found_user is None


@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.get_password_hash")  # Patch Hasher
async def test_create_user_success(
        mock_get_password_hash: MagicMock,
        user_service: UserService,
        mock_db_session: AsyncMock
):
    # Arrange
    mock_get_password_hash.return_value = "hashed_super_password"
    user_in_schema = UserCreate(
        email="newuser@example.com",
        password="password123",
        full_name="New User",
        role_ids=[]  # No roles for simplicity in this test
    )

    # Mock the refresh operation
    async def mock_refresh(obj, attribute_names=None):  # Simulate refresh
        return obj

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Act
    created_user = await user_service.create_user(user_in=user_in_schema)

    # Assert
    mock_get_password_hash.assert_called_once_with("password123")
    mock_db_session.add.assert_called_once()  # Check that db.add was called
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()

    added_user_arg = mock_db_session.add.call_args[0][0]  # Get the object passed to add
    assert isinstance(added_user_arg, UserModel)
    assert added_user_arg.email == user_in_schema.email
    assert added_user_arg.full_name == user_in_schema.full_name
    assert added_user_arg.hashed_password == "hashed_super_password"
    assert created_user.email == user_in_schema.email


@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.get_password_hash")
async def test_create_user_with_roles(
        mock_get_password_hash: MagicMock,
        user_service: UserService,
        mock_db_session: AsyncMock
):
    # Arrange
    mock_get_password_hash.return_value = "hashed_role_user_password"
    role_id_1, role_id_2 = 10, 11
    user_in_schema = UserCreate(
        email="roleuser@example.com",
        password="password123",
        role_ids=[role_id_1, role_id_2]
    )

    mock_role_1 = RoleModel(id=role_id_1, name="Editor")
    mock_role_2 = RoleModel(id=role_id_2, name="Viewer")

    # Configure mock for fetching roles
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_role_1, mock_role_2]

    async def mock_refresh_roles(obj, attribute_names=None):
        # Simulate that roles are populated after refresh if attribute_names=['roles']
        if attribute_names and 'roles' in attribute_names:
            # This is a simplification; real refresh would hit DB.
            # For the test, we ensure the created_user object has roles populated as expected.
            obj.roles = [mock_role_1, mock_role_2]
        return obj

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh_roles)

    # Act
    created_user = await user_service.create_user(user_in=user_in_schema)

    # Assert
    mock_db_session.add.assert_called_once()
    added_user_arg = mock_db_session.add.call_args[0][0]
    assert added_user_arg.email == user_in_schema.email

    # Check that the query for roles was made
    assert mock_db_session.execute.call_count == 1  # For select(Role)
    # More detailed assertion for the role query content might be needed if complex

    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(added_user_arg, attribute_names=['roles'])

    assert len(created_user.roles) == 2
    assert mock_role_1 in created_user.roles
    assert mock_role_2 in created_user.roles


@pytest.mark.asyncio
async def test_update_user_success(user_service: UserService, mock_db_session: AsyncMock):
    # Arrange
    existing_user = UserModel(id=1, email="old@example.com", hashed_password="old_pw", full_name="Old Name",
                              is_active=True, roles=[])
    user_update_schema = UserUpdate(full_name="New Name", email="new@example.com")

    async def mock_refresh(obj, attribute_names=None): return obj

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Act
    updated_user = await user_service.update_user(user=existing_user, user_in=user_update_schema)

    # Assert
    mock_db_session.add.assert_called_once_with(existing_user)  # Check the same object is added
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(existing_user, attribute_names=['roles'])

    assert updated_user.full_name == "New Name"
    assert updated_user.email == "new@example.com"
    assert updated_user.id == 1  # Ensure ID hasn't changed


@pytest.mark.asyncio
@patch("app.security.hashing.Hasher.get_password_hash")
async def test_update_user_password_change(
        mock_get_password_hash: MagicMock,
        user_service: UserService,
        mock_db_session: AsyncMock
):
    # Arrange
    mock_get_password_hash.return_value = "new_hashed_password"
    existing_user = UserModel(id=1, email="user@example.com", hashed_password="old_hashed_pw", roles=[])
    user_update_schema = UserUpdate(password="new_plain_password")

    async def mock_refresh(obj, attribute_names=None): return obj

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Act
    updated_user = await user_service.update_user(user=existing_user, user_in=user_update_schema)

    # Assert
    mock_get_password_hash.assert_called_once_with("new_plain_password")
    assert updated_user.hashed_password == "new_hashed_password"
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_user(user_service: UserService, mock_db_session: AsyncMock):
    # Arrange
    active_user = UserModel(id=1, email="active@example.com", is_active=True, roles=[])

    async def mock_refresh(obj): return obj  # Simplified refresh

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Act
    deactivated_user = await user_service.deactivate_user(user=active_user)

    # Assert
    mock_db_session.add.assert_called_once_with(active_user)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(active_user)
    assert deactivated_user.is_active is False


@pytest.mark.asyncio
async def test_get_multi_with_pagination(user_service: UserService, mock_db_session: AsyncMock):
    # Arrange
    mock_users = [UserModel(id=i, email=f"user{i}@example.com", roles=[]) for i in range(5)]
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_users

    # Act
    users = await user_service.get_multi_with_pagination(skip=0, limit=5)

    # Assert
    mock_db_session.execute.assert_called_once()
    assert len(users) == 5
    assert users == mock_users


@pytest.mark.asyncio
async def test_get_total_user_count(user_service: UserService, mock_db_session: AsyncMock):
    # Arrange
    # The count method in BaseService uses `scalar_one_or_none` or `scalar_one`
    # So we mock `session.execute().scalar_one_or_none()` or `scalar_one()`
    mock_db_session.execute.return_value.scalar_one.return_value = 25

    # Act
    count = await user_service.get_total_user_count()

    # Assert
    mock_db_session.execute.assert_called_once()
    assert count == 25
