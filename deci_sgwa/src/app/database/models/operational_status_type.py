from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from .base_model import Base


class OperationalStatusType(Base):
    # __tablename__ will be "operational_status_types"
    # As per SSR 8.4.14

    name = Column(String(100), unique=True, nullable=False, index=True) # e.g., "Operational", "Under Maintenance"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    infrastructure_items = relationship("Infrastructure", back_populates="operational_status")

    def __repr__(self):
        return f"<OperationalStatusType(id={self.id}, name='{self.name}')>"
