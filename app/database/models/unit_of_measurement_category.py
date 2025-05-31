from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base_model import Base

class UnitOfMeasurementCategory(Base):
    __tablename__ = "unit_of_measurement_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    # Relationships
    units_of_measurement = relationship("UnitOfMeasurement", back_populates="category")

    def __repr__(self):
        return f"<UnitOfMeasurementCategory(id={self.id}, name='{self.name}')>"
