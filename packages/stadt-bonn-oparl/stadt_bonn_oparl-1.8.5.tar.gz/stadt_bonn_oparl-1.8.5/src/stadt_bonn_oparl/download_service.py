"""
Druchsachen-Download-Server for downloading OParl Files and Papers.

This module provides functionality to download files from the OParl API
and save them to disk. It supports both synchronous and asynchronous
operations via Celery tasks.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx
from loguru import logger
from pydantic import BaseModel

from stadt_bonn_oparl.api.models import FileResponse as OparlFile
from stadt_bonn_oparl.api.models import PaperResponse as OparlPaper
from stadt_bonn_oparl.config import OPARL_BASE_URL


class DownloadException(Exception):
    """Base exception for download server errors."""


class DownloadFileNotFoundError(DownloadException):
    """Exception raised when a file cannot be found."""


class DownloadFailedError(DownloadException):
    """Exception raised when a download fails."""


class DownloadServiceConfig(BaseModel):
    """Configuration for download operations."""

    base_path: Path = Path("./data-100")
    create_subdirs: bool = True
    timeout: int = 300  # 5 minutes
    chunk_size: int = 8192
    max_retries: int = 3


class DruchsachenDownloadService:
    """Service for downloading OParl Files and Papers."""

    def __init__(
        self,
        http_client: Optional[httpx.Client] = None,
        config: Optional[DownloadServiceConfig] = None,
    ):
        """
        Initialize the Download Server.

        Args:
            http_client: HTTP client for API calls (will create one if not provided)
            config: Download configuration (will use defaults if not provided)
        """
        self.config = config or DownloadServiceConfig()

        if http_client is None:
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=True,
            )
        else:
            self.http_client = http_client

        # Ensure base download directory exists
        self.config.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Download server initialized with base path: {self.config.base_path}"
        )

    def _get_entity_url(self, entity_type: str, entity_id: int) -> str:
        """Construct the OParl API URL for an entity."""
        entity_path = "file" if entity_type.lower() == "file" else "paper"
        return f"{OPARL_BASE_URL}/{entity_path}s/?id={entity_id}"

    def _get_download_path(self, entity: Union[OparlFile, OparlPaper]) -> Path:
        """
        Determine the download path for an entity.

        Args:
            entity: The OParl File or Paper object

        Returns:
            Path where the file should be saved
        """
        if isinstance(entity, OparlFile):
            # For files, organize by type and date
            file_type = entity.name.split(".")[-1] if entity.name else "unknown"
            date_part = str(entity.date) if entity.date else "undated"

            if self.config.create_subdirs:
                subdir = self.config.base_path / "files" / date_part / file_type
            else:
                subdir = self.config.base_path / "files"

            # Use original filename if available, otherwise generate one
            if entity.name:
                filename = f"{entity.id}_{entity.name}"
            else:
                filename = f"{entity.id}.{file_type}"

        elif isinstance(entity, OparlPaper):
            # For papers, organize by reference and date
            date_part = str(entity.date) if entity.date else "undated"

            if self.config.create_subdirs:
                subdir = self.config.base_path / "papers" / date_part
            else:
                subdir = self.config.base_path / "papers"

            # Use reference as filename base
            filename = (
                f"{entity.id}_{entity.reference}.pdf"
                if entity.reference
                else f"{entity.id}.pdf"
            )
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")

        # Create subdirectory if needed
        subdir.mkdir(parents=True, exist_ok=True)

        return subdir / filename

    async def download_file(
        self,
        entity: Union[OparlFile, OparlPaper, int, str],
        entity_type: Optional[str] = None,
        dtyp: Optional[int] = None,
    ) -> Path:
        """
        Download a file from the OParl API.

        Args:
            entity: Either an OParl File/Paper object or an entity ID
            entity_type: Required if entity is an ID. Either 'file' or 'paper'
            dtyp: Optional download type

        Returns:
            Path to the downloaded file

        Raises:
            DownloadException: If download fails
            FileNotFoundError: If entity not found
        """
        # Fetch entity data if only ID provided
        if isinstance(entity, (int, str)):
            if not entity_type:
                raise ValueError("entity_type required when using entity ID")

            # Convert string ID to int if needed
            if isinstance(entity, str):
                # Check if it's a URL and extract the ID parameter
                if entity.startswith("http"):
                    import httpx
                    try:
                        url_obj = httpx.URL(entity)
                        entity_id = url_obj.params.get("id")
                        if entity_id:
                            entity = int(entity_id)
                        else:
                            raise ValueError(f"No 'id' parameter found in URL: {entity}")
                    except Exception as e:
                        raise ValueError(f"Invalid entity URL format: {entity}") from e
                else:
                    try:
                        entity = int(entity)
                    except ValueError:
                        raise ValueError(f"Invalid entity ID format: {entity}")

            entity_data = await self._fetch_entity(entity, entity_type, dtyp)
            logger.debug(f"Fetched {entity_type} data: {entity_data}")
            if entity_type.lower() == "file":
                entity = OparlFile(**entity_data)
            else:
                entity = OparlPaper(**entity_data)

        # Get download URL
        if isinstance(entity, OparlFile):
            if not entity.downloadUrl:
                raise DownloadFailedError(f"File {entity.id} has no download URL")
            download_url = entity.downloadUrl
        elif isinstance(entity, OparlPaper):
            # For papers, we need to download the main file
            # if not entity.mainFile_ref:
            #     raise DownloadFailedError(
            #         f"Paper {entity.id} has no main file reference"
            #     )

            # # Fetch the main file data
            # main_file_data = await self._fetch_entity("file", entity.mainFile_ref)
            # main_file = OparlFile(**main_file_data)

            # if not main_file.downloadUrl:
            #     raise DownloadFailedError(
            #         f"Paper {entity.id} main file has no download URL"
            #     )
            # download_url = main_file.downloadUrl
            # FIXME: file download from UPSTREAM is still delivering 500, 2025-Jun-12
            if not entity.mainFileAccessUrl:
                raise DownloadFailedError(
                    f"Paper {entity.id} has no main file access URL"
                )
            download_url = entity.mainFileAccessUrl
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")

        # Determine download path
        download_path = self._get_download_path(entity)

        # Skip if file already exists
        if download_path.exists():
            logger.info(f"File already exists: {download_path}")
            return download_path

        # Download the file
        logger.info(f"Downloading {download_url} to {download_path}")

        try:
            with self.http_client.stream("GET", download_url) as response:
                response.raise_for_status()

                # Write to temporary file first
                temp_path = download_path.with_suffix(download_path.suffix + ".tmp")

                with open(temp_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=self.config.chunk_size):
                        f.write(chunk)

                # Move to final location
                temp_path.rename(download_path)

        except httpx.HTTPError as e:
            logger.error(f"Download failed: {e}")
            raise DownloadFailedError(f"Failed to download {download_url}: {e}")

        logger.info(f"Successfully downloaded to {download_path}")
        return download_path

    async def _fetch_entity(
        self, entity_id: int, entity_type: str, dtyp: Optional[int]
    ) -> Dict[str, Any]:
        """
        Fetch entity data from the OParl API.

        Args:
            entity_id: ID of the entity
            entity_type: Type of entity ('file' or 'paper')

        Returns:
            Entity data as dictionary

        Raises:
            FileNotFoundError: If entity not found
        """
        params = {}

        # Handle string IDs that might be URLs
        if isinstance(entity_id, str) and entity_id.startswith("http"):
            url = entity_id
        else:
            url = f"{OPARL_BASE_URL}/{entity_type}s/"
            params = {"id": entity_id}
            if dtyp:
                params["dtyp"] = dtyp

        try:
            response = self.http_client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise DownloadFileNotFoundError(
                    f"{entity_type} {entity_id} not found"
                ) from e
            raise
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch {entity_type} {entity_id}: {e}")
            raise DownloadException(f"Failed to fetch {entity_type}: {e}") from e

    async def _fetch_entity_from_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch entity data directly from a URL.

        Args:
            url: Direct URL to the entity

        Returns:
            Entity data as dictionary

        Raises:
            DownloadFileNotFoundError: If entity not found
            DownloadException: If fetch fails
        """
        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise DownloadFileNotFoundError(f"Entity not found at {url}") from e
            raise
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch entity from {url}: {e}")
            raise DownloadException(f"Failed to fetch entity from URL: {e}") from e

    def download_file_sync(
        self,
        entity: Union[OparlFile, OparlPaper, int, str],
        entity_type: Optional[str] = None,
        dtyp: Optional[int] = None,
    ) -> Path:
        """
        Synchronous wrapper for download_file.

        Args:
            entity: Either an OParl File/Paper object or an entity ID
            entity_type: Required if entity is an ID. Either 'file' or 'paper'

        Returns:
            Path to the downloaded file
        """
        import asyncio

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        logger.debug(f"Starting synchronous download for {entity_type}: {entity}")
        return loop.run_until_complete(self.download_file(entity, entity_type, dtyp))

    async def download_paper_files(
        self, paper: Union[OparlPaper, int, str]
    ) -> Dict[str, Path]:
        """
        Download all files associated with a paper.

        Args:
            paper: Either an OParl Paper object or a paper ID

        Returns:
            Dictionary mapping file types to downloaded paths
        """
        # Fetch paper data if only ID provided
        if isinstance(paper, (int, str)):
            # Convert string ID to int if needed
            if isinstance(paper, str):
                # Check if it's a URL and extract the ID parameter
                if paper.startswith("http"):
                    import httpx
                    try:
                        url_obj = httpx.URL(paper)
                        paper_id = url_obj.params.get("id")
                        if paper_id:
                            paper = int(paper_id)
                        else:
                            raise ValueError(f"No 'id' parameter found in URL: {paper}")
                    except Exception as e:
                        raise ValueError(f"Invalid paper URL format: {paper}") from e
                else:
                    try:
                        paper = int(paper)
                    except ValueError:
                        raise ValueError(f"Invalid paper ID format: {paper}")
            
            paper_data = await self._fetch_entity(paper, "paper", dtyp=None)
            paper = OparlPaper(**paper_data)

        downloads = {}

        # Download main file
        if paper.mainFile:
            try:
                downloads["main"] = await self.download_file(paper)
            except DownloadException as e:
                logger.error(f"Failed to download main file for paper {paper.id}: {e}")

        # Download auxiliary files
        if paper.auxiliaryFile:
            for i, aux_file_ref in enumerate(paper.auxiliaryFile):
                try:
                    aux_file_data = await self._fetch_entity(
                        "file", aux_file_ref, dtyp=None
                    )
                    aux_file = OparlFile(**aux_file_data)
                    downloads[f"auxiliary_{i}"] = await self.download_file(aux_file)
                except DownloadException as e:
                    logger.error(
                        f"Failed to download auxiliary file {aux_file_ref}: {e}"
                    )

        return downloads

    async def download_paper_files_direct(
        self, paper: Union[OparlPaper, int, str]
    ) -> Dict[str, Path]:
        """
        Download all files associated with a paper by traversing directAccessURL references.
        This method downloads files directly without using the download_file() method.

        Args:
            paper: Either an OParl Paper object or a paper ID

        Returns:
            Dictionary mapping file types to downloaded paths
        """
        # Fetch paper data if only ID provided
        if isinstance(paper, (int, str)):
            # Convert string ID to int if needed
            if isinstance(paper, str):
                # Check if it's a URL and extract the ID parameter
                if paper.startswith("http"):
                    import httpx
                    try:
                        url_obj = httpx.URL(paper)
                        paper_id = url_obj.params.get("id")
                        if paper_id:
                            paper = int(paper_id)
                        else:
                            raise ValueError(f"No 'id' parameter found in URL: {paper}")
                    except Exception as e:
                        raise ValueError(f"Invalid paper URL format: {paper}") from e
                else:
                    try:
                        paper = int(paper)
                    except ValueError:
                        raise ValueError(f"Invalid paper ID format: {paper}")
            
            paper_data = await self._fetch_entity(paper, "paper", dtyp=None)
            paper = OparlPaper(**paper_data)

        downloads = {}

        # Helper function to download file directly from URL
        async def _download_from_url(url: str, file_type: str) -> Optional[Path]:
            try:
                # Fetch the file metadata from the directAccessURL
                file_data = await self._fetch_entity_from_url(url)
                file_obj = OparlFile(**file_data)

                # Determine download URL
                download_url = file_obj.downloadUrl or file_obj.accessUrl
                if not download_url:
                    logger.error(f"No download URL found for file at {url}")
                    return None

                # Determine download path
                download_path = self._get_download_path(file_obj)

                # Skip if file already exists
                if download_path.exists():
                    logger.info(f"File already exists: {download_path}")
                    return download_path

                # Download the file
                logger.info(f"Downloading {download_url} to {download_path}")

                with self.http_client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    # Write to temporary file first
                    temp_path = download_path.with_suffix(download_path.suffix + ".tmp")

                    with open(temp_path, "wb") as f:
                        for chunk in response.iter_bytes(
                            chunk_size=self.config.chunk_size
                        ):
                            f.write(chunk)

                    # Move to final location
                    temp_path.rename(download_path)

                logger.info(f"Successfully downloaded to {download_path}")
                return download_path

            except Exception as e:
                logger.error(f"Failed to download {file_type} file from {url}: {e}")
                return None

        # Download main file via directAccessURL
        if paper.mainFileAccessUrl:
            result = await _download_from_url(paper.mainFileAccessUrl, "main")
            if result:
                downloads["main"] = result

        # Handle auxiliary files
        # Note: auxiliaryFile in the Paper model might be auxilaryFile (typo in OParl spec)
        auxiliary_files = getattr(paper, "auxilaryFile", None) or getattr(
            paper, "auxiliaryFile", None
        )

        if auxiliary_files:
            for i, aux_file in enumerate(auxiliary_files):
                if isinstance(aux_file, str) and aux_file.startswith("http"):
                    result = await _download_from_url(aux_file, "auxiliary")
                    if result:
                        downloads[f"auxiliary_{i}"] = result
                elif isinstance(aux_file, OparlFile) and aux_file.accessUrl:
                    result = await _download_from_url(aux_file.accessUrl, "auxiliary")
                    if result:
                        downloads[f"auxiliary_{i}"] = result

        # Also check for any file references in auxilaryFiles_ref (internal reference field)
        if paper.auxilaryFiles_ref:
            for i, aux_file_ref in enumerate(paper.auxilaryFiles_ref):
                if aux_file_ref.startswith("http"):
                    result = await _download_from_url(aux_file_ref, "auxiliary_ref")
                    if result:
                        downloads[f"auxiliary_ref_{i}"] = result

        return downloads

    def download_paper_files_direct_sync(
        self, paper: Union[OparlPaper, int, str]
    ) -> Dict[str, Path]:
        """
        Synchronous wrapper for download_paper_files_direct.

        Args:
            paper: Either an OParl Paper object or a paper ID

        Returns:
            Dictionary mapping file types to downloaded paths
        """
        import asyncio

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        logger.debug(f"Starting synchronous direct download for paper: {paper}")
        return loop.run_until_complete(self.download_paper_files_direct(paper))

    def close(self):
        """Close the HTTP client."""
        self.http_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
