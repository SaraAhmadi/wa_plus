from pydantic import Field, constr
from typing import Optional
from .base_schema import BaseSchema, BaseSchemaRead


class CurrencyBase(BaseSchema):
    # Using constr for regex validation of currency code (optional but good)
    code: constr(strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]{3}$') = Field( # type: ignore
        ..., examples=["USD", "EUR", "IRR"], description="Standard 3-letter currency code (ISO 4217)"
    )
    name: str = Field(max_length=100, examples=["US Dollar", "Euro", "Iranian Rial"])


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseSchema):
    code: Optional[constr(strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]{3}$')] = Field(None, description="Standard 3-letter currency code (ISO 4217)") # type: ignore
    name: Optional[str] = Field(None, max_length=100)


class Currency(CurrencyBase, BaseSchemaRead):
    pass
