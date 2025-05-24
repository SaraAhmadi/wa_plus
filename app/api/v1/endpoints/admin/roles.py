# app/api/v1/endpoints/admin/roles.py (Minimal Example)
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_active_superuser
from app.schemas.role import Role as RoleSchema, RoleCreate, RoleUpdate
# from app.services.role_service import RoleService # You would create this service


router = APIRouter(
    # prefix="/roles", # Prefix will be applied when including in api_router_v1
    tags=["Admin - Roles"],
    dependencies=[Depends(get_current_active_superuser)]
)


@router.post("/", response_model=RoleSchema, status_code=201)
async def create_role_by_admin(role_in: RoleCreate, db: AsyncSession = Depends(get_db)):
    # role_service = RoleService(db)
    # role = await role_service.create_role(role_in=role_in)
    # return role
    raise HTTPException(status_code=501, detail="Create role not implemented yet")


@router.get("/", response_model=List[RoleSchema])
async def read_roles_by_admin(db: AsyncSession = Depends(get_db)):
    # role_service = RoleService(db)
    # roles = await role_service.get_all_roles()
    # return roles
    raise HTTPException(status_code=501, detail="Read roles not implemented yet")

# ... Add GET by ID, PUT, DELETE for roles ...
