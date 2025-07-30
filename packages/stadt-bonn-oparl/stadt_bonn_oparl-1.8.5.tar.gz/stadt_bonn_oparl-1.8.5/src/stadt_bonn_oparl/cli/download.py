"""CLI commands for downloading OParl files and papers."""

from pathlib import Path
from typing import Annotated, Optional

import cyclopts
import logfire
import rich
from cyclopts import App
from loguru import logger
from pydantic import DirectoryPath

from stadt_bonn_oparl.api.client import OParlAPIClient
from stadt_bonn_oparl.processors import download_oparl_pdfs
from stadt_bonn_oparl.download_service import (
    DruchsachenDownloadService,
    DownloadServiceConfig,
    DownloadException,
)

download = App(name="download", help="Download OPARL artifacts")

# Global download parameters as type aliases for reuse
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

DownloadTimeout = Annotated[
    int,
    cyclopts.Parameter(
        help="Download timeout in seconds",
    ),
]

OutputDirectory = Annotated[
    Optional[Path],
    cyclopts.Parameter(
        help="Directory to save the downloaded files (default: ./data-100)",
    ),
]

CreateSubdirs = Annotated[
    bool,
    cyclopts.Parameter(
        help="Create subdirectories for organization",
    ),
]

UpsertToChromaDB = Annotated[
    bool,
    cyclopts.Parameter(
        help="Upsert converted documents to ChromaDB after download",
    ),
]


def _process_papers_celery(
    api_base_url: str,
    data_path: Path,
    start_page: int,
    max_pages: int,
    timeout: int,
    wait: bool,
    upsert_to_chromadb: bool = False,
) -> bool:
    """
    Process papers download using Celery tasks.

    This function fetches paper IDs from the API and submits them as Celery tasks.
    """
    from celery import group
    from stadt_bonn_oparl.tasks.download import download_entity_task

    # First, get the list of paper IDs from the API
    paper_ids = []

    with OParlAPIClient(api_base_url) as client:
        if not client.health_check():
            logger.error(
                f"API server at {api_base_url} is not accessible. Please ensure the server is running."
            )
            return False

        logger.info("Fetching paper IDs from API...")

        # Fetch paper IDs page by page
        for page in range(start_page, start_page + max_pages):
            try:
                # Get papers from the current page
                response = client.get_papers(page=page, limit=100)
                if response and "data" in response:
                    for paper in response["data"]:
                        if "id" in paper:
                            # Extract paper ID from URL
                            paper_id = paper["id"].split("=")[-1]
                            paper_ids.append(int(paper_id))
                else:
                    break  # No more pages
            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break

    if not paper_ids:
        logger.warning("No paper IDs found to download")
        return False

    logger.info(f"Found {len(paper_ids)} papers to download")

    # Prepare configuration for downloads
    config_dict = {
        "base_path": str(data_path),
        "create_subdirs": True,
        "timeout": timeout,
    }

    # Create Celery tasks
    celery_tasks = [
        download_entity_task.s(
            entity_type="paper",
            entity_id=paper_id,
            upsert_to_chromadb=upsert_to_chromadb,
            config_dict=config_dict
        )
        for paper_id in paper_ids
    ]

    # Create and execute task group
    job = group(celery_tasks)
    logger.info(f"📤 Submitting {len(paper_ids)} paper download tasks to Celery...")
    result = job.apply_async()

    if not wait:
        # Don't wait for results
        rich.print(
            f"[bold green]✅ Submitted {len(paper_ids)} paper download tasks to Celery[/bold green]"
        )
        rich.print(f"[dim]Task Group ID: {result.id}[/dim]")
        rich.print(
            "\n💡 Tasks are running in the background. Check Celery logs for progress."
        )
        return True

    # Wait for results
    rich.print("[bold]⏳ Waiting for downloads to complete...[/bold]")

    completed = 0
    successful = 0
    failed = 0

    for task_result in result:
        completed += 1
        try:
            download_path = task_result.get(timeout=timeout)
            if download_path:
                successful += 1
                rich.print(
                    f"✅ [{completed}/{len(paper_ids)}] Downloaded to: {download_path}"
                )
            else:
                failed += 1
                rich.print(
                    f"⚠️  [{completed}/{len(paper_ids)}] Paper not found or already exists"
                )
        except Exception as e:
            failed += 1
            rich.print(f"❌ [{completed}/{len(paper_ids)}] Download failed: {e}")

    # Summary
    rich.print("\n📊 Download Summary:")
    rich.print(f"  ✅ Successful: {successful}")
    rich.print(f"  ❌ Failed: {failed}")
    rich.print(f"  📁 Total: {len(paper_ids)}")

    return successful > 0


