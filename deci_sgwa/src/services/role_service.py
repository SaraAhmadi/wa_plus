from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.database.models.role import Role
from src.database.models.permission import Permission
from src.schemas.role import RoleCreate, RoleUpdate
from src.services.base_service import BaseService

class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Role)
        self.db_session = db_session

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        query = select(self.model).options(selectinload(Role.permissions)).where(self.model.name == name)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def create_role(self, role_in: RoleCreate) -> Optional[Role]:
        # It's generally better for the endpoint to check for existing role by name first
        # to provide a specific HTTP 409 Conflict if needed.
        # This service method will attempt creation and let database unique constraints handle conflicts if not pre-checked.

        role_data = role_in.dict(exclude={"permission_ids"})
        db_role = Role(**role_data)

        if role_in.permission_ids:
            permissions_query = select(Permission).where(Permission.id.in_(role_in.permission_ids))
            perm_result = await self.db_session.execute(permissions_query)
            permissions_to_assign = perm_result.scalars().all()
            if len(permissions_to_assign) != len(set(role_in.permission_ids)):
                # This indicates some permission IDs were not found, which could be an error.
                # Handle this appropriately, e.g., by raising an exception or logging.
                # For now, we'll assign only the ones found.
                pass
            db_role.permissions = permissions_to_assign
        else:
            db_role.permissions = []

        self.db_session.add(db_role)
        try:
            await self.db_session.commit()
            # Re-fetch to ensure all relationships, especially `permissions`, are correctly loaded for the response.
            # This avoids issues with Pydantic trying to access unloaded attributes.
            created_role_id = db_role.id
            return await self.get_role_by_id(role_id=created_role_id)
        except IntegrityError: # Catches unique constraint violations (e.g., role name)
            await self.db_session.rollback()
            # Optionally, log the error or raise a custom exception
            return None # Indicates creation failed due to conflict

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        query = select(self.model).options(selectinload(Role.permissions)).where(self.model.id == role_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def list_roles(self, offset: int = 0, limit: int = 100) -> List[Role]:
        query = (
            select(self.model)
            .options(selectinload(Role.permissions))
            .offset(offset)
            .limit(limit)
            .order_by(Role.id) # Use Role.id or Role.name for consistent ordering
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_total_role_count(self) -> int:
        return await super().count(self.db_session)

    async def update_role(self, role_id: int, role_in: RoleUpdate) -> Optional[Role]:
        db_role = await self.get_role_by_id(role_id) # This already loads permissions initially
        if not db_role:
            return None

        update_data = role_in.dict(exclude_unset=True, exclude={"permission_ids"})

        for field, value in update_data.items():
            if hasattr(db_role, field): # Make sure the attribute exists
                setattr(db_role, field, value)

        if role_in.permission_ids is not None:
            if role_in.permission_ids:
                permissions_query = select(Permission).where(Permission.id.in_(role_in.permission_ids))
                perm_result = await self.db_session.execute(permissions_query)
                permissions_to_assign = perm_result.scalars().all()
                if len(permissions_to_assign) != len(set(role_in.permission_ids)):
                    # Handle cases where some permission IDs might be invalid
                    pass
                db_role.permissions = permissions_to_assign
            else:
                db_role.permissions = []

        self.db_session.add(db_role)
        try:
            await self.db_session.commit()
            # Re-fetch to ensure all relationships are correctly loaded for the response.
            return await self.get_role_by_id(role_id)
        except IntegrityError: # Handles potential unique constraint violations if name is changed
            await self.db_session.rollback()
            return None # Indicates update failed

    async def delete_role(self, role_id: int) -> Optional[Role]:
        # Fetch the role with permissions loaded, so it can be returned if needed by the endpoint
        db_role = await self.get_role_by_id(role_id)
        if not db_role:
            return None

        await self.db_session.delete(db_role)
        await self.db_session.commit()
        # db_role is now detached but contains the state at deletion, including loaded permissions.
        return db_role
