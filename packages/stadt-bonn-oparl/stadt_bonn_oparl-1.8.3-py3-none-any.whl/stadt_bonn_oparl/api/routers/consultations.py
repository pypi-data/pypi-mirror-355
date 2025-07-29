from typing import Optional

import httpx
import logfire
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from loguru import logger

from stadt_bonn_oparl.api.dependencies import (
    chromadb_consultations_collection,
    http_client_factory,
)
from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.models import Consultation


def chromadb_upsert_consultation(data: Consultation, collection):
    """Upsert file into ChromaDB."""
    logger.debug(f"Upserting consultation into ChromaDB: {data.id}, {data.bi}")
    collection.upsert(
        documents=[data.model_dump_json()],
        metadatas=[
            {
                "id": str(data.id),
                "id_ref": data.id_ref,
                "bi": data.bi,
                "type": data.type,
                "meeting_ref": data.paper_ref,
                "paper_ref": data.paper_ref,
            }
        ],
        ids=[str(data.id)],
    )


router = APIRouter()


@router.get(
    "/consultations/",
    tags=["oparl"],
    response_model=Consultation,
    response_model_exclude_none=True,
)
async def consultations(
    background_tasks: BackgroundTasks,
    consultation_id: Optional[int] = Query(None, alias="id"),
    bi: Optional[int] = Query(None, alias="bi"),
    http_client: httpx.Client = Depends(http_client_factory),
    collection=Depends(chromadb_consultations_collection),
):
    """Abrufen der Konsultationen von der Stadt Bonn OParl API.

    Konsultationen sind öffentliche Anhörungen oder Konsultationen zu
    bestimmten Themen, die von der Stadt Bonn durchgeführt werden. Sie bildet die Beratung einer Drucksache
    in einer Sitzung ab. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit stattgefunden hat
    oder diese für die Zukunft geplant ist.

    Parameter
    ---------
    * consultation_id: Optional[int]
        - ID der Konsultation, um eine spezifische Konsultation abzurufen.
    * bi: Optional[int]
        - Bi-Nummer der Konsultation, um eine spezifische Konsultation abzurufen.
    """
    response: Consultation | None = None
    is_fresh: bool = False

    if not consultation_id or not bi:
        raise HTTPException(
            status_code=400,
            detail="'id' and 'bi' query parameter must be provided.",
        )

    if consultation_id:
        is_fresh, response = await _get_consultation(
            http_client=http_client,
            collection=collection,
            consultation_id=consultation_id,
            bi=bi,
        )
        if not response:
            raise HTTPException(status_code=404, detail="File not found")

    if response is not None:
        if is_fresh:
            with logfire.span(
                "Upserting Consultation into ChromaDB",
            ):
                background_tasks.add_task(
                    chromadb_upsert_consultation, response, collection
                )
        else:
            logger.debug("Consultation already exists in ChromaDB, skipping upsert.")

        return response
