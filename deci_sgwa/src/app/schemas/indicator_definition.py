from pydantic import BaseModel, Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead
from .unit_of_measurement import UnitOfMeasurement # Assuming schema exists
from .indicator_category import IndicatorCategory # Assuming schema exists


class IndicatorDefinitionBase(BaseSchema):
    code: str = Field(max_length=100)
    name_en: str = Field(max_length=255)
    name_local: Optional[str] = Field(None, max_length=255)
    description_en: Optional[str] = None
    description_local: Optional[str] = None
    data_type: str = Field(max_length=50)
    unit_of_measurement_id: Optional[int] = None
    category_id: Optional[int] = None
    wa_sheet_reference: Optional[str] = Field(None, max_length=50)
    is_spatial_raster: bool = False


class IndicatorDefinitionCreate(IndicatorDefinitionBase):
    pass


class IndicatorDefinitionUpdate(BaseSchema):
    code: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = Field(None, max_length=255)
    # ... other fields similarly optional
    unit_of_measurement_id: Optional[int] = None
    category_id: Optional[int] = None
    is_spatial_raster: Optional[bool] = None


class IndicatorDefinition(IndicatorDefinitionBase, BaseSchemaRead):
    unit_of_measurement: Optional[UnitOfMeasurement] = None
    category: Optional[IndicatorCategory] = None
