"""
Celery tasks for downloading OParl entities and converting PDFs.
"""

from typing import Any, Dict, Optional, Union

from loguru import logger

from stadt_bonn_oparl.download_service import (
    DownloadFileNotFoundError,
    DownloadServiceConfig,
    DruchsachenDownloadService,
)
from stadt_bonn_oparl.celery import app


@app.task(bind=True, max_retries=3)
def download_entity_task(
    self,
    entity_type: str,
    entity_id: Union[int, str],
    dtyp: Optional[int] = None,
    upsert_to_chromadb: bool = False,
    config_dict: Optional[Dict[str, Any]] = None,
) -> str | None | Dict[str, Any]:
    """
    Celery task for downloading OParl entities.

    Args:
        entity_type: Type of entity ('file' or 'paper')
        entity_id: ID of the entity to download
        config_dict: Optional configuration dictionary
        upsert_to_chromadb: Whether to chain a PDF conversion task with ChromaDB upsert

    Returns:
        Path to the downloaded file as string, or dict with download paths and conversion task ID
    """
    try:
        # Create configuration
        config = (
            DownloadServiceConfig(**config_dict)
            if config_dict
            else DownloadServiceConfig()
        )

        # Create download server
        with DruchsachenDownloadService(config=config) as server:
            if entity_type == "paper":
                # Use the new direct download method for papers
                download_results = server.download_paper_files_direct_sync(entity_id)

                # Get the main file path for compatibility with existing code
                main_file_path = download_results.get("main")
                if not main_file_path:
                    logger.warning(f"No main file downloaded for paper {entity_id}")
                    # Return all downloaded files if no main file
                    if download_results:
                        return {
                            "download_paths": {
                                k: str(v) for k, v in download_results.items()
                            },
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                        }
                    else:
                        return None

                download_path = main_file_path
                download_path_str = str(download_path)

                # Chain PDF conversion task if requested for paper entities
                if upsert_to_chromadb:
                    # Check if the downloaded file is a PDF
                    if download_path_str.lower().endswith(".pdf"):
                        from stadt_bonn_oparl.tasks.convert import (
                            convert_pdf_with_chromadb_task,
                        )

                        # Prepare output directory (same as download directory)
                        output_dir = str(download_path.parent)

                        # Chain the conversion task with paper ID
                        conversion_result = convert_pdf_with_chromadb_task.apply_async(
                            args=[download_path_str, output_dir],
                            kwargs={
                                "upsert_to_chromadb": True,
                                "paper_id": str(entity_id),  # Use entity_id as paper_id
                            },
                        )

                        logger.info(
                            f"Chained PDF conversion task {conversion_result.id} for paper {entity_id}"
                        )

                        return {
                            "download_path": download_path_str,
                            "download_paths": {
                                k: str(v) for k, v in download_results.items()
                            },
                            "conversion_task_id": conversion_result.id,
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                        }

                # Return all downloaded files for paper
                return {
                    "download_path": download_path_str,  # Main file for compatibility
                    "download_paths": {k: str(v) for k, v in download_results.items()},
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                }

            else:
                # Use the existing download method for files
                download_path = server.download_file_sync(entity_id, entity_type, dtyp)
                download_path_str = str(download_path)

                return download_path_str

    except DownloadFileNotFoundError as e:
        logger.error(f"File not found for {entity_type} {entity_id}: {e}")
        return None

    except Exception as e:
        logger.error(f"Download task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


@app.task(bind=True, max_retries=3)
def download_direct_url_task(
    self,
    url: str,
    data_path: str,
    filename: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
) -> str | None:
    """
    Celery task for downloading files directly from a URL.

    Args:
        url: Direct URL to download from
        data_path: Directory to save the file to
        filename: Optional filename, will be inferred from URL if not provided
        config_dict: Optional configuration dictionary

    Returns:
        Path to the downloaded file as string, or None if failed
    """
    try:
        import asyncio
        from pathlib import Path
        import httpx
        from urllib.parse import urlparse

        # Create configuration
        config = (
            DownloadServiceConfig(**config_dict)
            if config_dict
            else DownloadServiceConfig()
        )

        # Override base path with provided data_path
        config.base_path = Path(data_path)
        config.base_path.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if not filename:
            parsed = urlparse(url)
            filename = Path(parsed.path).name or "downloaded_file"

        download_path = config.base_path / filename

        # Skip if file already exists
        if download_path.exists():
            logger.info(f"File already exists: {download_path}")
            return str(download_path)

        # Download the file directly
        logger.info(f"Downloading {url} to {download_path}")

        async def download():
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(config.timeout)
            ) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    # Write to temporary file first
                    temp_path = download_path.with_suffix(download_path.suffix + ".tmp")

                    with open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes(
                            chunk_size=config.chunk_size
                        ):
                            f.write(chunk)

                    # Move to final location
                    temp_path.rename(download_path)

        # Run the async download
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(download())

        logger.info(f"Successfully downloaded to {download_path}")

        # schedule a conversion and upsert task if the file is a PDF
        if download_path.suffix.lower() == ".pdf":
            # check if the file has the significant PDF header
            with open(download_path, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    logger.warning(
                        f"Downloaded file {download_path} is not a valid PDF."
                    )
                    return str(download_path)

            from stadt_bonn_oparl.tasks.convert import convert_pdf_with_chromadb_task

            # Prepare output directory (same as download directory)
            output_dir = str(download_path.parent)

            # Chain the conversion task
            conversion_result = convert_pdf_with_chromadb_task.apply_async(
                args=[str(download_path), output_dir],
                kwargs={"upsert_to_chromadb": True},
            )

            logger.info(
                f"Chained PDF conversion task {conversion_result.id} for direct download"
            )

            return {
                "download_path": str(download_path),
                "conversion_task_id": conversion_result.id,
            }

        return str(download_path)

    except Exception as e:
        logger.error(f"Direct download task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
