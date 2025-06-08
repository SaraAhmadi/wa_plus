from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.dependencies import get_db, get_current_user
from src.services.data_service import DataService
from src.schemas.indicator_timeseries import TimeseriesDataPoint # Your schema for chart-ready data points
from src.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]]) # Using Dict as DataService returns this
async def get_timeseries_data_points(
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user), # Time-series data usually requires auth
    indicator_codes: List[str] = Query(..., description="Comma-separated list of indicator codes"),
    start_date: datetime = Query(..., description="Start date for the time series (ISO format)"),
    end_date: datetime = Query(..., description="End date for the time series (ISO format)"),
    reporting_unit_ids: Optional[List[int]] = Query(None, description="Comma-separated list of reporting unit IDs"),
    infrastructure_ids: Optional[List[int]] = Query(None, description="Comma-separated list of infrastructure unit IDs"),
    temporal_resolution_name: Optional[str] = Query(None, description="Filter by source temporal resolution (e.g., 'Daily', 'Monthly')"),
    aggregate_to: Optional[str] = Query(None, description="Aggregate data to resolution (e.g., 'Monthly', 'Annual', 'Seasonal')")
):
    """
    Retrieve time-series data for specified indicators and locations/units.
    (Moved from data_exploration.py, aligns with SSR 8.5.1 GET /api/v1/timeseries_data)
    """
    if not reporting_unit_ids and not infrastructure_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either reporting_unit_ids or infrastructure_ids must be provided for timeseries data."
        )

    data_service = DataService(db)
    try:
        data_points = await data_service.get_timeseries_data(
            indicator_definition_codes=indicator_codes,
            start_date=start_date,
            end_date=end_date,
            reporting_unit_ids=reporting_unit_ids,
            infrastructure_ids=infrastructure_ids,
            temporal_resolution_name=temporal_resolution_name,
            aggregate_to=aggregate_to
        )
    except ValueError as e: # Catch specific errors from service, e.g., invalid aggregation method
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e for server-side details
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching time-series data.")

    # The service method already returns List[Dict[str, Any]], suitable for flexible charting.
    # If you defined a strict TimeseriesDataPoint Pydantic schema that matches the dict structure,
    # you could use response_model=List[TimeseriesDataPoint]
    return data_points
