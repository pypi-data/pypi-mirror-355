"""
PDF Conversion Service for converting PDF files to Docling format.

This module provides functionality to convert PDF files to markdown, docling,
and JSON formats using the docling library. It supports both synchronous and
asynchronous operations via Celery tasks.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

import logfire
from loguru import logger
from pydantic import BaseModel


class ConversionException(Exception):
    """Base exception for conversion service errors."""


class ConversionFileNotFoundError(ConversionException):
    """Exception raised when a file cannot be found."""


class ConversionFailedError(ConversionException):
    """Exception raised when a conversion fails."""


class InvalidFileTypeError(ConversionException):
    """Exception raised when file is not a PDF."""


class PDFConversionConfig(BaseModel):
    """Configuration for PDF conversion operations."""

    base_path: Path = Path("./converted")
    create_subdirs: bool = True
    num_threads: int = 12
    do_ocr: bool = False
    chunk_size: int = 8192
    max_retries: int = 3
    overwrite_existing: bool = False


class PDFConversionService:
    """Service for converting PDF files to Docling format."""

    def __init__(self, config: Optional[PDFConversionConfig] = None):
        """
        Initialize the PDF Conversion Service.

        Args:
            config: Conversion configuration (will use defaults if not provided)
        """
        self.config = config or PDFConversionConfig()

        # Ensure base conversion directory exists
        self.config.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"PDF conversion service initialized with base path: {self.config.base_path}"
        )

    def _get_conversion_paths(
        self, file_path: Path, output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Determine the output paths for conversion files.

        Args:
            file_path: Path to the input PDF file
            output_dir: Optional specific output directory

        Returns:
            Dictionary with paths for markdown, docling, and json files
        """
        if output_dir is None:
            if self.config.create_subdirs:
                # Organize by date if available from filename or file stats
                try:
                    file_date = file_path.stat().st_mtime
                    from datetime import datetime

                    date_str = datetime.fromtimestamp(file_date).strftime("%Y-%m-%d")
                    output_dir = self.config.base_path / date_str
                except Exception:
                    output_dir = self.config.base_path / "undated"
            else:
                output_dir = self.config.base_path

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output file paths
        stem = file_path.stem
        return {
            "markdown": output_dir / f"{stem}.md",
            "docling": output_dir / f"{stem}.docling",
            "json": output_dir / f"{stem}.json",
        }

    def _check_existing_files(self, paths: Dict[str, Path]) -> bool:
        """
        Check if all conversion output files already exist.

        Args:
            paths: Dictionary of output file paths

        Returns:
            True if all files exist, False otherwise
        """
        return all(path.exists() for path in paths.values())

    def convert_pdf(
        self,
        file_path: Union[Path, str],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """
        Convert a PDF file to Docling format.

        Args:
            file_path: Path to the PDF file to convert
            output_dir: Optional specific output directory for converted files

        Returns:
            Dictionary mapping output types to their file paths

        Raises:
            ConversionException: If conversion fails
            InvalidFileTypeError: If file is not a PDF
            ConversionFileNotFoundError: If input file not found
        """
        # Convert to Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Validate input file
        if not file_path.exists():
            raise ConversionFileNotFoundError(f"Input file not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise InvalidFileTypeError(f"{file_path} is not a PDF file")

        # Get output paths
        output_paths = self._get_conversion_paths(file_path, output_dir)

        # Check if files already exist and skip if not overwriting
        if not self.config.overwrite_existing and self._check_existing_files(
            output_paths
        ):
            logger.debug(
                f"All converted files for {file_path} already exist. Skipping conversion."
            )
            return output_paths

        logger.info(f"Converting PDF file: {file_path}")

        with logfire.span(f"converting PDF {file_path}"):
            try:
                # Import docling components
                from docling.datamodel.base_models import InputFormat
                from docling.datamodel.pipeline_options import (
                    AcceleratorDevice,
                    AcceleratorOptions,
                    PdfPipelineOptions,
                )
                from docling.document_converter import (
                    DocumentConverter,
                    PdfFormatOption,
                )

                # Configure conversion pipeline
                with logfire.suppress_instrumentation():
                    pipeline_options = PdfPipelineOptions()
                    pipeline_options.do_ocr = self.config.do_ocr
                    pipeline_options.accelerator_options = AcceleratorOptions(
                        num_threads=self.config.num_threads,
                        device=AcceleratorDevice.AUTO,
                    )

                    converter = DocumentConverter(
                        format_options={
                            InputFormat.PDF: PdfFormatOption(
                                pipeline_options=pipeline_options
                            )
                        }
                    )

                    # Perform conversion
                    doc = converter.convert(file_path).document

                # Save converted files
                try:
                    with logfire.suppress_instrumentation():
                        # Save markdown
                        with open(output_paths["markdown"], "w", encoding="utf-8") as f:
                            f.write(doc.export_to_markdown())

                        # Save docling format
                        doc.save_as_doctags(output_paths["docling"])

                        # Save JSON format
                        doc.save_as_json(output_paths["json"])

                except Exception as e:
                    logger.error(f"Failed to save converted document: {e}")
                    raise ConversionFailedError(f"Failed to save converted files: {e}")

            except ImportError as e:
                logger.error(f"Failed to import docling components: {e}")
                raise ConversionFailedError(f"Docling library not available: {e}")
            except Exception as e:
                logger.error(f"PDF conversion failed: {e}")
                raise ConversionFailedError(f"Failed to convert {file_path}: {e}")

        logger.info(
            f"Successfully converted {file_path} to {len(output_paths)} formats"
        )
        return output_paths

    def convert_batch(
        self,
        file_paths: List[Path],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Union[Dict[str, Path], Dict[str, str]]]:
        """
        Convert multiple PDF files in batch.

        Args:
            file_paths: List of PDF file paths to convert
            output_dir: Optional base output directory for all conversions

        Returns:
            Dictionary mapping input file paths to their conversion results
        """
        results: Dict[str, Union[Dict[str, Path], Dict[str, str]]] = {}
        successful = 0
        failed = 0

        logger.info(f"Starting batch conversion of {len(file_paths)} PDF files")

        for i, file_path in enumerate(file_paths, 1):
            try:
                result = self.convert_pdf(file_path, output_dir)
                results[str(file_path)] = result
                successful += 1
                logger.info(f"✅ [{i}/{len(file_paths)}] Converted: {file_path}")
            except ConversionException as e:
                failed += 1
                results[str(file_path)] = {"error": str(e)}
                logger.error(
                    f"❌ [{i}/{len(file_paths)}] Failed to convert {file_path}: {e}"
                )

        logger.info(
            f"Batch conversion completed: {successful} successful, {failed} failed"
        )
        return results

    def get_conversion_status(self, file_path: Union[Path, str]) -> Dict[str, bool]:
        """
        Check the conversion status of a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary showing which output formats exist
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        output_paths = self._get_conversion_paths(file_path)
        return {
            format_type: path.exists() for format_type, path in output_paths.items()
        }

    def cleanup_partial_conversions(self, file_path: Union[Path, str]) -> bool:
        """
        Remove partially converted files for a given input file.

        Args:
            file_path: Path to the PDF file

        Returns:
            True if cleanup was successful
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        output_paths = self._get_conversion_paths(file_path)
        cleaned = 0

        for format_type, path in output_paths.items():
            if path.exists():
                try:
                    path.unlink()
                    cleaned += 1
                    logger.debug(f"Removed {format_type} file: {path}")
                except Exception as e:
                    logger.error(f"Failed to remove {format_type} file {path}: {e}")
                    return False

        if cleaned > 0:
            logger.info(
                f"Cleaned up {cleaned} partial conversion files for {file_path}"
            )

        return True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # No cleanup needed for this service
        pass
