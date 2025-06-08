from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update # Added delete and update

from src.database.models.base_model import Base as SQLAlchemyBaseModel # Alias to avoid name clash

# Define TypeVars for SQLAlchemy model and Pydantic schemas
ModelType = TypeVar("ModelType", bound=SQLAlchemyBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for CRUD operations on a SQLAlchemy model.
    """
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        :param model: A SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        """
        result = await db.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().all()

    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        """
        Get all records without pagination. Use with caution on large tables.
        """
        result = await db.execute(select(self.model))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        obj_in: Pydantic schema for creation.
        """
        # Pydantic v2: obj_in_data = obj_in.model_dump(exclude_unset=True)
        # Pydantic v1:
        obj_in_data = obj_in.dict(exclude_unset=True)

        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record.
        db_obj: The SQLAlchemy model instance to update.
        obj_in: Pydantic schema or dict with update data.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Pydantic v2: update_data = obj_in.model_dump(exclude_unset=True)
            # Pydantic v1:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        Remove a record by ID.
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj # Returns the deleted object or None if not found

    async def count(self, db: AsyncSession) -> int:
        """
        Count the total number of records.
        """
        # A more efficient way to count in SQLAlchemy
        from sqlalchemy import func
        count_query = select(func.count()).select_from(self.model)
        result = await db.execute(count_query)
        return result.scalar_one()
