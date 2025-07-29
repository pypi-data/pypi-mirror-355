from pathlib import Path
from typing import Annotated, Optional

import cyclopts
import rich
from cyclopts import App
from loguru import logger
from pydantic import DirectoryPath, FilePath

from stadt_bonn_oparl.processors import convert_oparl_pdf
from stadt_bonn_oparl.pdf_conversion_service import (
    PDFConversionConfig,
    PDFConversionService,
    ConversionException,
)


convert = App(
    name="convert", help="Convert OPARL Papers PDF to Markdown and Docling format"
)


@convert.command(name=["paper", "papers"])
def convert_paper(
    data_path: DirectoryPath | FilePath,
    from_file: FilePath | None = None,
    all: bool = False,
) -> bool:
    """
    Convert an OPARL Papers PDF to Markdown and Docling format.
    This function processes a single PDF file or all PDFs in the specified directory.

    If `from_file` is provided, it reads the list of PDFs to be converted from that file,
    otherwise, it processes the PDF provided as a single file at `data_path` or all PDFs
    in the specified directory will be converted.

    Parameters
    ----------
    data_path: DirectoryPath | FilePath
        Path to the directory containing OPARL Papers in PDF file
    from_file: FilePath
        Path to the file from which the list of PDFs to be converted will be read.
    all: bool
        If True, convert all PDFs in the directory

    Returns
    -------
        bool: True if conversion is successful, False otherwise
    """
    logger.debug("Starting OParl data conversion...")

    papers = None

    if from_file:
        # read the file into ListOfPapers
        from stadt_bonn_oparl.papers.find import ListOfPapers

        with open(from_file, "r", encoding="utf-8") as file:
            try:
                papers = ListOfPapers.model_validate_json(file.read()).papers
            except Exception as e:
                logger.error(f"Failed to read from file {from_file}: {e}")
                return False

    if all:
        # Assuming convert_oparl_pdf saves to CONVERTED_DATA_DIRECTORY
        papers = data_path.glob("**/*.pdf")
    else:
        if not data_path.is_file() or not data_path.suffix == ".pdf":
            logger.error("The provided path is not a PDF file.")
            return False

        papers = [data_path]

    if papers:
        for pdf_file in papers:
            if not pdf_file.is_file() or pdf_file.suffix != ".pdf":
                logger.error(f"Skipping non-PDF file: {pdf_file}")
                continue

            logger.debug(f"Converting PDF file: {pdf_file}")
            convert_oparl_pdf(pdf_file, data_path=pdf_file.parent)

    logger.debug("OParl data conversion completed.")

    return True


# Global conversion parameters as type aliases for reuse
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

ConversionTimeout = Annotated[
    int,
    cyclopts.Parameter(
        help="Conversion timeout in seconds",
    ),
]

OutputDirectory = Annotated[
    Optional[Path],
    cyclopts.Parameter(
        help="Directory to save the converted files (default: ./converted)",
    ),
]

CreateSubdirs = Annotated[
    bool,
    cyclopts.Parameter(
        help="Create subdirectories for organization",
    ),
]

OverwriteExisting = Annotated[
    bool,
    cyclopts.Parameter(
        help="Overwrite existing converted files",
    ),
]

NumThreads = Annotated[
    int,
    cyclopts.Parameter(
        help="Number of threads for conversion processing",
    ),
]

DoOCR = Annotated[
    bool,
    cyclopts.Parameter(
        help="Enable OCR processing for scanned PDFs",
    ),
]

UpsertToChromaDB = Annotated[
    bool,
    cyclopts.Parameter(
        help="Automatically upsert converted markdown to ChromaDB",
    ),
]

PaperID = Annotated[
    Optional[str],
    cyclopts.Parameter(
        help="Paper ID for ChromaDB upsert (required if --upsert-to-chromadb is used)",
    ),
]

ChromaDBCollection = Annotated[
    str,
    cyclopts.Parameter(
        help="ChromaDB collection name for upsert",
    ),
]


