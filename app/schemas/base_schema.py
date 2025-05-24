from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any, List, TypeVar, Generic # Added TypeVar and Generic

# Define a TypeVar for the items in the paginated response
ItemType = TypeVar('ItemType')


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')


class BaseSchemaRead(BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime


# For pagination responses, now make it Generic
class PaginatedResponse(BaseModel, Generic[ItemType]): # Inherit from Generic[ItemType]
    total: int
    page: int
    size: int
    pages: int
    items: List[ItemType] # Use the TypeVar here
    # model_config = ConfigDict(from_attributes=True) # Usually not needed if ItemType are Pydantic models
