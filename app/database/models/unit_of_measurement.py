from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base_model import Base


class UnitOfMeasurement(Base):
    # __tablename__ will be "units_of_measurement"
    # As per SSR 8.4.7

    name = Column(String(100), unique=True, nullable=False) # e.g., "mm", "m³/s"
    abbreviation = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("unit_of_measurement_categories.id"), nullable=True) # Or False if every unit MUST have a category

    # Relationships
    category = relationship("UnitOfMeasurementCategory", back_populates="units_of_measurement")
    # indicator_definitions = relationship("IndicatorDefinition", back_populates="unit_of_measurement")


    def __repr__(self):
        return f"<UnitOfMeasurement(id={self.id}, abbreviation='{self.abbreviation}', category_id={self.category_id})>"
    