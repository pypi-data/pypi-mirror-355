import uuid
from typing import Optional

import httpx
import logfire
from chromadb import Collection
from fastapi import HTTPException

from stadt_bonn_oparl.api.config import SELF_API_URL, UPSTREAM_API_URL
from stadt_bonn_oparl.api.helpers.processors import (
    _process_organization,
    _process_paper,
)
from stadt_bonn_oparl.api.models import (
    FileResponse,
    OrganizationListResponse,
    OrganizationResponse,
    PaperListResponse,
    PaperResponse,
)
from stadt_bonn_oparl.models import OrganizationType


async def _get_organization_all(
    http_client: httpx.Client,
) -> OrganizationListResponse:
    """Helper function to get all organizations from the OParl API."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/organizations"

    all_organizations = []
    current_url: Optional[str] = _url

    while current_url:
        response = http_client.get(current_url, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch organizations from OParl API",
            )

        _json = response.json()

        # Process each organization in this page
        for org in _json["data"]:
            _process_organization(org)
            logfire.info(f"Processing organization: {org}")
            all_organizations.append(OrganizationResponse(**org))

        # Check for next page
        current_url = None
        if "links" in _json and "next" in _json["links"]:
            current_url = _json["links"]["next"]

    # Return all organizations with updated pagination info
    return OrganizationListResponse(
        data=all_organizations, pagination={"total": len(all_organizations)}, links={}
    )


async def _get_organization_by_id(
    http_client: httpx.Client,
    organization_id: int,
    organization_type: OrganizationType = OrganizationType.gr,  # default to "gr" (Gremium)
) -> OrganizationResponse | None:
    """Helper function to get a organization by ID from the OParl API."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/organizations"

    response = http_client.get(
        _url + f"?typ={organization_type.name}&id={organization_id}"
    )

    if response.status_code == 200:
        _json = response.json()

        # check if the organization is deleted
        if _json.get("deleted", False):
            raise HTTPException(
                status_code=404,
                detail=f"Organization with ID {organization_id} not found in OParl API",
            )

        _process_organization(_json)
        return OrganizationResponse(**_json)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch organization {organization_id} information from OParl API",
        )


async def _get_organization_by_body_id(
    http_client: httpx.Client, body_id: str | int
) -> OrganizationListResponse:
    """Helper function to get organizations by body ID from the OParl API."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/organizations"

    if not isinstance(body_id, str):
        body_id = str(body_id)

    all_organizations = []
    current_url: Optional[str] = _url + f"?typ=gr&body={body_id}"

    while current_url:
        response = http_client.get(current_url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch organization with body ID {body_id} from OParl API",
            )

        _json = response.json()

        # Process each organization in this page
        for org in _json["data"]:
            _process_organization(org)
            all_organizations.append(OrganizationResponse(**org))

        # Check for next page
        current_url = None
        if "links" in _json and "next" in _json["links"]:
            current_url = _json["links"]["next"]

    # Return all organizations with updated pagination info
    return OrganizationListResponse(
        data=all_organizations, pagination={"total": len(all_organizations)}, links={}
    )


async def _get_paper_by_id(
    http_client: httpx.Client, collection: Collection | None, paper_id: int
) -> PaperResponse:
    """Helper function to get a paper by ID from the OParl API."""
    _url = UPSTREAM_API_URL + f"/papers?id={paper_id}"

    if collection is not None:
        with logfire.span("Checking ChromaDB for paper", paper_id=paper_id):
            paper_id_ref = uuid.uuid5(uuid.NAMESPACE_URL, str(_url))
            paper = collection.get(ids=[str(paper_id_ref)])
            if paper and paper["documents"]:
                # If we have a document, return it
                return PaperResponse.model_validate_json(paper["documents"][0])

    with logfire.span("Fetching paper from OParl API", paper_id=paper_id):
        response = http_client.get(_url, timeout=10.0)

    if response.status_code == 200:
        _json = response.json()

        # check if the object has deleted = True aka not found
        if _json.get("deleted", False):
            raise HTTPException(
                status_code=404,
                detail=f"Paper with ID {paper_id} not found in OParl API",
            )

        _process_paper(_json)
        return PaperResponse(**_json)

    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch paper with ID {paper_id} from OParl API",
    )


async def _get_papers_all(
    http_client: httpx.Client,
    page: int = 1,
    page_size: int = 10,
) -> PaperListResponse:
    """Helper function to get papers from the OParl API with pagination support."""
    _url = "https://www.bonn.sitzung-online.de/public/oparl/papers"

    # Build query parameters for pagination
    params = f"?page={page}&pageSize={page_size}"
    request_url = _url + params

    response = http_client.get(request_url, timeout=10.0)
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch papers from OParl API",
        )

    _json = response.json()

    # Process each paper in this page
    for paper in _json["data"]:
        _process_paper(paper)

    # Convert pagination links to use localhost URLs if they exist
    links = _json.get("links", {})
    converted_links = {}

    for link_name, link_url in links.items():
        if link_url:
            # Replace the upstream domain with localhost but keep the path and query params
            converted_links[link_name] = link_url.replace(
                "https://www.bonn.sitzung-online.de/public/oparl/papers",
                f"{SELF_API_URL}/papers",
            )
        else:
            converted_links[link_name] = link_url

    return PaperListResponse(
        data=[PaperResponse(**paper) for paper in _json["data"]],
        pagination=_json.get("pagination", {}),
        links=converted_links,
    )


async def _get_file_by_id(
    http_client: httpx.Client, file_id: int, dtyp: int = 130
) -> FileResponse:
    """Helper function to get a file by ID from the OParl API."""
    _url = UPSTREAM_API_URL + f"/files?id={file_id}&dtyp={dtyp}"

    response = http_client.get(_url, timeout=10.0)
    if response.status_code == 200:
        _json = response.json()

        # check if the object has deleted = True aka not found
        if _json.get("deleted", False):
            raise HTTPException(
                status_code=404,
                detail=f"File with ID {file_id} not found in OParl API",
            )

        # Process reference fields to convert URLs from upstream to self API
        # Process agendaItem references
        if "agendaItem" in _json and _json["agendaItem"]:
            _json["agendaItem_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL)
                for url in _json["agendaItem"]
            ]
        else:
            _json["agendaItem_ref"] = None
        _json["agendaItem"] = None

        # Process meeting reference
        _json["meeting_ref"] = _json.get("meeting", None)
        if _json["meeting_ref"]:
            _json["meeting_ref"] = _json["meeting_ref"].replace(
                UPSTREAM_API_URL, SELF_API_URL
            )
        _json["meeting"] = None

        # Process paper reference
        _json["paper_ref"] = _json.get("paper", None)
        if _json["paper_ref"]:
            _json["paper_ref"] = _json["paper_ref"].replace(
                UPSTREAM_API_URL, SELF_API_URL
            )
        _json["paper"] = None

        return FileResponse(**_json)

    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch file with ID {file_id} from OParl API",
    )
