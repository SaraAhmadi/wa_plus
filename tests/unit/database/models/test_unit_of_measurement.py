import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # If we test FK constraints, etc.

from app.database.models import UnitOfMeasurement, UnitOfMeasurementCategory

# Assuming a db_session fixture similar to the one described in the category model tests

def test_create_uom_without_category(db_session: Session):
    """Test creating a UnitOfMeasurement without a category."""
    uom_name = "Meter"
    uom_abbr = "m"
    uom = UnitOfMeasurement(name=uom_name, abbreviation=uom_abbr, description="Length unit")

    db_session.add(uom)
    db_session.commit()
    db_session.refresh(uom)

    assert uom.id is not None
    assert uom.name == uom_name
    assert uom.abbreviation == uom_abbr
    assert uom.category_id is None
    assert uom.category is None

def test_create_uom_with_category_via_object(db_session: Session):
    """Test creating a UnitOfMeasurement and associating it with a category object."""
    category = UnitOfMeasurementCategory(name="Length")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category) # Get category.id

    uom = UnitOfMeasurement(name="Kilometer", abbreviation="km", category=category)
    db_session.add(uom)
    db_session.commit()
    db_session.refresh(uom)
    db_session.refresh(category) # Refresh category to see back-population

    assert uom.id is not None
    assert uom.category_id == category.id
    assert uom.category == category
    assert uom in category.units_of_measurement

def test_create_uom_with_category_via_id(db_session: Session):
    """Test creating a UnitOfMeasurement and associating it via category_id."""
    category = UnitOfMeasurementCategory(name="Area")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    uom = UnitOfMeasurement(name="Square Meter", abbreviation="m2", category_id=category.id)
    db_session.add(uom)
    db_session.commit()
    db_session.refresh(uom)

    assert uom.id is not None
    assert uom.category_id == category.id
    assert uom.category is not None # SQLAlchemy should load it
    assert uom.category.name == "Area"
    assert uom in category.units_of_measurement


def test_uom_category_relationship_loads_correctly(db_session: Session):
    """Test that the category relationship loads after fetching a UoM."""
    category = UnitOfMeasurementCategory(name="Volume")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    uom_id = UnitOfMeasurement(name="Cubic Meter", abbreviation="m3", category_id=category.id)
    db_session.add(uom_id)
    db_session.commit()
    uom_id = uom_id.id # Store the ID

    # Clear session to simulate fetching from DB in a new context
    # db_session.expunge_all() # or db_session.close(), then get a new session
    # For a simple SQLite in-memory test, direct refetch might be okay,
    # but for true lazy load testing, a new session is better.
    # Let's assume for now direct fetch is sufficient for this unit test structure.

    fetched_uom = db_session.query(UnitOfMeasurement).filter_by(id=uom_id).one()

    assert fetched_uom is not None
    assert fetched_uom.category is not None
    assert fetched_uom.category.id == category.id
    assert fetched_uom.category.name == "Volume"

def test_uom_repr_with_category(db_session: Session):
    """Test the __repr__ method of UnitOfMeasurement when category is present."""
    category = UnitOfMeasurementCategory(name="Time")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    uom = UnitOfMeasurement(name="Second", abbreviation="s", category_id=category.id)
    db_session.add(uom)
    db_session.commit()
    db_session.refresh(uom)

    expected_repr = f"<UnitOfMeasurement(id={uom.id}, abbreviation='s', category_id={category.id})>"
    assert repr(uom) == expected_repr

def test_uom_repr_without_category(db_session: Session):
    """Test the __repr__ method of UnitOfMeasurement when category is not present."""
    uom = UnitOfMeasurement(name="Count", abbreviation="count")
    db_session.add(uom)
    db_session.commit()
    db_session.refresh(uom)

    expected_repr = f"<UnitOfMeasurement(id={uom.id}, abbreviation='count', category_id=None)>"
    assert repr(uom) == expected_repr

def test_uom_category_id_fk_constraint(db_session: Session):
    """Test the foreign key constraint on category_id (optional, needs specific DB setup)."""
    # This test usually works best in integration tests with a real DB that enforces FKs.
    # SQLite by default does NOT enforce FKs unless PRAGMA foreign_keys=ON is issued per connection.
    # Assuming the db_session fixture might handle this, or this test might pass vacuously on default SQLite.

    # Try to create a UoM with a non-existent category_id
    with pytest.raises(IntegrityError):
        uom = UnitOfMeasurement(name="OrphanUnit", abbreviation="orphan", category_id=99999) # 99999 does not exist
        db_session.add(uom)
        db_session.commit() # This is where the FK constraint (if enforced) would typically fail

    # It's important to rollback after an IntegrityError if the session is to be reused
    db_session.rollback()

# Placeholder for other UoM specific tests if any (e.g. name/abbreviation constraints)
def test_uom_name_abbreviation_constraints(db_session: Session):
    """Test constraints on name and abbreviation for UnitOfMeasurement."""
    # Name not nullable
    with pytest.raises(IntegrityError):
        uom = UnitOfMeasurement(name=None, abbreviation="x")
        db_session.add(uom)
        db_session.commit()
    db_session.rollback()

    # Abbreviation not nullable
    with pytest.raises(IntegrityError):
        uom = UnitOfMeasurement(name="Test", abbreviation=None)
        db_session.add(uom)
        db_session.commit()
    db_session.rollback()

    # Name unique
    uom1 = UnitOfMeasurement(name="UniqueName", abbreviation="un1")
    db_session.add(uom1)
    db_session.commit()
    with pytest.raises(IntegrityError):
        uom2 = UnitOfMeasurement(name="UniqueName", abbreviation="un2")
        db_session.add(uom2)
        db_session.commit()
    db_session.rollback()

    # Abbreviation unique
    uom3 = UnitOfMeasurement(name="Another Name", abbreviation="ua1")
    db_session.add(uom3)
    db_session.commit()
    with pytest.raises(IntegrityError):
        uom4 = UnitOfMeasurement(name="Yet Another Name", abbreviation="ua1")
        db_session.add(uom4)
        db_session.commit()
    db_session.rollback()
