from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base_model import Base


class ReportingUnitType(Base):
    # __tablename__ will be "reporting_unit_types"
    # As per SSR 8.4.2

    name = Column(String(100), unique=True, nullable=False, index=True) # e.g., "River Basin", "Sub-Basin", "Irrigation Scheme"
    description = Column(Text, nullable=True)

    reporting_units = relationship("ReportingUnit", back_populates="unit_type")

    def __repr__(self):
        return f"<ReportingUnitType(id={self.id}, name='{self.name}')>"