from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.dependencies import get_db, get_current_active_user, UserModel
from app.services.data_service import DataService
# from app.schemas.user import User as UserSchema # Replaced by UserModel
# Define a Pydantic schema for summary data if its structure is stable
# from app.schemas.summary import SummaryDataPoint

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]]) # Using Dict as DataService returns this
async def get_summary_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user), # Summary data often requires auth
    indicator_codes: List[str] = Query(..., description="List of indicator codes"),
    time_period_start: datetime = Query(..., description="Start of the period for summary"),
    time_period_end: datetime = Query(..., description="End of the period for summary"),
    reporting_unit_ids: Optional[List[int]] = Query(None, description="List of reporting unit IDs"),
    infrastructure_ids: Optional[List[int]] = Query(None, description="List of infrastructure IDs"),
    # group_by_field: Optional[str] = Query(None, description="Field to group by (e.g., 'crop_type') - Advanced"),
    aggregation_method: str = Query("Average", description="Method for aggregation (e.g., 'Average', 'Sum', 'Min', 'Max', 'Count')")
):
    """
    Retrieve aggregated/summary data for comparisons or KPIs.
    (Moved from data_exploration.py, aligns with SSR 8.5.1 GET /api/v1/summary_data)
    """
    # Basic validation: either reporting_unit_ids or infrastructure_ids or neither (for global summary)
    # Add more specific validation if needed based on use cases.
    # if not reporting_unit_ids and not infrastructure_ids:
    #     pass # Allow global summaries if service supports it

    data_service = DataService(db)
    try:
        summary_data = await data_service.get_summary_data(
            indicator_definition_codes=indicator_codes,
            time_period_start=time_period_start,
            time_period_end=time_period_end,
            reporting_unit_ids=reporting_unit_ids,
            infrastructure_ids=infrastructure_ids,
            # group_by_field=group_by_field, # Pass if implemented in service
            aggregation_method=aggregation_method
        )
    except ValueError as e: # Catch specific errors from service, e.g., invalid aggregation method
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching summary data.")

    return summary_data
