import json
from pathlib import Path
from typing import Annotated

import chromadb
import cyclopts
import rich
from chromadb.config import Settings
from cyclopts import App
from loguru import logger
from pydantic import DirectoryPath

from stadt_bonn_oparl.config import CLI_QUERYABLE_OPARL_TYPES
from stadt_bonn_oparl.papers.models import UnifiedPaper
from stadt_bonn_oparl.papers.vector_db import VectorDb

vectordb = App(name="vectordb", help="Ingest OPARL Papers into VectorDB")


@vectordb.command()
def ingest(data_path: DirectoryPath, vectordb_name: str = "vectordb-100") -> bool:
    """
    Ingest (add or update) OPARL Papers, including metadata, analysis and content, to VectorDB.

    Parameters
    ----------
    data_path: DirectoryPath
        Path to the directory containing OPARL Papers in PDF file
    vector_db_name: str
        Name of the VectorDB to ingest data into
    """
    db = VectorDb(vectordb_name)

    # Check if the directory exists
    if not data_path.exists():
        logger.error(f"Directory {data_path} does not exist.")
        return False

    for dir_path in data_path.iterdir():
        try:
            rats_info = _create_paper(dir_path)
            doc_id = db.create_document(rats_info)
            logger.debug(f"Document created with ID: {doc_id}")
        except FileNotFoundError as e:
            logger.error(e)

    return True


def _create_paper(data_path: DirectoryPath) -> UnifiedPaper:
    """
    Create a Paper object from a directory path.
    """
    # Assuming the directory contains metadata.json and content.txt files
    metadata_path = data_path / "metadata.json"
    analysis_path = data_path / "analysis.json"
    content_path = data_path.glob("*.md")  # Get the first markdown file
    content = ""
    analysis = {}
    metadata = {}

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found in {data_path}")
    if not content_path:
        raise FileNotFoundError(f"No markdown files found in {data_path}")

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    with open(analysis_path, "r") as f:
        analysis = json.load(f)

    for file in content_path:
        if file.suffix == ".md":
            with open(file, "r") as f:
                content = f.read()

    return UnifiedPaper(
        paper_id=metadata.get("id"),
        metadata=metadata,
        markdown_text=content,
        analysis=analysis,
        enrichment_status="enriched",
        external_oparl_data={},
    )


@vectordb.command()
def query(oparl_type: CLI_QUERYABLE_OPARL_TYPES, query_text: str):
    """
    Query the VectorDB for a specific OParl type and query text.

    Parameters
    ----------
    oparl_type: str
        The type of OParl object to query (e.g., "Paper", "Meeting")
    query_text: str
        The text to search for in the VectorDB
    """

    chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(
            anonymized_telemetry=False,  # disable posthog telemetry
        ),
    )

    if oparl_type == "Organization":
        organizations_collection = chromadb_client.get_or_create_collection(
            name="organizations"
        )

        rich.print(
            f"[yellow]Searching for organizations with query: {query_text}[/yellow]"
        )
        results = organizations_collection.query(
            query_texts=[query_text],
            where_document={"$contains": query_text},
            n_results=10,
        )

        if not results["documents"]:
            rich.print("[red]No organizations found matching the query.[/red]")
            return

        rich.print(f"[green]Found {len(results['documents'])} organizations:[/green]")
        rich.print(results)


# Type aliases for common parameters
UseCelery = Annotated[
    bool,
    cyclopts.Parameter(
        help="Use Celery tasks for distributed processing",
    ),
]

WaitForCompletion = Annotated[
    bool,
    cyclopts.Parameter(
        help="Wait for Celery tasks to complete (use --no-wait to submit without waiting)",
    ),
]

ChromaDBTimeout = Annotated[
    int,
    cyclopts.Parameter(
        help="ChromaDB operation timeout in seconds",
    ),
]

CollectionName = Annotated[
    str,
    cyclopts.Parameter(
        help="ChromaDB collection name",
    ),
]


