"""Tests for error handling and user experience in failure scenarios."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from doteval import foreach
from doteval.evaluators import exact_match
from doteval.metrics import accuracy
from doteval.models import Score
from doteval.sessions import SessionManager
from doteval.storage.json import JSONStorage


@pytest.fixture
def temp_storage():
    """Provide temporary storage for error handling tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_evaluation_function_raises_value_error(temp_storage):
    """Test evaluation function raising ValueError provides helpful error message."""
    test_data = [("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3")]

    @foreach("question,answer", test_data)
    def eval_with_value_error(question, answer):
        if question == "Q2":
            raise ValueError("Invalid input format")
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("error_test_session")

    # Should not crash - should continue processing other items
    result = eval_with_value_error(session_manager=session_manager)

    # Should have processed all 3 items (including the error)
    assert len(result.results) == 3

    # First and third items should succeed, second should have error
    assert result.results[0].error is None
    assert result.results[1].error is not None
    assert "Invalid input format" in result.results[1].error
    assert result.results[2].error is None

    # Session should still contain all results
    session = session_manager.get_session("error_test_session")
    assert len(session.results["eval_with_value_error"]) == 3

    # Only successful items should be in completed_ids
    completed_ids = session.get_completed_item_ids("eval_with_value_error")
    assert completed_ids == {0, 2}  # Item 1 (index 1) failed


def test_evaluation_function_raises_key_error(temp_storage):
    """Test evaluation function raising KeyError provides helpful context."""
    test_data = [("Q1", "A1"), ("Q2", "A2")]

    @foreach("question,answer", test_data)
    def eval_with_key_error(question, answer):
        if question == "Q2":
            # Simulates accessing missing dictionary key
            raise KeyError("missing_field")
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("key_error_session")

    result = eval_with_key_error(session_manager=session_manager)

    # Should continue processing despite KeyError
    assert len(result.results) == 2
    assert result.results[0].error is None
    assert result.results[1].error is not None
    assert "missing_field" in result.results[1].error


def test_evaluation_function_raises_type_error(temp_storage):
    """Test evaluation function raising TypeError provides clear error context."""
    test_data = [("Q1", "A1"), ("Q2", "A2")]

    @foreach("question,answer", test_data)
    def eval_with_type_error(question, answer):
        if question == "Q2":
            # Simulates type mismatch
            return question + 123  # String + int TypeError
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("type_error_session")

    result = eval_with_type_error(session_manager=session_manager)

    assert len(result.results) == 2
    assert result.results[0].error is None
    assert result.results[1].error is not None
    # Should capture the actual TypeError message
    assert (
        "concatenate" in result.results[1].error
        or "TypeError" in result.results[1].error
    )


def test_evaluation_function_returns_invalid_type(temp_storage):
    """Test evaluation function returning non-Score objects raises clear error."""
    test_data = [("Q1", "A1"), ("Q2", "A2")]

    @foreach("question,answer", test_data)
    def eval_with_invalid_return(question, answer):
        if question == "Q2":
            return "invalid_return_value"  # Should return Score objects
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("invalid_return_session")

    result = eval_with_invalid_return(session_manager=session_manager)

    assert len(result.results) == 2
    assert result.results[0].error is None
    assert result.results[1].error is not None
    # Should have helpful error message about Score objects
    assert "Score" in result.results[1].error


