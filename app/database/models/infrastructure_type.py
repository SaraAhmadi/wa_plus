from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from .base_model import Base


class InfrastructureType(Base):
    # __tablename__ will be "infrastructure_types"
    # As per SSR 8.4.13

    name = Column(String(100), unique=True, nullable=False, index=True) # e.g., "Dam", "Pumping Station"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    infrastructure_items = relationship("Infrastructure", back_populates="infrastructure_type")

    def __repr__(self):
        return f"<InfrastructureType(id={self.id}, name='{self.name}')>"
