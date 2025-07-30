import uuid

import chromadb
import httpx
from chromadb.config import Settings
from fastapi import APIRouter, Depends

from stadt_bonn_oparl.api.dependencies import (
    chromadb_meetings_collection,
    http_client_factory,
)
from stadt_bonn_oparl.config import UPSTREAM_API_URL
from stadt_bonn_oparl.reference_resolver import ReferenceResolver

router = APIRouter()


@router.get(
    "/meetings/{meeting_id}/references",
    tags=["oparl", "experimental"],
)
async def get_meetings_reference_status(
    meeting_id: int,
    http_client: httpx.Client = Depends(http_client_factory),
    collection=Depends(chromadb_meetings_collection),
):
    """Get the reference resolution status for a consultation."""

    # FIXME: this should not happen in here
    chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(
            anonymized_telemetry=False,  # disable posthog telemetry
        ),
    )

    resolver = ReferenceResolver(http_client, chromadb_client)

    # Get status
    status = await resolver.check_references_resolved(str(meeting_id), "Meeting")

    # Get entity with current state
    entity = await resolver.get_or_resolve_entity("Meeting", str(meeting_id))

    return {
        "meeting_id": meeting_id,
        "reference_status": status,
        "has_paper": entity.get("paper") is not None if entity else False,
        "has_meeting": entity.get("meeting") is not None if entity else False,
        "paper_name": entity.get("paper", {}).get("name") if entity else None,
        "meeting_name": entity.get("meeting", {}).get("name") if entity else None,
    }
