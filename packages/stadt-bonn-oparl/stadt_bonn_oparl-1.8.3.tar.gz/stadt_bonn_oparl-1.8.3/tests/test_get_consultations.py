import json
import httpx
import pytest
from fastapi import HTTPException

from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.helpers.processors import _process_consultation
from stadt_bonn_oparl.api.models import Consultation

http_client = httpx.Client(base_url="https://www.bonn.sitzung-online.de/public/oparl")


@pytest.fixture(autouse=True)
def patch_http_client(monkeypatch):
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data

        def json(self):
            return self._json

    responses = {}

    def set_response(url, status_code, json_data):
        responses[url] = MockResponse(status_code, json_data)

    def fake_get(url, params=None):
        # Build URL with params for matching
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_str}"
        else:
            full_url = url
        return responses.get(full_url, responses.get(url))

    monkeypatch.setattr(http_client, "get", fake_get)
    return set_response


@pytest.fixture
def consultation_fixture():
    """Load the consultation fixture data."""
    with open("tests/fixtures/consultation_2030327_bi_2047329.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_get_consultation_success(patch_http_client, consultation_fixture):
    consultation_id = 2030327
    bi = 2047329
    url = "https://www.bonn.sitzung-online.de/public/oparl/consultations?bi=2047329&id=2030327"

    patch_http_client(url, 200, consultation_fixture)

    is_fresh, result = await _get_consultation(http_client, None, consultation_id, bi)

    assert is_fresh is True
    assert isinstance(result, Consultation)
    assert result.id is not None
    assert result.id_ref is not None
    assert result.role == "Empfehlung"
    assert result.authoritative is False
    assert (
        result.paper_ref
        == "https://www.bonn.sitzung-online.de/public/oparl/papers?id=2021241"
    )
    assert (
        result.meeting_ref
        == "https://www.bonn.sitzung-online.de/public/oparl/meetings?id=2004507"
    )


@pytest.mark.asyncio
async def test_get_consultation_http_error(patch_http_client):
    consultation_id = 2030327
    bi = 2047329
    url = "https://www.bonn.sitzung-online.de/public/oparl/consultations?bi=2047329&id=2030327"

    patch_http_client(url, 500, {})

    with pytest.raises(HTTPException) as excinfo:
        await _get_consultation(http_client, None, consultation_id, bi)

    assert excinfo.value.status_code == 500
    assert (
        f"Failed to fetch consultation {consultation_id} with bi {bi} from OParl API"
        in str(excinfo.value.detail)
    )


@pytest.mark.asyncio
async def test_get_consultation_not_found(patch_http_client):
    consultation_id = 99999
    bi = 99999
    url = "https://www.bonn.sitzung-online.de/public/oparl/consultations?bi=99999&id=99999"

    patch_http_client(url, 200, {})

    with pytest.raises(HTTPException) as excinfo:
        await _get_consultation(http_client, None, consultation_id, bi)

    assert excinfo.value.status_code == 404
    assert f"Consultation with ID {consultation_id} and bi {bi} not found" in str(
        excinfo.value.detail
    )


@pytest.mark.asyncio
async def test_get_consultation_no_id_in_response(patch_http_client):
    consultation_id = 2030327
    bi = 2047329
    url = "https://www.bonn.sitzung-online.de/public/oparl/consultations?bi=2047329&id=2030327"

    # Response without id field
    invalid_data = {
        "type": "https://schema.oparl.org/1.1/Consultation",
        "role": "Empfehlung",
    }

    patch_http_client(url, 200, invalid_data)

    with pytest.raises(HTTPException) as excinfo:
        await _get_consultation(http_client, None, consultation_id, bi)

    assert excinfo.value.status_code == 404
    assert f"Consultation with ID {consultation_id} and bi {bi} not found" in str(
        excinfo.value.detail
    )


@pytest.mark.asyncio
async def test_get_consultation_data_processing(consultation_fixture):
    """Test that the consultation data is properly processed."""
    consultation_id = 2030327
    bi = 2047329
    url = "https://www.bonn.sitzung-online.de/public/oparl/consultations?id=2030327&bi=2047329"
    c = consultation_fixture
    _process_consultation(c)

    con = Consultation.model_validate(c)

    # Verify that processing occurred (_process_consultation was called)
    assert con.paper_ref is not None
    assert isinstance(con.paper_ref, str)

    assert con.paper_ref is not None
    assert isinstance(con.paper_ref, str)

    assert con.organization_ref is not None
    assert isinstance(con.organization_ref, list)
    assert con.organizations is not None
    assert isinstance(con.organizations, list)

    # Verify the UUID was generated
    assert con.id is not None
    assert con.id_ref == url
