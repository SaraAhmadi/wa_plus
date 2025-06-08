from pydantic import BaseModel, Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


# Shared properties
class PermissionBase(BaseSchema):
    name: str = Field(min_length=3, max_length=100) # e.g., "users:create", "data:read_basin_alpha"
    description: Optional[str] = None


# Properties to receive via API on creation
class PermissionCreate(PermissionBase):
    pass


# Properties to receive via API on update
class PermissionUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None


# Properties to return to client
class Permission(PermissionBase, BaseSchemaRead):
    pass
