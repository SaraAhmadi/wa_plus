from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class DataQualityFlagBase(BaseSchema):
    name: str = Field(max_length=100, examples=["Measured", "Estimated", "Validated"])
    description: Optional[str] = None


class DataQualityFlagCreate(DataQualityFlagBase):
    pass


class DataQualityFlagUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class DataQualityFlag(DataQualityFlagBase, BaseSchemaRead):
    pass