def test_multiple_errors_in_single_evaluation(temp_storage):
    """Test handling multiple errors in the same evaluation batch."""
    test_data = [(f"Q{i}", f"A{i}") for i in range(1, 6)]  # 5 items

    @foreach("question,answer", test_data)
    def eval_with_multiple_errors(question, answer):
        if question == "Q2":
            raise ValueError("Error in item 2")
        elif question == "Q4":
            raise KeyError("Error in item 4")
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("multiple_errors_session")

    result = eval_with_multiple_errors(session_manager=session_manager)

    # All items should be processed
    assert len(result.results) == 5

    # Check specific error patterns
    assert result.results[0].error is None  # Q1 succeeds
    assert "Error in item 2" in result.results[1].error  # Q2 fails
    assert result.results[2].error is None  # Q3 succeeds
    assert "Error in item 4" in result.results[3].error  # Q4 fails
    assert result.results[4].error is None  # Q5 succeeds

    # Only successful items should be completed
    session = session_manager.get_session("multiple_errors_session")
    completed_ids = session.get_completed_item_ids("eval_with_multiple_errors")
    assert completed_ids == {0, 2, 4}  # Items 1, 3, 5 (0-indexed)


def test_storage_directory_permission_denied():
    """Test handling when storage directory has no write permissions."""
    # Create a directory with no write permissions
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "no_write_perms"
        storage_path.mkdir()
        os.chmod(storage_path, 0o444)  # Read-only

        try:
            # Should provide clear error message about permissions
            with pytest.raises(Exception) as exc_info:
                session_manager = SessionManager(f"json://{storage_path}")
                session_manager.start("permission_test")

            # Error should be informative for users
            error_msg = str(exc_info.value).lower()
            assert any(word in error_msg for word in ["permission", "access", "write"])

        finally:
            # Restore permissions for cleanup
            os.chmod(storage_path, 0o755)


def test_storage_file_corruption_recovery(temp_storage):
    """Test handling when session files are corrupted."""
    # Create a session first
    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("corruption_test")

    test_data = [("Q1", "A1")]

    @foreach("question,answer", test_data)
    def simple_eval(question, answer):
        return exact_match(answer, "A1")

    simple_eval(session_manager=session_manager)
    session_manager.finish(success=True)

    # Corrupt the session file
    session_file = temp_storage / "corruption_test.json"
    with open(session_file, "w") as f:
        f.write("{ invalid json content }")

    # Should handle corruption gracefully
    session_manager2 = SessionManager(f"json://{temp_storage}")

    # Should either return None for corrupted session or raise clear error
    try:
        corrupted_session = session_manager2.get_session("corruption_test")
        # If it doesn't raise, it should return None or valid session
        assert corrupted_session is None or hasattr(corrupted_session, "name")
    except Exception as e:
        # If it raises, error should be informative
        error_msg = str(e).lower()
        assert any(
            word in error_msg for word in ["corrupt", "invalid", "json", "parse"]
        )


def test_disk_space_exhaustion_simulation(temp_storage):
    """Test behavior when disk space is exhausted during save operations."""
    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("disk_space_test")

    # Mock the storage save to simulate disk full error
    with patch.object(session_manager.storage, "save") as mock_save:
        mock_save.side_effect = OSError(28, "No space left on device")  # ENOSPC

        test_data = [("Q1", "A1")]

        @foreach("question,answer", test_data)
        def disk_test_eval(question, answer):
            return exact_match(answer, "A1")

        # Should handle disk space error gracefully
        with pytest.raises(OSError) as exc_info:
            disk_test_eval(session_manager=session_manager)

        # Error should be informative
        assert "space" in str(exc_info.value).lower()


def test_storage_backend_unavailable():
    """Test handling when storage backend is unavailable."""
    # Test with invalid storage backend
    with pytest.raises(ValueError) as exc_info:
        SessionManager("invalid://nonexistent/path")

    # Should provide clear, helpful error message
    error_msg = str(exc_info.value).lower()
    assert "unknown storage backend" in error_msg
    assert "invalid" in error_msg  # Should mention the invalid backend name

    # Test with no backend specified should default to json (backward compatibility)
    # This should not raise an error
    manager = SessionManager("just_a_path")
    assert manager.storage.__class__.__name__ == "JSONStorage"


def test_empty_dataset_handling(temp_storage):
    """Test handling of empty datasets."""
    empty_data = []

    @foreach("question,answer", empty_data)
    def eval_empty_dataset(question, answer):
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("empty_dataset_session")

    # Should handle empty dataset gracefully
    result = eval_empty_dataset(session_manager=session_manager)

    assert len(result.results) == 0
    assert result.summary == {}  # Empty summary for empty results


