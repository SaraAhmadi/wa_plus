```python
import pytest
from typing import Dict, List
from httpx import AsyncClient
from fastapi import status

from app.schemas.unit_of_measurement_category import (
    UnitOfMeasurementCategory as UnitOfMeasurementCategorySchema,
    UnitOfMeasurementCategoryCreate as UnitOfMeasurementCategoryCreateSchema
)
# Assuming conftest.py provides test_client, db_session, normal_user_token_headers

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

BASE_URL = "/api/v1/unit-of-measurement-categories"

async def test_create_uom_category_success(
    test_client: AsyncClient, normal_user_token_headers: Dict[str, str]
):
    category_data = {"name": "Length"}
    response = await test_client.post(
        BASE_URL + "/",
        json=category_data,
        headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_category = response.json()
    assert created_category["name"] == category_data["name"]
    assert "id" in created_category

async def test_create_uom_category_duplicate_name(
    test_client: AsyncClient, normal_user_token_headers: Dict[str, str]
):
    category_data = {"name": "Area"} # Use a unique name for first creation
    # First creation
    response = await test_client.post(
        BASE_URL + "/",
        json=category_data,
        headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Attempt to create again with the same name
    response_duplicate = await test_client.post(
        BASE_URL + "/",
        json=category_data,
        headers=normal_user_token_headers
    )
    assert response_duplicate.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response_duplicate.json()["detail"]

async def test_create_uom_category_unauthenticated(
    test_client: AsyncClient
):
    category_data = {"name": "Volume"}
    response = await test_client.post(BASE_URL + "/", json=category_data) # No headers
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # or 403 if Depends(get_current_user) is strict

async def test_read_uom_categories_empty(test_client: AsyncClient):
    # This test assumes a clean database state or that categories created by other tests are not visible/cleaned up.
    # If tests run in parallel or if the DB is not reset per test, this might be flaky.
    # For now, we assume test_client provides a clean context for GETs before POSTs in *this* test file.
    # To be more robust, one might clear data in setup or use a specific tag for this test.

    # A better approach for "empty" would be to ensure no items are created *within this test's scope*
    # and then check. If other tests created items, this test would need to account for them or have
    # true DB isolation. Let's assume other tests clean up after themselves or run in isolated dbs.

    # First, ensure we are dealing with a potentially "dirty" list by getting all.
    all_items_response = await test_client.get(BASE_URL + "/")
    all_items = all_items_response.json()

    # This test is tricky without proper DB cleanup between tests.
    # For now, we'll just check if the endpoint works.
    # A true "empty" state test is better with a guaranteed fresh DB.
    # If this is the *first* test to run against this endpoint, it might be empty.
    # Otherwise, we just check it returns a list.
    assert all_items_response.status_code == status.HTTP_200_OK
    assert isinstance(all_items, list)
    # We cannot assert all_items == [] reliably without inter-test DB state management.

async def test_read_uom_categories_with_items(
    test_client: AsyncClient, normal_user_token_headers: Dict[str, str]
):
    # Create a couple of categories
    cat1_data = {"name": "Weight"}
    res1 = await test_client.post(BASE_URL + "/", json=cat1_data, headers=normal_user_token_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    cat2_data = {"name": "Time"}
    res2 = await test_client.post(BASE_URL + "/", json=cat2_data, headers=normal_user_token_headers)
    assert res2.status_code == status.HTTP_201_CREATED

    response = await test_client.get(BASE_URL + "/")
    assert response.status_code == status.HTTP_200_OK
    categories = response.json()

    # Check if the created names are present in the response
    names_in_response = [cat["name"] for cat in categories]
    assert cat1_data["name"] in names_in_response
    assert cat2_data["name"] in names_in_response
    # We make it >=2 because other tests might have added "Length", "Area", etc.
    # For more precise count, DB should be reset for each test or test collection.
    assert len(categories) >= 2


async def test_read_uom_categories_pagination(
    test_client: AsyncClient, normal_user_token_headers: Dict[str, str]
):
    # Ensure a known number of items for pagination, beyond existing ones.
    # Get current count
    initial_response = await test_client.get(BASE_URL + "/")
    initial_count = len(initial_response.json())

    base_names = ["Speed", "Pressure", "Energy"]
    created_ids = []
    for i, name in enumerate(base_names):
        # Ensure unique names if tests run multiple times or don't clean up
        unique_name = f"{name}_{i}"
        res = await test_client.post(BASE_URL + "/", json={"name": unique_name}, headers=normal_user_token_headers)
        assert res.status_code == status.HTTP_201_CREATED
        created_ids.append(res.json()["id"])

    total_expected_after_additions = initial_count + len(base_names)

    # Test limit: get only the first of our new items (or overall if initial_count was 0)
    response_limit_1 = await test_client.get(f"{BASE_URL}/?limit=1")
    assert response_limit_1.status_code == status.HTTP_200_OK
    data_limit_1 = response_limit_1.json()
    assert len(data_limit_1) == 1
    first_item_name_limit_1 = data_limit_1[0]["name"]

    # Test skip and limit: skip 1, get 1. This should be the second item.
    # The skip is global, so it skips items that might have existed before this test too.
    response_skip_1_limit_1 = await test_client.get(f"{BASE_URL}/?skip=1&limit=1")
    assert response_skip_1_limit_1.status_code == status.HTTP_200_OK
    data_skip_1_limit_1 = response_skip_1_limit_1.json()
    assert len(data_skip_1_limit_1) == 1
    second_item_name_skip_1 = data_skip_1_limit_1[0]["name"]

    assert first_item_name_limit_1 != second_item_name_skip_1

    # Check total count with a large limit to see if all items are there
    response_all = await test_client.get(f"{BASE_URL}/?limit={total_expected_after_additions + 10}")
    assert len(response_all.json()) == total_expected_after_additions


async def test_read_uom_category_by_id_success(
    test_client: AsyncClient, normal_user_token_headers: Dict[str, str]
):
    category_data = {"name": "Power"}
    create_response = await test_client.post(
        BASE_URL + "/",
        json=category_data,
        headers=normal_user_token_headers
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_category_id = create_response.json()["id"]

    response = await test_client.get(f"{BASE_URL}/{created_category_id}")
    assert response.status_code == status.HTTP_200_OK
    retrieved_category = response.json()
    assert retrieved_category["id"] == created_category_id
    assert retrieved_category["name"] == category_data["name"]

async def test_read_uom_category_by_id_not_found(test_client: AsyncClient):
    non_existent_id = 999999 # Assuming this ID will not exist
    response = await test_client.get(f"{BASE_URL}/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]

```
