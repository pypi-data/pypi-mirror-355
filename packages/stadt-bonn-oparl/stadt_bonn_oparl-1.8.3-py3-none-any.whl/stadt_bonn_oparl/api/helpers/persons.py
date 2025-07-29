import uuid

import httpx
import logfire
from chromadb import Collection
from fastapi import HTTPException

from stadt_bonn_oparl.api.config import SELF_API_URL, UPSTREAM_API_URL
from stadt_bonn_oparl.api.helpers.processors import _process_person
from stadt_bonn_oparl.api.models import PersonListResponse, PersonResponse


async def _get_person(
    http_client: httpx.Client, collection: Collection | None, person_id: int | str
) -> tuple[bool, PersonResponse]:
    """Helper function to get a person by ID from the OParl API."""
    _url = UPSTREAM_API_URL + f"/persons?id={person_id}"

    # TODO: refactor
    if isinstance(person_id, int):
        # Convert integer ID to string for URL consistency
        person_id = str(person_id)

    if collection is not None:
        with logfire.span("Checking ChromaDB for person", person_id=person_id):
            _id_ref = uuid.uuid5(uuid.NAMESPACE_URL, str(_url))
            _doc = collection.get(ids=[str(_id_ref)])
            if _doc and _doc["documents"]:
                # If we have a document, return it
                return False, PersonResponse.model_validate_json(_doc["documents"][0])

    with logfire.span("Fetching person from OParl API", person_id=person_id):
        response = http_client.get(_url, timeout=10.0)

    if response.status_code == 200:
        _json = response.json()

        # check if the person is deleted
        if _json.get("deleted", False):
            raise HTTPException(
                status_code=404,
                detail=f"Person with ID {person_id} not found in OParl API",
            )

        _process_person(_json)
        return True, PersonResponse(**_json)

    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch person {person_id} information from OParl API",
    )


async def _get_persons_by_body_id(
    http_client: httpx.Client,
    collection: Collection | None,
    body_id: int,
    page: int = 1,
    size: int = 10,
) -> tuple[PersonListResponse, list[PersonResponse]]:
    """Helper function to get persons by body ID from the OParl API."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/persons"

    response = http_client.get(
        _url + f"?body={body_id}&page={page}&pageSize={size}", timeout=30.0
    )
    if response.status_code == 200:
        _json = response.json()

        # Process each person in the response and check ChromaDB
        fresh_persons = []
        for person_data in _json["data"]:
            _process_person(person_data)
            person_obj = PersonResponse(**person_data)

            # Check if person already exists in ChromaDB
            if collection is not None:
                with logfire.span(
                    "Checking ChromaDB for person", person_id=person_obj.id
                ):
                    _id_ref = uuid.uuid5(uuid.NAMESPACE_URL, str(person_obj.id_ref))
                    _doc = collection.get(ids=[str(_id_ref)])
                    if not (_doc and _doc["documents"]):
                        # Person not in ChromaDB, mark for upserting
                        fresh_persons.append(person_obj)

        # Convert pagination links to use localhost URLs if they exist
        links = _json.get("links", {})
        converted_links = {}

        for link_name, link_url in links.items():
            if link_url:
                # Replace the upstream domain with localhost but keep the path and query params
                converted_links[link_name] = link_url.replace(
                    "https://www.bonn.sitzung-online.de/public/oparl/persons",
                    f"{SELF_API_URL}/persons",
                )
            else:
                converted_links[link_name] = link_url

        response_obj = PersonListResponse(
            data=_json["data"],
            pagination=_json.get("pagination", {}),
            links=converted_links,
        )

        return response_obj, fresh_persons

    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch persons with body ID {body_id} from OParl API",
    )
