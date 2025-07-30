import json
import os

import pytest
from PIL import Image

from doteval.models import EvaluationResult, Score
from doteval.sessions import Session, SessionStatus
from doteval.storage import JSONStorage


@pytest.fixture
def storage_dir(tmp_path):
    """Create a temporary directory for storage tests."""
    return tmp_path


@pytest.fixture
def storage(storage_dir):
    """Create a JSONStorage instance."""
    return JSONStorage(str(storage_dir))


def test_json_storage_initialization(storage_dir):
    """Test JSONStorage initialization creates directory."""
    storage = JSONStorage(str(storage_dir))
    assert storage_dir.exists()
    assert storage.dir == storage_dir


def test_json_storage_save_and_load_session(storage):
    """Test saving and loading a session."""
    session = Session(name="test_session")
    session.metadata = {"key": "value", "number": 42}
    session.status = SessionStatus.completed

    score1 = Score("evaluator1", True, [])
    score2 = Score("evaluator2", 0.95, [])
    result1 = EvaluationResult(
        scores=[score1, score2],
        item_id=0,
        item_data={"input": "test", "expected": "output"},
        error=None,
        timestamp=1234567890.0,
    )
    result2 = EvaluationResult(
        scores=[score1],
        item_id=1,
        item_data={"input": "test2"},
        error="Test error",
        timestamp=1234567891.0,
    )

    session.add_results("test_func", [result1, result2])
    storage.save(session)

    # Load the session
    loaded = storage.load("test_session")

    assert loaded is not None
    assert loaded.name == session.name
    assert loaded.metadata == session.metadata
    assert loaded.created_at == session.created_at
    assert loaded.status == session.status

    assert "test_func" in loaded.results
    loaded_results = loaded.results["test_func"]
    assert len(loaded_results) == 2

    assert loaded_results[0].item_id == 0
    assert len(loaded_results[0].scores) == 2
    assert loaded_results[0].scores[0].name == "evaluator1"
    assert loaded_results[0].scores[0].value is True
    assert loaded_results[0].scores[1].name == "evaluator2"
    assert loaded_results[0].scores[1].value == 0.95
    assert loaded_results[0].item_data == {"input": "test", "expected": "output"}
    assert loaded_results[0].error is None
    assert loaded_results[0].timestamp == 1234567890.0

    assert loaded_results[1].item_id == 1
    assert loaded_results[1].error == "Test error"


def test_json_storage_load_nonexistent_session(storage):
    """Test loading a non-existent session returns None."""
    loaded = storage.load("nonexistent")
    assert loaded is None


def test_json_storage_load_corrupted_json(storage, storage_dir):
    """Test loading corrupted JSON returns None."""
    corrupted_file = storage_dir / "corrupted.json"
    corrupted_file.write_text("{ invalid json")

    loaded = storage.load("corrupted")
    assert loaded is None


def test_json_storage_list_names(storage):
    """Test listing session names."""
    assert storage.list_names() == []

    session1 = Session("session1")
    session2 = Session("session2")
    session3 = Session("session3")

    storage.save(session1)
    storage.save(session2)
    storage.save(session3)

    names = storage.list_names()
    assert len(names) == 3
    assert set(names) == {"session1", "session2", "session3"}


def test_json_storage_overwrite_session(storage):
    """Test that saving a session with the same name overwrites it."""
    # Save initial session
    session1 = Session("test_session")
    session1.metadata = {"version": 1}
    storage.save(session1)

    # Save session with same name but different data
    session2 = Session("test_session")
    session2.metadata = {"version": 2}
    storage.save(session2)

    # Load and verify it's the second version
    loaded = storage.load("test_session")
    assert loaded.metadata == {"version": 2}


def test_lock_is_created_and_removed(storage):
    session_name = "testsession"
    lock_path = os.path.join(storage.dir, f"{session_name}.lock")

    # Should not be locked initially
    assert not storage.is_locked(session_name)
    assert not os.path.exists(lock_path)

    # Acquire lock
    storage.acquire_lock(session_name)
    assert storage.is_locked(session_name)
    assert os.path.exists(lock_path)

    # Release lock
    storage.release_lock(session_name)
    assert not storage.is_locked(session_name)
    assert not os.path.exists(lock_path)


