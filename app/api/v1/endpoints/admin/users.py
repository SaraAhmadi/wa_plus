from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_active_superuser
# from app.dependencies.rbac import CheckPermissions # Example if using permission strings
from app.database.models.user import User as UserModel  # SQLAlchemy model
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.schemas.base_schema import PaginatedResponse  # For paginated list response
from app.services.user_service import UserService

# All routes in this router will require the user to be an active superuser
# This can be done by adding `dependencies=[Depends(get_current_active_superuser)]` to the APIRouter
# or to individual routes. Adding to the router is cleaner for a whole admin module.
router = APIRouter(
    prefix="/users",
    tags=["Admin - Users"],
    dependencies=[Depends(get_current_active_superuser)]
)


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
        *,
        db: AsyncSession = Depends(get_db),
        user_in: UserCreate
        # current_superuser: UserModel = Depends(get_current_active_superuser) # Implicitly handled by router dependency
) -> UserModel:  # Return SQLAlchemy model, FastAPI converts to UserSchema
    """
    Create new user by an admin.
    Corresponds to SSR 8.5.6 POST /api/v1/admin/users
    """
    user_service = UserService(db)
    existing_user = await user_service.get_user_by_email(email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = await user_service.create_user(user_in=user_in)
    return user


@router.get("/", response_model=PaginatedResponse[UserSchema])
async def read_users_by_admin(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, description="Number of records to skip for pagination", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=200)
) -> PaginatedResponse[UserSchema]:
    """
    Retrieve users with pagination.
    Corresponds to SSR 8.5.6 GET /api/v1/admin/users
    """
    user_service = UserService(db)
    total_users = await user_service.get_total_user_count()
    users_list = await user_service.get_multi_with_pagination(skip=skip, limit=limit)

    return PaginatedResponse[UserSchema](
        total=total_users,
        page=(skip // limit) + 1 if limit > 0 else 1, # Ensure page is at least 1
        size=len(users_list),
        pages=(total_users + limit - 1) // limit if limit > 0 else (1 if total_users > 0 else 0), # Handle limit=0 or total_users=0
        items=users_list
    )


@router.get("/{user_id}", response_model=UserSchema)
async def read_user_by_admin(
        user_id: int,
        db: AsyncSession = Depends(get_db)
        # current_superuser: UserModel = Depends(get_current_active_superuser) # Implicit
) -> UserModel:
    """
    Get a specific user by ID.
    """
    user_service = UserService(db)
    # Fetch with relations for a complete view if needed by the response schema
    user = await user_service.get_user_by_id_with_relations(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user_by_admin(
        user_id: int,
        *,
        db: AsyncSession = Depends(get_db),
        user_in: UserUpdate
        # current_superuser: UserModel = Depends(get_current_active_superuser) # Implicit
) -> UserModel:
    """
    Update a user.
    Corresponds to SSR 8.5.6 PUT /api/v1/admin/users/{user_id}
    """
    user_service = UserService(db)
    user = await user_service.get(db, id=user_id)  # Get the existing user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    # Check for email conflict if email is being changed
    if user_in.email and user_in.email != user.email:
        existing_user_with_new_email = await user_service.get_user_by_email(email=user_in.email)
        if existing_user_with_new_email and existing_user_with_new_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

    updated_user = await user_service.update_user(user=user, user_in=user_in)
    return updated_user


@router.delete("/{user_id}", response_model=UserSchema)  # Or status_code=204 if no content
async def delete_user_by_admin(
        user_id: int,
        db: AsyncSession = Depends(get_db)
        # current_superuser: UserModel = Depends(get_current_active_superuser) # Implicit
) -> UserModel:  # Returning the "deleted" user (often just marked inactive)
    """
    Deactivate or "delete" a user (soft delete preferred).
    Corresponds to SSR 8.5.6 DELETE /api/v1/admin/users/{user_id}
    This example deactivates the user. True deletion would use user_service.remove().
    """
    user_service = UserService(db)
    user = await user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already inactive.",
        )
    # For a soft delete (deactivation):
    deactivated_user = await user_service.deactivate_user(user=user)
    return deactivated_user

    # For a hard delete:
    # deleted_user = await user_service.remove(db, id=user_id)
    # if not deleted_user: # Should not happen if already fetched, but good check
    #     raise HTTPException(status_code=404, detail="User not found for deletion")
    # return Response(status_code=status.HTTP_204_NO_CONTENT) # For hard delete
