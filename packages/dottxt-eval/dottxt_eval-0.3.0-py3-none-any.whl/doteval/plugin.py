import inspect

import pytest

from doteval.core import run_evaluation
from doteval.sessions import SessionManager


@pytest.hookimpl
def pytest_addoption(parser):
    """Add command line options that are specific to doteval"""
    parser.addoption(
        "--samples", type=int, help="Maximum number of dataset samples to evaluate"
    )
    parser.addoption("--session", type=str, help="Name of the evaluation session.")
    parser.addoption("--storage", type=str, help="Path of the session storage")


@pytest.hookimpl
def pytest_configure(config):
    """Configure pytest.

    We configure pytest to also collect files prefixed by `eval_` and
    functions also prefixed by `eval_`.

    """
    config.addinivalue_line("markers", "doteval: mark test as LLM evaluation")
    config.addinivalue_line("python_files", "eval_*.py")
    config.addinivalue_line("python_functions", "eval_*")
    config._evaluation_results = {}


@pytest.hookimpl
def pytest_pyfunc_call(pyfuncitem):
    """Intercept function calls for doteval functions"""
    if hasattr(pyfuncitem.function, "_metadata"):
        # For doteval functions, return True to indicate we handled the call
        # This prevents the RuntimeError from the wrapper
        return True


@pytest.hookimpl
def pytest_generate_tests(metafunc):
    """Handle doteval functions - minimal parametrization to prevent fixture errors"""
    if hasattr(metafunc.function, "_metadata"):
        metadata = metafunc.function._metadata
        columns = [col.strip() for col in metadata.column_spec.split(",")]

        # Only parametrize dataset columns that pytest thinks are fixtures
        for column in columns:
            if column in metafunc.fixturenames:
                metafunc.parametrize(column, [None])


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Mark evaluations and enable output for progress bars.

    This allows users to only run evals or regular tests with:

        >>> pytest -m "doteval"
        >>> pytest -m "not doteval"

    """
    for item in items:
        if hasattr(item.function, "_metadata"):
            item.add_marker(pytest.mark.doteval)

    # Note: Users should use -s flag to see progress bars
    # Future: Could auto-enable output for better UX


@pytest.hookimpl
def pytest_runtest_setup(item):
    """Setup phase.

    For doteval functions, we skip normal pytest setup since
    we handle everything in pytest_runtest_call.
    """
    if hasattr(item.function, "_metadata"):
        # Collect options for later use
        samples = item.config.getoption("--samples")
        item._samples = samples
        session = item.config.getoption("--session")
        item._session = session
        storage = item.config.getoption("--storage")
        item._storage = storage

        # Skip normal pytest fixture resolution by not calling fixtures
        # pytest_runtest_call will handle everything


@pytest.hookimpl
def pytest_sessionstart(session):
    session_name = session.config.getoption("--session")
    storage = session.config.getoption("--storage")
    if not session_name:
        return

    session_manager = SessionManager(storage)
    session_manager.start(session_name)

    session.config._session_manager = session_manager


@pytest.hookimpl
def pytest_runtest_call(item):
    """Execute the evaluation function"""
    if hasattr(item.function, "_metadata"):
        metadata = item.function._metadata
        samples = getattr(item, "_samples", None)
        session_manager = getattr(item.config, "_session_manager", None)

        # Get the evaluation function signature
        sig = inspect.signature(metadata.eval_fn)
        expected_params = set(sig.parameters.keys())

        # Remove dataset columns from expected params
        columns = {col.strip() for col in metadata.column_spec.split(",")}
        expected_fixture_params = expected_params - columns

        # Get fixture values that the function actually expects
        fixture_kwargs = {}
        if hasattr(item, "funcargs"):
            for param_name in expected_fixture_params:
                if param_name in item.funcargs:
                    fixture_kwargs[param_name] = item.funcargs[param_name]

        result = run_evaluation(
            metadata.eval_fn,
            metadata.column_spec,
            metadata.dataset,
            samples=samples,
            session_manager=session_manager,
            eval_fn_wrapper=item.function,
            **fixture_kwargs,
        )

        item.config._evaluation_results[item.function.__name__] = result
