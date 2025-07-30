"""
Reference Resolver for populating object references in ChromaDB.

This module provides functionality to resolve URL references (e.g., paper_ref, meeting_ref)
to full objects, enabling efficient querying and reducing API calls.
"""

import json
from typing import Any, Dict, Optional
import uuid

import chromadb
import httpx
from celery import group
from chromadb import Collection
from chromadb.api import ClientAPI
from chromadb.config import Settings
from loguru import logger

from stadt_bonn_oparl.config import UPSTREAM_API_URL


class ResolverException(Exception):
    """Base exception for reference resolver errors."""


class ResolverCantFindEntiry(ResolverException):
    """Exception raised when an entity cannot be found in ChromaDB."""


class ReferenceResolver:
    """Service for resolving and populating object references in ChromaDB."""

    def __init__(
        self, http_client: httpx.Client, chromadb_client: Optional[ClientAPI] = None
    ):
        """
        Initialize the Reference Resolver.

        Args:
            http_client: HTTP client for API calls
            chromadb_client: ChromaDB client (will create one if not provided)
        """
        self.http_client = http_client

        # Initialize ChromaDB client if not provided
        if chromadb_client is None:
            self.chromadb_client = chromadb.PersistentClient(
                path="./chroma-api",
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            self.chromadb_client = chromadb_client

        # Get or create collections
        self.collections = {
            "agendaitems": self.chromadb_client.get_or_create_collection("agendaitems"),
            "consultations": self.chromadb_client.get_or_create_collection(
                "consultations"
            ),
            "files": self.chromadb_client.get_or_create_collection("files"),
            "meetings": self.chromadb_client.get_or_create_collection("meetings"),
            "memberships": self.chromadb_client.get_or_create_collection("memberships"),
            "organizations": self.chromadb_client.get_or_create_collection(
                "organizations"
            ),
            "papers": self.chromadb_client.get_or_create_collection("papers"),
            "persons": self.chromadb_client.get_or_create_collection("persons"),
        }

    def _get_collection_name(self, entity_type: str) -> str:
        """Get the collection name for an entity type."""
        type_to_collection = {
            "consultation": "consultations",
            "meeting": "meetings",
            "paper": "papers",
            "person": "persons",
            "organization": "organizations",
            "file": "files",
            "membership": "memberships",
            "agendaItem": "agendaitems",
        }
        return type_to_collection.get(entity_type, entity_type.lower() + "s")

    def _get_collection(self, entity_type: str) -> Optional[Collection]:
        """Get the ChromaDB collection for an entity type."""
        collection_name = self._get_collection_name(entity_type.lower())
        return self.collections.get(collection_name)

    def get_collections(self) -> Dict[str, Collection]:
        """Get all managed collections."""
        return self.collections

    async def resolve_references(
        self, entity: Dict[str, Any], entity_type: str
    ) -> Dict[str, Any]:
        """
        Resolve all references for a given entity.

        This method identifies reference fields in an entity and queues
        background tasks to fetch and populate the referenced objects.

        Args:
            entity: The entity with reference fields
            entity_type: Type of the entity (e.g., 'Consultation', 'Meeting')

        Returns:
            Entity dict (references will be populated asynchronously)
        """
        # Import here to avoid circular imports
        from stadt_bonn_oparl.tasks.references import resolve_reference_task

        reference_map = self._get_reference_map(entity_type)
        tasks = []

        for ref_field, object_field in reference_map.items():
            ref_value = entity.get(ref_field)
            if ref_value:
                # Handle both single references and lists
                if isinstance(ref_value, list) and ref_value:
                    tasks.append(
                        resolve_reference_task.si(
                            str(entity["id"]),
                            entity_type,
                            ref_field,
                            ref_value,
                            object_field,
                        )
                    )
                elif isinstance(ref_value, str):
                    tasks.append(
                        resolve_reference_task.si(
                            str(entity["id"]),
                            entity_type,
                            ref_field,
                            ref_value,
                            object_field,
                        )
                    )

        # Execute tasks in parallel using Celery group
        if tasks:
            job = group(tasks)
            job.apply_async()
            logger.info(
                f"Queued {len(tasks)} reference resolution tasks for {entity_type} {entity['id']}"
            )

        return entity

    def _get_reference_map(self, entity_type: str) -> Dict[str, str]:
        """
        Get mapping of reference fields to object fields for an entity type.

        Args:
            entity_type: The type of entity to get mappings for

        Returns:
            Dictionary mapping reference field names to object field names
        """
        entity_type = entity_type.lower()
        maps = {
            "consultation": {
                "paper_ref": "paper",
                "meeting_ref": "meeting",
                "organization_ref": "organizations",
            },
            "meeting": {
                "location_ref": "location",
                "organizations_ref": "organizations",
                "participant_ref": "participants",
            },
            "paper": {
                "body_ref": "body",
                "relatedPapers_ref": "relatedPapers",
                "mainFile_ref": "mainFile",
                "auxiliaryFiles_ref": "auxiliaryFiles",
                "consultation_ref": "consultations",
                "originatorPerson_ref": "originatorPersons",
                "originatorOrganization_ref": "originatorOrganizations",
            },
            "person": {"membership_ref": "memberships", "location_ref": "location"},
            "organization": {
                "membership_ref": "memberships",
                "location_ref": "location",
                "meeting_ref": "meetings",
            },
            "file": {
                "agendaItem_ref": "agendaItems",
                "meeting_ref": "meetings",
                "paper_ref": "papers",
            },
        }
        return maps.get(entity_type, {})

    async def check_references_resolved(
        self, entity_id: str, entity_type: str
    ) -> Dict[str, bool]:
        """
        Check which references have been resolved for an entity.

        Args:
            entity_id: ID of the entity to check
            entity_type: Type of the entity

        Returns:
            Dict mapping object fields to resolution status
        """
        collection = self._get_collection(entity_type)
        if not collection:
            logger.error(f"No collection found for entity type {entity_type}")
            return {}

        # calculate the entity ID: it's the URSTEAM_URL and entity_type path and id...
        # FIXME files and consultations use two parameters, so this is not correct
        _url_ref = f"{UPSTREAM_API_URL}/{entity_type.lower()}s?id={entity_id}"

        _id_ref = str(uuid.uuid5(uuid.NAMESPACE_URL, _url_ref))
        logger.debug(f"Checking references for {entity_type} with ID {_url_ref}")

        logger.debug(f"Looking up ID: {_id_ref} in collection {collection.name}")
        result = collection.get(ids=[_id_ref])
        if not result or not result["documents"]:
            raise ResolverCantFindEntiry

        logger.debug(f"Found entity {entity_id}: {result}")

        entity = json.loads(result["documents"][0])
        reference_map = self._get_reference_map(entity_type)
        status = {}

        for _, object_field in reference_map.items():
            # Check if the object field exists and is populated
            status[object_field] = (
                object_field in entity and entity[object_field] is not None
            )
            logger.debug(f"{status}")

        return status

    async def get_or_resolve_entity(
        self,
        entity_type: str,
        entity_id: str,
        force_resolve: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get an entity from ChromaDB, optionally forcing reference resolution.

        Args:
            entity_type: Type of the entity
            entity_id: ID of the entity
            force_resolve: Whether to force re-resolution of references

        Returns:
            Entity dict with available resolved references, or None if not found
        """
        collection = self._get_collection(entity_type)
        if not collection:
            logger.error(f"No collection found for entity type {entity_type}")
            return None

        result = collection.get(ids=[entity_id])
        if not result or not result["documents"]:
            return None

        entity = json.loads(result["documents"][0])

        if force_resolve or self._should_resolve_references(entity, entity_type):
            await self.resolve_references(entity, entity_type)

        return entity

    def _should_resolve_references(
        self, entity: Dict[str, Any], entity_type: str
    ) -> bool:
        """
        Determine if references should be resolved for an entity.

        Args:
            entity: The entity to check
            entity_type: Type of the entity

        Returns:
            True if references should be resolved
        """
        reference_map = self._get_reference_map(entity_type)

        for ref_field, object_field in reference_map.items():
            # If we have a reference but no resolved object, we should resolve
            if entity.get(ref_field) and not entity.get(object_field):
                return True

        return False