@convert.command(name="pdf")
def convert_pdf_file(
    file_path: Path,
    output_dir: OutputDirectory = None,
    *,
    create_subdirs: CreateSubdirs = True,
    overwrite: OverwriteExisting = False,
    num_threads: NumThreads = 12,
    do_ocr: DoOCR = False,
    use_celery: UseCelery = False,
    wait: WaitForCompletion = True,
    timeout: ConversionTimeout = 300,
    upsert_to_chromadb: UpsertToChromaDB = False,
    paper_id: PaperID = None,
    chromadb_collection: ChromaDBCollection = "papers",
) -> None:
    """
    Convert a single PDF file to Docling format using the new PDFConversionService.

    Args:
        file_path: Path to the PDF file to convert
        output_dir: Directory to save converted files (default: ./data-100)
        create_subdirs: Create subdirectories for organization
        overwrite: Overwrite existing converted files
        num_threads: Number of threads for conversion processing
        do_ocr: Enable OCR processing for scanned PDFs
        use_celery: Use Celery task for async processing
        wait: Wait for Celery task to complete (use --no-wait to submit without waiting)
        timeout: Conversion timeout in seconds
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return

    if file_path.suffix.lower() != ".pdf":
        logger.error(f"File is not a PDF: {file_path}")
        return

    # Validate ChromaDB parameters
    if upsert_to_chromadb and not paper_id:
        logger.error("paper_id is required when upsert_to_chromadb is enabled")
        return

    config_dict = {
        "base_path": str(output_dir or Path("./data-100")),
        "create_subdirs": create_subdirs,
        "overwrite_existing": overwrite,
        "num_threads": num_threads,
        "do_ocr": do_ocr,
    }

    if use_celery:
        # Import the appropriate task based on ChromaDB requirements
        if upsert_to_chromadb:
            from stadt_bonn_oparl.tasks.convert import convert_pdf_with_chromadb_task

            task_func = convert_pdf_with_chromadb_task
            task_args = [
                str(file_path),
                str(output_dir) if output_dir else "",
                config_dict,
                upsert_to_chromadb,
                paper_id,
            ]
        else:
            from stadt_bonn_oparl.tasks.convert import convert_pdf_task

            task_func = convert_pdf_task
            task_args = [
                str(file_path),
                str(output_dir) if output_dir else "",
                config_dict,
            ]

        # Submit task to Celery
        rich.print(f"📤 Submitting PDF conversion task for {file_path} to Celery...")
        task = task_func.apply_async(args=task_args)

        if not wait:
            rich.print(
                f"[bold green]✅ Submitted conversion task for {file_path}[/bold green]"
            )
            rich.print(f"[dim]Task ID: {task.id}[/dim]")
            rich.print(
                "\n💡 Task is running in the background. Check Celery logs for progress."
            )
            return

        # Wait for result
        rich.print("[bold]⏳ Waiting for conversion to complete...[/bold]")
        try:
            result = task.get(timeout=timeout)
            if "error" in result:
                rich.print(f"❌ Conversion failed: {result['error']}")
            else:
                # Filter out non-format keys for display
                format_results = {
                    k: v
                    for k, v in result.items()
                    if k in ["markdown", "docling", "json"]
                }
                rich.print(f"✅ Converted PDF to {len(format_results)} formats:")
                for format_type, path in format_results.items():
                    rich.print(f"  - {format_type}: {path}")

                # Show ChromaDB status if applicable
                if "chromadb_task_id" in result:
                    rich.print(f"🗄️  ChromaDB upsert task: {result['chromadb_task_id']}")
                elif "chromadb_error" in result:
                    rich.print(f"❌ ChromaDB upsert failed: {result['chromadb_error']}")
                elif upsert_to_chromadb:
                    rich.print("⚠️  ChromaDB upsert was not triggered")

        except Exception as e:
            logger.error(f"❌ Conversion failed: {e}")
        return

    # Direct conversion without Celery
    config = PDFConversionConfig(**config_dict)

    try:
        with PDFConversionService(config=config) as service:
            result_paths = service.convert_pdf(file_path, output_dir)
            rich.print(f"✅ Converted PDF to {len(result_paths)} formats:")
            for format_type, path in result_paths.items():
                rich.print(f"  - {format_type}: {path}")

            # Handle ChromaDB upsert for direct conversion
            if upsert_to_chromadb and "markdown" in result_paths:
                rich.print(
                    f"🗄️  Upserting to ChromaDB collection '{chromadb_collection}'..."
                )
                try:
                    from stadt_bonn_oparl.chromadb_utils import get_collection

                    # Read markdown content
                    markdown_path = result_paths["markdown"]
                    with open(markdown_path, "r", encoding="utf-8") as f:
                        markdown_content = f.read()

                    # Prepare metadata
                    metadata = {
                        "paper_id": paper_id,
                        "content_type": "converted_pdf",
                        "markdown_file": str(markdown_path),
                        "conversion_timestamp": str(markdown_path.stat().st_mtime),
                        "has_docling": str(bool("docling" in result_paths)),
                        "has_json": str(bool("json" in result_paths)),
                    }

                    if "docling" in result_paths:
                        metadata["docling_file"] = str(result_paths["docling"])
                    if "json" in result_paths:
                        metadata["json_file"] = str(result_paths["json"])

                    # Upsert to ChromaDB
                    collection = get_collection(chromadb_collection)
                    collection.upsert(
                        ids=[str(paper_id)],
                        documents=[markdown_content],
                        metadatas=[metadata],
                    )

                    rich.print(f"✅ Successfully upserted paper {paper_id} to ChromaDB")

                except Exception as e:
                    rich.print(f"❌ ChromaDB upsert failed: {e}")

    except ConversionException as e:
        logger.error(f"❌ Conversion failed: {e}")


@convert.command(name="status")
def conversion_status(file_path: Path) -> None:
    """
    Check the conversion status of a PDF file.

    Args:
        file_path: Path to the PDF file
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return

    if file_path.suffix.lower() != ".pdf":
        logger.error(f"File is not a PDF: {file_path}")
        return

    service = PDFConversionService()
    status = service.get_conversion_status(file_path)

    rich.print(f"[bold]Conversion status for {file_path}:[/bold]")
    for format_type, exists in status.items():
        status_icon = "✅" if exists else "❌"
        rich.print(
            f"  {status_icon} {format_type}: {'exists' if exists else 'missing'}"
        )


@convert.command(name="cleanup")
def cleanup_conversion(file_path: Path) -> None:
    """
    Clean up partial conversion files for a PDF.

    Args:
        file_path: Path to the PDF file
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return

    if file_path.suffix.lower() != ".pdf":
        logger.error(f"File is not a PDF: {file_path}")
        return

    service = PDFConversionService()
    success = service.cleanup_partial_conversions(file_path)

    if success:
        rich.print(f"✅ Cleaned up conversion files for {file_path}")
    else:
        rich.print(f"❌ Failed to clean up conversion files for {file_path}")
