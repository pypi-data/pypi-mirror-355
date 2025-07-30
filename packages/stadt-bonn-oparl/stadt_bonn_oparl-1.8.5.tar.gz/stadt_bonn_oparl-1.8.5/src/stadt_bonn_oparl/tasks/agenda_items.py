"""
Celery tasks for synchronizing meeting data from OParl API.
"""

from typing import Any, Dict, Union
from uuid import UUID

import stadt_bonn_oparl_api_client.errors as sdk_errors
from loguru import logger
from stadt_bonn_oparl_api_client import Client
from stadt_bonn_oparl_api_client.api.oparl import agenda_items_agendaitems_get
from stadt_bonn_oparl_api_client.models import AgendaItemResponse, HTTPValidationError
from stadt_bonn_oparl_api_client.types import UNSET

from stadt_bonn_oparl.celery import app
from stadt_bonn_oparl.config import OPARL_BASE_URL


class NotImplementedError(Exception):
    """Custom exception for unimplemented features."""

    pass


@app.task(bind=True, max_retries=3)
def fetch_agenda_item_task(self, agenda_item_id: Union[UUID, int]) -> Dict[str, Any]:
    """
    Fetch an AgendaItem from the local API by either internal UUID or upstream ID.

    This task retrieves agenda item details from the local API, which triggers
    caching and ChromaDB ingestion.

    Args:
        agenda_item_id: Either an internal UUID or an upstream ID (int)

    Returns:
        Dict containing agenda item data or error information
    """
    logger.info(f"Fetching agenda item: {agenda_item_id}")

    try:
        # Initialize API client
        client = Client(base_url=OPARL_BASE_URL)

        # Determine ID type and convert to string for API call
        if isinstance(agenda_item_id, UUID):
            id_to_use = str(agenda_item_id)
            id_type = "uuid"
            logger.debug(f"Using internal UUID: {agenda_item_id}")
        elif isinstance(agenda_item_id, int):
            id_to_use = str(agenda_item_id)
            id_type = "upstream_id"
            logger.debug(f"Using upstream ID: {agenda_item_id}")
        else:
            # This should not happen with proper type hints, but handle gracefully
            raise ValueError(f"Invalid agenda_item_id type: {type(agenda_item_id)}")

        # Fetch agenda item from local API
        try:
            if id_type == "uuid":
                raise NotImplementedError(
                    "Fetching by internal UUID is not implemented yet. This feature is not provided by the OParl API."
                )

            response = agenda_items_agendaitems_get.sync(client=client, id=id_to_use)

            if isinstance(response, HTTPValidationError):
                logger.error(
                    f"Validation error for agenda item {id_to_use}: {response}"
                )
                return {
                    "success": False,
                    "error": "validation_error",
                    "details": str(response),
                    "agenda_item_id": str(agenda_item_id),
                }

            if isinstance(response, AgendaItemResponse):
                # Extract key information
                result = {
                    "success": True,
                    "agenda_item_id": str(agenda_item_id),
                    "data": {
                        "id": response.id if response.id is not UNSET else None,
                        "name": response.name if response.name is not UNSET else None,
                        "number": (
                            response.number if response.number is not UNSET else None
                        ),
                        "start": (
                            response.start.isoformat()
                            if response.start is not UNSET and response.start
                            else None
                        ),
                        "end": (
                            response.end.isoformat()
                            if response.end is not UNSET and response.end
                            else None
                        ),
                        "public": (
                            response.public if response.public is not UNSET else None
                        ),
                    },
                }

                # Add consultation info if available
                if response.consultation is not UNSET and response.consultation:
                    result["data"]["consultation_count"] = len(response.consultation)
                    result["data"]["consultations"] = []
                    for consultation in response.consultation:
                        cons_info = {
                            "id": (consultation if consultation is not UNSET else None),
                        }
                        result["data"]["consultations"].append(cons_info)

                # Add meeting reference if available
                if response.meeting is not UNSET and response.meeting:
                    result["data"]["meeting"] = str(response.meeting)

                logger.info(
                    f"Successfully fetched agenda item {id_to_use} ({id_type}): {result['data']['name'] or 'Unnamed'}"
                )

                return result

            # Unexpected response type
            logger.warning(f"Unexpected response type for agenda item {id_to_use}")
            return {
                "success": False,
                "error": "unexpected_response",
                "agenda_item_id": str(agenda_item_id),
                "id_type": id_type,
            }

        except sdk_errors.UnexpectedStatus as e:
            logger.error(f"API error fetching agenda item {id_to_use}: {e}")
            # Check if it's a 404 Not Found
            if hasattr(e, "status_code") and e.status_code == 404:
                return {
                    "success": False,
                    "error": "not_found",
                    "agenda_item_id": str(agenda_item_id),
                    "id_type": id_type,
                    "details": f"Agenda item {id_to_use} not found in local API",
                }
            return {
                "success": False,
                "error": "api_error",
                "status_code": getattr(e, "status_code", None),
                "details": str(e),
                "agenda_item_id": str(agenda_item_id),
                "id_type": id_type,
            }

    except Exception as e:
        logger.error(
            f"Unexpected error fetching agenda item {agenda_item_id}: {str(e)}"
        )
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