def test_acquire_lock_raises_if_locked(storage):
    session_name = "locked_session"
    storage.acquire_lock(session_name)

    with pytest.raises(RuntimeError, match="already locked"):
        storage.acquire_lock(session_name)

    # Clean up
    storage.release_lock(session_name)


def test_release_lock_noop_if_not_locked(storage):
    session_name = "not_locked"
    # Should not raise even if lock doesn't exist
    storage.release_lock(session_name)
    assert not storage.is_locked(session_name)


def test_is_locked_reports_correctly(storage):
    session_name = "lockcheck"
    assert not storage.is_locked(session_name)
    storage.acquire_lock(session_name)
    assert storage.is_locked(session_name)
    storage.release_lock(session_name)
    assert not storage.is_locked(session_name)


def test_pil_image_serialization(storage):
    """Test that PIL Images are properly serialized and deserialized."""
    # Create a test PIL Image
    test_image = Image.new("RGB", (100, 100), color="red")

    # Create a session with PIL Image in item_data
    session = Session(name="test_pil")
    result = EvaluationResult(
        scores=[Score("test", 1.0, [], {})],
        item_id="test_item",
        item_data=(test_image, "expected_info"),
        error=None,
        timestamp=0.0,
    )
    session.results["test"] = [result]

    # Save and load the session
    storage.save(session)

    # Verify the JSON file was created and contains base64 data
    json_path = storage.dir / "test_pil.json"
    with open(json_path) as f:
        data = json.load(f)

    # Check that the image was serialized as base64
    item_data = data["results"]["test"][0]["item_data"]
    assert item_data["__type__"] == "tuple"
    assert item_data["data"][0]["__type__"] == "PIL.Image"
    assert "data" in item_data["data"][0]  # base64 data
    assert item_data["data"][0]["mode"] == "RGB"
    assert item_data["data"][0]["size"] == [100, 100]

    # Load the session back
    loaded_session = storage.load("test_pil")
    assert loaded_session is not None

    # Verify the PIL Image was properly deserialized
    loaded_result = loaded_session.results["test"][0]
    loaded_image, loaded_info = loaded_result.item_data

    assert isinstance(loaded_image, Image.Image)
    assert loaded_image.mode == "RGB"
    assert loaded_image.size == (100, 100)
    assert loaded_info == "expected_info"


def test_nested_pil_images(storage):
    """Test serialization of nested structures containing PIL Images."""
    # Create test images
    img1 = Image.new("RGB", (50, 50), color="blue")
    img2 = Image.new("RGBA", (75, 75), color="green")

    # Create complex nested structure
    session = Session(name="test_nested")
    result = EvaluationResult(
        scores=[Score("test", 1.0, [], {})],
        item_id="nested_test",
        item_data={
            "images": [img1, img2],
            "metadata": {
                "primary_image": img1,
                "tuple_with_image": (img2, "description"),
            },
        },
        error=None,
        timestamp=0.0,
    )
    session.results["test"] = [result]

    # Save and load
    storage.save(session)

    loaded_session = storage.load("test_nested")
    assert loaded_session is not None

    loaded_data = loaded_session.results["test"][0].item_data

    # Verify images list
    assert len(loaded_data["images"]) == 2
    assert isinstance(loaded_data["images"][0], Image.Image)
    assert loaded_data["images"][0].size == (50, 50)
    assert loaded_data["images"][0].mode == "RGB"

    assert isinstance(loaded_data["images"][1], Image.Image)
    assert loaded_data["images"][1].size == (75, 75)
    assert loaded_data["images"][1].mode == "RGBA"

    # Verify nested metadata
    assert isinstance(loaded_data["metadata"]["primary_image"], Image.Image)
    assert loaded_data["metadata"]["primary_image"].size == (50, 50)

    # Verify tuple
    assert isinstance(loaded_data["metadata"]["tuple_with_image"], tuple)
    assert len(loaded_data["metadata"]["tuple_with_image"]) == 2
    assert isinstance(loaded_data["metadata"]["tuple_with_image"][0], Image.Image)
    assert loaded_data["metadata"]["tuple_with_image"][1] == "description"
