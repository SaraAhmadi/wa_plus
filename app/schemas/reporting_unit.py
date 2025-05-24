from pydantic import Field, BaseModel # BaseModel needed if not inheriting BaseSchema everywhere
from typing import Any, Optional, Dict, List # Added List
from .base_schema import BaseSchema, BaseSchemaRead # Ensure BaseSchema is correctly imported


# --- ReportingUnitType Schemas ---
class ReportingUnitTypeBase(BaseSchema):
    name: str = Field(max_length=100)
    description: Optional[str] = None


class ReportingUnitTypeCreate(ReportingUnitTypeBase):
    pass


class ReportingUnitTypeUpdate(ReportingUnitTypeBase): # Inherit BaseSchema or define model_config
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None # Ensure all fields from base are optional or have defaults


class ReportingUnitType(ReportingUnitTypeBase, BaseSchemaRead):
    pass # id, created_at, updated_at from BaseSchemaRead


# --- ReportingUnit Schemas ---
class ReportingUnitBase(BaseSchema):
    name: str = Field(max_length=255)
    code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    area_sqkm: Optional[float] = None
    unit_type_id: int
    parent_unit_id: Optional[int] = None
    # For GeoJSON, expect a dictionary structure. 'Any' can be used, or a more specific TypedDict/BaseModel.
    geom: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry object or WKT string")


class ReportingUnitCreate(ReportingUnitBase):
    pass # All fields from ReportingUnitBase are used for creation


class ReportingUnitUpdate(BaseSchema): # Does not inherit ReportingUnitBase to make all fields truly optional
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    area_sqkm: Optional[float] = None
    unit_type_id: Optional[int] = None
    parent_unit_id: Optional[int] = None
    geom: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry object or WKT string")


class ReportingUnit(ReportingUnitBase, BaseSchemaRead):
    unit_type: ReportingUnitType # Nested schema for reading


# For simpler list views without full geometry or deep nesting
class ReportingUnitSimple(BaseSchemaRead): # Inherits id, created_at, updated_at
    name: str
    code: Optional[str] = None
    # To include unit_type.name, you'd typically handle this in the service/API layer
    # or use a Pydantic V2 computed_field if unit_type object is always loaded.
    # For now, keeping it simple. If unit_type object is part of what's passed for ORM mode,
    # Pydantic can access it.
    unit_type: Optional[ReportingUnitTypeBase] = None # Or a simpler UnitType schema

# --- For model_rebuild if forward references are used extensively ---
# Ensure all schemas are defined before calling model_rebuild
# Example:
# User.model_rebuild()
# Role.model_rebuild()
# ReportingUnit.model_rebuild()
# ReportingUnitType.model_rebuild()
# This is usually done in schemas/__init__.py after all imports.
