from unittest.mock import MagicMock

import httpx
import pytest

from stadt_bonn_oparl.api.helpers import (
    _get_memberships_by_person_id,
)
from stadt_bonn_oparl.api.models import MembershipListResponse


# read json from fixture
@pytest.fixture
def memberships_list_response_fixture():
    """Fixture to provide a mock response for memberships list by person ID."""

    # read JSON from file
    with open("tests/fixtures/memberships_by_person_1997.json", "r") as f:
        import json

        return json.load(f)


@pytest.mark.asyncio
async def test_get_memberships_by_person_id_success(memberships_list_response_fixture):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = memberships_list_response_fixture

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result = await _get_memberships_by_person_id(mock_client, 1997)

    # Assert
    assert isinstance(result, MembershipListResponse)
    assert len(result.data) > 0
    assert result.data[0] is not None
    assert (
        result.data[0].id_ref
        == "https://www.bonn.sitzung-online.de/public/oparl/memberships?id=12376"
    )
    assert isinstance(result.data[0].person_ref, str)
    assert result.data[0].person_ref.startswith("http://localhost:8000/")
    assert result.data[0].person is None
    assert isinstance(result.data[0].organization_ref, str)
    assert result.data[0].organization_ref.startswith("http://localhost:8000/")
    assert result.data[0].organization is None
    print(result)

    # Verify the correct API call was made
    mock_client.get.assert_called_once_with(
        "https://www.bonn.sitzung-online.de/public/oparl/memberships?person=1997&page=1&pageSize=10"
    )


@pytest.mark.asyncio
async def test_get_memberships_by_person_id_with_custom_pagination(
    memberships_list_response_fixture,
):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = memberships_list_response_fixture

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result = await _get_memberships_by_person_id(mock_client, 1997, page=2, size=20)

    # Assert
    assert isinstance(result, MembershipListResponse)
    assert len(result.data) > 0

    # Verify the correct API call was made with custom pagination
    mock_client.get.assert_called_once_with(
        "https://www.bonn.sitzung-online.de/public/oparl/memberships?person=1997&page=2&pageSize=20"
    )


@pytest.mark.asyncio
async def test_get_memberships_by_person_id_api_failure():
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await _get_memberships_by_person_id(mock_client, 1997)

    assert "Failed to fetch memberships with person ID 1997 from OParl API" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_get_memberships_by_person_id_verifies_all_memberships_processed(
    memberships_list_response_fixture,
):
    # Arrange
    mock_response_json = memberships_list_response_fixture

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_json

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result = await _get_memberships_by_person_id(mock_client, 1997)

    # Assert
    # Verify we got all memberships from the fixture
    assert len(result.data) == len(mock_response_json["data"])

    # Check that all memberships have person_ref as 1997
    for membership in result.data:
        assert "1997" in membership.person_ref

    # Verify pagination info is preserved
    assert result.pagination["totalElements"] == 37
    assert result.pagination["elementsPerPage"] == 20
    assert result.pagination["currentPage"] == 1
    assert result.pagination["totalPages"] == 2

    # Verify links are rewritten to use localhost
    assert "self" in result.links
    assert "next" in result.links
    assert "last" in result.links
    assert result.links["self"].startswith("http://localhost:8000/memberships")
    assert result.links["next"].startswith("http://localhost:8000/memberships")
    assert result.links["last"].startswith("http://localhost:8000/memberships")
