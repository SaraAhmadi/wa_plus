from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .base_schema import BaseSchema, BaseSchemaRead
# from .reporting_unit import ReportingUnitSimple # For nested representation if needed
# from .indicator_definition import IndicatorDefinition # For nested representation if needed


class IndicatorTimeseriesBase(BaseSchema):
    reporting_unit_id: Optional[int] = None
    infrastructure_id: Optional[int] = None
    indicator_definition_id: int
    timestamp: datetime
    value_numeric: Optional[float] = None
    value_text: Optional[str] = Field(None, max_length=255)
    temporal_resolution_id: Optional[int] = None
    quality_flag_id: Optional[int] = None
    comments: Optional[str] = None


class IndicatorTimeseriesCreate(IndicatorTimeseriesBase):
    pass


class IndicatorTimeseriesUpdate(BaseSchema):
    # Usually time series data is immutable or replaced, not updated field by field.
    # If updates are needed, make fields optional.
    value_numeric: Optional[float] = None
    value_text: Optional[str] = Field(None, max_length=255)
    quality_flag_id: Optional[int] = None
    comments: Optional[str] = None


class IndicatorTimeseries(IndicatorTimeseriesBase, BaseSchemaRead):
    # Nested full objects can be large for lists; consider simpler representations if needed
    # reporting_unit: Optional[ReportingUnitSimple] = None
    # indicator_definition: Optional[IndicatorDefinition] = None
    # temporal_resolution_name: Optional[str] = None # Derived
    # quality_flag_name: Optional[str] = None # Derived
    pass


# For API requests that might bundle multiple timeseries points
class IndicatorTimeseriesBulkCreate(BaseModel):
    items: List[IndicatorTimeseriesCreate]


# Response for time series queries, often used in charts
class TimeseriesDataPoint(BaseModel):
    timestamp: datetime
    value: float # Or Any if value_text is also possible
    # Optionally include unit, indicator_code, reporting_unit_name if not clear from context
    unit: Optional[str] = None
