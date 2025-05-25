from sqlalchemy import Column, Text, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base_model import Base


class IndicatorTimeseries(Base):
    # __tablename__ will be "indicator_timeseries"
    # As per SSR 8.4.4 (Note: SSR index was 8.4.2, but content matches 8.4.4)

    reporting_unit_id = Column(Integer, ForeignKey('reporting_units.id'), nullable=True, index=True)
    infrastructure_id = Column(Integer, ForeignKey('infrastructures.id'), nullable=True, index=True) # Added from SSR 8.4.4
    indicator_definition_id = Column(Integer, ForeignKey('indicator_definitions.id'), nullable=False, index=True) # Link to master indicator list

    timestamp = Column(DateTime, nullable=False, index=True)
    value_numeric = Column(Float, nullable=True) # Renamed from 'value' for clarity if text values are possible
    value_text = Column(String(255), nullable=True) # As per SSR 8.4.4
    # value_category_id (FK, INTEGER, Nullable): Link to a lookup table if the value is from a predefined category list. (Consider if needed)

    temporal_resolution_id = Column(Integer, ForeignKey('temporal_resolutions.id'), nullable=True) # SSR 8.4.4
    quality_flag_id = Column(Integer, ForeignKey('data_quality_flags.id'), nullable=True) # SSR 8.4.4
    comments = Column(Text, nullable=True) # SSR 8.4.4

    # source_dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    # dataset = relationship("Dataset")

    reporting_unit = relationship("ReportingUnit", back_populates="indicator_timeseries")
    infrastructure = relationship("Infrastructure", back_populates="indicator_timeseries") # Added
    indicator_definition = relationship("IndicatorDefinition", back_populates="timeseries_data") # Added
    temporal_resolution = relationship("TemporalResolution") # Added
    quality_flag = relationship("DataQualityFlag") # Added

    def __repr__(self):
        return (f"<IndicatorTimeseries(id={self.id}, "
                f"indicator='{self.indicator_definition.name if self.indicator_definition else None}', "
                f"timestamp='{self.timestamp}')>")