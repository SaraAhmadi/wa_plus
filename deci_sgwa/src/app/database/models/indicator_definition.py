from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base_model import Base


class IndicatorDefinition(Base):
    # __tablename__ will be "indicator_definitions"
    # As per SSR 8.4.3

    code = Column(String(100), unique=True, nullable=False, index=True) # indicator_code from SSR
    name_en = Column(String(255), nullable=False) # indicator_name_en from SSR
    name_local = Column(String(255), nullable=True)
    description_en = Column(Text, nullable=True)
    description_local = Column(Text, nullable=True)
    data_type = Column(String(50), nullable=False) # e.g., "Numeric", "Categorical"

    unit_of_measurement_id = Column(Integer, ForeignKey('unit_of_measurements.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('indicator_categories.id'), nullable=True)
    wa_sheet_reference = Column(String(50), nullable=True)
    is_spatial_raster = Column(Boolean, default=False, nullable=False) # If typically a raster

    unit_of_measurement = relationship("UnitOfMeasurement")
    category = relationship("IndicatorCategory")
    timeseries_data = relationship("IndicatorTimeseries", back_populates="indicator_definition")
    raster_layers = relationship("RasterMetadata", back_populates="indicator_definition")

    def __repr__(self):
        return f"<IndicatorDefinition(id={self.id}, code='{self.code}', name_en='{self.name_en}')>"