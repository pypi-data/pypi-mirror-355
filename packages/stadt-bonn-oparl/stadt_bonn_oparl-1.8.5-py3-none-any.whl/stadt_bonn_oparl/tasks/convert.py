"""
Celery tasks for downloading OParl entities and converting PDFs.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from celery import shared_task
from loguru import logger

from stadt_bonn_oparl.pdf_conversion_service import (
    ConversionException,
    PDFConversionConfig,
    PDFConversionService,
)


@shared_task(bind=True, max_retries=3)
def convert_pdf_with_chromadb_task(
    self,
    file_path: str,
    output_dir: str,
    config_dict: Optional[Dict[str, Any]] = None,
    upsert_to_chromadb: bool = False,
    paper_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Celery task for converting PDF files to Docling format with optional ChromaDB integration.

    Args:
        file_path: Path to the PDF file to convert
        output_dir: Optional output directory for converted files
        config_dict: Optional configuration dictionary
        upsert_to_chromadb: Whether to upsert the converted markdown to ChromaDB
        paper_id: Paper ID for ChromaDB upsert (required if upsert_to_chromadb=True)

    Returns:
        Dictionary mapping output types to their file paths (as strings)
        If ChromaDB upsert is triggered, includes 'chromadb_task_id' in the result
    """
    try:
        # Create configuration
        config = (
            PDFConversionConfig(**config_dict) if config_dict else PDFConversionConfig()
        )

        # Create conversion service
        with PDFConversionService(config=config) as service:
            # Convert the PDF
            result_paths = service.convert_pdf(
                file_path=Path(file_path),
                output_dir=Path(output_dir) if output_dir and output_dir.strip() else None,
            )

        # Convert Path objects to strings for JSON serialization
        result = {format_type: str(path) for format_type, path in result_paths.items()}

        # Upsert to ChromaDB if requested
        if upsert_to_chromadb and paper_id and "markdown" in result:
            from stadt_bonn_oparl.tasks.chromadb import upsert_paper_markdown_task

            try:
                # Chain the ChromaDB upsert task
                markdown_file_path = result["markdown"]
                
                # Prepare additional metadata from conversion results
                additional_metadata = {
                    "conversion_source": "pdf_conversion",
                    "has_docling": str("docling" in result),
                    "has_json": str("json" in result),
                }
                
                if "docling" in result:
                    additional_metadata["docling_file"] = result["docling"]
                if "json" in result:
                    additional_metadata["json_file"] = result["json"]
                
                upsert_result = upsert_paper_markdown_task.apply_async(
                    args=[paper_id, markdown_file_path, additional_metadata]
                )

                result["chromadb_task_id"] = upsert_result.id
                logger.info(
                    f"Triggered ChromaDB upsert task {upsert_result.id} for paper {paper_id}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to trigger ChromaDB upsert for paper {paper_id}: {e}"
                )
                result["chromadb_error"] = str(e)

        return result

    except ConversionException as e:
        logger.error(f"PDF conversion failed for {file_path}: {e}")
        return {"error": str(e)}

    except Exception as e:
        logger.error(f"PDF conversion task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


# Backward compatibility: Keep the original task for existing Celery workers
@shared_task(bind=True, max_retries=3)
def convert_pdf_task(
    self,
    file_path: str,
    output_dir: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Legacy Celery task for converting PDF files to Docling format (without ChromaDB).
    
    For ChromaDB integration, use convert_pdf_with_chromadb_task instead.
    """
    try:
        # Create configuration
        config = (
            PDFConversionConfig(**config_dict) if config_dict else PDFConversionConfig()
        )

        # Create conversion service
        with PDFConversionService(config=config) as service:
            # Convert the PDF
            result_paths = service.convert_pdf(
                file_path=Path(file_path),
                output_dir=Path(output_dir) if output_dir and output_dir.strip() else None,
            )

        # Convert Path objects to strings for JSON serialization
        return {format_type: str(path) for format_type, path in result_paths.items()}

    except ConversionException as e:
        logger.error(f"PDF conversion failed for {file_path}: {e}")
        return {"error": str(e)}

    except Exception as e:
        logger.error(f"PDF conversion task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
