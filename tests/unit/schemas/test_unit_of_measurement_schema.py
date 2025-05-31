import pytest
from pydantic import ValidationError
from typing import Optional # Required for Optional type hints in tests if not globally available

from app.schemas.unit_of_measurement import (
    UnitOfMeasurement,
    UnitOfMeasurementCreate,
    UnitOfMeasurementBase,
    UnitOfMeasurementUpdate # Assuming it exists
)
from app.schemas.unit_of_measurement_category import UnitOfMeasurementCategory as UnitOfMeasurementCategorySchema
from app.database.models import UnitOfMeasurement as UnitOfMeasurementModel
from app.database.models import UnitOfMeasurementCategory as UnitOfMeasurementCategoryModel

# Helper to create a category model instance
def _create_category_model(id: int, name: str) -> UnitOfMeasurementCategoryModel:
    return UnitOfMeasurementCategoryModel(id=id, name=name)

# Helper to create a UoM model instance
def _create_uom_model(
    id: int,
    name: str,
    abbreviation: str,
    category_model: Optional[UnitOfMeasurementCategoryModel] = None,
    description: Optional[str] = None
) -> UnitOfMeasurementModel:
    uom = UnitOfMeasurementModel(
        id=id,
        name=name,
        abbreviation=abbreviation,
        description=description
    )
    if category_model:
        uom.category = category_model # This also sets category_id if relationships are set up
        uom.category_id = category_model.id
    return uom

# --- UnitOfMeasurementBase Tests ---
def test_uom_base_valid_data():
    data = {"name": "Meter", "abbreviation": "m"}
    schema = UnitOfMeasurementBase(**data)
    assert schema.name == data["name"]
    assert schema.abbreviation == data["abbreviation"]
    assert schema.category_id is None # Default

def test_uom_base_with_category_id():
    data = {"name": "Kilogram", "abbreviation": "kg", "category_id": 1}
    schema = UnitOfMeasurementBase(**data)
    assert schema.name == data["name"]
    assert schema.abbreviation == data["abbreviation"]
    assert schema.category_id == 1

def test_uom_base_category_id_none():
    data = {"name": "Watt", "abbreviation": "W", "category_id": None}
    schema = UnitOfMeasurementBase(**data)
    assert schema.category_id is None

def test_uom_base_missing_required_fields():
    with pytest.raises(ValidationError):
        UnitOfMeasurementBase(name="OnlyName") # Abbreviation missing
    with pytest.raises(ValidationError):
        UnitOfMeasurementBase(abbreviation="OnlyAbbr") # Name missing

# --- UnitOfMeasurementCreate Tests ---
def test_uom_create_valid_data():
    data = {"name": "Second", "abbreviation": "s", "description": "Time unit"}
    schema = UnitOfMeasurementCreate(**data)
    assert schema.name == data["name"]
    assert schema.abbreviation == data["abbreviation"]
    assert schema.description == data["description"]
    assert schema.category_id is None

def test_uom_create_with_category_id():
    data = {"name": "Ampere", "abbreviation": "A", "category_id": 2}
    schema = UnitOfMeasurementCreate(**data)
    assert schema.category_id == 2

def test_uom_create_category_id_invalid_type():
    with pytest.raises(ValidationError):
        # category_id should be int
        UnitOfMeasurementCreate(name="Volt", abbreviation="V", category_id="not-an-int")

# --- UnitOfMeasurement (Read Schema) Tests ---
def test_uom_read_from_orm_without_category():
    """Test conversion from ORM model without a category."""
    orm_uom = _create_uom_model(id=1, name="Hertz", abbreviation="Hz")

    schema = UnitOfMeasurement.model_validate(orm_uom) # Pydantic V2
    # schema = UnitOfMeasurement.from_orm(orm_uom) # Pydantic V1

    assert schema.id == orm_uom.id
    assert schema.name == orm_uom.name
    assert schema.abbreviation == orm_uom.abbreviation
    assert schema.category_id is None
    assert schema.category is None
    assert schema.model_config.get('from_attributes') is True

def test_uom_read_from_orm_with_category():
    """Test conversion from ORM model with a linked category."""
    orm_category = _create_category_model(id=10, name="Electrical Units")
    orm_uom = _create_uom_model(id=2, name="Ohm", abbreviation="Ω", category_model=orm_category)

    schema = UnitOfMeasurement.model_validate(orm_uom)

    assert schema.id == orm_uom.id
    assert schema.name == orm_uom.name
    assert schema.abbreviation == orm_uom.abbreviation
    assert schema.category_id == orm_category.id

    assert schema.category is not None
    assert isinstance(schema.category, UnitOfMeasurementCategorySchema)
    assert schema.category.id == orm_category.id
    assert schema.category.name == orm_category.name

def test_uom_read_schema_ensure_config_from_attributes():
    assert UnitOfMeasurement.model_config.get('from_attributes') is True, \
        "UnitOfMeasurement schema must have from_attributes=True in its Config"

# --- UnitOfMeasurementUpdate Tests (example, assuming it exists) ---
def test_uom_update_all_fields_optional():
    """Test that UnitOfMeasurementUpdate allows partial updates."""
    # Empty data should be valid if all fields in Update schema are Optional
    schema_empty = UnitOfMeasurementUpdate()
    assert schema_empty.name is None
    assert schema_empty.abbreviation is None
    assert schema_empty.description is None
    assert schema_empty.category_id is None # Assuming category_id is also optional in Update

    data_partial = {"name": "Kelvin"}
    schema_partial = UnitOfMeasurementUpdate(**data_partial)
    assert schema_partial.name == "Kelvin"
    assert schema_partial.abbreviation is None

    data_partial_cat_id = {"category_id": 5}
    schema_partial_cat = UnitOfMeasurementUpdate(**data_partial_cat_id)
    assert schema_partial_cat.category_id == 5

# Test that category_id on create schema is indeed optional
def test_uom_create_category_id_is_optional():
    data = {"name": "Candela", "abbreviation": "cd"} # No category_id
    schema = UnitOfMeasurementCreate(**data)
    assert schema.name == "Candela"
    assert schema.category_id is None

    data_with_none = {"name": "Mole", "abbreviation": "mol", "category_id": None}
    schema_with_none = UnitOfMeasurementCreate(**data_with_none)
    assert schema_with_none.name == "Mole"
    assert schema_with_none.category_id is None
