from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # For eager loading roles/permissions

from app.database.models.user import User
from app.database.models.role import Role # Import Role for type hinting and operations
from app.schemas.user import UserCreate, UserUpdate
from app.security.hashing import Hasher
from .base_service import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(User)
        self.db_session = db_session # Store session for methods not in BaseService

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address.
        Includes eager loading of roles and their permissions.
        """
        query = (
            select(self.model)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
            .where(self.model.email == email)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by their username.
        Includes eager loading of roles and their permissions.
        """
        query = (
            select(self.model)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
            .where(self.model.username == username)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_user_by_id_with_relations(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID, including roles and permissions.
        """
        query = (
            select(self.model)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
            .where(self.model.id == user_id)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def create_user(self, user_in: UserCreate) -> User:
        """
        Create a new user, hash their password, and assign roles.
        """
        # Pydantic v2: create_data = user_in.model_dump(exclude={"password", "role_ids"})
        # Pydantic v1:
        create_data = user_in.dict(exclude={"password", "role_ids"})

        hashed_password = Hasher.get_password_hash(user_in.password)
        db_user = User(**create_data, hashed_password=hashed_password)

        if user_in.role_ids:
            # Fetch Role objects for the given IDs
            roles_query = select(Role).where(Role.id.in_(user_in.role_ids))
            result = await self.db_session.execute(roles_query)
            roles_to_assign = result.scalars().all()
            db_user.roles = roles_to_assign
        else:
            db_user.roles = [] # Ensure it's an empty list if no roles

        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user, attribute_names=['roles']) # Refresh to get roles populated
        return db_user

    async def update_user(self, user: User, user_in: UserUpdate) -> User:
        """
        Update an existing user, potentially including password and roles.
        """
        # Pydantic v2: update_data = user_in.model_dump(exclude_unset=True, exclude={"password", "role_ids"})
        # Pydantic v1:
        update_data = user_in.dict(exclude_unset=True, exclude={"password", "role_ids"})

        for field, value in update_data.items():
            setattr(user, field, value)

        if user_in.password:
            user.hashed_password = Hasher.get_password_hash(user_in.password)

        if user_in.role_ids is not None: # Allow setting roles to empty list
            if user_in.role_ids:
                roles_query = select(Role).where(Role.id.in_(user_in.role_ids))
                result = await self.db_session.execute(roles_query)
                roles_to_assign = result.scalars().all()
                user.roles = roles_to_assign
            else:
                user.roles = [] # Clear existing roles

        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user, attribute_names=['roles'])
        return user

    async def activate_user(self, user: User) -> User:
        user.is_active = True
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def deactivate_user(self, user: User) -> User:
        user.is_active = False
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    # This method is specific to UserService and doesn't fit BaseService
    async def get_multi_with_pagination(
        self, offset: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Get multiple users with pagination, eagerly loading roles and their permissions.
        """
        query = (
            select(self.model)
            .options(selectinload(User.roles).selectinload(Role.permissions)) # Eagerly load roles and their permissions
            .offset(offset)

            .limit(limit)
            .order_by(User.id) # Consistent ordering for pagination
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_total_user_count(self) -> int:
        """
        Get the total count of users.
        """
        return await super().count(self.db_session)

# Example of how a service might be instantiated and used (e.g., in an endpoint)
# async def example_usage(db: AsyncSession = Depends(get_db)):
#     user_service = UserService(db)
#     user = await user_service.get_user_by_email("test@example.com")
#     # ...
