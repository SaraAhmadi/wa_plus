# app/api/v1/endpoints/admin/roles.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List # Keep List for PaginatedResponse type hint
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_active_superuser
from app.schemas.role import Role as RoleSchema, RoleCreate, RoleUpdate
from app.schemas.base_schema import PaginatedResponse # For paginated list response
from app.services.role_service import RoleService # Import the new service

router = APIRouter(
    # prefix="/roles", # Prefix will be applied by main admin router
    tags=["Admin - Roles"],
    dependencies=[Depends(get_current_active_superuser)]
)

@router.post("/", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role_by_admin(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_db)
):
    role_service = RoleService(db)
    # Check for existing role by name to provide a specific 409 conflict
    existing_role = await role_service.get_role_by_name(name=role_in.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_in.name}' already exists.",
        )

    created_role = await role_service.create_role(role_in=role_in)
    if not created_role: # Should be caught by name check or DB integrity from service
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 400 if specific input issue not caught by Pydantic
            detail="Failed to create role due to an unexpected error or data conflict.",
        )
    return created_role

@router.get("/", response_model=PaginatedResponse[RoleSchema])
async def read_roles_by_admin(
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=200)
):
    role_service = RoleService(db)
    total_roles = await role_service.get_total_role_count()
    roles_list = await role_service.list_roles(offset=offset, limit=limit)

    return PaginatedResponse[RoleSchema](
        total=total_roles,
        page=(offset // limit) + 1 if limit > 0 else 1,
        size=len(roles_list),
        pages=(total_roles + limit - 1) // limit if limit > 0 else (1 if total_roles > 0 else 0),
        items=roles_list
    )

@router.get("/{role_id}", response_model=RoleSchema)
async def read_role_by_admin(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    role_service = RoleService(db)
    role = await role_service.get_role_by_id(role_id=role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found.",
        )
    return role

@router.put("/{role_id}", response_model=RoleSchema)
async def update_role_by_admin(
    role_id: int,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_db)
):
    role_service = RoleService(db)
    # Check if role exists before attempting update
    existing_role_check = await role_service.get_role_by_id(role_id=role_id)
    if not existing_role_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found.",
        )

    # Check for name conflict if name is being changed
    if role_in.name and role_in.name != existing_role_check.name:
        conflicting_role = await role_service.get_role_by_name(name=role_in.name)
        if conflicting_role and conflicting_role.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another role with name '{role_in.name}' already exists.",
            )

    updated_role = await role_service.update_role(role_id=role_id, role_in=role_in)
    if not updated_role: # Should be caught by existence check or DB integrity from service
        # This could happen if update_role returns None due to IntegrityError during commit
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 400/409 depending on cause
            detail=f"Failed to update role with ID {role_id}.",
        )
    return updated_role

@router.delete("/{role_id}", response_model=RoleSchema) # Or use status_code=204 and no response_model
async def delete_role_by_admin(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    role_service = RoleService(db)
    # Fetch role first to see if it exists
    role_to_delete = await role_service.get_role_by_id(role_id=role_id)
    if role_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found.",
        )

    deleted_role = await role_service.delete_role(role_id=role_id)
    # The service's delete_role method returns the object that was deleted (or None if it failed somehow after re-fetch)
    # If the service's delete_role now simply returns the object passed to db.delete(obj),
    # then deleted_role will be the object that was deleted.
    # For consistency, the service was designed to return the object state at deletion.
    if deleted_role is None: # Should not happen if role_to_delete was found
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role with ID {role_id} after it was found.",
        )
    return deleted_role
