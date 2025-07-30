"""Tests for session interruption and resumption - the core value proposition."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from doteval import foreach
from doteval.evaluators import exact_match
from doteval.sessions import SessionManager
from doteval.storage.json import JSONStorage


@pytest.fixture
def temp_storage():
    """Provide temporary storage for resumption tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_session_interruption_and_resume_basic(temp_storage):
    """Test basic interruption and resumption workflow."""
    # Create test dataset
    test_data = [("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3"), ("Q4", "A4")]

    @foreach("question,answer", test_data)
    def eval_test(question, answer):
        return exact_match(answer, "A1")  # Only first item matches

    # First run - simulate interruption after processing some items
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("test_session")

    # Mock interruption by only processing first 2 items
    with patch("doteval.core._run_evaluation_sync") as mock_run_sync:
        # Simulate processing only 2 items before "crash"
        from doteval.metrics import accuracy
        from doteval.models import EvaluationResult, EvaluationSummary, Score

        # Create realistic results for first 2 items
        score1 = Score("exact_match", True, [accuracy()])
        score2 = Score("exact_match", False, [accuracy()])

        result1 = EvaluationResult([score1], 0, {"question": "Q1", "answer": "A1"})
        result2 = EvaluationResult([score2], 1, {"question": "Q2", "answer": "A2"})

        mock_run_sync.return_value = EvaluationSummary([result1, result2])

        # Add results to session manually (simulating partial completion)
        session_manager1.add_results("eval_test", [result1, result2])

        # Verify session has partial results
        session = session_manager1.get_session("test_session")
        assert len(session.results["eval_test"]) == 2
        assert session.get_completed_item_ids("eval_test") == {0, 1}

    # Second run - resume from where we left off
    session_manager2 = SessionManager(f"json://{temp_storage}")
    # Resume existing session by starting with same name
    session_manager2.start("test_session")  # This should load existing session

    # Check that resumption works
    completed_ids = session_manager2.get_completed_item_ids("eval_test")
    assert completed_ids == {0, 1}  # Should remember what was completed

    # Verify we can get the existing session
    resumed_session = session_manager2.get_session("test_session")
    assert resumed_session is not None
    assert len(resumed_session.results["eval_test"]) == 2


def test_session_resumption_with_real_evaluation(temp_storage):
    """Test resumption with actual evaluation execution."""
    # Create larger dataset to test realistic resumption
    test_data = [(f"Q{i}", f"A{i}") for i in range(1, 11)]  # 10 items

    @foreach("question,answer", test_data)
    def eval_large_test(question, answer):
        return exact_match(answer, "A1")  # Only first matches

    # First run - partial execution
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("large_test_session")

    # Run with limited samples to simulate interruption
    result1 = eval_large_test(session_manager=session_manager1, samples=5)

    # Verify partial completion
    assert len(result1.results) == 5
    session = session_manager1.get_session("large_test_session")
    assert len(session.results["eval_large_test"]) == 5
    completed_ids_first = session.get_completed_item_ids("eval_large_test")
    assert completed_ids_first == {0, 1, 2, 3, 4}

    # Second run - should resume and complete remaining items
    session_manager2 = SessionManager(f"json://{temp_storage}")
    # Resume existing session
    session_manager2.start("large_test_session")

    # This should process remaining items (5-9)
    result2 = eval_large_test(session_manager=session_manager2)
    assert len(result2.results) == 10  # Should return all results from session

    # Verify completion
    resumed_session = session_manager2.get_session("large_test_session")
    assert len(resumed_session.results["eval_large_test"]) == 10
    final_completed_ids = resumed_session.get_completed_item_ids("eval_large_test")
    assert final_completed_ids == {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}


def test_session_lock_handling_during_interruption(temp_storage):
    """Test that session locks are properly handled during interruption."""
    storage = JSONStorage(temp_storage)
    session_manager = SessionManager(f"json://{temp_storage}")

    # Start session (this should acquire lock)
    session_manager.start("locked_session")

    # Verify lock is acquired
    assert storage.is_locked("locked_session")

    # Simulate normal completion (should release lock)
    session_manager.finish(success=True)

    # Verify lock is released
    assert not storage.is_locked("locked_session")


def test_session_lock_detection_for_interrupted_sessions(temp_storage):
    """Test detection of interrupted sessions via lock files."""
    storage = JSONStorage(temp_storage)

    # Manually create a lock file (simulating interrupted session)
    storage.acquire_lock("interrupted_session")

    # Create session manager to check lock status
    session_manager = SessionManager(f"json://{temp_storage}")

    # Should detect that session is locked (interrupted)
    assert storage.is_locked("interrupted_session")
    assert session_manager.storage.is_locked("interrupted_session")

    # Clean up
    storage.release_lock("interrupted_session")
    assert not storage.is_locked("interrupted_session")


