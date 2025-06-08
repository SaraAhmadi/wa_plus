# app/api/v1/api_router_v1.py
from fastapi import APIRouter

from src.api.v1.endpoints import auth
from src.api.v1.endpoints.admin import users as admin_users
from src.api.v1.endpoints.admin import roles as admin_roles
from src.api.v1.endpoints import exports
from src.api.v1.endpoints import land_and_agriculture
from src.api.v1.endpoints import map_layers
from src.api.v1.endpoints import metadata_catalog
from src.api.v1.endpoints import summary_data
from src.api.v1.endpoints import timeseries
from src.api.v1.endpoints import unit_of_measurement_category


api_router_v1 = APIRouter()

api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(admin_users.router, prefix="/admin")

api_router_v1.include_router(metadata_catalog.router, prefix="/metadata", tags=["Metadata Catalog"])
api_router_v1.include_router(timeseries.router, prefix="/timeseries", tags=["Time Series Data"])
api_router_v1.include_router(summary_data.router, prefix="/summary-data", tags=["Summary Data"])
api_router_v1.include_router(land_and_agriculture.router, prefix="/land-agriculture", tags=["Land and Agriculture"])
api_router_v1.include_router(map_layers.router, prefix="/map-layers", tags=["Map Layers"])
api_router_v1.include_router(unit_of_measurement_category.router, prefix="/measurement-units", tags=["Unit of Measurement Categories"])
api_router_v1.include_router(exports.router, prefix="/export", tags=["Data Export"])

api_router_v1.include_router(admin_roles.router, prefix="/admin/roles", tags=["Admin - Roles"])
