from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead
<<<<<<< HEAD
=======
from .unit_of_measurement_category import UnitOfMeasurementCategory
>>>>>>> origin/main


# Shared properties for UnitOfMeasurement
class UnitOfMeasurementBase(BaseSchema):
    name: str = Field(max_length=100, examples=["Millimeter", "Cubic meter per second"])
    abbreviation: str = Field(max_length=20, examples=["mm", "m³/s"])
    description: Optional[str] = None
<<<<<<< HEAD
=======
    category_id: Optional[int] = Field(None, description="ID of the category this unit belongs to")
>>>>>>> origin/main


# Properties to receive via API on creation
class UnitOfMeasurementCreate(UnitOfMeasurementBase):
    pass


# Properties to receive via API on update
class UnitOfMeasurementUpdate(BaseSchema): # Not inheriting Base to make all fields optional
    name: Optional[str] = Field(None, max_length=100)
    abbreviation: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None


# Properties to return to client
class UnitOfMeasurement(UnitOfMeasurementBase, BaseSchemaRead):
<<<<<<< HEAD
    pass # id, created_at, updated_at inherited from BaseSchemaRead
=======
    category: Optional[UnitOfMeasurementCategory] = None # Nested category information

    class Config: # Ensure from_attributes is enabled for ORM to Pydantic conversion
        from_attributes = True


# Ensure forward references are resolved.
# This is often done in __init__.py but can be here if specific to this model's complexity.
UnitOfMeasurement.model_rebuild(force=True)
>>>>>>> origin/main
