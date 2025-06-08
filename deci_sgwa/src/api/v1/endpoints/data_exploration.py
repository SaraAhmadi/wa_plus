from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.dependencies import get_db, get_current_user # For authenticated routes
from src.services.data_service import DataService
from src.schemas.reporting_unit import ReportingUnit as ReportingUnitSchema, ReportingUnitType as ReportingUnitTypeSchema, ReportingUnitSimple
from src.schemas.indicator_definition import IndicatorDefinition as IndicatorDefinitionSchema
from src.schemas.indicator_category import IndicatorCategory as IndicatorCategorySchema # Assuming you created this schema
from src.schemas.unit_of_measurement import UnitOfMeasurement as UnitOfMeasurementSchema # Assuming you created this schema
from src.schemas.indicator_timeseries import TimeseriesDataPoint # For chart-ready data
from src.schemas.crop import Crop as CropSchema # Assuming you created this schema
from src.schemas.cropping_pattern import CroppingPattern as CroppingPatternSchema # Assuming you created this schema
# Import other relevant schemas as needed, e.g., for financial summary

router = APIRouter()


# --- Geographic Units & Types ---
@router.get("/geographic-units", response_model=List[ReportingUnitSchema])
async def get_geographic_units(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Uncomment if this route needs auth
    unit_type_id: Optional[int] = Query(None, description="Filter by reporting unit type ID"),
    parent_unit_id: Optional[int] = Query(None, description="Filter by parent unit ID to get children"),
    search: Optional[str] = Query(None, description="Search term for unit name"),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Retrieve a list of available geographic/reporting units.
    Corresponds to SSR 8.5.1 GET /api/v1/geographic_units
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
async def get_geographic_unit_by_id(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Uncomment if auth needed
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
async def get_geographic_unit_types(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Uncomment if auth needed
):
    """
    Retrieve a list of available geographic/reporting unit types.
    """
    data_service = DataService(db)
    unit_types = await data_service.get_reporting_unit_types()
    return unit_types


# --- Indicator Definitions & Lookups ---
@router.get("/indicators", response_model=List[IndicatorDefinitionSchema])
async def get_indicators(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Uncomment if auth needed
    category_id: Optional[int] = Query(None, description="Filter by indicator category ID"),
    data_type: Optional[str] = Query(None, description="Filter by data type (e.g., 'time-series', 'spatial_raster')"),
    offset: int = Query(0, description="Number of records to offset for pagination", ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Retrieve a list of available WA+ indicator definitions.
    Corresponds to SSR 8.5.1 GET /api/v1/indicators
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
async def get_indicator_by_code(
    indicator_code: str,
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Uncomment if auth needed
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
async def get_indicator_categories(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user)
):
    """Retrieve available indicator categories."""
    data_service = DataService(db)
    return await data_service.get_indicator_categories()


@router.get("/units-of-measurement", response_model=List[UnitOfMeasurementSchema])
async def get_units_of_measurement(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user)
):
    """Retrieve available units of measurement."""
    data_service = DataService(db)
    return await data_service.get_units_of_measurement()


# --- TimeSeries & Summary Data ---
@router.get("/timeseries-data", response_model=List[Dict[str, Any]]) # Using Dict for flexibility from service
async def get_timeseries_data_points(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Typically timeseries data requires auth
    indicator_codes: List[str] = Query(..., description="Comma-separated list of indicator codes"), # '...' means required
    start_date: datetime = Query(..., description="Start date for the time series (ISO format)"),
    end_date: datetime = Query(..., description="End date for the time series (ISO format)"),
    reporting_unit_ids: Optional[List[int]] = Query(None, description="Comma-separated list of reporting unit IDs"),
    infrastructure_ids: Optional[List[int]] = Query(None, description="Comma-separated list of infrastructure unit IDs"),
    temporal_resolution_name: Optional[str] = Query(None, description="Filter by source temporal resolution (e.g., 'Daily', 'Monthly')"),
    aggregate_to: Optional[str] = Query(None, description="Aggregate data to resolution (e.g., 'Monthly', 'Annual')")
):
    """
    Retrieve time-series data for specified indicators and locations/units.
    Corresponds to SSR 8.5.1 GET /api/v1/timeseries_data
    Note: FastAPI handles comma-separated query params for List[type] automatically.
    """
    if not reporting_unit_ids and not infrastructure_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either reporting_unit_ids or infrastructure_ids must be provided."
        )
    data_service = DataService(db)
    data_points = await data_service.get_timeseries_data(
        indicator_definition_codes=indicator_codes,
        start_date=start_date,
        end_date=end_date,
        reporting_unit_ids=reporting_unit_ids,
        infrastructure_ids=infrastructure_ids,
        temporal_resolution_name=temporal_resolution_name,
        aggregate_to=aggregate_to
    )
    if not data_points and data_points is not None: # Check for empty list explicitly if service returns [] for no data
        # Decided behavior for no data: return empty list or 404. Empty list is often preferred for timeseries.
        pass
    return data_points


@router.get("/summary-data", response_model=List[Dict[str, Any]])
async def get_summary_statistics(
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Likely requires auth
    indicator_codes: List[str] = Query(..., description="List of indicator codes"),
    time_period_start: datetime = Query(..., description="Start of the period for summary"),
    time_period_end: datetime = Query(..., description="End of the period for summary"),
    reporting_unit_ids: Optional[List[int]] = Query(None, description="List of reporting unit IDs"),
    infrastructure_ids: Optional[List[int]] = Query(None, description="List of infrastructure IDs"),
    # group_by_field: Optional[str] = Query(None, description="Field to group by (e.g., 'crop_type') - Advanced"),
    aggregation_method: str = Query("Average", description="Method for aggregation (e.g., 'Average', 'Sum')")
):
    """
    Retrieve aggregated/summary data for comparisons or KPIs.
    Corresponds to SSR 8.5.1 GET /api/v1/summary_data
    """
    if not reporting_unit_ids and not infrastructure_ids:
         # Or allow global summary if that makes sense for some indicators
        pass # Modify this if summaries without specific location are allowed

    data_service = DataService(db)
    summary_data = await data_service.get_summary_data(
        indicator_definition_codes=indicator_codes,
        time_period_start=time_period_start,
        time_period_end=time_period_end,
        reporting_unit_ids=reporting_unit_ids,
        infrastructure_ids=infrastructure_ids,
        # group_by_field=group_by_field, # Pass if implemented in service
        aggregation_method=aggregation_method
    )
    return summary_data


# --- Cropping Patterns (SSR 8.5.3) ---
@router.get("/cropping-patterns", response_model=List[Dict[str, Any]]) # Using Dict from service for now
async def get_cropping_pattern_data(
    reporting_unit_id: int = Query(..., description="ID of the reporting unit"),
    time_period_year: int = Query(..., description="Agricultural or calendar year"),
    time_period_season: Optional[str] = Query(None, description="Specific season (e.g., 'Kharif', 'Rabi')"),
    pattern_type: Optional[str] = Query(None, description="Type of pattern ('Actual', 'Planned')"),
    db: AsyncSession = Depends(get_db),
    # current_user: Any = Depends(get_current_user), # Likely requires auth
):
    """
    Retrieve data on actual or planned cropping patterns.
    Corresponds to SSR 8.5.3 GET /api/v1/cropping_patterns
    """
    data_service = DataService(db)
    patterns = await data_service.get_cropping_patterns(
        reporting_unit_id=reporting_unit_id,
        time_period_year=time_period_year,
        time_period_season=time_period_season,
        pattern_type=pattern_type
    )
    if not patterns and patterns is not None:
        # Return empty list if no patterns found, or 404 if unit/year itself is invalid
        pass
    return patterns


# --- Financial Data (Simplified example - SSR 8.5.4) ---
# More financial endpoints would go into a dedicated financial_endpoints.py
@router.get("/financial-summary", response_model=Dict[str, Any])
async def get_financial_overview(
    start_date: datetime = Query(..., description="Start date for financial period"),
    end_date: datetime = Query(..., description="End date for financial period"),
    reporting_unit_id: Optional[int] = Query(None, description="Filter by reporting unit ID"),
    infrastructure_id: Optional[int] = Query(None, description="Filter by infrastructure ID"),
    group_by_account_type: bool = Query(False, description="Group results by specific account types"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user), # Financial data almost always requires auth
):
    """
    Retrieve a financial summary (costs, revenues).
    Corresponds to API SSR 8.5.4 /financial_accounts/summary
    """
    data_service = DataService(db)
    summary = await data_service.get_financial_accounts_summary(
        start_date=start_date,
        end_date=end_date,
        reporting_unit_id=reporting_unit_id,
        infrastructure_id=infrastructure_id,
        group_by_account_type=group_by_account_type
    )
    return summary

# Placeholder for Land Use Summary (SSR 8.5.3) - requires LandUse model and service logic
# @router.get("/land-use-summary", ...)
# async def get_land_use_summary_data(...): ...
