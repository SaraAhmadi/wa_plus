import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models import UnitOfMeasurementCategory # Adjusted import path

# Assuming a fixture like this exists in conftest.py:
# @pytest.fixture
# def db_session():
#     # Setup in-memory SQLite or test DB session
#     from sqlalchemy import create_engine
#     from app.database.models.base_model import Base
#     engine = create_engine("sqlite:///:memory:")
#     Base.metadata.create_all(engine)
#     session = Session(engine)
#     try:
#         yield session
#     finally:
#         session.close()
#         Base.metadata.drop_all(engine)


def test_create_unit_of_measurement_category(db_session: Session):
    """Test basic creation of UnitOfMeasurementCategory."""
    category_name = "Weight"
    category = UnitOfMeasurementCategory(name=category_name)

    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    assert category.id is not None
    assert category.name == category_name
    assert "UnitOfMeasurementCategory" in repr(category)
    assert category_name in repr(category)

def test_uom_category_name_not_nullable(db_session: Session):
    """Test that the name field cannot be null."""
    with pytest.raises(IntegrityError):
        category = UnitOfMeasurementCategory(name=None)
        db_session.add(category)
        db_session.commit() # IntegrityError for NOT NULL is usually raised on commit

def test_uom_category_name_unique(db_session: Session):
    """Test that the name field is unique."""
    category_name = "Length"
    category1 = UnitOfMeasurementCategory(name=category_name)
    db_session.add(category1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        category2 = UnitOfMeasurementCategory(name=category_name)
        db_session.add(category2)
        db_session.commit() # IntegrityError for UNIQUE is usually raised on commit

# Example of how one might test __repr__ more specifically if needed
def test_uom_category_repr(db_session: Session):
    category = UnitOfMeasurementCategory(name="Volume")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    expected_repr = f"<UnitOfMeasurementCategory(id={category.id}, name='Volume')>"
    assert repr(category) == expected_repr