@download.command(name="papers")
def download_papers(
    data_path: DirectoryPath,
    start_page: int = 1,
    max_pages: int = 2,
    api_base_url: str = "http://localhost:8000",
    *,
    use_celery: UseCelery = False,
    wait: WaitForCompletion = True,
    timeout: DownloadTimeout = 300,
    upsert_to_chromadb: UpsertToChromaDB = False,
) -> bool:
    """
    Process OParl data and download PDFs via API server.

    Parameters
    ----------
    data_path: DirectoryPath
        Path to the directory where OParl data will be saved.
    start_page: int
        The page number to start downloading from.
    max_pages: int
        The maximum number of pages to download.
    api_base_url: str
        Base URL of the local API server.
    use_celery: bool
        Use Celery tasks for distributed processing.
    wait: bool
        Wait for Celery tasks to complete (use --no-wait to submit without waiting).
    timeout: int
        Download timeout in seconds per file.
    upsert_to_chromadb: bool
        Upsert converted documents to ChromaDB after download.
    """
    logger.info("Starting OParl data processing via API server...")

    logger.debug(
        f"Downloading OParl data via API server {api_base_url}, "
        f"starting at page {start_page} and ending after {max_pages} pages at {start_page + max_pages}..."
    )

    if use_celery:
        # Process using Celery tasks
        return _process_papers_celery(
            api_base_url,
            data_path,
            start_page,
            max_pages,
            timeout,
            wait,
            upsert_to_chromadb,
        )

    # Original direct processing
    with OParlAPIClient(api_base_url) as client:
        # Check if API server is accessible
        if not client.health_check():
            logger.error(
                f"API server at {api_base_url} is not accessible. Please ensure the server is running."
            )
            return False

        with logfire.span(f"downloading OParl data via API server {api_base_url}"):
            total_downloads, actual_pdfs, html_pages = download_oparl_pdfs(
                client,
                start_page=start_page,
                max_pages=max_pages,
                data_path=data_path,
            )

    logger.info(
        f"OParl processing finished. Downloaded {total_downloads} files: {actual_pdfs} actual PDFs, {html_pages} HTML pages"
    )

    if html_pages > 0 and actual_pdfs == 0:
        logger.warning(
            "No actual PDFs were downloaded. The documents appear to be behind an authentication wall. "
            "You may need to obtain access credentials to download the actual PDFs."
        )

    return True


@download.command(name="file")
def download_file(
    file_id: int,
    dtyp: int = 0,
    output_dir: OutputDirectory = None,
    *,
    create_subdirs: CreateSubdirs = True,
    timeout: DownloadTimeout = 300,
    use_celery: UseCelery = True,
    wait: WaitForCompletion = True,
) -> None:
    """
    Download an OParl file by ID.

    Args:
        file_id: The ID of the file to download
        dtyp: The type of file to download
        output_dir: Directory to save the file (default: ./data-100)
        create_subdirs: Create subdirectories for organization
        timeout: Download timeout in seconds
        use_celery: Use Celery task for async processing
        wait: Wait for Celery task to complete (use --no-wait to submit without waiting)
    """
    task_config = {
        "base_path": str(output_dir or Path("./data-100")),
        "create_subdirs": create_subdirs,
        "timeout": timeout,
    }

    if use_celery:
        from stadt_bonn_oparl.tasks.download import download_entity_task

        # Submit task to Celery
        logger.info(f"📤 Submitting file {file_id} download task to Celery...")
        task = download_entity_task.apply_async(
            args=["file", file_id, dtyp, task_config]
        )

        if not wait:
            rich.print(
                f"[bold green]✅ Submitted download task for file {file_id}[/bold green]"
            )
            rich.print(f"[dim]Task ID: {task.id}[/dim]")
            rich.print(
                "\n💡 Task is running in the background. Check Celery logs for progress."
            )
            return

        # Wait for result
        rich.print("[bold]⏳ Waiting for download to complete...[/bold]")
        try:
            download_path = task.get(timeout=timeout)
            if download_path:
                rich.print(f"✅ Downloaded file to: {download_path}")
            else:
                rich.print("⚠️  File not found or already exists")
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
        return

    # Direct download without Celery
    config = DownloadServiceConfig(**task_config)

    try:
        with DruchsachenDownloadService(config=config) as server:
            download_path = server.download_file_sync(file_id, "file")
            logger.success(f"✅ Downloaded file to: {download_path}")
    except DownloadException as e:
        logger.error(f"❌ Download failed: {e}")


