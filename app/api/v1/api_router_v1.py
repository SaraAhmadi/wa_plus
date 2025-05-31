# app/api/v1/api_router_v1.py
from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints.admin import users as admin_users
from app.api.v1.endpoints.admin import roles as admin_roles # UNCOMMENTED


api_router_v1 = APIRouter()

api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(admin_users.router, prefix="/admin") # This will make user routes /admin/users/...
api_router_v1.include_router(admin_roles.router, prefix="/admin/roles", tags=["Admin - Roles"]) # UNCOMMENTED, results in /admin/roles/...
