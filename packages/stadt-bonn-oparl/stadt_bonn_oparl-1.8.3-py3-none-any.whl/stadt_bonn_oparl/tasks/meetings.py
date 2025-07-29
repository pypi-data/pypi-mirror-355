"""
Celery tasks for synchronizing meeting data from OParl API.
"""

from typing import Dict, Any, Optional
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
                        logger.info(
                            f"Fetched {len(response.data)} meetings from page {page}"
                        )

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
                logger.error(
                    f"Value error (possibly UUID parsing) on page {page}: {str(e)}"
                )
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
                logger.debug(
                    f"Fetching meeting details from local API for ID: {meeting_id}"
                )

                response = meetings_meetings_get.sync(
                    client=api_client, id=int(meeting_id)
                )

                if isinstance(response, HTTPValidationError):
                    logger.error(
                        f"Validation error for meeting {meeting_id}: {response}"
                    )
                    meetings_failed += 1
                elif isinstance(response, MeetingResponse):
                    logger.info(
                        f"Successfully retrieved meeting {meeting_id}: {response.name if response.name is not UNSET else 'Unnamed'}"
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
