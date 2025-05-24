from sqlalchemy import Column, String
# from sqlalchemy.orm import relationship
from .base_model import Base


class Currency(Base):
    # __tablename__ will be "currencies"
    # As per SSR 8.4.17

    code = Column(String(3), unique=True, nullable=False, index=True) # e.g., "IRR", "USD"
    name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Currency(id={self.id}, code='{self.code}')>"
    