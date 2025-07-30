from abc import ABC, abstractmethod
from typing import Optional, Type

from doteval.sessions import Session

__all__ = ["Storage", "StorageRegistry", "_registry"]


class Storage(ABC):
    """Abstract storage interface"""

    @abstractmethod
    def save(self, session: Session):
        pass

    @abstractmethod
    def load(self, name: str) -> Optional[Session]:
        pass

    @abstractmethod
    def list_names(self) -> list[str]:
        pass

    @abstractmethod
    def rename(self, old_name: str, new_name: str):
        pass

    @abstractmethod
    def delete(self, name: str):
        pass

    @abstractmethod
    def acquire_lock(self, name: str):
        pass

    @abstractmethod
    def release_lock(self, name: str):
        pass

    @abstractmethod
    def is_locked(self, name: str) -> bool:
        pass


class StorageRegistry:
    """Registry for storage backends."""

    def __init__(self):
        self._backends = {}

    def register(self, name: str, storage_class: Type[Storage]):
        """Register a storage backend.

        Args:
            name: The name of the backend (e.g., "json", "sqlite", "redis")
            storage_class: The storage class that implements the Storage interface
        """
        self._backends[name] = storage_class

    def get_backend(self, name: str) -> Type[Storage]:
        """Get a storage backend by name.

        Args:
            name: The name of the backend

        Returns:
            The storage class

        Raises:
            ValueError: If the backend is not registered
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        return self._backends[name]

    def list_backends(self) -> list[str]:
        """List all registered backend names."""
        return list(self._backends.keys())


# Global registry instance
_registry = StorageRegistry()
