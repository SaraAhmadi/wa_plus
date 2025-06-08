from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime
from .base_schema import BaseSchema, BaseSchemaRead # Assuming you create this

# This schema is more for the API response of `/map_layers` (SSR 8.5.2)
# than directly mirroring RasterMetadata model for CRUD on RasterMetadata.
# It describes what the frontend needs to know about a GeoServer layer.


class MapLayerMetadata(BaseSchema): # Not inheriting BaseSchemaRead as it's not a DB model itself
    layer_id: str # Could be layer_name_geoserver or a composite ID
    title: str
    abstract: Optional[str] = None
    geoserver_workspace: str
    geoserver_layer_name: str
    service_type: str # WMS, WMTS, WFS
    service_endpoint: HttpUrl
    associated_indicator_code: Optional[str] = None
    default_style_name: Optional[str] = None
    legend_url: Optional[HttpUrl] = None
    temporal_validity_start: Optional[datetime] = None
    temporal_validity_end: Optional[datetime] = None
    spatial_resolution_desc: Optional[str] = None
    # Add other relevant fields as needed by frontend
    