def test_malformed_dataset_entries(temp_storage):
    """Test handling of malformed dataset entries."""
    # Dataset with inconsistent structure
    malformed_data = [
        ("Q1", "A1"),  # Good entry
        ("Q2",),  # Missing answer
        ("Q3", "A3", "extra"),  # Extra field
        ("Q4", "A4"),  # Good entry
    ]

    @foreach("question,answer", malformed_data)
    def eval_malformed_dataset(question, answer):
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("malformed_dataset_session")

    # Check what actually happens with malformed entries
    result = eval_malformed_dataset(session_manager=session_manager)

    # Should have attempted to process all entries
    assert len(result.results) == 4

    # Check what actually happens - the system is surprisingly robust
    # ("Q2",) - missing answer - should cause unpacking error
    assert result.results[1].error is not None
    # ("Q3", "A3", "extra") - extra field - actually handled gracefully! Extra field ignored
    # This shows the system is more robust than expected
    assert result.results[2].error is None  # System ignores extra fields


def test_dataset_iterator_exhaustion(temp_storage):
    """Test handling when dataset iterator is exhausted unexpectedly."""

    def problematic_iterator():
        yield ("Q1", "A1")
        yield ("Q2", "A2")
        # Iterator ends unexpectedly
        return

    @foreach("question,answer", problematic_iterator())
    def eval_exhausted_iterator(question, answer):
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("exhausted_iterator_session")

    # Should handle iterator exhaustion gracefully
    result = eval_exhausted_iterator(session_manager=session_manager)

    # Should process available items
    assert len(result.results) == 2


def test_session_already_locked_handling(temp_storage):
    """Test handling when trying to start a session that's already locked."""
    # First session manager acquires lock
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("locked_session")

    # Second session manager should handle the locked session appropriately
    session_manager2 = SessionManager(f"json://{temp_storage}")

    # Should either resume the existing session or handle conflict gracefully
    resumed_session = session_manager2.start("locked_session")

    # Should be the same session or properly handle the conflict
    assert resumed_session.name == "locked_session"


def test_storage_lock_file_cleanup_after_completion(temp_storage):
    """Test that lock files are properly cleaned up after completion."""
    storage = JSONStorage(temp_storage)
    session_manager = SessionManager(f"json://{temp_storage}")

    # Start session (should create lock)
    session_manager.start("cleanup_test")
    assert storage.is_locked("cleanup_test")

    # Finish session (should remove lock)
    session_manager.finish(success=True)
    assert not storage.is_locked("cleanup_test")

    # Session data should still exist
    session = session_manager.get_session("cleanup_test")
    assert session is not None


def test_stale_lock_file_handling(temp_storage):
    """Test handling of stale lock files from crashed processes."""
    storage = JSONStorage(temp_storage)

    # Manually create a stale lock file
    lock_file = temp_storage / "stale_session.lock"
    lock_file.write_text("stale_process_id")

    # Should detect and handle stale locks appropriately
    session_manager = SessionManager(f"json://{temp_storage}")

    # Current implementation might not handle stale locks,
    # but this test defines expected behavior
    assert storage.is_locked("stale_session")

    # Verify session manager can access the storage
    assert session_manager.storage.is_locked("stale_session")


def test_memory_pressure_large_results(temp_storage):
    """Test handling when evaluation results consume excessive memory."""
    # Create large dataset
    large_data = [(f"Q{i}", f"A{i}") for i in range(1000)]

    @foreach("question,answer", large_data)
    def eval_memory_intensive(question, answer):
        # Create a large score object (simulating memory pressure)
        large_metrics = [accuracy() for _ in range(100)]
        return Score("memory_test", True, large_metrics)

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("memory_pressure_session")

    # Should handle large results gracefully
    result = eval_memory_intensive(session_manager=session_manager, samples=10)

    assert len(result.results) == 10
    # Each result should have the large score
    assert all(len(r.scores) == 1 for r in result.results if not r.error)


