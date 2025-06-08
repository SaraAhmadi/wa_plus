from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class IndicatorCategoryBase(BaseSchema):
    name_en: str = Field(max_length=100, examples=["Climate Data", "Water Consumption"])
    name_local: Optional[str] = Field(None, max_length=100)
    # description: Optional[str] = None # If you add description to model


class IndicatorCategoryCreate(IndicatorCategoryBase):
    pass


class IndicatorCategoryUpdate(BaseSchema):
    name_en: Optional[str] = Field(None, max_length=100)
    name_local: Optional[str] = Field(None, max_length=100)
    # description: Optional[str] = None


class IndicatorCategory(IndicatorCategoryBase, BaseSchemaRead):
    pass
