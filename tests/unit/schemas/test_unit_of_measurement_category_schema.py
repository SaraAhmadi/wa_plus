import pytest
from pydantic import ValidationError

from app.schemas.unit_of_measurement_category import (
    UnitOfMeasurementCategory,
    UnitOfMeasurementCategoryCreate,
    UnitOfMeasurementCategoryBase
)
# Import the ORM model to test 'from_orm' or 'model_validate'
from app.database.models import UnitOfMeasurementCategory as UnitOfMeasurementCategoryModel

def test_uom_category_base_valid():
    """Test UnitOfMeasurementCategoryBase with valid data."""
    data = {"name": "Area"}
    schema = UnitOfMeasurementCategoryBase(**data)
    assert schema.name == data["name"]

def test_uom_category_base_missing_name():
    """Test UnitOfMeasurementCategoryBase with missing name."""
    with pytest.raises(ValidationError) as exc_info:
        UnitOfMeasurementCategoryBase() # name is required
    assert "name" in str(exc_info.value)

def test_uom_category_create_valid():
    """Test UnitOfMeasurementCategoryCreate with valid data."""
    data = {"name": "Volume"}
    schema = UnitOfMeasurementCategoryCreate(**data)
    assert schema.name == data["name"]

def test_uom_category_create_missing_name():
    """Test UnitOfMeasurementCategoryCreate with missing name."""
    with pytest.raises(ValidationError) as exc_info:
        UnitOfMeasurementCategoryCreate() # name is required
    assert "name" in str(exc_info.value)

def test_uom_category_read_schema_from_orm():
    """Test UnitOfMeasurementCategory (read schema) conversion from ORM model."""
    orm_model = UnitOfMeasurementCategoryModel(id=1, name="Pressure")

    # For Pydantic V2, use model_validate. For V1, from_orm.
    # Assuming Pydantic V2 as it's more current.
    # If using Pydantic V1, replace with: schema = UnitOfMeasurementCategory.from_orm(orm_model)
    schema = UnitOfMeasurementCategory.model_validate(orm_model)

    assert schema.id == orm_model.id
    assert schema.name == orm_model.name
    assert schema.model_config.get('from_attributes') is True


def test_uom_category_read_schema_from_orm_invalid_type():
    """Test UnitOfMeasurementCategory conversion with incompatible object."""
    class NotACategory:
        pass

    with pytest.raises(ValidationError): # Pydantic V2 raises ValidationError
        UnitOfMeasurementCategory.model_validate(NotACategory())

def test_uom_category_base_extra_fields():
    """Test UnitOfMeasurementCategoryBase with extra fields (should be ignored by default)."""
    data = {"name": "Temperature", "extra_field": "should_be_ignored"}
    schema = UnitOfMeasurementCategoryBase(**data)
    assert schema.name == "Temperature"
    assert not hasattr(schema, "extra_field")

def test_uom_category_read_schema_data_integrity():
    """Test UnitOfMeasurementCategory with various data types for id."""
    # Valid: id is int
    orm_model_valid = UnitOfMeasurementCategoryModel(id=10, name="Energy")
    schema_valid = UnitOfMeasurementCategory.model_validate(orm_model_valid)
    assert schema_valid.id == 10

    # Invalid: id is string (Pydantic should try to coerce or fail if strict)
    # If your model's id is strictly int, this might pass due to coercion.
    # For testing strictness, you might need a strict version of the schema.
    # This test depends on whether 'id: int' in Pydantic coerces "20" to 20.
    # Pydantic v2 generally coerces.
    data_with_str_id = {"id": "20", "name": "Power"}
    schema_coerced = UnitOfMeasurementCategory(**data_with_str_id)
    assert schema_coerced.id == 20

    # Invalid: id is None (if not Optional)
    # The 'id: int' field in UnitOfMeasurementCategory is not Optional.
    with pytest.raises(ValidationError) as exc_info:
        UnitOfMeasurementCategory(id=None, name="Frequency")
    assert "id" in str(exc_info.value).lower() # Check that 'id' field is mentioned in the error
    assert "none is not an allowed value" in str(exc_info.value).lower() or "type_error.integer" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info_name:
        UnitOfMeasurementCategory(id=1, name=None) # name is also not Optional
    assert "name" in str(exc_info_name.value).lower()

# Ensure from_attributes (or orm_mode) is True in the schema for from_orm/model_validate to work
def test_uom_category_config():
    assert UnitOfMeasurementCategory.model_config.get('from_attributes') is True

# Test that the create schema doesn't have an id field
def test_uom_category_create_no_id_field():
    data = {"name": "Luminance"}
    schema = UnitOfMeasurementCategoryCreate(**data)
    assert not hasattr(schema, "id")

    # If you try to pass 'id' to Create schema, it should ideally ignore it or raise error
    # depending on Pydantic config (extra='forbid' or 'ignore').
    # By default, Pydantic v2 ignores extra fields.
    data_with_id = {"name": "Luminous Flux", "id": 123}
    schema_with_id = UnitOfMeasurementCategoryCreate(**data_with_id)
    assert schema_with_id.name == "Luminous Flux"
    assert not hasattr(schema_with_id, "id")
