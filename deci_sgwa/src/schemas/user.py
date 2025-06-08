from pydantic import EmailStr, Field
from typing import Optional, List
from .base_schema import BaseSchema, BaseSchemaRead
from .role import Role # Forward reference if Role also refers to User


# Shared properties
class UserBase(BaseSchema):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(min_length=8)
    role_ids: Optional[List[int]] = Field(default_factory=list) # Use default_factory for mutable defaults


# Properties to receive via API on update
class UserUpdate(BaseSchema): # Not inheriting UserBase if email update has different rules or is pk
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8) # Allow None, but if string, min_length applies
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_ids: Optional[List[int]] = None


# Properties to return to client
class User(UserBase, BaseSchemaRead):
    username: Optional[str] = None
    roles: List[Role] = Field(default_factory=list)


# Properties stored in DB (not typically returned unless for specific internal use)
class UserInDBBase(UserBase): # Schema for what's in DB, used by service layer
    hashed_password: str


class UserInDB(UserInDBBase, BaseSchemaRead): # For ORM mapping from DB object
    roles: List[Role] = Field(default_factory=list)
