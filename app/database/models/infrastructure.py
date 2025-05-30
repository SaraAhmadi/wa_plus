from sqlalchemy import String, Float, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry # type: ignore
from typing import List, Optional, Any # For type hints
from .base_model import Base


class Infrastructure(Base):
    # __tablename__ will be "infrastructures" (generated by Base)
    # As per SSR 8.4.12

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    infrastructure_type_id: Mapped[int] = mapped_column(ForeignKey('infrastructure_types.id'), nullable=False)
    reporting_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey('reporting_units.id'), nullable=True)
    operational_status_id: Mapped[Optional[int]] = mapped_column(ForeignKey('operational_status_types.id'), nullable=True)

    geom: Mapped[Optional[Any]] = mapped_column(Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True), nullable=True)
    capacity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capacity_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey('unit_of_measurements.id'), nullable=True)
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True) # JSONB usually maps to dict

    infrastructure_type: Mapped["InfrastructureType"] = relationship(back_populates="infrastructure_items")
    reporting_unit: Mapped[Optional["ReportingUnit"]] = relationship(back_populates="infrastructure_items")
    operational_status: Mapped[Optional["OperationalStatusType"]] = relationship(back_populates="infrastructure_items")
    capacity_unit: Mapped[Optional["UnitOfMeasurement"]] = relationship() # No back_populates needed if UnitOfMeasurement doesn't link back

    indicator_timeseries: Mapped[List["IndicatorTimeseries"]] = relationship(back_populates="infrastructure")
    financial_accounts: Mapped[List["FinancialAccount"]] = relationship(back_populates="infrastructure")

    def __repr__(self):
        return f"<Infrastructure(id={self.id}, name='{self.name}')>"
