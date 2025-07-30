import asyncio
import functools
import itertools
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

from doteval.datasets.base import _registry
from doteval.models import EvaluationResult, EvaluationSummary, Score
from doteval.progress import EvaluationProgress, get_dataset_info
from doteval.sessions import SessionManager


@dataclass
class EvaluationMetadata:
    """Consolidated metadata for evaluation functions"""

    column_spec: str
    dataset: Iterator
    eval_fn: Callable
    loader: Optional[object] = None
    dataset_name: Optional[str] = None


class ForEach:
    def __call__(self, column_spec: str, dataset: Iterator):
        def core_foreach(column_spec: str, dataset: Iterator):
            """
            Decorator that marks a function for running against each item in a dataset.

            When used with `pytest`, the decorated function will be automatically
            executed against all dataset items as part of the evaluation suite.
            Functions decorated by `foreach` can also be executed as normal Python
            functions.

            Args:
                column_spec: Comma-separated list of column names
                dataset: An iterator of tuples or lists, each representing a row of data

            Returns:
                A decorated function that can be used as a regular function or as a `pytest` test

            """

            def decorator(eval_fn: Callable) -> Callable:
                @functools.wraps(eval_fn)
                def wrapper(*args, **kwargs):
                    return run_evaluation(
                        eval_fn, column_spec, dataset, eval_fn_wrapper=wrapper, **kwargs
                    )

                # Store consolidated metadata
                wrapper._metadata = EvaluationMetadata(  # type: ignore
                    column_spec=column_spec, dataset=dataset, eval_fn=eval_fn
                )

                return wrapper

            return decorator

        return core_foreach(column_spec, dataset)

    def __getattr__(self, dataset_name: str):
        def dataset_foreach(split: str = "test", **kwargs):
            dataset_class = _registry.get_dataset_class(dataset_name)
            dataset_instance = dataset_class(split, **kwargs)
            column_spec = ",".join(dataset_class.columns)

            # Create the decorator
            def decorator(eval_fn: Callable):
                @functools.wraps(eval_fn)
                def wrapper(*args, **kwargs):
                    return run_evaluation(
                        eval_fn,
                        column_spec,
                        dataset_instance,
                        eval_fn_wrapper=wrapper,
                        **kwargs,
                    )

                # Store consolidated metadata
                wrapper._metadata = EvaluationMetadata(  # type: ignore
                    column_spec=column_spec,
                    dataset=dataset_instance,  # type: ignore
                    eval_fn=eval_fn,
                    loader=dataset_instance,
                    dataset_name=dataset_name,
                )

                return wrapper

            # Add metadata for introspection
            decorator._dataset_name = dataset_name  # type: ignore
            decorator._split = split  # type: ignore
            return decorator

        return dataset_foreach


foreach = ForEach()


def run_evaluation(
    eval_fn: Callable,
    column_spec: str,
    dataset: Iterator,
    max_concurrency: int = 10,
    samples: Optional[int] = None,
    session_manager: Optional[SessionManager] = None,
    eval_fn_wrapper: Optional[Callable] = None,
    **kwargs,
) -> EvaluationSummary:
    """
    Run an evaluation function against each item in a dataset.

    Args:
        eval_fn: The function to run for each dataset item
        column_spec: Comma-separated list of column names
        dataset: An iterator of tuples or lists, each representing a row of data
        max_concurrency: The maximum number of concurrent requests
        samples: Maximum number of dataset samples to evaluate (None for all)
        session_manager: The current session's session manager
        **kwargs: Additional arguments to pass to the evaluation function

    Returns:
        An EvaluationSummary containing all results

    """
    columns = [col.strip() for col in column_spec.split(",")]
    test_name = eval_fn.__name__

    # Get dataset info for progress tracking
    dataset_info = (
        get_dataset_info(dataset, eval_fn_wrapper)
        if eval_fn_wrapper
        else {"name": "Dataset", "total_rows": None}
    )

    # Adjust total count if samples parameter is specified
    if samples is not None and dataset_info.get("total_rows") is not None:
        dataset_info["total_rows"] = min(samples, dataset_info["total_rows"])

    completed_ids: set[int] = set()
    if session_manager:
        completed_ids = session_manager.get_completed_item_ids(test_name)
        if len(completed_ids) > 0:
            print(
                f"📄 {test_name}: Resuming from {len(completed_ids)} completed samples"
            )

    dataset = itertools.islice(dataset, None, samples)
    dataset = (
        (item_id, row_data)
        for item_id, row_data in enumerate(dataset)
        if item_id not in completed_ids
    )

    if asyncio.iscoroutinefunction(eval_fn):
        return _run_evaluation_async(
            test_name,
            eval_fn,
            columns,
            dataset,
            max_concurrency,
            session_manager,
            samples,
            dataset_info,
        )
    else:
        return _run_evaluation_sync(
            test_name,
            eval_fn,
            columns,
            dataset,
            session_manager,
            samples,
            dataset_info,
            **kwargs,
        )


