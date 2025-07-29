import uuid

import chromadb
import httpx
import rich
from chromadb.config import Settings
from cyclopts import App
from loguru import logger
from pydantic import DirectoryPath

from stadt_bonn_oparl.api.helpers.meetings import _get_meeting
from stadt_bonn_oparl.api.models import MeetingResponse
from stadt_bonn_oparl.cli.helpers import (
    print_agenda_items,
    print_meeting_overview,
    print_participant,
)
from stadt_bonn_oparl.config import OPARL_BASE_URL, UPSTREAM_API_URL
from stadt_bonn_oparl.tasks.download import download_entity_task

meeting = App(name="meeting", help="work with OParl meetings present in VectorDB")


@meeting.command()
async def get(
    data_path: DirectoryPath,
    meeting_id: int,
    detailed: bool = False,
    show_participants: bool = False,
    download_files: bool = True,
):
    """
    Query the VectorDB for a specific Meeting by its ID and get/print it.

    Parameters
    ----------
    data_path: DirectoryPath
        Path to the directory where OParl data will be saved.
    meeting_id: int
        The ID of the meeting to query.
    detailed: bool
        Show detailed agenda items and all information (default: False)
    show_participants: bool
        Show all meeting participants (default: False)
    download_files: bool
        Download meeting files automatically (default: True)
    """
    result: MeetingResponse | None = None
    http_client = httpx.Client(base_url=OPARL_BASE_URL)
    chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(
            anonymized_telemetry=False,  # disable posthog telemetry
        ),
    )
    task_config = {
        "base_path": str(data_path),
        "create_subdirs": True,
        "timeout": 300,
    }

    collection = chromadb_client.get_collection(name="meetings")

    logger.debug(f"Searching for Sitzung {meeting_id}")

    # first, let's see if we got the meeting in our local VectorDB
    meeting_id_ref = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"{UPSTREAM_API_URL}/meetings?id={meeting_id}")
    )
    _results = collection.get(
        ids=[meeting_id_ref]
    )  # TODO: we need to get the Consultation embedded data like meeting and paper loaded in the background

    if _results and _results["documents"]:
        logger.debug(f"Meeting {meeting_id} found in VectorDB.")
        result = MeetingResponse.model_validate_json(_results["documents"][0])
    else:
        # first, let's get the meeting by its ID from the rest API
        _, result = await _get_meeting(http_client, collection, meeting_id)
        if not result:
            logger.warning(f"Metting with ID {meeting_id} not found.]")
            return

        logger.debug(f"Meeting {meeting_id} found via API.")

    # TODO: take all result.agendaItem and put them into the VectorDB

    # Print meeting overview - compact by default
    print_meeting_overview(result, detailed=detailed)

    # Download invitation file if requested and available
    if download_files and result.invitation:
        if detailed:
            rich.print(f"📄 [green]Einladung:[/green] {result.invitation.accessUrl}")

        # Extract the numeric ID from the invitation URL
        invitation_id = httpx.URL(result.invitation.id).params.get("id")
        
        # schedule the download task for the invitation file
        download_entity_task.apply_async(
            args=["file", invitation_id],
            kwargs={"config_dict": task_config}
        )

    # Print agenda items
    print_agenda_items(
        result.agendaItem,
        detailed=detailed,
        data_path=data_path,
        http_client=http_client,
        download_files=download_files,
    )
    # Download protocol if available and requested
    if download_files and result.verbatimProtocol:
        if detailed:
            rich.print(
                f"📝 [green]Protokoll:[/green] {result.verbatimProtocol.accessUrl}"
            )
        # Schedule direct download from accessUrl instead of going through OParl API
        from stadt_bonn_oparl.tasks.download import download_direct_url_task
        download_direct_url_task.apply_async(
            args=[result.verbatimProtocol.accessUrl, str(data_path)],
            kwargs={"filename": f"protocol_{result.id}_verbatim.pdf", "config_dict": task_config}
        )

    # Print participants only if requested
    if show_participants and result.participant_ref:
        rich.print("\n👥 [bold]Teilnehmende:[/bold]")
        for participant in result.participant_ref:
            print_participant(
                participant=participant,
                http_client=http_client,
            )
    elif result.participant_ref and not detailed:
        rich.print(
            f"\n👥 {len(result.participant_ref)} Teilnehmer (--show-participants für Details)"
        )
