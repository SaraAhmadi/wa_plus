from sqlalchemy import Column, String, Text
# from sqlalchemy.orm import relationship
from .base_model import Base


class DataQualityFlag(Base):
    # __tablename__ will be "data_quality_flags"
    # As per SSR 8.4.9

    name = Column(String(100), unique=True, nullable=False) # e.g., "Measured", "Estimated"
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DataQualityFlag(id={self.id}, name='{self.name}')>"
    