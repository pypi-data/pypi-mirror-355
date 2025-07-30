from typing import Optional

import httpx
import logfire
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from stadt_bonn_oparl.api.dependencies import (
    chromadb_meetings_collection,
    http_client_factory,
)
from stadt_bonn_oparl.api.helpers import (
    _get_all_meetings,
    _get_meeting,
    _get_meetings_by_organization_id,
)
from stadt_bonn_oparl.api.models import MeetingListResponse, MeetingResponse


def chromadb_upsert_meeting(data: MeetingResponse, collection):
    """Upsert meeting into ChromaDB."""
    collection.upsert(
        documents=[data.model_dump_json()],
        metadatas=[
            {
                "id": str(data.id),
                "id_ref": data.id_ref,
                "name": data.name,
                "start": data.start.isoformat() if data.start else None,
                "end": data.end.isoformat() if data.end else None,
                "meetingState": data.meetingState,
                "organization": data.organization,
            }
        ],
        ids=[str(data.id)],
    )


router = APIRouter()


@router.get(
    "/meetings/",
    tags=["oparl"],
    response_model=MeetingResponse | MeetingListResponse,
    response_model_exclude_none=True,
)
async def meetings(
    background_tasks: BackgroundTasks,
    meeting_id: Optional[int] = Query(None, alias="id"),
    body_id: Optional[int] = Query(None, alias="body"),
    organization_id: Optional[int] = Query(None, alias="organization"),
    page: int = Query(1, ge=1, le=1000),
    limit: int = Query(5, ge=1, le=100),
    http_client: httpx.Client = Depends(http_client_factory),
    collection=Depends(chromadb_meetings_collection),
):
    """Abrufen der Sitzungen (Meetings) von der Stadt Bonn OParl API.

    Eine Sitzung ist die Versammlung einer oder mehrerer Gruppierungen zu einem
    bestimmten Zeitpunkt an einem bestimmten Ort. Sitzungen enthalten geladene
    Teilnehmer, Tagesordnungspunkte und zugehörige Dokumente.

    Parameter
    ---------
    * **meeting_id**: ID der spezifischen Sitzung (optional)
      - Gibt eine einzelne Sitzung zurück
      - Kann nicht zusammen mit body_id oder organization_id verwendet werden
    * **body_id**: ID der Körperschaft für Sitzungsabruf (optional)
      - Noch nicht implementiert
    * **organization_id**: ID der Organisation für Sitzungsabruf (optional)
      - Gibt Sitzungen dieser Organisation zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Noch nicht implementiert
    * **limit**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Noch nicht implementiert

    Rückgabe
    --------
    * **MeetingResponse | MeetingListResponse**: Einzelne Sitzung oder Liste von Sitzungen

    Fehlerbehandlung
    ---------------
    * **400**: Mehrere Filterparameter gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen
    * **501**: Nicht unterstützte Parameterkombinationen

    Hinweise
    --------
    Die geladenen Teilnehmer sind als oparl:Person-Objekte referenziert.
    Verschiedene Dateien (Einladung, Ergebnis- und Wortprotokoll, Anlagen)
    können referenziert werden. Inhalte werden durch oparl:AgendaItem abgebildet.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-meeting
    """
    _response = None
    needs_upsert = True

    # TODO: implement pagination for fetching results from upstream and for delivering results to the client
    # if organization_id and body_id is provided, raise an error
    if meeting_id and organization_id and body_id:
        raise HTTPException(
            status_code=400,
            detail="Please provide either id or organization or body, not multiple.",
        )

    # If meeting_id is provided, fetch the specific meeting
    if meeting_id and not organization_id and not body_id:
        try:
            needs_upsert, _response = await _get_meeting(http_client, None, meeting_id)
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching meeting {meeting_id}: {e.response.text}",
            ) from e

    if organization_id and not meeting_id and not body_id:
        try:
            needs_upsert, _response = await _get_meetings_by_organization_id(
                http_client=http_client,
                collection=collection,
                organization_id=organization_id,
            )

            return _response
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching meetings for organization {organization_id}: {e.response.text}",
            ) from e

    # Let's deliver all meetings if no specific filters are provided
    if not meeting_id and not organization_id and not body_id:
        try:
            _response = await _get_all_meetings(
                http_client=http_client,
                page=page,
                limit=limit,
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching all meetings: {e.response.text}",
            ) from e

    if _response:
        if needs_upsert:
            # Upsert organization into ChromaDB
            if isinstance(_response, MeetingListResponse):
                for m in _response.data:
                    with logfire.span("Upserting meetings into ChromaDB"):
                        background_tasks.add_task(
                            chromadb_upsert_meeting, m, collection
                        )

            elif isinstance(_response, MeetingResponse):
                with logfire.span(f"Upserting meeting {meeting_id} into ChromaDB"):
                    background_tasks.add_task(
                        chromadb_upsert_meeting, _response, collection
                    )

        return _response

    # This endpoint is not implemented yet
    raise HTTPException(status_code=501, detail="Meetings endpoint not implemented yet")
