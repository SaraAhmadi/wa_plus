from pydantic import Field
from typing import Optional, List
from datetime import datetime # Not directly in model, but good for context if needed
from .base_schema import BaseSchema, BaseSchemaRead
from .reporting_unit import ReportingUnitSimple # Simple version for nesting
from .crop import Crop as CropSchema # Read schema for Crop


class CroppingPatternBase(BaseSchema):
    reporting_unit_id: int
    crop_id: int
    time_period_year: int = Field(..., examples=[2023], description="Agricultural or calendar year")
    time_period_season: Optional[str] = Field(None, max_length=50, examples=["Kharif", "Rabi", "Annual"])
    data_type: str = Field(..., max_length=50, examples=["Actual", "Proposed/Planned", "Target"]) # Required

    area_cultivated_ha: Optional[float] = None
    area_proposed_ha: Optional[float] = None
    yield_actual_ton_ha: Optional[float] = None
    yield_proposed_ton_ha: Optional[float] = None
    water_allocation_mcm: Optional[float] = None
    water_consumed_actual_mcm: Optional[float] = None
    comments: Optional[str] = None
    # source_dataset_id: Optional[int] = None # If you add this to the model


class CroppingPatternCreate(CroppingPatternBase):
    pass


class CroppingPatternUpdate(BaseSchema): # All fields optional for PATCH
    reporting_unit_id: Optional[int] = None
    crop_id: Optional[int] = None
    time_period_year: Optional[int] = None
    time_period_season: Optional[str] = Field(None, max_length=50)
    data_type: Optional[str] = Field(None, max_length=50)

    area_cultivated_ha: Optional[float] = None
    area_proposed_ha: Optional[float] = None
    yield_actual_ton_ha: Optional[float] = None
    yield_proposed_ton_ha: Optional[float] = None
    water_allocation_mcm: Optional[float] = None
    water_consumed_actual_mcm: Optional[float] = None
    comments: Optional[str] = None
    # source_dataset_id: Optional[int] = None


class CroppingPattern(CroppingPatternBase, BaseSchemaRead):
    reporting_unit: Optional[ReportingUnitSimple] = None # Nested simple representation
    crop: Optional[CropSchema] = None # Nested full crop representation
