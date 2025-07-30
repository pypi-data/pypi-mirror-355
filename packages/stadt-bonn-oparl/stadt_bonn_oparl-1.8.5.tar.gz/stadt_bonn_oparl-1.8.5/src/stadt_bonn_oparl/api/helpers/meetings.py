import uuid
import httpx
import logfire
from chromadb import Collection
from fastapi import HTTPException
from loguru import logger

from stadt_bonn_oparl.api.config import UPSTREAM_API_URL
from stadt_bonn_oparl.api.helpers.processors import _process_meeting
from stadt_bonn_oparl.api.models import MeetingListResponse, MeetingResponse
from stadt_bonn_oparl.models import OrganizationType


async def _get_all_meetings(
    http_client: httpx.Client,
    page: int = 1,
    limit: int = 5,
) -> MeetingListResponse:
    """Helper function to get all meetings from the OParl API. This will always fetch the latest data from the upstream OParl API."""
    url = f"{UPSTREAM_API_URL}/meetings"
    params = {"page": page, "limit": limit}

    with logfire.span("Fetching meetings from upstream OParl API"):
        response = http_client.get(url, params=params, timeout=60.0)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch meetings from upstream OParl API",
        )

    meetings_data = response.json()

    if not meetings_data or "data" not in meetings_data:
        raise HTTPException(
            status_code=404,
            detail="No meetings found",
        )

    for meeting in meetings_data["data"]:
        _process_meeting(meeting)

    # ok, we got the data we want and it's fresh
    logger.debug("Processed Meetings data")
    return MeetingListResponse(**meetings_data)


async def _get_meeting(
    http_client: httpx.Client, collection: Collection | None, meeting_id: int
) -> tuple[bool, MeetingResponse]:
    """Helper function to get a meeting by ID from the OParl API."""
    url = UPSTREAM_API_URL + "/meetings"
    params = {"id": meeting_id}

    # TODO: check collection for meeting first
    if collection is not None:
        with logfire.span("Checking ChromaDB for Meeting", meeting_id=meeting_id):
            url = str(httpx.URL(url))
            _id_ref = uuid.uuid5(uuid.NAMESPACE_URL, str(f"{url}?id={meeting_id}"))
            logger.debug(
                f"Checking ChromaDB for Meeting {meeting_id}, internal id: {_id_ref}",
            )
            _doc = collection.get(ids=[str(_id_ref)])
            if _doc and _doc["documents"]:
                logger.debug("Found Meeting in ChromaDB", meeting_id=meeting_id)
                return False, MeetingResponse.model_validate_json(_doc["documents"][0])

    with logfire.span("Fetching meeting from OParl API", meeting_id=meeting_id):
        # TODO: retry on timeut or connection errors
        response = http_client.get(url, params=params, timeout=30.0)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch Meeting {meeting_id} from OParl API",
        )

    meeting_data = response.json()
    logger.debug(
        "Fetched Meeting data from OParl or ChromdDB API",
        meeting_id=meeting_id,
    )

    if not meeting_data or "id" not in meeting_data:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with ID {meeting_id} not found",
        )

    _process_meeting(meeting_data)

    # ok, we got the data we want and it's fresh
    logger.debug(
        "Processed Meeting data",
        meeting_id=meeting_id,
    )
    return True, MeetingResponse.model_validate(meeting_data)


async def _get_meetings_by_organization_id(
    http_client: httpx.Client,
    collection: Collection | None,
    organization_id: int,
    organization_type: OrganizationType = OrganizationType.gr,
) -> tuple[bool, MeetingListResponse]:
    """Helper function to get meetings by organization ID from the OParl API.
    If the meetings are already in the ChromaDB collection, it will return them from there.
    If not, it will fetch them from the OParl API and upsert them into the collection.

    Parameters
    ----------
    http_client : httpx.Client
        The HTTP client to use for making requests.
    collection : Collection | None
        The ChromaDB collection to use for caching meetings.
    organization_id : int
        The ID of the organization to fetch meetings for.
    organization_type : OrganizationType, optional
        The type of the organization (default is OrganizationType.gr).

    Returns
    -------
    tuple[bool, MeetingListResponse]
        A tuple containing a boolean indicating if the meetings were fetched freshly from the OParl API,
        and a MeetingListResponse containing the meetings.
    """
    _url = f"{UPSTREAM_API_URL}/meetings?organization={organization_id}&typ={organization_type.name}"

    if collection is not None:
        with logfire.span(
            "Checking ChromaDB for meetings", organization_id=organization_id
        ):
            # TODO
            pass

    with logfire.span(
        "Fetching meetings from OParl API", organization_id=organization_id
    ):
        # TODO implement pagination
        response = http_client.get(_url, timeout=120.0)
        if response.status_code == 200:
            _json = response.json()

            for meeting in _json["data"]:
                _process_meeting(meeting)

            return True, MeetingListResponse(**_json)

        elif response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"No meetings found for organization ID {organization_id}",
            )
    raise HTTPException(
        status_code=500,
        detail=f"Failed to fetch meetings with organization ID {organization_id} from OParl API",
    )
