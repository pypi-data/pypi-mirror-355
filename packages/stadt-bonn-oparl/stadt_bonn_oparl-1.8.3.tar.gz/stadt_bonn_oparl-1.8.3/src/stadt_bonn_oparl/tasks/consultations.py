import asyncio
from http.client import HTTPException

from celery import shared_task
import chromadb
import httpx
from chromadb.config import Settings
from httpx import URL
from loguru import logger

from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.helpers.helpers import _get_paper_by_id
from stadt_bonn_oparl.api.helpers.meetings import _get_meeting
from stadt_bonn_oparl.api.models import Consultation, MeetingResponse, PaperResponse
from stadt_bonn_oparl.celery import app
from stadt_bonn_oparl.logging import configure_logging

configure_logging(2)


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

        meeting = asyncio.run(_get_meeting(http_client, meeting_ref_id))
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
