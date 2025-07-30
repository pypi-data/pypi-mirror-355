import json
from pathlib import Path
from typing import Optional

from doteval.metrics import registry
from doteval.models import EvaluationResult, Score
from doteval.sessions import Session, SessionStatus
from doteval.storage.base import Storage, _registry

__all__ = ["JSONStorage"]


class JSONStorage(Storage):
    def __init__(self, path: str):
        self.dir = Path(path)
        self.dir.mkdir(exist_ok=True)

    def save(self, session: Session):
        """Save a Session instance to a JSON file"""
        data = serialize(session)

        file_path = self.dir / f"{session.name}.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, name: str) -> Optional[Session]:
        """Load a `Session` instance from a JSON file"""
        file_path = self.dir / f"{name}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path) as f:
                data = json.load(f)
            return deserialize(data)
        except json.JSONDecodeError:
            return None

    def list_names(self) -> list[str]:
        return [f.stem for f in self.dir.glob("*.json")]

    def rename(self, old_name: str, new_name: str):
        old_session_path = self.dir / f"{old_name}.json"
        new_session_path = self.dir / f"{new_name}.json"

        if old_session_path.exists():
            old_session_path.rename(new_session_path)

    def delete(self, name: str):
        session_path = self.dir / f"{name}.json"

        if session_path.exists():
            session_path.unlink()
        else:
            raise ValueError(f"{name}: session not found.")

    def acquire_lock(self, name: str):
        lock = self.dir / f"{name}.lock"
        if lock.exists():
            raise RuntimeError(f"Session '{name}' is already locked.")
        lock.touch()

    def release_lock(self, name: str):
        lock = self.dir / f"{name}.lock"
        if lock.exists():
            lock.unlink()

    def is_locked(self, name: str) -> bool:
        lock = self.dir / f"{name}.lock"
        return lock.exists()


def serialize(session: Session) -> dict:
    data: dict = {
        "name": session.name,
        "metadata": session.metadata,
        "created_at": session.created_at,
        "status": session.status.value,
        "results": {},
    }

    for test_name, results in session.results.items():
        data["results"][test_name] = [
            {
                "item_id": r.item_id,
                "scores": [
                    {
                        "name": s.name,
                        "value": s.value,
                        "metrics": [metric.__name__ for metric in s.metrics],
                        "metadata": s.metadata,
                    }
                    for s in r.scores
                ],
                "item_data": r.item_data,
                "error": r.error,
                "timestamp": r.timestamp,
            }
            for r in results
        ]

    return data


def deserialize(data: dict) -> Session:
    session = Session(
        name=data["name"],
        metadata=data["metadata"],
        created_at=data["created_at"],
        status=SessionStatus(data["status"]),
    )

    for test_name, results_data in data["results"].items():
        results = []
        for r_data in results_data:
            scores = [
                Score(
                    s["name"],
                    s["value"],
                    [registry[name] for name in s["metrics"]],
                    s["metadata"],
                )
                for s in r_data["scores"]
            ]
            result = EvaluationResult(
                scores=scores,
                item_id=r_data["item_id"],
                item_data=r_data["item_data"],
                error=r_data["error"],
                timestamp=r_data["timestamp"],
            )
            results.append(result)
        session.results[test_name] = results

    return session


# Register the JSON backend
_registry.register("json", JSONStorage)
