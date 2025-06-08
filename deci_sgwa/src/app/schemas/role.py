from pydantic import Field
from typing import Optional, List
from .base_schema import BaseSchema, BaseSchemaRead
from .permission import Permission # Forward reference if Permission also refers to Role


# Shared properties
class RoleBase(BaseSchema):
    name: str = Field(min_length=2, max_length=100) # Min length usually > 1
    description: Optional[str] = None


# Properties to receive via API on creation
class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = Field(default_factory=list)


# Properties to receive via API on update
class RoleUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


# Properties to return to client
class Role(RoleBase, BaseSchemaRead):
    permissions: List[Permission] = Field(default_factory=list)