@vectordb.command(name="upsert-markdown")
def upsert_paper_markdown(
    paper_id: str,
    markdown_file: Path,
    *,
    use_celery: UseCelery = False,
    wait: WaitForCompletion = True,
    timeout: ChromaDBTimeout = 300,
) -> None:
    """
    Upsert a paper's markdown content to ChromaDB.

    Args:
        paper_id: The paper ID or reference number
        markdown_file: Path to the markdown file
        use_celery: Use Celery task for async processing
        wait: Wait for Celery task to complete (use --no-wait to submit without waiting)
        timeout: Operation timeout in seconds
    """
    if not markdown_file.exists():
        logger.error(f"Markdown file not found: {markdown_file}")
        return

    if markdown_file.suffix.lower() != ".md":
        logger.error(f"File is not a markdown file: {markdown_file}")
        return

    if use_celery:
        from stadt_bonn_oparl.tasks.chromadb import upsert_paper_markdown_task

        # Submit task to Celery
        rich.print("📤 Submitting paper markdown upsert task to Celery...")
        task = upsert_paper_markdown_task.apply_async(
            args=[paper_id, str(markdown_file), None]
        )

        if not wait:
            rich.print(
                f"[bold green]✅ Submitted upsert task for paper {paper_id}[/bold green]"
            )
            rich.print(f"[dim]Task ID: {task.id}[/dim]")
            rich.print(
                "\\n💡 Task is running in the background. Check Celery logs for progress."
            )
            return

        # Wait for result
        rich.print("[bold]⏳ Waiting for upsert to complete...[/bold]")
        try:
            result = task.get(timeout=timeout)
            if result["status"] == "success":
                rich.print(
                    f"✅ Successfully {result['operation']}d paper {paper_id} in collection 'papers'"
                )
                rich.print(
                    f"  📄 Content length: {result['content_length']} characters"
                )
                rich.print(
                    f"  📊 Metadata fields: {', '.join(result['metadata_fields'])}"
                )
            elif result["status"] == "error":
                rich.print(f"❌ Upsert failed: {result.get('error', 'Unknown error')}")
            elif result["status"] == "skipped":
                rich.print(
                    f"⚠️  Upsert skipped: {result.get('reason', 'Unknown reason')}"
                )
        except Exception as e:
            logger.error(f"❌ Upsert failed: {e}")
        return

    rich.print("[red]This is not implemented![/red]")


@vectordb.command(name="get-paper")
def get_paper_from_chromadb(
    paper_id: str,
    *,
    use_celery: UseCelery = True,
    timeout: ChromaDBTimeout = 60,
) -> None:
    """
    Retrieve a paper from ChromaDB by ID.

    Args:
        paper_id: The paper ID to retrieve
        use_celery: Use Celery task for async processing
        timeout: Operation timeout in seconds
    """
    if use_celery:
        from stadt_bonn_oparl.tasks.chromadb import get_paper_from_chromadb_task

        # Submit task to Celery
        rich.print("📤 Submitting paper retrieval task to Celery...")
        task = get_paper_from_chromadb_task.apply_async(args=[paper_id])

        # Wait for result
        rich.print("[bold]⏳ Waiting for retrieval to complete...[/bold]")
        try:
            result = task.get(timeout=timeout)
            _display_paper_result(result)
        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
        return

    rich.print("[red]This is not implemented![/red]")


def _display_paper_result(result: dict) -> None:
    """Helper function to display paper retrieval results."""
    if result["status"] == "found":
        rich.print(f"[green]✅ Found paper {result['paper_id']}[/green]")

        metadata = result.get("metadata", {})
        if metadata:
            rich.print("\n[bold]📊 Metadata:[/bold]")
            for key, value in metadata.items():
                rich.print(f"  {key}: {value}")

        document = result.get("document")
        if document:
            content_preview = (
                document[:200] + "..." if len(document) > 200 else document
            )
            rich.print("\n[bold]📄 Content preview:[/bold]")
            rich.print(f"  Length: {len(document)} characters")
            rich.print(f"  Preview: {content_preview}")

    elif result["status"] == "not_found":
        rich.print(
            f"[red]❌ Paper {result['paper_id']} not found in collection '{result['collection']}'[/red]"
        )
    elif result["status"] == "error":
        rich.print(
            f"[red]❌ Error retrieving paper: {result.get('error', 'Unknown error')}[/red]"
        )
    else:
        rich.print(
            f"[yellow]⚠️  Unknown status: {result.get('status', 'Unknown')}[/yellow]"
        )
