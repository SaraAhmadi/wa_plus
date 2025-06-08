from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_active_user, UserModel # Standard dependencies
from app.schemas.unit_of_measurement_category import (
    UnitOfMeasurementCategory as UnitOfMeasurementCategorySchema, # Read Schema
    UnitOfMeasurementCategoryCreate as UnitOfMeasurementCategoryCreateSchema
)
from app.services import unit_of_measurement_category_service as uom_category_service
# from app.schemas.user import User as UserSchema # Replaced by UserModel

router = APIRouter(
    prefix="/categories",
    tags=["Unit of Measurement Categories"],
    # dependencies=[Depends(get_current_active_user)] # Uncomment if all routes need auth
)


@router.post(
    "/",
    response_model=UnitOfMeasurementCategorySchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_user)] # Example: require auth for creation
)
async def create_unit_of_measurement_category(
    category_in: UnitOfMeasurementCategoryCreateSchema,
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user) # Already in dependencies list for the route
):
    """
    Create a new unit of measurement category.
    """
    existing_category = await uom_category_service.get_category_by_name(db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A unit of measurement category with the name '{category_in.name}' already exists.",
        )

    created_category = await uom_category_service.create_category(db=db, category_in=category_in)
    if not created_category: # Should ideally not happen if previous check passed, but handles race or other issues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 400 if name constraint hit in DB
            detail="Failed to create unit of measurement category due to a conflict or server error.",
        )
    return created_category


@router.get("/list/", response_model=List[UnitOfMeasurementCategorySchema])
async def read_unit_of_measurement_categories(
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=200),
    # current_user: UserModel = Depends(get_current_active_user) # Optional: Add if listing needs auth
):
    """
    Retrieve a list of unit of measurement categories.
    """
    categories = await uom_category_service.get_categories(db=db, offset=offset, limit=limit)
    return categories


@router.get("/{category_id}", response_model=UnitOfMeasurementCategorySchema)
async def read_unit_of_measurement_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user) # Optional: Add if detail view needs auth
):
    """
    Retrieve a specific unit of measurement category by its ID.
    """
    category = await uom_category_service.get_category(db=db, category_id=category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit of measurement category with ID {category_id} not found.",
        )
    return category
