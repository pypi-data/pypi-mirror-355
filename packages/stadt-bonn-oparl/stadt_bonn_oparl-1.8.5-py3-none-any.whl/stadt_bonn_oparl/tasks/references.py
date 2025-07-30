"""
Celery tasks for resolving object references in ChromaDB.

This module contains asynchronous tasks that fetch referenced objects
from the OParl API and update entities in ChromaDB with the resolved data.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

import httpx
from celery import shared_task
from chromadb import Collection
from loguru import logger

from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.helpers.helpers import (
    _get_organization_by_id,
    _get_paper_by_id,
)
from stadt_bonn_oparl.api.helpers.meetings import _get_meeting
from stadt_bonn_oparl.api.helpers.persons import _get_person
from stadt_bonn_oparl.chromadb_utils import get_chromadb_manager, get_collection_for_entity_type


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def resolve_reference_task(
    self,
    entity_id: str,
    entity_type: str,
    ref_field: str,
    ref_urls: Union[str, List[str]],
    object_field: str,
):
    """
    Celery task to resolve a single reference or list of references.

    This task fetches objects from their reference URLs and updates
    the entity in ChromaDB with the resolved objects.

    Args:
        entity_id: ID of the entity to update
        entity_type: Type of the entity (e.g., 'Consultation', 'Meeting')
        ref_field: Name of the reference field (e.g., 'paper_ref')
        ref_urls: URL(s) to resolve
        object_field: Name of the field to populate (e.g., 'paper')

    Raises:
        Exception: If resolution fails after max retries
    """
    try:
        # Initialize HTTP client
        http_client = httpx.Client()
        
        # Get the appropriate collection for the entity type
        collection = get_collection_for_entity_type(entity_type)
        if not collection:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Handle single vs multiple references
        is_list = isinstance(ref_urls, list)
        urls = ref_urls if is_list else [ref_urls]

        resolved_objects = []

        for url in urls:
            try:
                obj = _resolve_single_reference(http_client, url)
                if obj:
                    resolved_objects.append(obj)
            except Exception as e:
                logger.error(f"Failed to resolve reference {url}: {e}")
                continue

        # Update entity in ChromaDB
        if resolved_objects:
            _update_entity_references(
                collection,
                entity_id,
                object_field,
                resolved_objects if is_list else resolved_objects[0],
            )

        logger.info(
            f"Successfully resolved {len(resolved_objects)} references for {entity_type} {entity_id}"
        )

    except Exception as e:
        logger.error(f"Task failed for entity {entity_id}, ref {ref_field}: {e}")
        raise self.retry(exc=e)


def _get_collection_by_name(collection_name: str) -> Optional[Collection]:
    """Get a ChromaDB collection by name."""
    manager = get_chromadb_manager()
    return manager.get_collection(collection_name)


def _resolve_single_reference(
    http_client: httpx.Client, url: str
) -> Optional[Any]:
    """
    Resolve a single URL reference to its object.

    Args:
        http_client: HTTP client for API calls
        url: URL to resolve

    Returns:
        Resolved object as dict, or None if resolution fails
    """
    try:
        # Parse URL to determine object type and ID
        # Example: https://www.bonn.sitzung-online.de/public/oparl/papers?id=2021241
        parts = url.split("/")
        if len(parts) < 2:
            logger.error(f"Invalid URL format: {url}")
            return None

        # Get the last part which contains type and parameters
        last_part = parts[-1]
        if "?" not in last_part:
            logger.error(f"No parameters in URL: {url}")
            return None

        object_type = last_part.split("?")[0]
        param_string = last_part.split("?")[1]
        params = {}

        # Parse parameters
        for param in param_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value

        # Route to appropriate helper based on object type
        logger.debug(f"Resolving {object_type} with params {params}")

        if object_type == "papers" and "id" in params:
            papers_collection = get_collection_for_entity_type("Paper")
            paper = asyncio.run(
                _get_paper_by_id(http_client, papers_collection, int(params["id"]))
            )
            return paper.model_dump() if paper else None

        elif object_type == "meetings" and "id" in params:
            meetings_collection = get_collection_for_entity_type("Meeting")
            _, meeting = asyncio.run(
                _get_meeting(http_client, meetings_collection, int(params["id"]))
            )
            return meeting.model_dump() if meeting else None

        elif object_type == "consultations" and "id" in params and "bi" in params:
            consultations_collection = get_collection_for_entity_type("Consultation")
            _, consultation = asyncio.run(
                _get_consultation(
                    http_client, consultations_collection, int(params["id"]), int(params["bi"])
                )
            )
            return consultation.model_dump() if consultation else None

        elif object_type == "organizations" and "id" in params:
            # Note: _get_organization_by_id has different signature
            org = asyncio.run(
                _get_organization_by_id(http_client, int(params["id"]))
            )
            return org.model_dump() if org else None

        elif object_type == "persons" and "id" in params:
            persons_collection = get_collection_for_entity_type("Person")
            _, person = asyncio.run(
                _get_person(http_client, persons_collection, int(params["id"]))
            )
            return person.model_dump() if person else None

        # TODO: implement file-chromadb integration
        # elif object_type == "files" and "id" in params:
        #    file = asyncio.run(
        #        _get_file_by_id(http_client, collection, int(params["id"]))
        #    )
        #    return file.model_dump() if file else None

        else:
            logger.warning(f"Unknown object type or missing params: {object_type}")
            return None

    except Exception as e:
        logger.error(f"Error resolving reference {url}: {e}")
        return None


def _update_entity_references(
    collection: Collection,
    entity_id: str,
    field_name: str,
    value: Any,
):
    """
    Update an entity in ChromaDB with resolved references.

    Args:
        collection: ChromaDB collection
        entity_id: ID of the entity to update
        field_name: Name of the field to update
        value: Resolved value(s) to set
    """
    try:
        # Get current entity
        result = collection.get(ids=[entity_id])
        if not result or not result["documents"]:
            logger.error(f"Entity {entity_id} not found in ChromaDB")
            return

        # Parse entity
        entity = json.loads(result["documents"][0])

        # Update field
        entity[field_name] = value

        # Preserve metadata
        metadata = result["metadatas"][0] if result["metadatas"] else {}

        # Update in ChromaDB
        collection.update(
            ids=[entity_id], documents=[json.dumps(entity)], metadatas=[metadata]
        )

        logger.info(f"Updated entity {entity_id} with resolved {field_name}")

    except Exception as e:
        logger.error(f"Failed to update entity {entity_id}: {e}")
        raise


@shared_task
def batch_resolve_references(entity_type: str, entity_ids: List[str]):
    """
    Batch task to resolve references for multiple entities.

    Args:
        entity_type: Type of entities to process
        entity_ids: List of entity IDs to process
    """
    try:
        from stadt_bonn_oparl.reference_resolver import ReferenceResolver
        
        http_client = httpx.Client()
        chromadb_manager = get_chromadb_manager()
        resolver = ReferenceResolver(http_client, chromadb_manager.client)

        success_count = 0
        for entity_id in entity_ids:
            try:
                entity = asyncio.run(resolver.get_or_resolve_entity(entity_type, entity_id))
                if entity:
                    asyncio.run(resolver.resolve_references(entity, entity_type))
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to process entity {entity_id}: {e}")
                continue

        logger.info(
            f"Batch resolution completed: {success_count}/{len(entity_ids)} entities processed"
        )

    except Exception as e:
        logger.error(f"Batch resolution failed: {e}")
        raise


@shared_task
def check_and_resolve_missing_references():
    """
    Periodic task to find and resolve entities with missing references.

    This task scans the ChromaDB for entities that have reference fields
    but missing resolved objects, and queues them for resolution.
    """
    try:
        # Check each collection type
        entity_types = ["Consultation", "Meeting", "Paper", "Organization", "Person"]
        total_entities = 0
        
        for entity_type in entity_types:
            collection = get_collection_for_entity_type(entity_type)
            if not collection:
                continue
                
            # Query for entities in this collection
            results = collection.get(limit=100)  # Adjust limit as needed
            
            entities_to_resolve = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    entity = json.loads(doc)
                    
                    # Check if entity has unresolved references
                    if _has_unresolved_references(entity, entity_type):
                        entities_to_resolve.append(results["ids"][i])
            
            # Queue batch task for this entity type
            if entities_to_resolve:
                batch_resolve_references.delay(entity_type, entities_to_resolve)
                total_entities += len(entities_to_resolve)
                logger.info(
                    f"Queued {len(entities_to_resolve)} {entity_type} entities for reference resolution"
                )
        
        logger.info(
            f"Total queued for resolution: {total_entities} entities across all types"
        )

    except Exception as e:
        logger.error(f"Failed to check missing references: {e}")
        raise


def _has_unresolved_references(entity: Dict[str, Any], entity_type: str) -> bool:
    """
    Check if an entity has unresolved references.

    Args:
        entity: Entity to check
        entity_type: Type of the entity

    Returns:
        True if entity has unresolved references
    """
    # Define reference patterns for each entity type
    reference_patterns = {
        "Consultation": [("paper_ref", "paper"), ("meeting_ref", "meeting")],
        "Meeting": [
            ("organizations_ref", "organizations"),
            ("participant_ref", "participants"),
        ],
        "Paper": [
            ("mainFile_ref", "mainFile"),
            ("consultation_ref", "consultations"),
        ],
    }

    patterns = reference_patterns.get(entity_type, [])
    for ref_field, obj_field in patterns:
        if entity.get(ref_field) and not entity.get(obj_field):
            return True

    return False