@download.command(name="paper")
def download_paper_by_id(
    paper_id: int,
    output_dir: OutputDirectory = None,
    *,
    create_subdirs: CreateSubdirs = True,
    timeout: DownloadTimeout = 300,
    all_files: bool = False,
    use_celery: UseCelery = False,
    wait: WaitForCompletion = True,
    upsert_to_chromadb: UpsertToChromaDB = False,
) -> None:
    """
    Download an OParl paper by ID.

    Args:
        paper_id: The ID of the paper to download
        output_dir: Directory to save the file (default: ./data-100)
        create_subdirs: Create subdirectories for organization
        timeout: Download timeout in seconds
        all_files: Download all associated files (main + auxiliary)
        use_celery: Use Celery task for async processing
        wait: Wait for Celery task to complete (use --no-wait to submit without waiting)
        upsert_to_chromadb: Upsert converted documents to ChromaDB after download
    """
    config_dict = {
        "base_path": str(output_dir or Path("./data-100")),
        "create_subdirs": create_subdirs,
        "timeout": timeout,
    }

    if use_celery:
        from stadt_bonn_oparl.tasks.download import download_entity_task

        # Submit task to Celery
        rich.print(f"📤 Submitting paper {paper_id} download task to Celery...")
        task = download_entity_task.apply_async(
            args=["paper", paper_id, upsert_to_chromadb, config_dict]
        )

        if not wait:
            rich.print(
                f"[bold green]✅ Submitted download task for paper {paper_id}[/bold green]"
            )
            rich.print(f"[dim]Task ID: {task.id}[/dim]")
            rich.print(
                "\n💡 Task is running in the background. Check Celery logs for progress."
            )
            return

        # Wait for result
        rich.print("[bold]⏳ Waiting for download to complete...[/bold]")
        try:
            download_path = task.get(timeout=timeout)
            if download_path:
                rich.print(f"✅ Downloaded paper to: {download_path}")
            else:
                rich.print("⚠️  Paper not found or already exists")
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
        return

    # Direct download without Celery
    config = DownloadServiceConfig(**config_dict)

    try:
        with DruchsachenDownloadService(config=config) as server:
            if all_files:
                # Download all files associated with the paper
                import asyncio

                downloads = asyncio.run(server.download_paper_files(paper_id))

                rich.print(f"✅ Downloaded {len(downloads)} files:")
                for file_type, path in downloads.items():
                    logger.info(f"  - {file_type}: {path}")
            else:
                # Download only the main file
                download_path = server.download_file_sync(paper_id, "paper")
                rich.print(f"✅ Downloaded paper to: {download_path}")

    except DownloadException as e:
        logger.error(f"❌ Download failed: {e}")


def _process_direct_downloads(
    entity_type: str,
    ids: list[int],
    config_dict: dict,
) -> None:
    """Helper function to process downloads directly without Celery."""
    logger.info("Running downloads directly (without Celery)...")

    config = DownloadServiceConfig(**config_dict)
    successful = 0
    failed = 0

    with DruchsachenDownloadService(config=config) as server:
        for i, entity_id in enumerate(ids, 1):
            try:
                download_path = server.download_file_sync(entity_id, entity_type)
                successful += 1
                rich.print(
                    f"✅ [{i}/{len(ids)}] Downloaded {entity_type} {entity_id} to: {download_path}"
                )
            except Exception as e:
                failed += 1
                logger.error(
                    f"❌ [{i}/{len(ids)}] Failed to download {entity_type} {entity_id}: {e}"
                )

    # Summary
    rich.print("\n📊 Download Summary:")
    rich.print(f"  ✅ Successful: {successful}")
    rich.print(f"  ❌ Failed: {failed}")
    rich.print(f"  📁 Total: {len(ids)}")

    if failed > 0:
        logger.warning("Some downloads failed. Check the logs for details.")


