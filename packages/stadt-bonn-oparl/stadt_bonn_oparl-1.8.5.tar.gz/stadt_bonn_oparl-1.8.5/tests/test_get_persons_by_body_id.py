from unittest.mock import MagicMock

import httpx
import pytest

from stadt_bonn_oparl.api.helpers import (
    _get_persons_by_body_id,
)
from stadt_bonn_oparl.api.models import PersonListResponse


# read json from fixture
@pytest.fixture
def persons_list_response_fixture():
    """Fixture to provide a mock response for persons list."""

    # read JSON from file
    with open("tests/fixtures/person_by_body_id_1.json", "r") as f:
        import json

        return json.load(f)


@pytest.mark.asyncio
async def test_get_persons_by_body_id_success(persons_list_response_fixture):
    # Arrange
    mock_response_json = persons_list_response_fixture

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_json

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result, fresh_persons = await _get_persons_by_body_id(mock_client, None, 1)

    # Assert
    assert isinstance(result, PersonListResponse)
    assert isinstance(fresh_persons, list)
    assert len(result.data) > 0
    assert result.data[0] is not None
    assert (
        result.data[0].id_ref
        == "https://www.bonn.sitzung-online.de/public/oparl/persons?id=13129"
    )
    assert result.data[0].name == "Arezu Abdulkarim Abdullah"
    assert result.data[0].familyName == "Abdullah"
    assert result.data[0].givenName == "Arezu Abdulkarim"
    assert result.data[0].gender == "female"
    assert result.data[0].affix == "Mitglied des Integrationsrat"


@pytest.mark.asyncio
async def test_get_persons_by_body_id_with_pagination():
    # Arrange
    mock_response_json = {
        "data": [
            {
                "id": "https://www.bonn.sitzung-online.de/public/oparl/persons?id=1",
                "type": "https://schema.oparl.org/1.1/Person",
                "name": "Test Person",
                "familyName": "Person",
                "givenName": "Test",
                "gender": "unknown",
                "status": ["Politik"],
                "created": "2025-06-08T04:40:12+02:00",
                "modified": "2025-06-08T04:40:12+02:00",
                "deleted": False,
            }
        ],
        "pagination": {
            "totalElements": 100,
            "elementsPerPage": 1,
            "currentPage": 2,
            "totalPages": 100,
        },
        "links": {
            "self": "http://localhost:8000/persons?body=1&page=2",
            "first": "http://localhost:8000/persons?body=1&page=1",
            "prev": "http://localhost:8000/persons?body=1&page=1",
            "next": "http://localhost:8000/persons?body=1&page=3",
            "last": "http://localhost:8000/persons?body=1&page=100",
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_json

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result, fresh_persons = await _get_persons_by_body_id(
        mock_client, None, 1, page=2, size=1
    )

    # Assert
    assert isinstance(result, PersonListResponse)
    assert isinstance(fresh_persons, list)
    assert len(result.data) == 1
    assert result.pagination["currentPage"] == 2
    assert result.pagination["totalElements"] == 100

    # Check that links are converted to localhost
    assert result.links["self"].startswith("http://localhost:8000/")
    assert result.links["next"].startswith("http://localhost:8000/")

    # Verify correct API call was made
    mock_client.get.assert_called_once_with(
        "https://www.bonn.sitzung-online.de/public/oparl/persons?body=1&page=2&pageSize=1"
    )


@pytest.mark.asyncio
async def test_get_persons_by_body_id_http_error():
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await _get_persons_by_body_id(mock_client, None, 1)

    assert "Failed to fetch persons with body ID 1 from OParl API" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_get_persons_by_body_id_string_body_id():
    # Arrange
    mock_response_json = {"data": [], "pagination": {}, "links": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_json

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result, fresh_persons = await _get_persons_by_body_id(mock_client, None, 123)

    # Assert
    assert isinstance(result, PersonListResponse)
    assert isinstance(fresh_persons, list)
    mock_client.get.assert_called_once_with(
        "https://www.bonn.sitzung-online.de/public/oparl/persons?body=123&page=1&pageSize=10"
    )


@pytest.mark.asyncio
async def test_get_persons_by_body_id_integer_body_id():
    # Arrange
    mock_response_json = {"data": [], "pagination": {}, "links": {}}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_json

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    # Act
    result, fresh_persons = await _get_persons_by_body_id(mock_client, None, 456)

    # Assert
    assert isinstance(result, PersonListResponse)
    assert isinstance(fresh_persons, list)
    mock_client.get.assert_called_once_with(
        "https://www.bonn.sitzung-online.de/public/oparl/persons?body=456&page=1&pageSize=10"
    )
