from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB # For attributes
from sqlalchemy.orm import relationship
from .base_model import Base


class Crop(Base):
    # __tablename__ will be "crops"
    # As per SSR 8.4.5

    code = Column(String(50), unique=True, nullable=False, index=True)
    name_en = Column(String(100), nullable=False)
    name_local = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True) # e.g., "Cereal", "Fodder"
    attributes = Column(JSONB, nullable=True) # For other crop-specific parameters

    cropping_patterns = relationship("CroppingPattern", back_populates="crop")
    financial_accounts = relationship("FinancialAccount", back_populates="crop")

    def __repr__(self):
        return f"<Crop(id={self.id}, code='{self.code}', name_en='{self.name_en}')>"
    