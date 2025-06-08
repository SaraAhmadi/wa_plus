from pydantic import Field, HttpUrl # HttpUrl for potential legend URLs
from typing import Optional, List
from datetime import datetime
from .base_schema import BaseSchema, BaseSchemaRead
from .indicator_definition import IndicatorDefinition as IndicatorDefinitionSchema # For nesting


class RasterMetadataBase(BaseSchema):
    layer_name_geoserver: str = Field(max_length=255, description="Unique layer name used in GeoServer")
    geoserver_workspace: str = Field(max_length=100, description="GeoServer workspace name")
    description: Optional[str] = None
    indicator_definition_id: int = Field(..., description="FK to the master indicator definition")

    timestamp_valid_start: datetime = Field(..., description="Start date/time of validity for the raster data")
    timestamp_valid_end: Optional[datetime] = Field(None, description="End date/time of validity (can be same as start for static)")

    spatial_resolution_desc: Optional[str] = Field(None, max_length=100, examples=["250m", "30m"], description="Text description of spatial resolution")
    storage_path_or_postgis_table: str = Field(max_length=512, description="Path to raw/processed GeoTIFF or name of PostGIS raster table")
    default_style_name: Optional[str] = Field(None, max_length=100, description="Default SLD style name in GeoServer for this layer")
    # source_dataset_id: Optional[int] = None # If you add this to the model


class RasterMetadataCreate(RasterMetadataBase):
    pass


class RasterMetadataUpdate(BaseSchema): # All fields optional for PATCH
    layer_name_geoserver: Optional[str] = Field(None, max_length=255)
    geoserver_workspace: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    indicator_definition_id: Optional[int] = None

    timestamp_valid_start: Optional[datetime] = None
    timestamp_valid_end: Optional[datetime] = None

    spatial_resolution_desc: Optional[str] = Field(None, max_length=100)
    storage_path_or_postgis_table: Optional[str] = Field(None, max_length=512)
    default_style_name: Optional[str] = Field(None, max_length=100)
    # source_dataset_id: Optional[int] = None


class RasterMetadata(RasterMetadataBase, BaseSchemaRead):
    indicator_definition: Optional[IndicatorDefinitionSchema] = None # Nested representation
