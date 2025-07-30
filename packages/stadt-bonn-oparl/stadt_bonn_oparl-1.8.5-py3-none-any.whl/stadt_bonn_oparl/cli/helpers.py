from pathlib import Path

import httpx
import logfire
import rich
from loguru import logger

from stadt_bonn_oparl.api.models import Consultation, MeetingResponse
from stadt_bonn_oparl.config import OPARL_BASE_URL
from stadt_bonn_oparl.models import OParlAgendaItem, OParlFile
from stadt_bonn_oparl.tasks.download import download_entity_task


def print_agenda_item(
    agenda_item: OParlAgendaItem,
    data_path: Path,
    http_client: httpx.Client,
    download_files: bool = True,
):
    """
    Print the details of an agenda item, including its consultation and files.

    Args:
        agenda_item (AgendaItemResponse): The agenda item to print.
        data_path (Path): The path to the directory where files will be downloaded.
        http_client (httpx.Client): The HTTP client to use for API requests.
    """

    if agenda_item.consultation:
        cid = httpx.URL(agenda_item.consultation).params.get("id")
        bi = httpx.URL(agenda_item.consultation).params.get("bi")

        c = http_client.get(f"{OPARL_BASE_URL}/consultations/?id={cid}&bi={bi}")
        if c.status_code != 200:
            rich.print(f"[red]Error fetching consultation {cid}[/red]")

        logger.debug(f"Fetched consultation {cid} for agenda item {agenda_item.id}")
        logger.debug(f"Consultation data: {c.json()}")
        consultation = Consultation.model_validate_json(c.text)

        rich.print(
            f"  📋 [green]Drucksache:[/green] {consultation.paper_ref} (ID: {consultation.id})"
        )

        # schedule a download of the consultation paper
        if consultation.paper_ref and download_files:
            # extract the paper ID from the URL
            paper_id = httpx.URL(consultation.paper_ref).params.get("id")
            if paper_id:
                config_dict = {
                    "base_path": str(Path("./data-100")),
                    "create_subdirs": True,
                    "timeout": 300,
                }
                logger.debug(
                    f"Scheduling download for consultation paper {paper_id} with config {config_dict}"
                )
                condif_dict = {
                    "base_path": str(data_path),
                    "create_subdirs": True,
                    "timeout": 300,
                }
                download_entity_task.s("paper", paper_id, True, config_dict=config_dict)

    # if available, print all the files (only if they have an accessUrl) associated with the agenda item
    if download_files and agenda_item.resolutionFile:
        _resolution_oparl_file = OParlFile(**agenda_item.resolutionFile)
        if agenda_item.resolutionFile.get("accessUrl"):
            rich.print(
                f"  📄 [green]Beschluss:[/green] {agenda_item.resolutionFile['accessUrl']}"
            )
            config_dict = {
                "base_path": str(data_path),
                "create_subdirs": True,
                "timeout": 300,
            }
            # download_entity_task.delay("file", _resolution_oparl_file.id, config_dict=config_dict)

    if download_files and agenda_item.auxiliaryFile:
        for aux_file in agenda_item.auxiliaryFile:
            _aux_file_oparl_file = OParlFile(**aux_file)
            if aux_file.get("accessUrl"):
                rich.print(
                    f"  📎 [green]Zusatzdokument:[/green] {aux_file['accessUrl']}"
                )
                config_dict = {
                    "base_path": str(data_path),
                    "create_subdirs": True,
                    "timeout": 300,
                }
                # download_entity_task.delay("file", _aux_file_oparl_file.id, config_dict=config_dict)


