from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError # To handle potential unique constraint violations

from app.database.models.unit_of_measurement_category import UnitOfMeasurementCategory as UnitOfMeasurementCategoryModel
from app.schemas.unit_of_measurement_category import UnitOfMeasurementCategoryCreate as UnitOfMeasurementCategoryCreateSchema
# Using aliased imports for clarity between model and schema if names were identical


async def create_category(
    db: AsyncSession, category_in: UnitOfMeasurementCategoryCreateSchema
) -> Optional[UnitOfMeasurementCategoryModel]:
    """
    Create a new unit of measurement category.
    Returns the created category model, or None if a category with the same name already exists.
    """
    # Check if category with the same name already exists (case-sensitive)
    # For a case-insensitive check, you might need to use func.lower or similar
    existing_category_query = select(UnitOfMeasurementCategoryModel).where(
        UnitOfMeasurementCategoryModel.name == category_in.name
    )
    result = await db.execute(existing_category_query)
    if result.scalars().first():
        # Optionally, raise an HTTPException here or let the endpoint handle it
        return None # Or raise an error indicating duplication

    db_category = UnitOfMeasurementCategoryModel(**category_in.model_dump()) # Pydantic v2
    # For Pydantic v1: db_category = UnitOfMeasurementCategoryModel(**category_in.dict())

    db.add(db_category)
    try:
        await db.commit()
        await db.refresh(db_category)
        return db_category
    except IntegrityError: # Handles race conditions if another request created the same name concurrently
        await db.rollback()
        # Query again to be sure, or just return None/raise
        result = await db.execute(existing_category_query) # Re-check
        return result.scalars().first() # Could be None if rollback was for other IntegrityError


async def get_category(
    db: AsyncSession, category_id: int
) -> Optional[UnitOfMeasurementCategoryModel]:
    """
    Get a unit of measurement category by its ID.
    """
    query = select(UnitOfMeasurementCategoryModel).where(UnitOfMeasurementCategoryModel.id == category_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_categories(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[UnitOfMeasurementCategoryModel]:
    """
    Get a list of unit of measurement categories with pagination.
    """
    query = select(UnitOfMeasurementCategoryModel).offset(skip).limit(limit).order_by(UnitOfMeasurementCategoryModel.id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_category_by_name(
    db: AsyncSession, name: str
) -> Optional[UnitOfMeasurementCategoryModel]:
    """
    Get a unit of measurement category by its name.
    Helpful for checking existence before creation if needed by endpoint.
    """
    query = select(UnitOfMeasurementCategoryModel).where(UnitOfMeasurementCategoryModel.name == name)
    result = await db.execute(query)
    return result.scalars().first()


