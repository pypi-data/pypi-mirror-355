"""
Celery tasks for ChromaDB operations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from celery import Celery, shared_task
from loguru import logger

from stadt_bonn_oparl.api.models import PaperResponse
from stadt_bonn_oparl.chromadb_utils import get_collection
from stadt_bonn_oparl.logging import configure_logging
from stadt_bonn_oparl.utils import generate_paper_reference_data
from stadt_bonn_oparl.celery import app


configure_logging(2)


class ChromaDBTaskException(Exception):
    """Base exception for ChromaDB task errors."""


class PaperNotFoundError(ChromaDBTaskException):
    """Exception raised when a paper cannot be found."""


class MarkdownFileNotFoundError(ChromaDBTaskException):
    """Exception raised when a markdown file cannot be found."""


@shared_task(bind=True, max_retries=3)
def upsert_paper_markdown_task(
    self,
    paper_id: str,
    markdown_file_path: str,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Celery task to upsert paper markdown content to ChromaDB.

    Args:
        paper_id: The OParl paper ID or reference number
        markdown_file_path: Path to the markdown file
        additional_metadata: Optional additional metadata to include

    Returns:
        Dictionary with operation result and paper information
    """
    try:
        # Validate inputs
        markdown_path = Path(markdown_file_path)
        if not markdown_path.exists():
            raise MarkdownFileNotFoundError(
                f"Markdown file not found: {markdown_file_path}"
            )

        if markdown_path.suffix.lower() != ".md":
            raise ChromaDBTaskException(
                f"File is not a markdown file: {markdown_file_path}"
            )

        # Read markdown content
        with open(markdown_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        if not markdown_content.strip():
            logger.warning(f"Markdown file is empty: {markdown_file_path}")
            return {
                "status": "skipped",
                "reason": "empty_file",
                "paper_id": paper_id,
                "file_path": markdown_file_path,
            }

        # Get ChromaDB collection
        collection = get_collection("papers")

        # Convert paper_id to internal reference and UUID format
        _paper_ref, _paper_id = generate_paper_reference_data(paper_id)

        # Check if paper already exists in collection
        existing_papers = collection.get(
            ids=[str(_paper_id)], include=["documents", "metadatas"]
        )

        base_metadata = {
            "id": str(_paper_id),
            "id_ref": _paper_ref,
            "paper_id": paper_id,
            "content_type": "markdown",
            "source_file": str(markdown_path),
            "file_stem": markdown_path.stem,
            "last_updated": str(markdown_path.stat().st_mtime),
        }

        if additional_metadata:
            base_metadata.update(additional_metadata)

        # Filter metadata to only include ChromaDB-compatible types
        filtered_metadata = {
            k: v
            for k, v in base_metadata.items()
            if isinstance(v, (str, int, float, bool)) and v is not None
        }

        # preserve the existing document and add an attribute 'markdown_content' to it
        existing_paper = None
        if existing_papers["documents"]:
            existing_paper = PaperResponse.model_validate_json(
                existing_papers["documents"][0]
            )
            existing_paper.markdown_content = markdown_content

        operation_type = "update" if existing_papers["ids"] else "create"

        # Upsert the paper if we have an existing_document
        if existing_paper:
            logger.debug(
                f"Upserting existing paper {_paper_id} with updated markdown content: {existing_paper}"
            )
            collection.upsert(
                ids=[str(_paper_id)],
                documents=[existing_paper.model_dump_json()],
            )

        return {
            "status": "success",
            "operation": operation_type,
            "paper_id": paper_id,
            "file_path": markdown_file_path,
            "content_length": len(markdown_content),
            "metadata_fields": list(filtered_metadata.keys()),
        }

    except MarkdownFileNotFoundError as e:
        logger.error(f"Markdown file not found for paper {paper_id}: {e}")
        return {
            "status": "error",
            "error_type": "file_not_found",
            "paper_id": paper_id,
            "file_path": markdown_file_path,
            "error": str(e),
        }

    except Exception as e:
        logger.error(f"ChromaDB upsert task failed for paper {paper_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def update_paper_with_converted_content_task(
    self,
    paper_id: str,
    conversion_result: Dict[str, str],
    collection_name: str = "papers",
) -> Dict[str, Any]:
    """
    Update a paper in ChromaDB with converted PDF content (markdown, docling, json).

    Args:
        paper_id: The OParl paper ID or reference number
        conversion_result: Result from PDF conversion containing file paths
        collection_name: ChromaDB collection name (default: "papers")

    Returns:
        Dictionary with operation result
    """
    try:
        if "error" in conversion_result:
            logger.error(
                f"Cannot update paper {paper_id}: conversion failed with error: {conversion_result['error']}"
            )
            return {
                "status": "error",
                "error_type": "conversion_failed",
                "paper_id": paper_id,
                "error": conversion_result["error"],
            }

        # Extract file paths from conversion result
        markdown_path = conversion_result.get("markdown")
        docling_path = conversion_result.get("docling")
        json_path = conversion_result.get("json")

        if not markdown_path:
            raise ChromaDBTaskException("No markdown path found in conversion result")

        # Read content from converted files
        content_data = {}

        # Read markdown content (primary content)
        markdown_file = Path(markdown_path)
        if markdown_file.exists():
            with open(markdown_file, "r", encoding="utf-8") as f:
                content_data["markdown_content"] = f.read()
        else:
            raise MarkdownFileNotFoundError(
                f"Converted markdown file not found: {markdown_path}"
            )

        # Read JSON metadata if available
        if json_path and Path(json_path).exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    json_content = json.load(f)
                    content_data["docling_metadata"] = json_content
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON file {json_path}: {e}")

        # Prepare metadata for ChromaDB
        metadata = {
            "paper_id": paper_id,
            "content_type": "converted_pdf",
            "markdown_file": str(markdown_path),
            "conversion_timestamp": str(Path(markdown_path).stat().st_mtime),
            "has_docling": str(bool(docling_path and Path(docling_path).exists())),
            "has_json": str(bool(json_path and Path(json_path).exists())),
        }

        if docling_path:
            metadata["docling_file"] = str(docling_path)
        if json_path:
            metadata["json_file"] = str(json_path)

        # Get ChromaDB collection and upsert
        collection = get_collection("papers")

        # Use markdown content as the primary document content for search
        collection.upsert(
            ids=[paper_id],
            documents=[content_data["markdown_content"]],
            metadatas=[metadata],
        )

        logger.info(
            f"Successfully updated paper {paper_id} with converted content in ChromaDB"
        )

        return {
            "status": "success",
            "operation": "update_with_conversion",
            "paper_id": paper_id,
            "files_processed": {
                "markdown": bool(markdown_path),
                "docling": bool(docling_path and Path(docling_path).exists()),
                "json": bool(json_path and Path(json_path).exists()),
            },
            "content_length": len(content_data["markdown_content"]),
        }

    except Exception as e:
        logger.error(f"Failed to update paper {paper_id} with converted content: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


@app.task(bind=True)
def get_paper_from_chromadb_task(
    self,
    paper_id: str,
) -> Dict[str, Any]:
    """
    Retrieve a paper from ChromaDB by ID.

    Args:
        paper_id: The paper ID to retrieve

    Returns:
        Dictionary with paper data or error information
    """
    try:
        collection = get_collection("papers")
        _paper_ref, _paper_id = generate_paper_reference_data(paper_id)
        result = collection.get(ids=[_paper_id], include=["documents", "metadatas"])

        if not result["ids"]:
            return {
                "status": "not_found",
                "paper_id": paper_id,
            }

        paper_data = {
            "status": "found",
            "paper_id": paper_id,
            "document": result["documents"][0] if result["documents"] else None,
            "metadata": result["metadatas"][0] if result["metadatas"] else {},
        }

        return paper_data

    except Exception as e:
        logger.error(f"Failed to retrieve paper {paper_id} from ChromaDB: {e}")
        return {
            "status": "error",
            "paper_id": paper_id,
            "collection": "papers",
            "error": str(e),
        }
