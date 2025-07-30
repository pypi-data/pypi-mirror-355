import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from doteval.models import EvaluationResult


class SessionStatus(Enum):
    running: str = "Running"
    completed: str = "Completed"
    failed: str = "Failed"


@dataclass
class Session:
    name: str
    results: dict[str, list[EvaluationResult]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    status: SessionStatus = SessionStatus.running

    def add_results(self, test_name: str, new_results: list[EvaluationResult]):
        if test_name not in self.results:
            self.results[test_name] = []

        self.results[test_name].extend(new_results)

    def get_completed_item_ids(self, test_name: str) -> set[int]:
        if test_name not in self.results:
            return set()

        return {r.item_id for r in self.results[test_name] if not r.error}

    def get_results(self, test_name: str):
        return self.results.get(test_name, [])


class SessionManager:
    """Manages session lifecycle and storage"""

    def __init__(self, storage_path: Optional[str]):
        from doteval.storage import get_storage

        storage_path = "json://evals" if storage_path is None else storage_path
        self.storage = get_storage(storage_path)
        self.current: Session | None = None

    def start(self, name: str) -> Session:
        # Try loading an existing session if it's locked (resumable)
        if self.storage.is_locked(name):
            session = self.storage.load(name)

            if session and session.status in [
                SessionStatus.running,
                SessionStatus.failed,
            ]:
                # Resume existing session - set status to running
                session.status = SessionStatus.running
                self.storage.save(session)
                self.current = session
                return session

        # Check if trying to start a completed session
        existing_session = self.storage.load(name)
        if existing_session and existing_session.status == SessionStatus.completed:
            raise ValueError(
                f"Session '{name}' is already completed. "
                "Use a different session name to start a new evaluation."
            )

        # Create a new session
        self.storage.acquire_lock(name)
        session = Session(name=name)
        session.metadata["git_commit"] = self.get_git_commit()

        self.storage.save(session)
        self.current = session

        return session

    def add_results(self, test_name: str, results: list[EvaluationResult]):
        if self.current:
            self.current.add_results(test_name, results)
            self.storage.save(self.current)

    def get_completed_item_ids(self, test_name: str) -> set[int]:
        if not self.current:
            return set()

        return self.current.get_completed_item_ids(test_name)

    def get_results(self, test_name: str):
        if self.current:
            return self.current.get_results(test_name)

    def finish(self, success: bool = True):
        if self.current:
            self.current.status = (
                SessionStatus.completed if success else SessionStatus.failed
            )
            self.storage.save(self.current)
            if success:  # Only release lock if truly completed
                self.storage.release_lock(self.current.name)
            self.current = None

    def get_session(self, name: str) -> Optional[Session]:
        return self.storage.load(name)

    def delete_session(self, name: str):
        """Delete a session if it exists."""
        self.storage.delete(name)

    def list_sessions(self) -> list[str]:
        return self.storage.list_names()

    def get_git_commit(self) -> Optional[str]:
        """Get git commit if available"""
        try:
            import subprocess

            return (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()[:8]
            )
        except subprocess.CalledProcessError:
            return None
