import asyncio
from http.client import HTTPException
from typing import Any, Dict, Union
from uuid import UUID

from celery import shared_task
import chromadb
import httpx
from chromadb.config import Settings
from httpx import URL
from loguru import logger
import stadt_bonn_oparl_api_client.errors as sdk_errors
from stadt_bonn_oparl_api_client import Client
from stadt_bonn_oparl_api_client.api.oparl import consultations_consultations_get
from stadt_bonn_oparl_api_client.models import Consultation as ConsultationResponse, HTTPValidationError
from stadt_bonn_oparl_api_client.types import UNSET

from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.helpers.helpers import _get_paper_by_id
from stadt_bonn_oparl.api.helpers.meetings import _get_meeting
from stadt_bonn_oparl.api.models import Consultation, MeetingResponse, PaperResponse
from stadt_bonn_oparl.celery import app
from stadt_bonn_oparl.config import OPARL_BASE_URL
from stadt_bonn_oparl.logging import configure_logging

configure_logging(2)


class CustomNotImplementedError(Exception):
    """Custom exception for unimplemented features."""

    pass


def load_paper(
    http_client: httpx.Client, pcoll: chromadb.Collection, consultation: Consultation
) -> PaperResponse | None:
    """Load the paper for a given consultation.

    Args:
        consultation (Consultation): The consultation object to update with the paper.

    Returns:
        PaperResponse: The updated consultation object with the paper loaded.
    """
    paper = None

    if consultation.paper_ref and consultation.paper_ref is not None:
        paper_ref_id = URL(consultation.paper_ref).params.get("id")

        try:
            paper = asyncio.run(_get_paper_by_id(http_client, pcoll, paper_ref_id))
            if not paper:
                raise ValueError(f"Paper with id {paper_ref_id} not found")
        except HTTPException as e:
            logger.error(f"Error fetching paper with id {paper_ref_id}: {e}")
            return None

        return paper
    else:
        logger.warning(
            f"Consultation {consultation.id} has no paper reference, skipping paper load."
        )
        return None


def load_meeting(
    http_client: httpx.Client, consultation: Consultation
) -> MeetingResponse | None:
    """Load the meeting for a given consultation.

    Args:
        consultation (Consultation): The consultation object to update with the paper.

    Returns:
        MeetingResponse: The updated consultation object with the paper loaded.
    """
    if consultation.meeting_ref and consultation.meeting_ref is not None:
        meeting_ref_id = URL(consultation.meeting_ref).params.get("id")

        meeting = asyncio.run(_get_meeting(http_client, None, meeting_ref_id))
        if not meeting:
            raise ValueError(f"Meeting with id {meeting_ref_id} not found")

        return meeting
    else:
        logger.warning(
            f"Consultation {consultation.id} has no meeting reference, skipping meeting load."
        )
        return None


@shared_task(
    name="stadt_bonn_oparl.tasks.consultations.loadsert_references",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=15,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def loadsert_references(self, _consultation_ref: str) -> bool:
    """This task will update the Paper referenced in a consultation.

    Args:
        consultation_id (uuid.UUID): The ID of the consultation to update
        paper_ref (URL): The URL of the paper to reference

    Returns:
        bool: True if the update was successful, False otherwise
    """
    http_client = httpx.Client()
    chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(
            anonymized_telemetry=False,  # disable posthog telemetry
        ),
    )
    ccoll = chromadb_client.get_collection(name="consultations")
    pcoll = chromadb_client.get_collection(name="papers")

    consultation_ref = URL(_consultation_ref)
    paper_ref_id: int = 0

    _, consultation = asyncio.run(
        _get_consultation(
            http_client,
            ccoll,
            int(consultation_ref.params.get("id")),
            int(consultation_ref.params.get("bi")),
        )
    )
    if not consultation:
        raise ValueError(f"Consultation with ref {consultation_ref} not found")

    paper = load_paper(http_client, pcoll, consultation)
    if not paper:
        logger.error(f"Paper with ref {paper_ref_id} not found")
    else:
        consultation.paper = paper
        consultation.paper_ref = None

    meeting = load_meeting(http_client, consultation)
    if not meeting:
        logger.error(f"Meeting with ref {consultation.meeting_ref} not found")
    else:
        consultation.meeting = meeting
        consultation.meeting_ref = None

    # upsert the updated consultation
    logger.debug(
        f"Upserting consultation into ChromaDB: {consultation.id}, {consultation.bi}"
    )
    ccoll.upsert(
        documents=[consultation.model_dump_json()],
        ids=[str(consultation.id)],
    )

    return True


