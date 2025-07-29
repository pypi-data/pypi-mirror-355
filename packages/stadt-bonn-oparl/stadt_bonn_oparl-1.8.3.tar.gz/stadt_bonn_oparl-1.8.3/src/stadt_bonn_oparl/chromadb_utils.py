"""
Utilities for ChromaDB collection management.

This module provides shared utilities for managing ChromaDB collections
across the application, ensuring consistency between the API, tasks, and CLI.
"""

from typing import Dict, Optional

import chromadb
from chromadb import Collection
from chromadb.config import Settings
from loguru import logger


class ChromaDBManager:
    """Manager for ChromaDB collections with consistent naming and access."""
    
    def __init__(self, path: str = "./chroma-api"):
        """
        Initialize the ChromaDB manager.
        
        Args:
            path: Path to the ChromaDB storage directory
        """
        self.client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collections: Dict[str, Collection] = {}
    
    def get_collection(self, name: str) -> Collection:
        """
        Get or create a collection by name.
        
        Args:
            name: Name of the collection
            
        Returns:
            ChromaDB collection
        """
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name=name)
            logger.debug(f"Created/retrieved collection: {name}")
        
        return self._collections[name]
    
    def get_collection_for_entity_type(self, entity_type: str) -> Optional[Collection]:
        """
        Get collection for a specific entity type.
        
        Args:
            entity_type: The entity type (e.g., 'Consultation', 'Meeting')
            
        Returns:
            Collection for that entity type, or None if unknown type
        """
        collection_name = self.get_collection_name(entity_type)
        if not collection_name:
            return None
        
        return self.get_collection(collection_name)
    
    @staticmethod
    def get_collection_name(entity_type: str) -> Optional[str]:
        """
        Get the collection name for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            Collection name, or None if unknown type
        """
        type_to_collection = {
            "Consultation": "consultations",
            "Meeting": "meetings",
            "Paper": "papers",
            "Person": "persons",
            "Organization": "organizations",
            "File": "files",
            "Membership": "memberships",
            "AgendaItem": "agendaitems",
        }
        return type_to_collection.get(entity_type)
    
    def get_all_collections(self) -> Dict[str, Collection]:
        """
        Get all managed collections.
        
        Returns:
            Dictionary of collection name to Collection objects
        """
        # Ensure all standard collections are created
        standard_collections = [
            "agendaitems", "consultations", "files", "meetings",
            "memberships", "organizations", "papers", "persons"
        ]
        
        for name in standard_collections:
            self.get_collection(name)
        
        return self._collections.copy()
    
    def list_collections(self) -> list:
        """List all collections in the database."""
        return self.client.list_collections()
    
    def delete_collection(self, name: str) -> None:
        """
        Delete a collection.
        
        Args:
            name: Name of the collection to delete
        """
        try:
            self.client.delete_collection(name=name)
            if name in self._collections:
                del self._collections[name]
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            raise


# Global instance for shared use
_chromadb_manager: Optional[ChromaDBManager] = None


def get_chromadb_manager() -> ChromaDBManager:
    """Get the global ChromaDB manager instance."""
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager()
    return _chromadb_manager


def get_collection(name: str) -> Collection:
    """Convenience function to get a collection."""
    return get_chromadb_manager().get_collection(name)


def get_collection_for_entity_type(entity_type: str) -> Optional[Collection]:
    """Convenience function to get collection for entity type."""
    return get_chromadb_manager().get_collection_for_entity_type(entity_type)