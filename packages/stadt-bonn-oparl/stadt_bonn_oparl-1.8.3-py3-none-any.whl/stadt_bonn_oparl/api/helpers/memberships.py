import uuid
from chromadb import Collection
from fastapi import HTTPException
import httpx
import logfire

from stadt_bonn_oparl.api.config import SELF_API_URL
from stadt_bonn_oparl.api.helpers.processors import _process_membership
from stadt_bonn_oparl.api.models import MembershipListResponse, MembershipResponse
from stadt_bonn_oparl.config import UPSTREAM_API_URL


async def _get_membership(
    http_client: httpx.Client, collection: Collection | None, membership_id: str
) -> tuple[bool, MembershipResponse]:
    """Helper function to get a membership by ID from the OParl API."""
    _url = UPSTREAM_API_URL + f"/memberships?id={membership_id}"

    if collection is not None:
        with logfire.span(
            "Checking ChromaDB for membership", membership_id=membership_id
        ):
            _id_ref = uuid.uuid5(uuid.NAMESPACE_URL, str(_url))
            _doc = collection.get(ids=[str(_id_ref)])
            if _doc and _doc["documents"]:
                # If we have a document, return it
                return False, MembershipResponse.model_validate_json(
                    _doc["documents"][0]
                )

    with logfire.span(
        "Fetching membership from OParl API", membership_id=membership_id
    ):
        response = http_client.get(_url, timeout=10.0)

    response = http_client.get(_url)
    if response.status_code == 200:
        _json = response.json()
        _process_membership(_json)
        return True, MembershipResponse(**_json)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch membership {membership_id} information from OParl API",
        )


async def _get_memberships_by_body_id(
    http_client: httpx.Client, body_id: str | int, page: int = 1, size: int = 10
) -> MembershipListResponse:
    """Helper function to get memberships by body ID from the OParl API."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/memberships"

    if not isinstance(body_id, str):
        body_id = str(body_id)

    response = http_client.get(_url + f"?body={body_id}&page={page}&pageSize={size}")
    if response.status_code == 200:
        _json = response.json()

        # check if the object has deleted = True aka not found
        for membership in _json["data"]:
            _process_membership(membership)

        # Convert pagination links to use localhost URLs if they exist
        links = _json.get("links", {})
        converted_links = {}

        for link_name, link_url in links.items():
            if link_url:
                # Replace the upstream domain with localhost but keep the path and query params
                converted_links[link_name] = link_url.replace(
                    "https://www.bonn.sitzung-online.de/public/oparl/memberships",
                    f"{SELF_API_URL}/memberships",
                )
            else:
                converted_links[link_name] = link_url

        return MembershipListResponse(
            data=_json["data"],
            pagination=_json.get("pagination", {}),
            links=converted_links,
        )

    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch memberships with body ID {body_id} from OParl API",
    )


async def _get_memberships_by_person_id(
    http_client: httpx.Client, person_id: int, page: int = 1, size: int = 10
) -> MembershipListResponse:
    """Helper function to get memberships by person ID from the OParl API."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/memberships"

    response = http_client.get(
        _url + f"?person={person_id}&page={page}&pageSize={size}"
    )
    if response.status_code == 200:
        _json = response.json()

        # check if the object has deleted = True aka not found
        for membership in _json["data"]:
            _process_membership(membership)

        # Convert pagination links to use localhost URLs if they exist
        links = _json.get("links", {})
        converted_links = {}

        for link_name, link_url in links.items():
            if link_url:
                # Replace the upstream domain with localhost but keep the path and query params
                converted_links[link_name] = link_url.replace(
                    "https://www.bonn.sitzung-online.de/public/oparl/memberships",
                    f"{SELF_API_URL}/memberships",
                )
            else:
                converted_links[link_name] = link_url

        return MembershipListResponse(
            data=_json["data"],
            pagination=_json.get("pagination", {}),
            links=converted_links,
        )

    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch memberships with person ID {person_id} from OParl API",
    )
