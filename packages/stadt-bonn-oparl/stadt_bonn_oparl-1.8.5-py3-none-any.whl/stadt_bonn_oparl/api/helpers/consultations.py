import uuid
from chromadb import Collection
import httpx
import logfire
from fastapi import HTTPException
from loguru import logger
from regex import W

from stadt_bonn_oparl.api.helpers.processors import _process_consultation
from stadt_bonn_oparl.api.models import Consultation
from stadt_bonn_oparl.config import UPSTREAM_API_URL


async def _get_consultation(
    http_client: httpx.Client,
    collection: Collection | None,
    consultation_id: int,
    bi: int,
) -> tuple[bool, Consultation]:
    """Get a specific consultation by ID or bi number."""
    url = UPSTREAM_API_URL + "/consultations"
    params = {"id": consultation_id, "bi": bi}

    if collection is not None:
        with logfire.span(
            "Checking ChromaDB for Collection", consultation_id=consultation_id, bi=bi
        ):
            url = str(httpx.URL(url))
            _id_ref = uuid.uuid5(
                uuid.NAMESPACE_URL, str(f"{url}?id={consultation_id}&bi={bi}")
            )
            logger.debug(
                f"Checking ChromaDB for consultation {consultation_id} with bi {bi}, internal id: {_id_ref}",
            )
            _doc = collection.get(ids=[str(_id_ref)])
            if _doc and _doc["documents"]:
                # If we have a document, return it
                logger.debug(
                    "Found consultation in ChromaDB",
                    consultation_id=consultation_id,
                    bi=bi,
                )
                return False, Consultation.model_validate_json(_doc["documents"][0])

    with logfire.span(
        "Fetching consultation from OParl API", consultation_id=consultation_id, bi=bi
    ):
        response = http_client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch consultation {consultation_id} with bi {bi} from OParl API",
        )

    consultation_data = response.json()
    logger.debug(
        "Fetched consultation data from OParl or ChromdDB API",
        consultation_id=consultation_id,
        bi=bi,
    )
    if not consultation_data or "id" not in consultation_data:
        raise HTTPException(
            status_code=404,
            detail=f"Consultation with ID {consultation_id} and bi {bi} not found",
        )

    _process_consultation(consultation_data)
    consultation_data["bi"] = bi

    # ok, we got the data we want and it's fresh
    logger.debug(
        "Processed consultation data",
        consultation=consultation_data,
    )
    return True, Consultation.model_validate(consultation_data)
