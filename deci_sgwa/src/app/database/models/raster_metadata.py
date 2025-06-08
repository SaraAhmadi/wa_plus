from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey # Added Integer
from sqlalchemy.orm import relationship # Added
from .base_model import Base


class RasterMetadata(Base):
    # __tablename__ will be "raster_metadatas"
    # As per SSR 8.4.11 (Raster_Layers_Metadata Table)

    layer_name_geoserver = Column(String(255), nullable=False, unique=True, index=True)
    geoserver_workspace = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    indicator_definition_id = Column(Integer, ForeignKey('indicator_definitions.id'), nullable=False, index=True) # Link to master indicator list

    timestamp_valid_start = Column(DateTime, nullable=False) # SSR 8.4.11
    timestamp_valid_end = Column(DateTime, nullable=True) # SSR 8.4.11

    spatial_resolution_desc = Column(String(100), nullable=True) # SSR 8.4.11 (e.g., "250m")
    # unit from original file was removed, as unit should come from IndicatorDefinition
    storage_path_or_postgis_table = Column(String(512), nullable=False) # SSR 8.4.11
    default_style_name = Column(String(100), nullable=True) # SSR 8.4.11
    # legend_url from original file was removed, can be derived or stored in UI config

    indicator_definition = relationship("IndicatorDefinition", back_populates="raster_layers") # Added

    # source_dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    # dataset = relationship("Dataset")

    def __repr__(self):
        return f"<RasterMetadata(id={self.id}, layer_name_geoserver='{self.layer_name_geoserver}')>"