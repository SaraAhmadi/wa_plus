from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class FinancialAccountTypeBase(BaseSchema):
    name: str = Field(max_length=255, examples=["Revenue - Agricultural Water Sales", "Operational Cost - Energy"])
    is_cost: bool = Field(..., description="True if this account type represents a cost, False if it's revenue/income")
    category: Optional[str] = Field(None, max_length=100, examples=["Operational", "Capital", "Revenue"])


class FinancialAccountTypeCreate(FinancialAccountTypeBase):
    pass


class FinancialAccountTypeUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    is_cost: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)


class FinancialAccountType(FinancialAccountTypeBase, BaseSchemaRead):
    pass