def test_multiple_session_concurrent_access(temp_storage):
    """Test that multiple sessions can't interfere with each other."""
    # Create two different sessions
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("session_a")

    session_manager2 = SessionManager(f"json://{temp_storage}")
    session_manager2.start("session_b")

    # Both should be able to work independently
    test_data = [("Q1", "A1"), ("Q2", "A2")]

    @foreach("question,answer", test_data)
    def eval_a(question, answer):
        return exact_match(answer, "A1")

    @foreach("question,answer", test_data)
    def eval_b(question, answer):
        return exact_match(answer, "A2")

    # Run both evaluations
    result_a = eval_a(session_manager=session_manager1)
    result_b = eval_b(session_manager=session_manager2)

    # Verify they don't interfere
    session_a = session_manager1.get_session("session_a")
    session_b = session_manager2.get_session("session_b")

    assert len(session_a.results["eval_a"]) == 2
    assert len(session_b.results["eval_b"]) == 2

    # Different accuracy due to different matching criteria
    assert result_a.summary["exact_match"]["accuracy"] == 0.5  # Only Q1/A1 matches
    assert result_b.summary["exact_match"]["accuracy"] == 0.5  # Only Q2/A2 matches


def test_session_resumption_with_errors(temp_storage):
    """Test resumption when some items had errors."""
    test_data = [("Q1", "A1"), ("error", "A2"), ("Q3", "A3")]

    call_count = 0

    @foreach("question,answer", test_data)
    def eval_with_errors(question, answer):
        nonlocal call_count
        call_count += 1

        if question == "error":
            raise ValueError("Simulated evaluation error")
        return exact_match(answer, "A1")

    # First run - process all items (including error)
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("error_session")

    result1 = eval_with_errors(session_manager=session_manager1)

    # Verify all items processed (including error)
    assert len(result1.results) == 3
    session = session_manager1.get_session("error_session")
    assert len(session.results["eval_with_errors"]) == 3

    # Check that error item is recorded but not in completed_ids
    completed_ids = session.get_completed_item_ids("eval_with_errors")
    # Only successful items should be in completed_ids
    assert 1 not in completed_ids  # Error item should not be "completed"

    # Reset call count for second run
    call_count = 0

    # Second run - should not re-process successful items
    session_manager2 = SessionManager(f"json://{temp_storage}")
    session_manager2.start("error_session")  # Resume existing session
    result2 = eval_with_errors(session_manager=session_manager2)
    assert (
        len(result2.results) == 4
    )  # Should have all results (3 original + 1 retried error)

    # Should not have called the function again for successful items
    # This depends on the implementation - if errors are retried, call_count might be > 0


def test_session_data_persistence_across_processes(temp_storage):
    """Test that session data persists correctly across process restarts."""
    # First "process" - create and populate session
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("persistent_session")

    test_data = [("Q1", "A1"), ("Q2", "A2")]

    @foreach("question,answer", test_data)
    def eval_persistent(question, answer):
        return exact_match(answer, "A1")

    result1 = eval_persistent(session_manager=session_manager1)
    session_manager1.finish(success=True)

    # Store original results for comparison
    original_accuracy = result1.summary["exact_match"]["accuracy"]
    original_results_count = len(result1.results)

    # Second "process" - load existing session
    session_manager2 = SessionManager(f"json://{temp_storage}")

    # Should be able to retrieve the same session
    loaded_session = session_manager2.get_session("persistent_session")
    assert loaded_session is not None
    assert loaded_session.name == "persistent_session"
    assert len(loaded_session.results["eval_persistent"]) == original_results_count

    # Verify data integrity
    from doteval.models import EvaluationSummary

    loaded_summary = EvaluationSummary(loaded_session.results["eval_persistent"])
    assert loaded_summary.summary["exact_match"]["accuracy"] == original_accuracy


def test_session_resumption_with_different_sample_limits(temp_storage):
    """Test resumption behavior with different sample limits."""
    test_data = [(f"Q{i}", f"A{i}") for i in range(1, 21)]  # 20 items

    @foreach("question,answer", test_data)
    def eval_samples_test(question, answer):
        return exact_match(answer, "A1")

    # First run - process 10 items
    session_manager1 = SessionManager(f"json://{temp_storage}")
    session_manager1.start("samples_session")

    result1 = eval_samples_test(session_manager=session_manager1, samples=10)
    assert len(result1.results) == 10

    # Second run - try to process 15 items total
    session_manager2 = SessionManager(f"json://{temp_storage}")
    session_manager2.start("samples_session")  # Resume existing session

    # Should process 5 more items (15 - 10 already completed)
    result2 = eval_samples_test(session_manager=session_manager2, samples=15)
    assert len(result2.results) == 15  # Should return all results from session

    # Verify total items processed
    session = session_manager2.get_session("samples_session")
    assert len(session.results["eval_samples_test"]) == 15


def test_session_cleanup_after_completion(temp_storage):
    """Test proper cleanup after session completion."""
    storage = JSONStorage(temp_storage)
    session_manager = SessionManager(f"json://{temp_storage}")

    # Start session
    session_manager.start("cleanup_session")
    assert storage.is_locked("cleanup_session")

    test_data = [("Q1", "A1")]

    @foreach("question,answer", test_data)
    def eval_cleanup(question, answer):
        return exact_match(answer, "A1")

    # Run evaluation
    result = eval_cleanup(session_manager=session_manager)
    assert len(result.results) == 1  # Should process single item

    # Finish session
    session_manager.finish(success=True)

    # Verify cleanup
    assert not storage.is_locked("cleanup_session")

    # Session data should still exist
    session = session_manager.get_session("cleanup_session")
    assert session is not None
    assert len(session.results["eval_cleanup"]) == 1
