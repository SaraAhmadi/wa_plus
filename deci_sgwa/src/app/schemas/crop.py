from pydantic import Field
from typing import Optional, Dict, Any
from .base_schema import BaseSchema, BaseSchemaRead


class CropBase(BaseSchema):
    code: str = Field(max_length=50, examples=["WHT", "MAZ_GRN"])
    name_en: str = Field(max_length=100, examples=["Wheat", "Maize (Grain)"])
    name_local: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100, examples=["Cereal", "Fodder"])
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CropCreate(CropBase):
    pass


class CropUpdate(BaseSchema):
    code: Optional[str] = Field(None, max_length=50)
    name_en: Optional[str] = Field(None, max_length=100)
    name_local: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    attributes: Optional[Dict[str, Any]] = None


class Crop(CropBase, BaseSchemaRead):
    pass
