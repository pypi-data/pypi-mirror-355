"""Integration tests for complete doteval workflows."""

import tempfile
from pathlib import Path

from doteval import foreach
from doteval.evaluators import exact_match
from doteval.sessions import SessionManager


def test_complete_evaluation_workflow():
    """Test the full user workflow end-to-end."""
    # Create temporary directory for test storage
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)

        # Simple test dataset
        test_data = [
            ("What is 2+2?", "4"),
            ("What is 3+3?", "6"),
            ("What is 5+5?", "10"),
        ]

        # Define evaluation function
        @foreach("question,answer", test_data)
        def eval_math(question, answer):
            # Simulate some processing
            return exact_match(answer, "4" if "2+2" in question else "wrong")

        # Create session manager with custom storage
        session_manager = SessionManager(f"json://{storage_path}")
        session_manager.start("test_session")

        # Run the evaluation
        result = eval_math(session_manager=session_manager)

        # Verify results
        assert len(result.results) == 3
        assert (
            result.summary["exact_match"]["accuracy"] == 1 / 3
        )  # Only first item matches

        # Verify session was created and persisted
        sessions = session_manager.list_sessions()
        assert len(sessions) > 0

        # Verify we can retrieve the session
        session = session_manager.get_session("test_session")
        assert session is not None
        assert len(session.results["eval_math"]) == 3


def test_session_persistence_across_runs():
    """Test that session state persists across multiple runs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)

        test_data = [("Q1", "A1"), ("Q2", "A2")]

        @foreach("question,answer", test_data)
        def eval_test(question, answer):
            return exact_match(answer, "A1")

        # First run
        session_manager1 = SessionManager(f"json://{storage_path}")
        session_manager1.start("test_session")
        result1 = eval_test(session_manager=session_manager1)
        assert len(result1.results) == 2  # Verify first run processed items

        # Second run with new session manager (simulates new process)
        session_manager2 = SessionManager(f"json://{storage_path}")

        # Should be able to retrieve the same session
        session = session_manager2.get_session("test_session")
        assert session is not None
        assert len(session.results["eval_test"]) == 2

        # Results should be the same
        sessions = session_manager2.list_sessions()
        assert len(sessions) == 1
