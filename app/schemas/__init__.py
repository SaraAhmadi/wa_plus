from .base_schema import BaseSchema, BaseSchemaRead, PaginatedResponse
from .token import Token, TokenData
from .user import User, UserCreate, UserUpdate, UserInDB # Assuming UserInDB is also defined
from .role import Role, RoleCreate, RoleUpdate
from .permission import Permission, PermissionCreate, PermissionUpdate

from .reporting_unit import (
    ReportingUnit, ReportingUnitCreate, ReportingUnitUpdate, ReportingUnitSimple,
    ReportingUnitType, ReportingUnitTypeCreate, ReportingUnitTypeUpdate
)
# Assuming these files now exist and define the specified schemas:
from .unit_of_measurement import UnitOfMeasurement, UnitOfMeasurementCreate, UnitOfMeasurementUpdate
from .unit_of_measurement_category import UnitOfMeasurementCategory, UnitOfMeasurementCategoryCreate, UnitOfMeasurementCategoryBase # New import
from .temporal_resolution import TemporalResolution, TemporalResolutionCreate, TemporalResolutionUpdate
from .data_quality_flag import DataQualityFlag, DataQualityFlagCreate, DataQualityFlagUpdate
from .indicator_category import IndicatorCategory, IndicatorCategoryCreate, IndicatorCategoryUpdate
from .indicator_definition import IndicatorDefinition, IndicatorDefinitionCreate, IndicatorDefinitionUpdate
from .indicator_timeseries import (IndicatorTimeseries, IndicatorTimeseriesCreate, IndicatorTimeseriesUpdate,
                                   TimeseriesDataPoint, IndicatorTimeseriesBulkCreate)

# CRUD schemas for RasterMetadata SQLAlchemy model
from .raster_metadata import RasterMetadata as RasterMetadataSchema
from .raster_metadata import RasterMetadataCreate as RasterMetadataCreateSchema
from .raster_metadata import RasterMetadataUpdate as RasterMetadataUpdateSchema

# DTO for map layer metadata API response
from .map_layer import MapLayerMetadata

from .crop import Crop as CropSchema, CropCreate, CropUpdate
from .cropping_pattern import CroppingPattern as CroppingPatternSchema, CroppingPatternCreate, CroppingPatternUpdate

from .infrastructure import Infrastructure as InfrastructureSchema, InfrastructureCreate, InfrastructureUpdate
from .infrastructure_type import (InfrastructureType as InfrastructureTypeSchema, InfrastructureTypeCreate,
                                  InfrastructureTypeUpdate)
from .operational_status_type import (OperationalStatusType as OperationalStatusTypeSchema, OperationalStatusTypeCreate,
                                      OperationalStatusTypeUpdate)

from .currency import Currency as CurrencySchema, CurrencyCreate, CurrencyUpdate
from .financial_account_type import (FinancialAccountType as FinancialAccountTypeSchema, FinancialAccountTypeCreate,
                                     FinancialAccountTypeUpdate)
from .financial_account import (FinancialAccount as FinancialAccountSchema, FinancialAccountCreate,
                                FinancialAccountUpdate)

# --- Resolve Forward References and Finalize Schema Definitions ---
# For Pydantic V2, model_rebuild() is used to update forward references
# and finalize model shapes. Call this for any schema that uses string
# type hints for forward references or has complex nested Pydantic models
# that depend on other schemas defined later in the import order.

# It's generally a good practice to call it on your main "Read" schemas
# that might have such dependencies.

User.model_rebuild(force=True) # Add force=True if you encounter issues with repeated calls or complex scenarios
Role.model_rebuild(force=True)
Permission.model_rebuild(force=True)

ReportingUnit.model_rebuild(force=True)
ReportingUnitType.model_rebuild(force=True) # Usually simple, but good practice
UnitOfMeasurement.model_rebuild(force=True)
UnitOfMeasurementCategory.model_rebuild(force=True) # New model_rebuild
TemporalResolution.model_rebuild(force=True)
DataQualityFlag.model_rebuild(force=True)
IndicatorCategory.model_rebuild(force=True)
IndicatorDefinition.model_rebuild(force=True)
IndicatorTimeseries.model_rebuild(force=True) # If it nests complex types

RasterMetadataSchema.model_rebuild(force=True) # For the CRUD schema
MapLayerMetadata.model_rebuild(force=True) # Though likely simple, doesn't hurt

CropSchema.model_rebuild(force=True)
CroppingPatternSchema.model_rebuild(force=True)

InfrastructureSchema.model_rebuild(force=True)
InfrastructureTypeSchema.model_rebuild(force=True)
OperationalStatusTypeSchema.model_rebuild(force=True)

CurrencySchema.model_rebuild(force=True)
FinancialAccountTypeSchema.model_rebuild(force=True)
FinancialAccountSchema.model_rebuild(force=True)


# --- __all__ definition for explicit exports (Optional but good practice) ---
__all__ = [
    "BaseSchema", "BaseSchemaRead", "PaginatedResponse",
    "Token", "TokenData",
    "User", "UserCreate", "UserUpdate", "UserInDB",
    "Role", "RoleCreate", "RoleUpdate",
    "Permission", "PermissionCreate", "PermissionUpdate",
    "ReportingUnit", "ReportingUnitCreate", "ReportingUnitUpdate", "ReportingUnitSimple",
    "ReportingUnitType", "ReportingUnitTypeCreate", "ReportingUnitTypeUpdate",
    "UnitOfMeasurement", "UnitOfMeasurementCreate", "UnitOfMeasurementUpdate",
    "UnitOfMeasurementCategoryBase", "UnitOfMeasurementCategoryCreate", "UnitOfMeasurementCategory", # New schemas in __all__
    "TemporalResolution", "TemporalResolutionCreate", "TemporalResolutionUpdate",
    "DataQualityFlag", "DataQualityFlagCreate", "DataQualityFlagUpdate",
    "IndicatorCategory", "IndicatorCategoryCreate", "IndicatorCategoryUpdate",
    "IndicatorDefinition", "IndicatorDefinitionCreate", "IndicatorDefinitionUpdate",
    "IndicatorTimeseries", "IndicatorTimeseriesCreate", "IndicatorTimeseriesUpdate",
    "TimeseriesDataPoint", "IndicatorTimeseriesBulkCreate",
    "RasterMetadataSchema", "RasterMetadataCreateSchema", "RasterMetadataUpdateSchema",
    "MapLayerMetadata",
    "CropSchema", "CropCreate", "CropUpdate",
    "CroppingPatternSchema", "CroppingPatternCreate", "CroppingPatternUpdate",
    "InfrastructureSchema", "InfrastructureCreate", "InfrastructureUpdate",
    "InfrastructureTypeSchema", "InfrastructureTypeCreate", "InfrastructureTypeUpdate",
    "OperationalStatusTypeSchema", "OperationalStatusTypeCreate", "OperationalStatusTypeUpdate",
    "CurrencySchema", "CurrencyCreate", "CurrencyUpdate",
    "FinancialAccountTypeSchema", "FinancialAccountTypeCreate", "FinancialAccountTypeUpdate",
    "FinancialAccountSchema", "FinancialAccountCreate", "FinancialAccountUpdate",
]