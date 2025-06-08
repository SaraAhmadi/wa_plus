from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class OperationalStatusTypeBase(BaseSchema):
    name: str = Field(max_length=100, examples=["Operational", "Under Maintenance", "Decommissioned"])


class OperationalStatusTypeCreate(OperationalStatusTypeBase):
    pass


class OperationalStatusTypeUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)


class OperationalStatusType(OperationalStatusTypeBase, BaseSchemaRead):
    pass
