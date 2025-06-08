from sqlalchemy import Column, String
# from sqlalchemy.orm import relationship
from .base_model import Base


class TemporalResolution(Base):
    # __tablename__ will be "temporal_resolutions"
    # As per SSR 8.4.8

    name = Column(String(100), unique=True, nullable=False) # e.g., "Daily", "Monthly"

    def __repr__(self):
        return f"<TemporalResolution(id={self.id}, name='{self.name}')>"
    