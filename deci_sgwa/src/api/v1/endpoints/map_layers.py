from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, get_current_user  # Assuming map layer info might be protected
from src.services.data_service import DataService
from src.schemas.map_layer import MapLayerMetadata  # Pydantic schema for the response
from src.schemas.user import User as UserSchema  # For current_user type hint

router = APIRouter()


@router.get("/", response_model=List[MapLayerMetadata])
async def get_available_map_layers(
        db: AsyncSession = Depends(get_db),
        current_user: UserSchema = Depends(get_current_user),  # Often, knowing available layers requires auth
        reporting_unit_id: Optional[int] = Query(None,
                                                 description="Filter layers relevant to a specific geographic reporting unit ID (future use, complex to implement for rasters)"),
        indicator_code: Optional[str] = Query(None, description="Filter layers representing a specific indicator code"),
        layer_type: Optional[str] = Query(None,
                                          description="Filter by layer type (e.g., 'Raster', 'VectorChoropleth', 'VectorPoint') - conceptual filter")
        # time_instance: Optional[datetime] = Query(None, description="Filter layers valid for a specific time instance (if layers are time-specific)") # Not yet fully supported in service
):
    """
    Retrieve metadata about available map layers published via GeoServer.
    This helps the frontend construct OGC requests.
    Corresponds to SSR 8.5.2 GET /api/v1/map_layers
    """
    data_service = DataService(db)

    # The DataService.get_map_layers_metadata method currently implements filtering
    # by indicator_definition_code. Other filters like reporting_unit_id for rasters
    # or a generic layer_type are more complex and would need refinement in the service
    # and potentially the underlying RasterMetadata model or a new VectorLayerMetadata model.

    try:
        map_layers = await data_service.get_map_layers_metadata(
            reporting_unit_id=reporting_unit_id,  # Pass through, service might not use it yet
            indicator_definition_code=indicator_code,
            layer_type=layer_type  # Pass through, service might not use it yet
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching map layers metadata: {str(e)}"
        )

    if not map_layers and map_layers is not None:  # Handle empty list explicitly if needed
        # Depending on desired behavior, could return 404 if specific filters yield no results,
        # or always return an empty list. Empty list is usually fine.
        pass

    return map_layers

# Example of how one might get details for a SINGLE specific map layer if needed,
# though the primary use case is listing available layers.
# @router.get("/{layer_id}", response_model=MapLayerMetadata)
# async def get_map_layer_detail(
#     layer_id: str, # This would be e.g., the geoserver_layer_name
#     db: AsyncSession = Depends(get_db),
#     current_user: UserSchema = Depends(get_current_user)
# ):
#     """
#     Get detailed metadata for a single specific map layer.
#     """
#     data_service = DataService(db)
#     # This would require a new method in DataService, e.g., get_map_layer_by_geoserver_name()
#     # layer_detail = await data_service.get_specific_map_layer_details(layer_id)
#     # if not layer_detail:
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Map layer not found")
#     # return layer_detail
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Fetching single layer detail not implemented yet")