def _process_celery_downloads(
    entity_type: str,
    ids: list[int],
    config_dict: dict,
    timeout: int,
    wait: bool,
    upsert_to_chromadb: bool = False,
) -> None:
    """Helper function to process downloads using Celery."""
    # Import Celery task and group
    from celery import group
    from stadt_bonn_oparl.tasks.download import download_entity_task

    # Create Celery tasks for each entity
    celery_tasks = [
        download_entity_task.s(entity_type, entity_id, upsert_to_chromadb, config_dict)
        for entity_id in ids
    ]

    # Create a group of tasks
    job = group(celery_tasks)

    # Execute all tasks
    logger.info(f"📤 Submitting {len(ids)} download tasks to Celery...")
    result = job.apply_async()

    if not wait:
        # Don't wait for results
        rich.print(
            f"[bold green]✅ Submitted {len(ids)} download tasks to Celery[/bold green]"
        )
        rich.print(f"[dim]Task Group ID: {result.id}[/dim]")
        rich.print(
            "\n💡 Tasks are running in the background. Check Celery logs for progress."
        )
        return

    # Wait for results with progress tracking
    rich.print("[bold]⏳ Waiting for downloads to complete...[/bold]")

    completed = 0
    failed_downloads = []
    successful_downloads = []

    # Get results as they complete
    for task_result in result:
        completed += 1
        try:
            download_path = task_result.get(timeout=timeout)
            successful_downloads.append(download_path)
            rich.print(f"✅ [{completed}/{len(ids)}] Downloaded to: {download_path}")
        except Exception as e:
            failed_downloads.append(str(e))
            rich.print(f"❌ [{completed}/{len(ids)}] Download failed: {e}")

    # Summary
    rich.print("\n📊 Download Summary:")
    rich.print(f"  ✅ Successful: {len(successful_downloads)}")
    rich.print(f"  ❌ Failed: {len(failed_downloads)}")
    rich.print(f"  📁 Total: {len(ids)}")

    if failed_downloads:
        logger.warning("Some downloads failed. Check the logs for details.")


@download.command(name="batch")
def download_batch(
    entity_type: str,
    ids_file: Path,
    output_dir: OutputDirectory = None,
    *,
    create_subdirs: CreateSubdirs = True,
    timeout: DownloadTimeout = 300,
    use_celery: UseCelery = True,
    wait: WaitForCompletion = True,
    upsert_to_chromadb: UpsertToChromaDB = False,
) -> None:
    """
    Download multiple files or papers from a list of IDs using Celery tasks.

    Args:
        entity_type: Type of entities to download ('file' or 'paper')
        ids_file: Text file containing one ID per line
        output_dir: Directory to save files (default: ./data-100)
        create_subdirs: Create subdirectories for organization
        timeout: Download timeout in seconds per file
        use_celery: Use Celery tasks for distributed processing
        wait: Wait for Celery tasks to complete (use --no-wait to submit without waiting)
        upsert_to_chromadb: Upsert converted documents to ChromaDB after download
    """
    if entity_type not in ["file", "paper"]:
        logger.error("entity_type must be 'file' or 'paper'")
        return

    if not ids_file.exists():
        logger.error(f"IDs file not found: {ids_file}")
        return

    # Read IDs from file
    with open(ids_file, encoding="utf-8") as f:
        ids = [int(line.strip()) for line in f if line.strip().isdigit()]

    if not ids:
        logger.error("No valid IDs found in file")
        return

    logger.info(f"Found {len(ids)} {entity_type} IDs to download")

    # Prepare configuration
    config_dict = {
        "base_path": str(output_dir or Path("./data-100")),
        "create_subdirs": create_subdirs,
        "timeout": timeout,
    }

    if use_celery:
        _process_celery_downloads(
            entity_type, ids, config_dict, timeout, wait, upsert_to_chromadb
        )
    else:
        _process_direct_downloads(entity_type, ids, config_dict)
