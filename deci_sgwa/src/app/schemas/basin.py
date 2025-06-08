from pydantic import Field
from typing import Optional, Any # Any for GeoJSON geometry
from .base_schema import BaseSchema, BaseSchemaWithTimestamps
from sqlalchemy.orm import mapped_column, Mapped
from geoalchemy2 import Geometry


# Shared properties
class BasinBase(BaseSchema):
    name: str = Field(..., example="Nile Basin")
    code: Optional[str] = Field(None, example="NB01", unique=True)
    description: Optional[str] = None
    area_sqkm: Optional[float] = Field(None, example=3349000.0)
    geom: Mapped[Optional[str]] = mapped_column(Geometry(geometry_type='MULTIPOLYGON', srid=4326,
                                                         spatial_index=True), nullable=True) # For GeoJSON representation, e.g., {"type": "MultiPolygon", "coordinates": ...}


# Properties to receive on creation
class BasinCreate(BasinBase):
    pass


# Properties to receive on update
class BasinUpdate(BasinBase):
    name: Optional[str] = None # All fields optional for update


# Properties to return to client
class Basin(BaseSchemaWithTimestamps, BasinBase):
    id: int
    # geom will be whatever GeoAlchemy2 serializes.
    # For proper GeoJSON, a custom serializer might be needed or handle in service layer.


# Properties stored in DB
class BasinInDB(Basin):
    pass