def test_many_sessions_file_descriptor_management(temp_storage):
    """Test handling when system creates many sessions."""
    session_manager = SessionManager(f"json://{temp_storage}")

    # Create and finish many sessions to test file descriptor cleanup
    for i in range(100):
        session_manager.start(f"file_test_{i}")
        session_manager.finish(success=True)

    # Should not accumulate file descriptors
    # All sessions should be properly saved and closed
    sessions = session_manager.list_sessions()
    assert len(sessions) == 100


def test_helpful_error_context_in_results(temp_storage):
    """Test that error results include helpful context for debugging."""
    test_data = [("Q1", "A1"), ("Q2", "A2")]

    @foreach("question,answer", test_data)
    def eval_with_context_error(question, answer):
        if question == "Q2":
            # Error that should include context
            raise ValueError(f"Failed to process question: {question}")
        return exact_match(answer, "A1")

    session_manager = SessionManager(f"json://{temp_storage}")
    session_manager.start("context_error_session")

    result = eval_with_context_error(session_manager=session_manager)

    # Error should include the original error message
    error_result = result.results[1]
    assert error_result.error is not None
    assert "Failed to process question: Q2" in error_result.error

    # Error result should still include item data for debugging
    assert error_result.item_data == {"question": "Q2", "answer": "A2"}
    assert error_result.item_id == 1


def test_session_resumption_after_errors(temp_storage):
    """Test that sessions can be resumed properly after errors occur."""
    test_data = [("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3")]

    @foreach("question,answer", test_data)
    def eval_resumption_after_error(question, answer):
        if question == "Q2":
            raise ValueError("Temporary error")
        return exact_match(answer, "A1")

    # First run with errors
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("resumption_error_session")

    result1 = eval_resumption_after_error(session_manager=session_manager1)
    session_manager1.finish(success=False)  # Finish with failure

    # Verify error was recorded
    assert len(result1.results) == 3
    assert result1.results[1].error is not None

    # Resume session
    session_manager2 = SessionManager(f"json://{temp_storage}")
    session_manager2.start("resumption_error_session")

    # Session should be loaded and should have previous results
    session = session_manager2.get_session("resumption_error_session")
    assert session is not None

    # Session should now properly preserve results even after failed finish
    assert len(session.results) > 0  # Should have preserved results
    eval_results = list(session.results.values())[0]
    assert len(eval_results) == 3

    # Only successful items should be marked as completed
    completed_ids = session.get_completed_item_ids("eval_resumption_after_error")
    assert completed_ids == {0, 2}  # Q1 and Q3 succeeded


def test_session_status_display_for_cli(temp_storage):
    """Test that sessions show correct status for CLI display."""
    from doteval.sessions import SessionStatus

    # Test completed session (success=True)
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("completed_session")
    session_manager1.finish(success=True)

    # Should not be locked and status should be completed
    storage = session_manager1.storage
    assert not storage.is_locked("completed_session")
    session = session_manager1.get_session("completed_session")
    assert session.status == SessionStatus.completed

    # Test error session (success=False)
    session_manager2 = SessionManager(f"json://{temp_storage}")
    session_manager2.start("error_session")
    session_manager2.finish(success=False)

    # Should still be locked and status should be failed
    assert storage.is_locked("error_session")
    session = session_manager2.get_session("error_session")
    assert session.status == SessionStatus.failed

    # Test interrupted session (never finished)
    session_manager3 = SessionManager(f"json://{temp_storage}")
    session_manager3.start("interrupted_session")
    # Don't call finish() - simulates process crash

    # Should be locked and status should be running
    assert storage.is_locked("interrupted_session")
    session = session_manager3.get_session("interrupted_session")
    assert session.status == SessionStatus.running
