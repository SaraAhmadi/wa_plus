from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class TemporalResolutionBase(BaseSchema):
    name: str = Field(max_length=100, examples=["Daily", "Monthly", "Annual"])
    # description: Optional[str] = None # If you add description to the model


class TemporalResolutionCreate(TemporalResolutionBase):
    pass


class TemporalResolutionUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)
    # description: Optional[str] = None


class TemporalResolution(TemporalResolutionBase, BaseSchemaRead):
    pass
