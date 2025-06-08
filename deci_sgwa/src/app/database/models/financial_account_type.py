from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base_model import Base


class FinancialAccountType(Base):
    # __tablename__ will be "financial_account_types"
    # As per SSR 8.4.16

    name = Column(String(255), unique=True, nullable=False, index=True) # e.g., "Revenue - Agricultural Water Sales"
    is_cost = Column(Boolean, nullable=False) # True if cost, False if revenue
    category = Column(String(100), nullable=True) # e.g., "Operational", "Capital"

    financial_accounts = relationship("FinancialAccount", back_populates="account_type")

    def __repr__(self):
        return f"<FinancialAccountType(id={self.id}, name='{self.name}')>"
