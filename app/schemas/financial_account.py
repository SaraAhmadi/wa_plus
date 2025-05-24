from pydantic import Field, AwareDatetime
from typing import Optional, List
from datetime import date, datetime  # Added datetime
from decimal import Decimal  # For precise monetary values

from .base_schema import BaseSchema, BaseSchemaRead
# Import related schemas for nesting in the Read model
from .reporting_unit import ReportingUnitSimple  # Simple version
from .infrastructure import InfrastructureSimple  # Simple version
from .financial_account_type import FinancialAccountType as FinancialAccountTypeSchema
from .crop import Crop as CropSchema
from .currency import Currency as CurrencySchema


class FinancialAccountBase(BaseSchema):
    reporting_unit_id: Optional[int] = None
    infrastructure_id: Optional[int] = None
    financial_account_type_id: int
    crop_id: Optional[int] = None

    transaction_date: date = Field(..., examples=["2023-10-27"],
                                   description="Date of the financial transaction or accounting period end")
    amount: Decimal = Field(..., max_digits=18, decimal_places=2, description="Monetary value")
    currency_id: int
    description: Optional[str] = None
    source_document_ref: Optional[str] = Field(None, max_length=255)


class FinancialAccountCreate(FinancialAccountBase):
    pass


class FinancialAccountUpdate(BaseSchema):  # All fields optional for PATCH
    reporting_unit_id: Optional[int] = None
    infrastructure_id: Optional[int] = None
    financial_account_type_id: Optional[int] = None
    crop_id: Optional[int] = None

    transaction_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, max_digits=18, decimal_places=2)
    currency_id: Optional[int] = None
    description: Optional[str] = None
    source_document_ref: Optional[str] = Field(None, max_length=255)


class FinancialAccount(FinancialAccountBase, BaseSchemaRead):
    # Nested representations for related objects
    reporting_unit: Optional[ReportingUnitSimple] = None
    infrastructure: Optional[InfrastructureSimple] = None
    account_type: Optional[FinancialAccountTypeSchema] = None  # Renamed from financial_account_type
    crop: Optional[CropSchema] = None
    currency: Optional[CurrencySchema] = None

    # Pydantic v2 Config for AwareDatetime if not handled globally
    # model_config = ConfigDict(arbitrary_types_allowed=True)
