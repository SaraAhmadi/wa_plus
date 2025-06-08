from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_active_user, UserModel
from app.services.data_service import DataService
# from app.schemas.user import User as UserSchema # Replaced by UserModel
# from app.schemas.cropping_pattern import CroppingPattern as CroppingPatternSchema # If DataService returned models

router = APIRouter()


@router.get("/cropping-patterns", response_model=List[Dict[str, Any]]) # DataService returns List[Dict]
async def get_cropping_pattern_data(
    reporting_unit_id: int = Query(..., description="ID of the reporting unit"),
    time_period_year: int = Query(..., description="Agricultural or calendar year"),
    time_period_season: Optional[str] = Query(None, description="Specific season (e.g., 'Kharif', 'Rabi')"),
    pattern_type: Optional[str] = Query(None, description="Type of pattern ('Actual', 'Planned')"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user), # Agricultural data likely requires auth
):
    """
    Retrieve data on actual or planned cropping patterns for a specific reporting unit and year/season.
    (Moved from data_exploration.py, aligns with SSR 8.5.3 GET /api/v1/cropping_patterns)
    """
    data_service = DataService(db)
    patterns = await data_service.get_cropping_patterns(
        reporting_unit_id=reporting_unit_id,
        time_period_year=time_period_year,
        time_period_season=time_period_season,
        pattern_type=pattern_type
    )
    if not patterns and patterns is not None: # If service returns [] for no data
        # Return empty list, or 404 if the reporting_unit_id itself is invalid.
        # Assuming service handles invalid reporting_unit_id by returning empty or raising error.
        pass
    return patterns

# Placeholder for Land Use Summary (SSR 8.5.3)
# This would require a dedicated LandUse model and service logic in DataService
# @router.get("/land-use-summary", ...)
# async def get_land_use_summary(
#     reporting_unit_id: int = Query(..., description="ID of the reporting unit"),
#     year: int = Query(..., description="Year for the land use summary"),
#     db: AsyncSession = Depends(get_db),
#     current_user: UserModel = Depends(get_current_active_user)
# ):
#     # data_service = DataService(db)
#     # summary = await data_service.get_land_use_summary(reporting_unit_id=reporting_unit_id, year=year)
#     # if not summary:
#     #     raise HTTPException(status_code=404, detail="Land use summary not found or unit invalid.")
#     # return summary
#     raise HTTPException(status_code=501, detail="Land use summary endpoint not implemented yet.")
