import chromadb
import httpx
import logfire
import rich
from chromadb.config import Settings
from cyclopts import App
from loguru import logger

from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.helpers.helpers import _get_paper_by_id
from stadt_bonn_oparl.api.helpers.meetings import _get_meeting

consultation = App(name="consultation", help="Summarize a Consultation")


@consultation.command(name="summarize")
async def summarize(
    consultation_id: int,
    bi: int,
) -> bool:
    """
    Summarize a Consultation.

    Args:
        consultation_id (int): The ID of the consultation to summarize.
        bi (int): The BI ID.

    Returns:
        bool: True if the summary was successful, False otherwise.
    """
    logger.info(f"Summarizing consultation {consultation_id}, {bi}")

    http_client = httpx.Client(base_url="http://localhost:8000")
    _chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(
            anonymized_telemetry=False,  # disable posthog telemetry
        ),
    )
    collection = _chromadb_client.get_collection(name="consultations")

    if not collection:
        logger.error("ChromaDB collection 'consultations' not found.")

    _, consultation_data = await _get_consultation(
        http_client, collection, consultation_id, bi
    )
    if consultation_data is None:
        logger.error(f"Consultation {consultation_id} not found.")
        return False

    # get the associated meeting meta-information
    meeting_id = (
        consultation_data.meeting_ref if consultation_data.meeting_ref else None
    )

    # extrace the meeting id from the URL
    if meeting_id and isinstance(meeting_id, str):
        try:
            meeting_id = int(meeting_id.split("=")[-1])
        except ValueError:
            logger.error(f"Invalid meeting ID format: {meeting_id}")
            meeting_id = None

    _, meeting = (
        await _get_meeting(
            http_client,
            None,
            meeting_id,
        )
        if meeting_id
        else None
    )

    if meeting is None:
        logger.error(f"Meeting {meeting_id} not found.")
        return False

    # get meta-information about the paper
    paper_id = consultation_data.paper_ref if consultation_data.paper_ref else None
    if paper_id and isinstance(paper_id, str):
        try:
            paper_id = int(paper_id.split("=")[-1])
        except ValueError:
            logger.error(f"Invalid paper ID format: {paper_id}")
            paper_id = None

    paper_collection = _chromadb_client.get_collection(name="papers")
    paper = (
        await _get_paper_by_id(
            http_client=http_client,
            collection=paper_collection,
            paper_id=paper_id,
        )
        if paper_id
        else None
    )

    if paper is None:
        logger.error(f"Paper {paper_id} not found.")
        return False

    # summarize consultation
    rich.print("[bold green]Beratungsübersicht[/bold green]")
    if meeting:
        rich.print(f"[bold blue]Sitzung:[/bold blue] {meeting.name}")
        rich.print(f"[bold blue]Datum:[/bold blue] {meeting.start}")
        rich.print(f"[bold blue]Ort:[/bold blue] {meeting.location or 'unbekannt'}")
        rich.print(
            f"[bold blue]Drucksache:[/bold blue] {paper.name} ({paper.paperType})"
        )
        rich.print(f"[bold blue]   URL:[/bold blue] {paper.mainFileAccessUrl}")

        if paper.consultation_ref:
            rich.print("[bold blue]   wurde beraten in:[/bold blue]")
            for other_consultation in paper.consultation_ref:
                rich.print(
                    f"[bold blue]       Beratung:[/bold blue] {other_consultation}"
                )

    return True