def print_agenda_items(
    agenda_items, detailed: bool, data_path, http_client, download_files: bool
):
    """Print agenda items in compact or detailed format."""
    if not agenda_items:
        return

    public_items = [item for item in agenda_items if item.name != "(nichtöffentlich)"]

    # Filter out postponed or cancelled items based on result field
    postponed_or_cancelled = [
        "vertagt",
        "bei Anerkennung der Tagesordnung nicht aufgenommen oder vertagt",
        "weitere Lesung erforderlich",
    ]

    # Filter active items (not postponed/cancelled)
    active_items = [
        item
        for item in public_items
        if not (item.result and item.result in postponed_or_cancelled)
    ]

    # Count postponed items for information
    postponed_count = len(public_items) - len(active_items)

    if detailed:
        # Detailed view - show all items with full info
        status_text = f"{len(active_items)} aktive Punkte"
        if postponed_count > 0:
            status_text += f", {postponed_count} vertagt/abgesetzt"
        rich.print(f"\n📋 [bold]Tagesordnung ({status_text}):[/bold]")
        for agenda_item in active_items:
            rich.print(f"\n• [bold]{agenda_item.name}[/bold]")
            if detailed:
                rich.print(f"  🆔 {agenda_item.id}")

            print_agenda_item(
                agenda_item=agenda_item,
                data_path=data_path,
                http_client=http_client,
                download_files=download_files,
            )
    else:
        # Compact view - show only active items with consultations (important topics)
        important_items = [item for item in active_items if item.consultation]

        if important_items:
            rich.print(
                f"\n🔗 [bold]Wichtige Themen ({len(important_items)} von {len(active_items)}):[/bold]"
            )
            for i, item in enumerate(
                important_items[:5], 1
            ):  # Show max 5 important items
                rich.print(f"  {i}. {item.name}")

            if len(important_items) > 5:
                rich.print(f"  ... und {len(important_items) - 5} weitere")

            rich.print(f"\nℹ️  Für alle {len(active_items)} TOPs: --detailed")
        else:
            status_msg = f"\n📋 {len(active_items)} aktive Tagesordnungspunkte"
            if postponed_count > 0:
                status_msg += f", {postponed_count} vertagt/abgesetzt"
            status_msg += " (--detailed für Details)"
            rich.print(status_msg)


def print_participant(participant: str, http_client: httpx.Client):
    """
    Print the details of a participant.

    Args:
        participant (str): The URL of the participant.
        http_client (httpx.Client): The HTTP client to use for API requests.
    """
    with logfire.span(
        "Fetching participant information from OParl Cache",
        participant=participant,
    ):
        p_id = httpx.URL(participant).params.get("id")
        response = http_client.get(f"{OPARL_BASE_URL}/persons/?id={p_id}")
        if response.status_code != 200:
            rich.print(f"[red]Error fetching participant {p_id}[/red]")
            return
        person = response.json()

    if not person:
        rich.print(f"[red]Participant {p_id} not found.[/red]")
        return

    affix = ""
    if person.get("affix"):
        affix = f", ({person['affix']})"
    rich.print(
        f"  • [green]{person['name']}{affix}[/green] - {person.get('role', 'keine Rolle in dieser Sitzung')}"
    )


def print_meeting_overview(meeting_result: MeetingResponse, detailed: bool = False):
    """Print a compact or detailed meeting overview."""
    if detailed:
        # Detailed view - current format
        rich.print(f"📅 [bold green]Sitzung:[/bold green] {meeting_result.name}")
        rich.print(f"🆔 [green]ID:[/green] {meeting_result.id}")
        rich.print(f"🕐 [green]Start:[/green] {meeting_result.start}")
        rich.print(f"📊 [green]Status:[/green] {meeting_result.meetingState}")
    else:
        # Compact view
        rich.print(f"📅 [bold]{meeting_result.name}[/bold]")

        # Format date nicely
        start_date = (
            meeting_result.start.strftime("%d.%m.%Y %H:%M")
            if meeting_result.start
            else "TBD"
        )
        rich.print(f"🕐 {start_date} | 📊 {meeting_result.meetingState}")

        # Count agenda items and participants
        agenda_count = len(
            [
                item
                for item in (meeting_result.agendaItem or [])
                if item.name != "(nichtöffentlich)"
            ]
        )
        participant_count = (
            len(meeting_result.participant_ref) if meeting_result.participant_ref else 0
        )

        rich.print(
            f"📋 {agenda_count} Tagesordnungspunkte | 👥 {participant_count} Teilnehmer"
        )

        # Show availability of documents
        docs = []
        if meeting_result.invitation:
            docs.append("📄 Einladung")
        if meeting_result.verbatimProtocol:
            docs.append("📝 Protokoll")

        if docs:
            rich.print(f"{' | '.join(docs)} verfügbar")
