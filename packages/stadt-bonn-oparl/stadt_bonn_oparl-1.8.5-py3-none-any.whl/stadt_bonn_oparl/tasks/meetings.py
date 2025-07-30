"""
Celery tasks for synchronizing meeting data from OParl API.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode
import httpx
from loguru import logger
from stadt_bonn_oparl_api_client import Client
from stadt_bonn_oparl_api_client.api.oparl import meetings_meetings_get
from stadt_bonn_oparl_api_client.models import (
    MeetingListResponse,
    MeetingResponse,
    HTTPValidationError,
)
from stadt_bonn_oparl_api_client.types import UNSET
import stadt_bonn_oparl_api_client.errors as sdk_errors

from stadt_bonn_oparl.celery import app
from stadt_bonn_oparl.config import UPSTREAM_API_URL, OPARL_BASE_URL
from stadt_bonn_oparl.tasks.download import (
    download_direct_url_task,
    download_entity_task,
)
from stadt_bonn_oparl.tasks.agenda_items import fetch_agenda_item_task


@app.task(bind=True, max_retries=3)
def sync_meetings_task(self, max_pages: Optional[int] = 1) -> Dict[str, Any]:
    """
    Periodic task to sync meetings from OParl API.

    Fetches the list of meetings from the upstream OParl API and retrieves
    detailed information for each meeting from the local API.

    Args:
        max_pages: Maximum number of pages to fetch from the OParl API

    Returns:
        Dict with sync statistics
    """
    logger.info("Starting periodic meeting sync task")

    data_path = Path("data-100/meetings")
    task_config = {
        "base_path": data_path,
        "create_subdirs": True,
        "timeout": 300,
    }

    meetings_processed = 0
    meetings_failed = 0
    all_meetings = []

    try:
        # Initialize SDK clients
        api_client = Client(base_url=OPARL_BASE_URL)

        page = 1

        # Fetch meetings from upstream OParl API
        while page <= (max_pages or 1000):  # Large number if max_pages is None
            logger.debug(f"Fetching meetings from page {page}")

            try:
                response = meetings_meetings_get.sync(
                    client=api_client,
                    page=page,
                    page_size=100,  # Maximize page size
                )

                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error: {response}")
                    break

                if isinstance(response, MeetingListResponse):
                    if response.data is not UNSET and response.data:
                        all_meetings.extend(response.data)
                        logger.info(f"Fetched {len(response.data)} meetings from page {page}")

                    # Check if there are more pages
                    if response.links is not UNSET and response.links:
                        # Check if there's a next link
                        has_next = False
                        if hasattr(response.links, "additional_properties"):
                            has_next = "next" in response.links.additional_properties

                        if not has_next:
                            break
                    else:
                        break
                else:
                    # Single meeting response, shouldn't happen when fetching list
                    logger.warning("Got single meeting response when expecting list")
                    break

                page += 1

            except sdk_errors.UnexpectedStatus as e:
                logger.error(f"Unexpected status from API: {e}")
                break
            except ValueError as e:
                # This might be the UUID parsing error
                logger.error(f"Value error (possibly UUID parsing) on page {page}: {str(e)}")
                logger.debug(f"Error details: {e.__class__.__name__}: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching page {page}: {str(e)}")
                logger.debug(f"Error type: {e.__class__.__name__}")
                break

        logger.info(f"Total meetings fetched: {len(all_meetings)}")

        # Process each meeting
        for meeting in all_meetings:
            meeting_id = None

            # Extract meeting ID
            if hasattr(meeting, "id_ref") and meeting.id_ref is not UNSET:
                # Parse ID from URL format if needed
                id_str = str(meeting.id_ref)
                if "id=" in id_str:
                    meeting_id = id_str.split("id=")[1].split("&")[0]
                else:
                    meeting_id = id_str

            if not meeting_id:
                logger.warning("Meeting without ID found, skipping")
                continue

            try:
                # Fetch detailed meeting information from local API
                logger.debug(f"Fetching meeting details from local API for ID: {meeting_id}")

                response = meetings_meetings_get.sync(client=api_client, id=int(meeting_id))

                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error for meeting {meeting_id}: {response}")
                    meetings_failed += 1
                elif isinstance(response, MeetingResponse):
                    logger.info(
                        f"Successfully retrieved meeting {meeting_id}: {response.name if response.name is not UNSET else 'Unnamed'}"
                    )
                    logger.debug("Meeting details: %s", response)
                    if response.invitation:
                        invitation_id = httpx.URL(response.invitation.id).params.get("id")

                        download_entity_task.apply_async(
                            args=["file", invitation_id],
                            kwargs={"config_dict": task_config},
                        )
                    if response.verbatim_protocol:
                        download_direct_url_task.apply_async(
                            args=[
                                response.verbatim_protocol.access_url,
                                str(data_path),
                            ],
                            kwargs={
                                "filename": f"protocol_{meeting_id}_verbatim.pdf",
                                "config_dict": task_config,
                            },
                        )

                    meetings_processed += 1
                else:
                    logger.warning(f"Unexpected response type for meeting {meeting_id}")
                    meetings_failed += 1

            except sdk_errors.UnexpectedStatus as e:
                logger.error(f"Failed to fetch meeting {meeting_id}: {e}")
                meetings_failed += 1
            except Exception as e:
                logger.error(f"Error processing meeting {meeting_id}: {str(e)}")
                meetings_failed += 1

    except Exception as e:
        logger.error(f"Unexpected error during meeting sync: {str(e)}")
        raise self.retry(exc=e, countdown=60)

    result = {
        "total_meetings": len(all_meetings),
        "meetings_processed": meetings_processed,
        "meetings_failed": meetings_failed,
        "success_rate": meetings_processed / len(all_meetings) if all_meetings else 0,
    }

    logger.info(f"Meeting sync completed: {result}")
    return result


@app.task()
def fetch_meeting_details_task(meeting_id: str) -> Dict[str, Any]:
    """
    Task to fetch detailed information for a specific meeting.

    Args:
        meeting_id: The ID of the meeting to fetch

    Returns:
        Dict with meeting details
    """
    logger.info(f"Fetching details for meeting {meeting_id}")

    try:
        # Initialize SDK client for local API
        client = Client(base_url=OPARL_BASE_URL)

        # Fetch meeting details
        response = meetings_meetings_get.sync(client=client, id=int(meeting_id))

        if isinstance(response, HTTPValidationError):
            logger.error(f"Validation error for meeting {meeting_id}: {response}")
            raise ValueError(f"Invalid meeting ID: {meeting_id}")

        if isinstance(response, MeetingResponse):
            logger.info(f"Meeting {meeting_id} found in local API")
            return response.to_dict()

        # Shouldn't get MeetingListResponse for single ID query
        logger.error(f"Unexpected response type for meeting {meeting_id}")
        raise ValueError(f"Unexpected response for meeting {meeting_id}")

    except sdk_errors.UnexpectedStatus as e:
        logger.error(f"Failed to fetch meeting {meeting_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching meeting {meeting_id}: {str(e)}")
        raise


@app.task(bind=True, max_retries=3)
def sync_meetings_timeframe_task(
    self,
    created_since: str,
    created_until: str,
    data_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sync meetings from OParl API within a specified time window.

    Fetches all meetings created within the specified timeframe from the upstream
    OParl API, then retrieves each meeting from the local API to ensure it's
    cached and ingested into ChromaDB.

    Args:
        created_since: ISO 8601 datetime string for start of time window (e.g., "2025-05-01T00:00:00+01:00")
        created_until: ISO 8601 datetime string for end of time window (e.g., "2025-06-01T00:00:00+01:00")
        data_path: Optional path to store meeting data. Defaults to "data-100/meetings"

    Returns:
        Dict with sync statistics
    """
    logger.info(f"Starting timeframe meeting sync: {created_since} to {created_until}")

    if data_path is None:
        data_path = "data-100/meetings"

    task_config = {
        "base_path": str(Path(data_path)),
        "create_subdirs": True,
        "timeout": 300,
    }

    meetings_processed = 0
    meetings_failed = 0
    all_meetings = []

    try:
        # Initialize clients
        local_api_client = Client(base_url=OPARL_BASE_URL)

        # Build upstream API URL with time parameters
        params = {
            "created_since": created_since,
            "created_until": created_until,
            "limit": 25,  # Page size
        }

        page = 0
        has_more_pages = True

        # Fetch all meetings from upstream API with pagination
        while has_more_pages:
            page += 1
            logger.debug(f"Fetching meetings from upstream API, page {page}")

            # Add page parameter if not first page
            if page > 1:
                params["page"] = page

            # Build URL with parameters
            url = f"{UPSTREAM_API_URL}/meetings?{urlencode(params)}"

            try:
                # Make request to upstream API
                with httpx.Client() as client:
                    response = client.get(url, timeout=180)
                    response.raise_for_status()

                    data = response.json()

                    # Extract meetings from response
                    if "data" in data and isinstance(data["data"], list):
                        meetings_batch = data["data"]
                        all_meetings.extend(meetings_batch)
                        logger.info(f"Fetched {len(meetings_batch)} meetings from page {page}")

                        # Check for more pages
                        if "links" in data and "next" in data.get("links", {}):
                            has_more_pages = True
                        else:
                            has_more_pages = False
                    else:
                        logger.warning("No data found in upstream API response")
                        break

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from upstream API: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching from upstream API: {str(e)}")
                break

        logger.info(f"Total meetings fetched from upstream: {len(all_meetings)}")

        # Process each meeting through local API
        for meeting_data in all_meetings:
            meeting_id = None

            # Extract meeting ID from data
            if "id" in meeting_data:
                # Handle different ID formats
                id_str = str(meeting_data["id"])
                if "id=" in id_str:
                    meeting_id = id_str.split("id=")[1].split("&")[0]
                elif id_str.startswith("http"):
                    # Extract ID from URL
                    if "id=" in id_str:
                        meeting_id = id_str.split("id=")[1].split("&")[0]
                    else:
                        # Try to extract numeric ID from end of URL
                        parts = id_str.rstrip("/").split("/")
                        if parts[-1].isdigit():
                            meeting_id = parts[-1]
                else:
                    meeting_id = id_str

            if not meeting_id:
                logger.warning(f"Could not extract meeting ID from: {meeting_data}")
                meetings_failed += 1
                continue

            logger.debug(f"Processing meeting ID: {meeting_id}")
            try:
                # Fetch meeting from local API to trigger caching and ChromaDB ingestion
                logger.debug(f"Fetching meeting {meeting_id} from local API for caching")

                response = meetings_meetings_get.sync(client=local_api_client, id=int(meeting_id))

                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error for meeting {meeting_id}: {response}")
                    meetings_failed += 1
                elif isinstance(response, MeetingResponse):
                    meeting_name = response.name if response.name is not UNSET else "Unnamed"
                    logger.info(f"Successfully cached meeting {meeting_id}: {meeting_name}")

                    # Download associated files if configured
                    if response.invitation and response.invitation.id:
                        invitation_id = httpx.URL(response.invitation.id).params.get("id")
                        if invitation_id:
                            logger.debug(f"Downloading invitation file for {meeting_id}")
                            download_entity_task.apply_async(
                                args=["file", invitation_id],
                                kwargs={"config_dict": task_config},
                            )

                    if response.verbatim_protocol and response.verbatim_protocol.access_url:
                        logger.debug(f"Downloading verbatim protocol for {meeting_id}")
                        download_direct_url_task.apply_async(
                            args=[
                                response.verbatim_protocol.access_url,
                                str(task_config["base_path"]),
                            ],
                            kwargs={
                                "filename": f"protocol_{meeting_id}_verbatim.pdf",
                                "config_dict": task_config,
                            },
                        )

                    # get all AgendaItems and fetch them via local API
                    if response.agenda_item:
                        for item in response.agenda_item:
                            item_id = item.id
                            if item_id:
                                item_id_str = str(item_id)
                                if "id=" in item_id_str:
                                    item_id_str = item_id_str.split("id=")[1].split("&")[0]
                                logger.debug(f"Processing agenda item {item_id_str} for meeting {meeting_id}")
                                # Fetch agenda item using Celery task
                                try:
                                    # Convert string ID to integer for the task
                                    item_id_int = int(item_id_str)
                                    
                                    # Queue the agenda item fetch task asynchronously
                                    fetch_agenda_item_task.apply_async(
                                        args=[item_id_int],
                                        kwargs={},
                                        retry=True,
                                        retry_policy={
                                            'max_retries': 3,
                                            'interval_start': 0,
                                            'interval_step': 0.2,
                                            'interval_max': 0.2,
                                        }
                                    )
                                    logger.info(f"Queued agenda item fetch task for {item_id_str} (meeting {meeting_id})")
                                
                                except ValueError:
                                    logger.error(f"Invalid agenda item ID format: {item_id_str}")
                                except Exception as e:
                                    logger.error(f"Failed to queue agenda item task {item_id_str} for meeting {meeting_id}: {e}")

                    meetings_processed += 1
                else:
                    logger.warning(f"Unexpected response type for meeting {meeting_id}")
                    meetings_failed += 1

            except sdk_errors.UnexpectedStatus as e:
                logger.error(f"Failed to fetch meeting {meeting_id} from local API: {e}")
                meetings_failed += 1
            except Exception as e:
                logger.error(f"Error processing meeting {meeting_id}: {str(e)}")
                meetings_failed += 1

    except Exception as e:
        logger.error(f"Unexpected error during timeframe meeting sync: {str(e)}")
        raise self.retry(exc=e, countdown=60)

    result = {
        "timeframe": {
            "created_since": created_since,
            "created_until": created_until,
        },
        "total_meetings": len(all_meetings),
        "meetings_processed": meetings_processed,
        "meetings_failed": meetings_failed,
        "success_rate": meetings_processed / len(all_meetings) if all_meetings else 0,
    }

    logger.info(f"Timeframe meeting sync completed: {result}")
    return result
