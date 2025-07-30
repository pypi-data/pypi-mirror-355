"""Test the storage registry system for extensibility."""

import pytest

from doteval.sessions import Session
from doteval.storage.base import Storage


class MockStorage(Storage):
    """A mock storage backend for testing."""

    def __init__(self, path: str):
        self.path = path
        self.sessions: dict[str, Session] = {}
        self.locks: set[str] = set()

    def save(self, session: Session):
        self.sessions[session.name] = session

    def load(self, name: str):
        return self.sessions.get(name)

    def list_names(self):
        return list(self.sessions.keys())

    def rename(self, old_name: str, new_name: str):
        if old_name in self.sessions:
            self.sessions[new_name] = self.sessions.pop(old_name)

    def delete(self, name: str):
        if name in self.sessions:
            del self.sessions[name]
        else:
            raise ValueError(f"{name}: session not found.")

    def acquire_lock(self, name: str):
        if name in self.locks:
            raise RuntimeError(f"Session '{name}' is already locked.")
        self.locks.add(name)

    def release_lock(self, name: str):
        self.locks.discard(name)

    def is_locked(self, name: str):
        return name in self.locks


def test_register_custom_backend():
    """Test registering a custom storage backend."""
    from doteval.storage import get_storage, register

    # Register the mock backend
    register("mock", MockStorage)

    # Create storage using the custom backend
    storage = get_storage("mock://test/path")

    assert isinstance(storage, MockStorage)
    assert storage.path == "test/path"


def test_get_storage_with_unknown_backend():
    """Test that unknown backends raise an error."""
    from doteval.storage import get_storage

    with pytest.raises(ValueError, match="Unknown storage backend: unknown"):
        get_storage("unknown://path")


def test_backward_compatibility(tmp_path):
    """Test that existing storage paths still work."""
    from doteval.storage import get_storage
    from doteval.storage.json import JSONStorage
    from doteval.storage.sqlite import SQLiteStorage

    # Test JSON backend
    json_path = tmp_path / "json_storage"
    json_storage = get_storage(f"json://{json_path}")
    assert isinstance(json_storage, JSONStorage)

    # Test SQLite backend
    sqlite_path = tmp_path / "db.sqlite"
    sqlite_storage = get_storage(f"sqlite://{sqlite_path}")
    assert isinstance(sqlite_storage, SQLiteStorage)


def test_custom_backend_functionality():
    """Test that custom backends work with SessionManager."""
    from doteval.sessions import SessionManager
    from doteval.storage import register

    # Register mock backend
    register("mock", MockStorage)

    # Use it with SessionManager
    manager = SessionManager(storage_path="mock://memory")

    # Create and save a session
    session = manager.start("test_session")
    assert session.name == "test_session"

    # Verify it's saved
    loaded = manager.get_session("test_session")
    assert loaded is not None
    assert loaded.name == "test_session"


def test_list_backends():
    """Test listing available backends."""
    from doteval.storage import list_backends, register

    # Register a test backend
    register("test_backend", MockStorage)

    backends = list_backends()
    assert "json" in backends
    assert "sqlite" in backends
    assert "test_backend" in backends


def test_reregister_backend():
    """Test that re-registering a backend overwrites the previous one."""
    from doteval.storage import get_storage, register

    class AnotherMockStorage(MockStorage):
        pass

    # Register first version
    register("retest", MockStorage)
    storage1 = get_storage("retest://path")
    assert isinstance(storage1, MockStorage)

    # Re-register with different class
    register("retest", AnotherMockStorage)
    storage2 = get_storage("retest://path")
    assert isinstance(storage2, AnotherMockStorage)


def test_storage_path_without_protocol(tmp_path):
    """Test that paths without protocol default to json."""
    from doteval.storage import get_storage
    from doteval.storage.json import JSONStorage

    # Path without protocol should default to JSON
    storage_path = tmp_path / "storage"
    storage = get_storage(str(storage_path))
    assert isinstance(storage, JSONStorage)
