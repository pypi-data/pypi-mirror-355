"""Tests for the doteval pytest plugin functionality.

These are tests that specifically test the pytest plugin integration.
Tests for the core foreach functionality are in test_core.py.
"""

import os
import subprocess
import sys
import tempfile


def test_pytest_plugin_basic_execution():
    """Test that the pytest plugin can execute doteval tests."""
    # Create a temporary test file
    test_content = """
import doteval
from doteval.evaluators import exact_match

dataset = [("Hello", "Hello"), ("World", "World")]

@doteval.foreach("input,expected", dataset)
def eval_basic(input, expected):
    return exact_match(input, expected)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_content)
        f.flush()

        try:
            # Run pytest on the temp file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f.name, "-v"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            # Check that the test passed
            assert result.returncode == 0
            assert "eval_basic" in result.stdout
            assert "1 passed" in result.stdout

        finally:
            os.unlink(f.name)


def test_pytest_plugin_parametrize():
    """Test that the pytest plugin can execute doteval tests."""
    # Create a temporary test file
    test_content = """
import doteval
import pytest
from doteval.evaluators import exact_match

dataset = [("Hello", "Hello"), ("World", "World")]

@pytest.mark.parametrize(
    "add", ["a", "b", "c"]
)
@doteval.foreach("input,expected", dataset)
def eval_basic(input, expected, add):
    return exact_match(input, expected)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_content)
        f.flush()

        try:
            # Run pytest on the temp file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f.name, "-v"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            # Check that the test passed
            assert result.returncode == 0
            assert "eval_basic" in result.stdout
            assert "3 passed" in result.stdout

        finally:
            os.unlink(f.name)


def test_pytest_plugin_fixture():
    """Test that the pytest plugin can execute doteval tests with fixtures."""
    # Create a temporary test file
    test_content = """
import doteval
import pytest
from doteval.evaluators import exact_match

@pytest.fixture
def add():
    return "a"

dataset = [("Hello", "Hello"), ("World", "World")]

@doteval.foreach("input,expected", dataset)
def eval_basic(input, expected, add):
    add()
    return exact_match(input, expected)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_content)
        f.flush()

        try:
            # Run pytest on the temp file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f.name, "-v"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            # Check that the test passed
            assert result.returncode == 0
            assert "eval_basic" in result.stdout
            assert "1 passed" in result.stdout

        finally:
            os.unlink(f.name)


def test_pytest_plugin_samples_option():
    """Test that the --samples option works with pytest."""
    # Create a temporary test file with larger dataset
    test_content = """
import doteval
from doteval.evaluators import exact_match

dataset = [
    ("Q1", "A1"),
    ("Q2", "A2"),
    ("Q3", "A3"),
    ("Q4", "A4"),
    ("Q5", "A5")
]

@doteval.foreach("question,answer", dataset)
def eval_with_samples(question, answer):
    return exact_match(question, answer)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_content)
        f.flush()

        try:
            # Run pytest with --samples option
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    f.name,
                    "--samples",
                    "2",
                    "-v",  # Verbose to show function names
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            # Check that the test passed
            assert result.returncode == 0
            assert "eval_with_samples" in result.stdout
            assert "1 passed" in result.stdout

        finally:
            os.unlink(f.name)


def test_pytest_plugin_custom_column_names():
    """Test that custom column names work in pytest."""
    test_content = """
import doteval
from doteval.evaluators import exact_match

dataset = [("user_input", "model_output", "extra_context")]

@doteval.foreach("user_prompt,model_response,context", dataset)
def eval_custom_columns(user_prompt, model_response, context):
    combined = f"{user_prompt}-{model_response}-{context}"
    expected = "user_input-model_output-extra_context"
    return exact_match(combined, expected)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_content)
        f.flush()

        try:
            # Run pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f.name, "-v"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            # Check that the test passed
            assert result.returncode == 0
            assert "eval_custom_columns" in result.stdout
            assert "1 passed" in result.stdout

        finally:
            os.unlink(f.name)
