# app/database/models/base_model.py
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, declared_attr
from typing import Any
import re
from datetime import datetime


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models using SQLAlchemy 2.0 Mapped Annotations.
    It provides a default __tablename__ and id, created_at, updated_at columns.
    """
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # To be defined in subclasses for __tablename__ generation
    __name__: str

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case for table names
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Basic pluralization logic (can be improved if needed)
        if name.endswith('y') and name[-2] not in 'aeiou':
            # e.g. category -> categories, currency -> currencies
            name = name[:-1] + "ies"
        elif name.endswith('s') or name.endswith('sh') or name.endswith('ch') or name.endswith('x') or name.endswith('z'):
            # e.g. address -> addresses, bus -> buses
            name = name + "es"
        elif not name.endswith('s'):
            name = name + "s"
        return name