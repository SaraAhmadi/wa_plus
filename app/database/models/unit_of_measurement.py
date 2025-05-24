from sqlalchemy import Column, String, Text
# from sqlalchemy.orm import relationship # Not strictly needed if no back_populates from here
from .base_model import Base


class UnitOfMeasurement(Base):
    # __tablename__ will be "units_of_measurement"
    # As per SSR 8.4.7

    name = Column(String(100), unique=True, nullable=False) # e.g., "mm", "m³/s"
    abbreviation = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # No direct back_populates defined in SSR, but could have:
    # indicator_definitions = relationship("IndicatorDefinition", back_populates="unit_of_measurement")

    def __repr__(self):
        return f"<UnitOfMeasurement(id={self.id}, abbreviation='{self.abbreviation}')>"
    