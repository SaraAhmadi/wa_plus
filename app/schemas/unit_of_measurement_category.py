from pydantic import BaseModel

# Base schema for UnitOfMeasurementCategory
class UnitOfMeasurementCategoryBase(BaseModel):
    name: str

# Schema for creating a UnitOfMeasurementCategory
# Inherits 'name' from Base
class UnitOfMeasurementCategoryCreate(UnitOfMeasurementCategoryBase):
    pass

# Schema for reading/returning a UnitOfMeasurementCategory
# Includes fields from Base plus 'id' and potentially others from the ORM model
class UnitOfMeasurementCategory(UnitOfMeasurementCategoryBase):
    id: int

    class Config:
        from_attributes = True
