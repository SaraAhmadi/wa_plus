from pydantic import Field
from typing import Optional, Dict, Any, List # Added List
from .base_schema import BaseSchema, BaseSchemaRead
from .reporting_unit import ReportingUnitSimple # Optional for nesting
from .infrastructure_type import InfrastructureType as InfrastructureTypeSchema
from .operational_status_type import OperationalStatusType as OperationalStatusTypeSchema
from .unit_of_measurement import UnitOfMeasurement as UnitOfMeasurementSchema # For capacity_unit

# Forward references might be needed if IndicatorTimeseries/FinancialAccount schemas refer back
# from .indicator_timeseries import IndicatorTimeseries
# from .financial_account import FinancialAccount


class InfrastructureBase(BaseSchema):
    name: str = Field(max_length=255)
    infrastructure_type_id: int
    reporting_unit_id: Optional[int] = None
    operational_status_id: Optional[int] = None
    geom: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry object or WKT string") # For GeoJSON
    capacity: Optional[float] = None
    capacity_unit_id: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Type-specific attributes as JSON")


class InfrastructureCreate(InfrastructureBase):
    pass


class InfrastructureUpdate(BaseSchema): # All fields optional
    name: Optional[str] = Field(None, max_length=255)
    infrastructure_type_id: Optional[int] = None
    reporting_unit_id: Optional[int] = None
    operational_status_id: Optional[int] = None
    geom: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry object or WKT string")
    capacity: Optional[float] = None
    capacity_unit_id: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None


class Infrastructure(InfrastructureBase, BaseSchemaRead):
    infrastructure_type: Optional[InfrastructureTypeSchema] = None
    reporting_unit: Optional[ReportingUnitSimple] = None # Using simple version
    operational_status: Optional[OperationalStatusTypeSchema] = None
    capacity_unit: Optional[UnitOfMeasurementSchema] = None

    # If you want to include related timeseries or financial accounts directly in this schema:
    # This can make responses very large. Often fetched separately.
    # indicator_timeseries: List[IndicatorTimeseries] = Field(default_factory=list)
    # financial_accounts: List[FinancialAccount] = Field(default_factory=list)


# Schema for simpler list views of infrastructure
class InfrastructureSimple(BaseSchemaRead):
    name: str
    infrastructure_type_name: Optional[str] = None # To be populated by service/endpoint
    reporting_unit_name: Optional[str] = None # To be populated
