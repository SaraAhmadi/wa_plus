from sqlalchemy import Column, String, Text, ForeignKey, Integer, Date, Numeric
from sqlalchemy.orm import relationship
from .base_model import Base


class FinancialAccount(Base):
    # __tablename__ will be "financial_accounts"
    # As per SSR 8.4.15

    reporting_unit_id = Column(Integer, ForeignKey('reporting_units.id'), nullable=True)
    infrastructure_id = Column(Integer, ForeignKey('infrastructure.id'), nullable=True)
    financial_account_type_id = Column(Integer, ForeignKey('financial_account_types.id'), nullable=False)
    crop_id = Column(Integer, ForeignKey('crops.id'), nullable=True) # If entry is crop-specific

    transaction_date = Column(Date, nullable=False) # Date of transaction or period end
    amount = Column(Numeric(18, 2), nullable=False) # Monetary value
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    description = Column(Text, nullable=True)
    source_document_ref = Column(String(255), nullable=True)

    reporting_unit = relationship("ReportingUnit", back_populates="financial_accounts")
    infrastructure = relationship("Infrastructure", back_populates="financial_accounts")
    account_type = relationship("FinancialAccountType", back_populates="financial_accounts")
    crop = relationship("Crop", back_populates="financial_accounts")
    currency = relationship("Currency")

    def __repr__(self):
        return (f"<FinancialAccount(id={self.id}, type='{self.account_type.name if self.account_type else None}', "
                f"date='{self.transaction_date}', amount={self.amount})>")
