from fastapi import APIRouter, Depends
from app.dashboard.dashboard_service import DashboardService
from app.dependencies.get_current_user import get_current_active_user
from app.database.models.user import User

router = APIRouter()

@router.get("/dashboard", response_model=dict)
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(DashboardService)
):
    """
    Retrieve data for the WAPlus dashboard.
    """
    data = await dashboard_service.get_dashboard_data()
    return data