@app.task(bind=True, max_retries=3)
def fetch_consultation_task(self, consultation_id: Union[UUID, int]) -> Dict[str, Any]:
    """
    Fetch a Consultation from the local API by either internal UUID or upstream ID.

    This task retrieves consultation details from the local API, which triggers
    caching and ChromaDB ingestion.

    Args:
        consultation_id: Either an internal UUID or an upstream ID (int)

    Returns:
        Dict containing consultation data or error information
    """
    logger.info(f"Fetching consultation: {consultation_id}")

    try:
        # Initialize API client
        client = Client(base_url=OPARL_BASE_URL)

        # Determine ID type and convert to string for API call
        if isinstance(consultation_id, UUID):
            id_to_use = str(consultation_id)
            id_type = "uuid"
            logger.debug(f"Using internal UUID: {consultation_id}")
        elif isinstance(consultation_id, int):
            id_to_use = consultation_id
            id_type = "upstream_id"
            logger.debug(f"Using upstream ID: {consultation_id}")
        else:
            # This should not happen with proper type hints, but handle gracefully
            raise ValueError(f"Invalid consultation_id type: {type(consultation_id)}")

        # Fetch consultation from local API
        try:
            if id_type == "uuid":
                raise CustomNotImplementedError(
                    "Fetching by internal UUID is not implemented yet. This feature is not provided by the OParl API."
                )

            response = consultations_consultations_get.sync(client=client, id=int(id_to_use))

            if isinstance(response, HTTPValidationError):
                logger.error(
                    f"Validation error for consultation {id_to_use}: {response}"
                )
                return {
                    "success": False,
                    "error": "validation_error",
                    "details": str(response),
                    "consultation_id": str(consultation_id),
                }

            if isinstance(response, ConsultationResponse):
                # Extract key information
                result = {
                    "success": True,
                    "consultation_id": str(consultation_id),
                    "data": {
                        "id": str(response.id),
                        "bi": response.bi if response.bi is not UNSET else None,
                        "role": response.role,
                        "keyword": (
                            response.keyword if response.keyword is not UNSET else None
                        ),
                    },
                }

                # Add paper reference if available
                if response.paper_ref is not UNSET and response.paper_ref:
                    result["data"]["paper_ref"] = response.paper_ref
                elif response.paper is not UNSET and response.paper:
                    result["data"]["paper"] = response.paper.model_dump() if hasattr(response.paper, 'model_dump') else str(response.paper)

                # Add meeting reference if available
                if response.meeting_ref is not UNSET and response.meeting_ref:
                    result["data"]["meeting_ref"] = response.meeting_ref
                elif response.meeting is not UNSET and response.meeting:
                    result["data"]["meeting"] = response.meeting.model_dump() if hasattr(response.meeting, 'model_dump') else str(response.meeting)

                # Add organization references if available
                if response.organization_ref is not UNSET and response.organization_ref:
                    result["data"]["organization_refs"] = response.organization_ref
                elif response.organizations is not UNSET and response.organizations:
                    result["data"]["organization_count"] = len(response.organizations)
                    result["data"]["organizations"] = [
                        org.model_dump() if hasattr(org, 'model_dump') else str(org) for org in response.organizations
                    ]

                logger.info(
                    f"Successfully fetched consultation {id_to_use} ({id_type}): role={result['data']['role']}"
                )

                return result

            # Unexpected response type
            logger.warning(f"Unexpected response type for consultation {id_to_use}")
            return {
                "success": False,
                "error": "unexpected_response",
                "consultation_id": str(consultation_id),
                "id_type": id_type,
            }

        except sdk_errors.UnexpectedStatus as e:
            logger.error(f"API error fetching consultation {id_to_use}: {e}")
            # Check if it's a 404 Not Found
            if hasattr(e, "status_code") and e.status_code == 404:
                return {
                    "success": False,
                    "error": "not_found",
                    "consultation_id": str(consultation_id),
                    "id_type": id_type,
                    "details": f"Consultation {id_to_use} not found in local API",
                }
            return {
                "success": False,
                "error": "api_error",
                "status_code": getattr(e, "status_code", None),
                "details": str(e),
                "consultation_id": str(consultation_id),
                "id_type": id_type,
            }

    except Exception as e:
        logger.error(
            f"Unexpected error fetching consultation {consultation_id}: {str(e)}"
        )
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
