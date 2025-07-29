"""
Example implementation showing how to integrate the Reference Resolver
into existing API helpers.

This demonstrates the pattern that can be applied to all entity helpers.
"""

# Example: Updated consultation helper with reference resolution

import httpx
from chromadb import Collection
from loguru import logger

from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.models import Consultation
from stadt_bonn_oparl.reference_resolver import ReferenceResolver


async def _get_consultation_with_resolution(
    http_client: httpx.Client,
    collection: Collection | None,
    consultation_id: int,
    bi: int,
) -> tuple[bool, Consultation]:
    """
    Get a consultation and trigger background reference resolution.

    This is an enhanced version of _get_consultation that automatically
    queues reference resolution tasks when fetching fresh data.
    """
    # Get the consultation using existing helper
    is_fresh, consultation = await _get_consultation(
        http_client, collection, consultation_id, bi
    )

    # If we fetched fresh data and have a collection, trigger resolution
    if is_fresh and collection is not None:
        try:
            resolver = ReferenceResolver(http_client, collection)
            await resolver.resolve_references(consultation.model_dump(), "Consultation")
            logger.info(
                f"Queued reference resolution for Consultation {consultation_id}"
            )
        except Exception as e:
            # Don't fail the request if resolution queueing fails
            logger.error(
                f"Failed to queue reference resolution for Consultation {consultation_id}: {e}"
            )

    return is_fresh, consultation


# Example: CLI command that checks reference status

import cyclopts

from stadt_bonn_oparl.cli import app
from stadt_bonn_oparl.reference_resolver import ReferenceResolver


@app.command
async def check_references(entity_type: str, entity_id: str | int):
    """Check the reference resolution status for an entity.

    Parameters
    ----------
    entity_type: The type of entity (e.g., "Consultation").
    entity_id: The ID of the entity to check.
    """

    if isinstance(entity_id, int):
        entity_id = str(entity_id)

    http_client = httpx.Client()
    collection = get_chromadb_collection()
    resolver = ReferenceResolver(http_client, collection)

    # Check status
    status = await resolver.check_references_resolved(entity_id, entity_type)

    print(f"\n📊 Reference Status for {entity_type} {entity_id}:")
    print("-" * 50)

    for field, is_resolved in status.items():
        icon = "✅" if is_resolved else "⏳"
        print(f"{icon} {field}: {'Resolved' if is_resolved else 'Pending'}")

    # Get the entity to show current state
    entity = await resolver.get_or_resolve_entity(entity_type, entity_id)
    if entity:
        print(f"\n📄 Entity Details:")

        # Show example fields based on type
        if entity_type == "Consultation":
            if entity.get("paper"):
                print(f"  Paper: {entity['paper'].get('name', 'N/A')}")
            else:
                print(f"  Paper Reference: {entity.get('paper_ref', 'N/A')}")

            if entity.get("meeting"):
                print(f"  Meeting: {entity['meeting'].get('name', 'N/A')}")
            else:
                print(f"  Meeting Reference: {entity.get('meeting_ref', 'N/A')}")


# Example: API endpoint that returns resolution status

from fastapi import APIRouter, Depends

from stadt_bonn_oparl.api.dependencies import get_chromadb_collection, get_http_client

router = APIRouter()


@router.get("/consultations/{consultation_id}/references")
async def get_consultation_reference_status(
    consultation_id: int,
    bi: int,
    http_client: httpx.Client = Depends(get_http_client),
    collection: Collection = Depends(get_chromadb_collection),
):
    """Get the reference resolution status for a consultation."""

    resolver = ReferenceResolver(http_client, collection)

    # Build the entity ID (same as used in ChromaDB)
    entity_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://www.bonn.sitzung-online.de/public/oparl/consultations?id={consultation_id}&bi={bi}",
        )
    )

    # Get status
    status = await resolver.check_references_resolved(entity_id, "Consultation")

    # Get entity with current state
    entity = await resolver.get_or_resolve_entity("Consultation", entity_id)

    return {
        "consultation_id": consultation_id,
        "bi": bi,
        "reference_status": status,
        "has_paper": entity.get("paper") is not None if entity else False,
        "has_meeting": entity.get("meeting") is not None if entity else False,
        "paper_name": entity.get("paper", {}).get("name") if entity else None,
        "meeting_name": entity.get("meeting", {}).get("name") if entity else None,
    }


# Example: Periodic task to resolve references for recent consultations

from datetime import datetime, timedelta

from celery import shared_task


@shared_task
def resolve_recent_consultation_references():
    """
    Find consultations added in the last 24 hours and ensure
    their references are being resolved.
    """
    collection = get_chromadb_collection()

    # Query for recent consultations
    # In practice, you'd filter by creation date
    results = collection.get(where={"type": "Consultation"}, limit=100)

    if results and results["documents"]:
        entity_ids = []
        for i, doc in enumerate(results["documents"]):
            entity = json.loads(doc)
            # Check if created recently (simplified - would need proper date check)
            if "created" in entity:
                entity_ids.append(results["ids"][i])

        if entity_ids:
            batch_resolve_references.delay("Consultation", entity_ids)
            logger.info(
                f"Queued reference resolution for {len(entity_ids)} recent consultations"
            )


# Example: Helper function for displaying entities with references


def format_consultation_with_references(consultation: Consultation) -> str:
    """Format a consultation for display, showing resolved references."""

    output = []
    output.append(f"📋 Consultation (ID: {consultation.id})")
    output.append(f"   Role: {consultation.role}")
    output.append(f"   Authoritative: {'Yes' if consultation.authoritative else 'No'}")

    # Show paper information
    if consultation.paper:
        output.append(f"\n📄 Paper (Resolved):")
        output.append(f"   Name: {consultation.paper.name}")
        output.append(f"   Reference: {consultation.paper.reference}")
        output.append(f"   Type: {consultation.paper.paperType}")
    elif consultation.paper_ref:
        output.append(f"\n📄 Paper (Reference): {consultation.paper_ref}")
        output.append("   ⏳ Full paper data loading in background...")

    # Show meeting information
    if consultation.meeting:
        output.append(f"\n📅 Meeting (Resolved):")
        output.append(f"   Name: {consultation.meeting.name}")
        output.append(f"   Date: {consultation.meeting.start}")
        output.append(f"   State: {consultation.meeting.meetingState}")
    elif consultation.meeting_ref:
        output.append(f"\n📅 Meeting (Reference): {consultation.meeting_ref}")
        output.append("   ⏳ Full meeting data loading in background...")

    # Show organizations
    if consultation.organizations:
        output.append(f"\n🏢 Organizations ({len(consultation.organizations)}):")
        for org in consultation.organizations[:3]:  # Show first 3
            output.append(f"   - {org.name}")
    elif consultation.organization_ref:
        output.append(
            f"\n🏢 Organizations: {len(consultation.organization_ref)} references"
        )
        output.append("   ⏳ Organization data loading in background...")

    return "\n".join(output)
