import json
from pathlib import Path

import httpx
from loguru import logger

from stadt_bonn_oparl.celery import app
from stadt_bonn_oparl.logging import configure_logging
from stadt_bonn_oparl.models import OParlFile
from stadt_bonn_oparl.utils import download_file, sanitize_name

configure_logging(2)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=15,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def download_oparl_file(self, _data_path: str, _file: str) -> bool:
    """Download a file and save it to the specified path.

    Args:
        data_path: Path to save the downloaded file
        file: OParlFile object containing file metadata

    Returns:
        bool: True if download was successful, False otherwise
    """
    if not _data_path:
        logger.error("No data path provided.")
        return False

    data_path = Path(_data_path)
    file = OParlFile.model_validate_json(_file)
    logger.info(f"Downloading file: {file.id} - {file.name}")

    try:
        response = httpx.get(file.id, timeout=30)

        if response.status_code == 200:
            _metadata = response.json()
            logger.info(f"Downloading file: {file.name}: {_metadata}")

            paper_name = file.name
            paper_date = file.date if file.date else ""

            # Create a sanitized name for the file
            file_prefix = ""
            if paper_date:
                file_prefix += f"{paper_date} "

            paper_dir_name = sanitize_name(f"{file_prefix}{paper_name}")
            file_dir = data_path / paper_dir_name
            file_dir.mkdir(parents=True, exist_ok=True)

            # Save metadata
            try:
                metadata_path = file_dir / "metadata.json"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(_metadata, f, ensure_ascii=False, indent=2)
                logger.debug(f"Saved metadata for {file_dir} to {metadata_path}")
            except Exception as e:
                logger.error(f"Failed to save metadata for {file_dir}: {e}")

            # Download file from the access URL

            if _metadata.get("accessUrl"):
                file_url = _metadata.get("accessUrl")
                file_name = _metadata.get("fileName", "document.pdf")
                download_path = file_dir / sanitize_name(file_name)

                # Check if the file already exists
                if download_path.exists():
                    logger.info(f"File already exists: {download_path}")
                    return False

                success, content_type = download_file(
                    file_url,
                    download_path,
                    item_title=f"PDF for '{paper_name}'",
                    check_pdf=True,
                )

            return True
        else:
            logger.error(f"Failed to download {file.id}: HTTP {response.status_code}")
            raise Exception(f"HTTP {response.status_code} for {file.id}")

    except Exception as e:
        logger.error(f"Error saving {file.id}: {e}")
        raise self.retry(exc=e, countdown=5)
