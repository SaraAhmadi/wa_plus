from sqlalchemy import Column, Text, String, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base_model import Base


class CroppingPattern(Base):
    # __tablename__ will be "cropping_patterns"
    # As per SSR 8.4.6

    reporting_unit_id = Column(Integer, ForeignKey('reporting_units.id'), nullable=False)
    crop_id = Column(Integer, ForeignKey('crops.id'), nullable=False)

    time_period_year = Column(Integer, nullable=False) # e.g., 2023 for 2022-2023 season
    time_period_season = Column(String(50), nullable=True) # e.g., "Kharif", "Rabi"
    data_type = Column(String(50), nullable=False)  # "Actual", "Proposed/Planned", "Target"

    area_cultivated_ha = Column(Float, nullable=True)
    area_proposed_ha = Column(Float, nullable=True)
    yield_actual_ton_ha = Column(Float, nullable=True)
    yield_proposed_ton_ha = Column(Float, nullable=True)
    water_allocation_mcm = Column(Float, nullable=True)
    water_consumed_actual_mcm = Column(Float, nullable=True)
    comments = Column(Text, nullable=True)

    # source_dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)

    reporting_unit = relationship("ReportingUnit", back_populates="cropping_patterns")
    crop = relationship("Crop", back_populates="cropping_patterns")

    __table_args__ = (
        UniqueConstraint('reporting_unit_id', 'crop_id', 'time_period_year', 'time_period_season', 'data_type',
                         name='uq_cropping_pattern_entry'),
    )

    def __repr__(self):
        return (f"<CroppingPattern(id={self.id}, unit_id={self.reporting_unit_id}, "
                f"crop_id={self.crop_id}, year={self.time_period_year}, type='{self.data_type}')>")
