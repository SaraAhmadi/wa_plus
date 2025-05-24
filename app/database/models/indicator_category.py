from sqlalchemy import Column, String
# from sqlalchemy.orm import relationship
from .base_model import Base


class IndicatorCategory(Base):
    # __tablename__ will be "indicator_categories"
    # As per SSR 8.4.10

    name_en = Column(String(100), unique=True, nullable=False) # e.g., "Climate Data"
    name_local = Column(String(100), nullable=True)

    # indicator_definitions = relationship("IndicatorDefinition", back_populates="category")

    def __repr__(self):
        return f"<IndicatorCategory(id={self.id}, name_en='{self.name_en}')>"
    