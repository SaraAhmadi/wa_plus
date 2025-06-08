from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_active_user, UserModel # Assuming metadata might be protected
from app.services.data_service import DataService
from app.schemas.reporting_unit import ReportingUnit as ReportingUnitSchema, ReportingUnitType as ReportingUnitTypeSchema
from app.schemas.indicator_definition import IndicatorDefinition as IndicatorDefinitionSchema
from app.schemas.indicator_category import IndicatorCategory as IndicatorCategorySchema
from app.schemas.unit_of_measurement import UnitOfMeasurement as UnitOfMeasurementSchema
from app.schemas.temporal_resolution import TemporalResolution as TemporalResolutionSchema # Assuming you created this schema
from app.schemas.data_quality_flag import DataQualityFlag as DataQualityFlagSchema # Assuming you created this schema
# from app.schemas.user import User as UserSchema # Replaced by UserModel
from app.schemas.infrastructure_type import InfrastructureType as InfrastructureTypeSchema
from app.schemas.crop import Crop as CropSchema # For listing crop types


router = APIRouter()


# --- Geographic Units & Types ---
@router.get("/geographic-units", response_model=List[ReportingUnitSchema])
async def get_geographic_units_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user), # Auth if needed
    unit_type_id: Optional[int] = Query(None, description="Filter by reporting unit type ID"),
    parent_unit_id: Optional[int] = Query(None, description="Filter by parent unit ID to get children"),
    search: Optional[str] = Query(None, description="Search term for unit name"),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Retrieve a list of available geographic/reporting units.
    (Previously in data_exploration.py, aligns with SSR 8.5.1 GET /api/v1/geographic_units)
    """
    data_service = DataService(db)
    units = await data_service.get_reporting_units(
        unit_type_id=unit_type_id,
        parent_unit_id=parent_unit_id,
        search_term=search,
        offset=offset,
        limit=limit
    )
    return units


@router.get("/geographic-units/{unit_id}", response_model=ReportingUnitSchema)
async def get_geographic_unit_by_id_catalog(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user), # Auth if needed
):
    """
    Retrieve a specific geographic/reporting unit by its ID.
    """
    data_service = DataService(db)
    unit = await data_service.get_reporting_unit_by_id(unit_id=unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geographic unit not found")
    return unit


@router.get("/geographic-unit-types", response_model=List[ReportingUnitTypeSchema])
async def get_geographic_unit_types_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user), # Auth if needed
):
    """
    Retrieve a list of available geographic/reporting unit types.
    """
    data_service = DataService(db)
    unit_types = await data_service.get_reporting_unit_types()
    return unit_types


# --- Indicator Definitions & Lookups ---
@router.get("/indicators", response_model=List[IndicatorDefinitionSchema])
async def get_indicators_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user), # Auth if needed
    category_id: Optional[int] = Query(None, description="Filter by indicator category ID"),
    data_type: Optional[str] = Query(None, description="Filter by data type (e.g., 'time-series', 'spatial_raster')"),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Retrieve a list of available WA+ indicator definitions.
    (Previously in data_exploration.py, aligns with SSR 8.5.1 GET /api/v1/indicators)
    """
    data_service = DataService(db)
    indicators = await data_service.get_indicator_definitions(
        category_id=category_id,
        data_type_filter=data_type,
        offset=offset,
        limit=limit
    )
    return indicators


@router.get("/indicators/{indicator_code}", response_model=IndicatorDefinitionSchema)
async def get_indicator_by_code_catalog(
    indicator_code: str,
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user), # Auth if needed
):
    """
    Retrieve a specific indicator definition by its code.
    """
    data_service = DataService(db)
    indicator = await data_service.get_indicator_definition_by_code(code=indicator_code)
    if not indicator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator definition not found")
    return indicator


@router.get("/indicator-categories", response_model=List[IndicatorCategorySchema])
async def get_indicator_categories_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user)
):
    """Retrieve available indicator categories."""
    data_service = DataService(db)
    return await data_service.get_indicator_categories()


@router.get("/units-of-measurement", response_model=List[UnitOfMeasurementSchema])
async def get_units_of_measurement_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user)
):
    """Retrieve available units of measurement."""
    data_service = DataService(db)
    return await data_service.get_units_of_measurement()


@router.get("/temporal-resolutions", response_model=List[TemporalResolutionSchema])
async def get_temporal_resolutions_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user)
):
    """Retrieve available temporal resolutions."""
    # Assuming a get_temporal_resolutions method in DataService
    # data_service = DataService(db)
    # return await data_service.get_temporal_resolutions()
    raise HTTPException(status_code=501, detail="Temporal resolutions endpoint not fully implemented in service yet.")


@router.get("/data-quality-flags", response_model=List[DataQualityFlagSchema])
async def get_data_quality_flags_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user)
):
    """Retrieve available data quality flags."""
    # Assuming a get_data_quality_flags method in DataService
    # data_service = DataService(db)
    # return await data_service.get_data_quality_flags()
    raise HTTPException(status_code=501, detail="Data quality flags endpoint not fully implemented in service yet.")


# --- Infrastructure & Crop Lookups (can also be part of their respective domain endpoints) ---
@router.get("/infrastructure-types", response_model=List[InfrastructureTypeSchema])
async def get_infrastructure_types_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user)
):
    """Retrieve available infrastructure types."""
    data_service = DataService(db)
    return await data_service.get_infrastructure_types()


@router.get("/crops", response_model=List[CropSchema]) # Assuming CropSchema has basic fields
async def get_crops_catalog(
    db: AsyncSession = Depends(get_db),
    # current_user: UserModel = Depends(get_current_active_user),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """Retrieve a list of available crop types."""
    # This would need a general get_crops method in DataService
    # data_service = DataService(db)
    # crops = await data_service.get_all_crops(offset=offset, limit=limit) # Example method
    # return crops
    raise HTTPException(status_code=501, detail="Crops catalog endpoint not fully implemented in service yet.")