def _run_evaluation_sync(
    test_name,
    eval_fn,
    columns,
    dataset,
    session_manager,
    samples,
    dataset_info,
    **kwargs,
):
    """
    Run the evaluation when `eval_fn` is a Python function, against
    each item in the dataset.

    Args:
        eval_fn: The function to run for each dataset item
        column_spec: List of column names
        dataset: An iterator of tuples or lists, each representing a row of data
        session_manager: The current session's session manager
        **kwargs: Additional arguments to pass to the evaluation function

    Returns:
        An EvaluationSummary containing all results

    """
    new_results: list[EvaluationResult] = []

    success = True
    with EvaluationProgress(test_name, dataset_info) as progress:
        for item_id, row_data in dataset:
            row_dict = {col: data for col, data in zip(columns, row_data)}

            try:
                scores = eval_fn(**row_dict, **kwargs)

                if not isinstance(scores, tuple) and not isinstance(scores, list):
                    scores = (scores,)

                processed_scores = []
                for score in scores:
                    if isinstance(score, Score):
                        processed_scores.append(score)
                    else:
                        raise ValueError(
                            "Evaluation functions must only return `Score` objects, which are returned by evaluators."
                        )

                result = EvaluationResult(processed_scores, item_id, row_dict)
            except Exception as e:
                success = False
                result = EvaluationResult([], item_id, row_dict, str(e))

            new_results.append(result)
            progress.update_progress(result)
            if session_manager:
                session_manager.add_results(test_name, [result])

    results = session_manager.get_results(test_name) if session_manager else new_results
    if session_manager:
        # Only finish the session if we processed the full dataset (not limited by samples)
        if samples is None:
            session_manager.finish(success)
        # If samples was specified, leave session running for potential resumption

    return EvaluationSummary(results)


async def _run_evaluation_async(
    test_name,
    eval_fn,
    columns,
    dataset,
    max_concurrency,
    session_manager,
    samples,
    dataset_info,
    **kwargs,
):
    """
    Run the evaluation when `eval_fn` is a coroutine, against each item in the
    dataset.

    Args:
        eval_fn: The function to run for each dataset item
        column_spec: List of column names
        dataset: An iterator of tuples or lists, each representing a row of data
        max_concurrency: The maximum number of concurrent requests
        session_manager: The current session's session manager
        **kwargs: Additional arguments to pass to the evaluation function

    Returns:
        An EvaluationSummary containing all results

    """

    async def process_item(item_id, row_data):
        row_dict = {col: data for col, data in zip(columns, row_data)}

        success = True
        try:
            scores = await eval_fn(**row_dict, **kwargs)

            if not isinstance(scores, tuple) and not isinstance(scores, list):
                scores = (scores,)

            processed_scores = []
            for score in scores:
                if isinstance(score, Score):
                    processed_scores.append(score)
                else:
                    raise ValueError(
                        "Evaluation functions must only return `Score` objects, which are returned by evaluators."
                    )

            result = EvaluationResult(processed_scores, item_id, row_dict)

        except Exception as e:
            success = False
            result = EvaluationResult([], item_id, row_dict, str(e))

        if session_manager:
            session_manager.add_results(test_name, [result])

        return success, result

    # To keep processing `max_concurrency` items at all times we use a sliding window
    results = []
    pending_tasks = set()

    success = True
    with EvaluationProgress(
        test_name, dataset_info, show_individual_tasks=True
    ) as progress:
        try:
            # FIll the initial window to `max_concurrency`
            for _ in range(max_concurrency):
                try:
                    item_id, row_data = next(dataset)
                    task = asyncio.create_task(process_item(item_id, row_data))
                    pending_tasks.add(task)
                except StopIteration:
                    break

            while pending_tasks:
                done, pending_tasks = await asyncio.wait(
                    pending_tasks, return_when=asyncio.FIRST_COMPLETED
                )

                for task in done:
                    success_iter, result = await task
                    if success_iter is False:
                        success = False
                    results.append(result)
                    progress.update_progress(result)

                for _ in range(len(done)):
                    try:
                        item_id, row_data = next(dataset)
                        task = asyncio.create_task(process_item(item_id, row_data))
                        pending_tasks.add(task)
                    except StopIteration:
                        break

        except Exception:
            # Cancel remaining tasks on error
            success = False
            for task in pending_tasks:
                task.cancel()
            raise

    results = session_manager.get_results(test_name) if session_manager else results
    if session_manager:
        # Only finish the session if we processed the full dataset (not limited by samples)
        if samples is None:
            session_manager.finish(success)
        # If samples was specified, leave session running for potential resumption

    return EvaluationSummary(results)
