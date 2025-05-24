from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class InfrastructureTypeBase(BaseSchema):
    name: str = Field(max_length=100, examples=["Dam", "Pumping Station", "Main Canal"])


class InfrastructureTypeCreate(InfrastructureTypeBase):
    pass


class InfrastructureTypeUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)


class InfrastructureType(InfrastructureTypeBase, BaseSchemaRead):
    pass
