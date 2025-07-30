import asyncio

import pytest

from doteval.core import foreach, run_evaluation
from doteval.evaluators import evaluator, exact_match
from doteval.metrics import accuracy, metric


@pytest.fixture
def dataset():
    s1 = ("What is the first letter in the alphabet?", "a")
    s2 = ("What is the second letter in the alphabet?", "b")
    return [s1, s2]


@metric
def metric_any():
    def metric(scores: list[bool]) -> float:
        return True in scores

    return metric


def test_foreach_sync_simple(dataset):
    @foreach("question,answer", dataset)
    def eval_dummy(question, answer):
        does_match = exact_match(answer, "a")
        return does_match

    result = eval_dummy()
    assert isinstance(result.summary, dict)
    assert result.summary["exact_match"]["accuracy"] == 0.5


@pytest.mark.asyncio
async def test_foreach_async_simple(dataset):
    @foreach("question,answer", dataset)
    async def eval_dummy(question, answer):
        await asyncio.sleep(0.001)
        does_match = exact_match(answer, "a")
        print(question, answer, does_match)
        return does_match

    result = await eval_dummy()
    assert isinstance(result.summary, dict)
    assert result.summary["exact_match"]["accuracy"] == 0.5


def test_foreach_sync_two_metric(dataset):
    @evaluator(metrics=[accuracy(), metric_any()])
    def dummy_match(answer, target):
        return answer == target

    @foreach("question,answer", dataset)
    def eval_dummy(question, answer):
        does_match = dummy_match(answer, "a")
        return does_match

    result = eval_dummy()
    assert isinstance(result.summary, dict)
    assert result.summary["dummy_match"]["accuracy"] == 0.5
    assert result.summary["dummy_match"]["metric_any"] is True


@pytest.mark.asyncio
async def test_foreach_async_two_metric(dataset):
    @evaluator(metrics=[accuracy(), metric_any()])
    def dummy_match(answer, target):
        return answer == target

    @foreach("question,answer", dataset)
    async def eval_dummy(question, answer):
        await asyncio.sleep(0.001)
        does_match = dummy_match(answer, "a")
        return does_match

    result = await eval_dummy()
    assert isinstance(result.summary, dict)
    assert result.summary["dummy_match"]["accuracy"] == 0.5
    assert result.summary["dummy_match"]["metric_any"] is True


def test_foreach_sync_two_evaluators(dataset):
    @evaluator(metrics=[accuracy()])
    def mismatch(answer, target):
        return answer != target

    @foreach("question,answer", dataset)
    def eval_dummy(question, answer):
        does_match = exact_match(answer, "a")
        does_mismatch = mismatch(answer, "b")
        return does_match, does_mismatch

    result = eval_dummy()
    assert isinstance(result.summary, dict)
    assert result.summary["exact_match"]["accuracy"] == 0.5
    assert result.summary["mismatch"]["accuracy"] == 0.5


@pytest.mark.asyncio
async def test_foreach_async_two_evaluators(dataset):
    @evaluator(metrics=[accuracy()])
    def mismatch(answer, target):
        return answer != target

    @foreach("question,answer", dataset)
    async def eval_dummy(question, answer):
        await asyncio.sleep(0.001)
        does_match = exact_match(answer, "a")
        does_mismatch = mismatch(answer, "b")
        return does_match, does_mismatch

    result = await eval_dummy()
    assert isinstance(result.summary, dict)
    assert result.summary["exact_match"]["accuracy"] == 0.5
    assert result.summary["mismatch"]["accuracy"] == 0.5


@pytest.fixture
def large_dataset():
    """Fixture with larger dataset for testing samples."""
    return [
        ("Question 1", "Answer 1"),
        ("Question 2", "Answer 2"),
        ("Question 3", "Answer 3"),
        ("Question 4", "Answer 4"),
        ("Question 5", "Answer 5"),
    ]


def test_foreach_sync_samples_parameter(large_dataset):
    """Test the samples parameter when calling function directly."""

    @foreach("question,answer", large_dataset)
    def eval_samples(question, answer):
        return exact_match(question, answer)

    # Test without samples limit
    result_all = eval_samples()
    assert len(result_all.results) == 5

    # Test with samples limit
    result_limited = eval_samples(samples=2)
    assert len(result_limited.results) == 2

    # Verify the correct samples were processed
    assert result_limited.results[0].item_data["question"] == "Question 1"
    assert result_limited.results[1].item_data["question"] == "Question 2"


@pytest.mark.asyncio
async def test_foreach_async_samples_parameter(large_dataset):
    """Test the samples parameter when calling function directly."""

    @foreach("question,answer", large_dataset)
    async def eval_samples(question, answer):
        await asyncio.sleep(0.001)
        return exact_match(question, answer)

    # Test without samples limit
    result_all = await eval_samples()
    assert len(result_all.results) == 5

    # Test with samples limit
    result_limited = await eval_samples(samples=2)
    assert len(result_limited.results) == 2

    # Verify the correct samples were processed
    assert result_limited.results[0].item_data["question"] in [
        "Question 1",
        "Question 2",
    ]
    assert result_limited.results[1].item_data["question"] in [
        "Question 1",
        "Question 2",
    ]


def test_foreach_sync_samples_with_additional_kwargs(large_dataset):
    """Test that samples works alongside other kwargs."""

    @foreach("question,answer", large_dataset)
    def eval_with_kwargs(question, answer, extra_param=None):
        # Use the extra parameter in some way
        if extra_param:
            result = f"{question}-{extra_param}"
            expected = f"{question}-test"
        else:
            result = question
            expected = answer
        return exact_match(result, expected)

    # Test with samples and extra kwargs
    result = eval_with_kwargs(samples=2, extra_param="test")
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_foreach_async_samples_with_additional_kwargs(large_dataset):
    """Test that samples works alongside other kwargs."""

    @foreach("question,answer", large_dataset)
    async def eval_with_kwargs(question, answer, extra_param=None):
        # Use the extra parameter in some way
        await asyncio.sleep(0.001)
        if extra_param:
            result = f"{question}-{extra_param}"
            expected = f"{question}-test"
        else:
            result = question
            expected = answer
        return exact_match(result, expected)

    # Test with samples and extra kwargs
    result = await eval_with_kwargs(samples=2, extra_param="test")
    assert len(result.results) == 2


def test_foreach_sync_zero_samples(large_dataset):
    """Test samples=0 behavior."""

    @foreach("question,answer", large_dataset)
    def eval_zero_samples(question, answer):
        return exact_match(question, answer)

    result = eval_zero_samples(samples=0)
    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_foreach_async_zero_samples(large_dataset):
    """Test samples=0 behavior."""

    @foreach("question,answer", large_dataset)
    async def eval_zero_samples(question, answer):
        await asyncio.sleep(0.001)
        return exact_match(question, answer)

    result = await eval_zero_samples(samples=0)
    assert len(result.results) == 0


def test_foreach_sync_samples_larger_than_dataset(large_dataset):
    """Test samples larger than dataset size."""

    @foreach("question,answer", large_dataset)
    def eval_large_samples(question, answer):
        return exact_match(question, answer)

    result = eval_large_samples(samples=10)
    assert len(result.results) == 5  # Should only process available samples


@pytest.mark.asyncio
async def test_foreach_async_samples_larger_than_dataset(large_dataset):
    """Test samples larger than dataset size."""

    @foreach("question,answer", large_dataset)
    async def eval_large_samples(question, answer):
        await asyncio.sleep(0.001)
        return exact_match(question, answer)

    result = await eval_large_samples(samples=10)
    assert len(result.results) == 5  # Should only process available samples


def test_foreach_sync_run_evaluation_samples(large_dataset):
    """Test calling run_evaluation directly with samples parameter."""

    def simple_eval(question, answer):
        return exact_match(question, answer)

    # Test run_evaluation directly
    result = run_evaluation(simple_eval, "question,answer", large_dataset, samples=2)
    assert len(result.results) == 2
    assert result.results[0].item_data["question"] == "Question 1"
    assert result.results[1].item_data["question"] == "Question 2"

    # Test without samples
    result_full = run_evaluation(simple_eval, "question,answer", large_dataset)
    assert len(result_full.results) == 5


def test_foreach_sync_samples_order(large_dataset):
    """Test that samples parameter works consistently across different call methods."""

    @foreach("question,answer", large_dataset)
    def eval_consistency(question, answer):
        return exact_match(question, answer)

    # Test different sample sizes
    for sample_size in [1, 2, 3, 5]:
        result = eval_consistency(samples=sample_size)
        assert len(result.results) == sample_size

        # Verify correct samples were processed (should be first N)
        for i in range(sample_size):
            expected_question = f"Question {i + 1}"
            actual_question = result.results[i].item_data["question"]
            assert actual_question == expected_question


@pytest.mark.asyncio
async def test_foreach_async_samples_order(large_dataset):
    """Test that samples parameter works consistently across different call methods."""

    @foreach("question,answer", large_dataset)
    async def eval_consistency(question, answer):
        await asyncio.sleep(0.001)
        return exact_match(question, answer)

    # Test different sample sizes
    for sample_size in [1, 2, 3, 5]:
        result = await eval_consistency(samples=sample_size)
        assert len(result.results) == sample_size

        # Verify correct samples were processed (should be first N)
        expected_questions = [f"Question {n + 1}" for n in range(sample_size)]
        for i in range(sample_size):
            actual_question = result.results[i].item_data["question"]
            assert actual_question in expected_questions


def test_foreach_sync_empty_dataset():
    """Test behavior with empty dataset."""
    dataset = []

    @foreach("question,answer", dataset)
    def eval_empty(question, answer):
        return exact_match(question, answer)

    result = eval_empty()
    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_foreach_async_empty_dataset():
    """Test behavior with empty dataset."""
    dataset = []

    @foreach("question,answer", dataset)
    async def eval_empty(question, answer):
        await asyncio.sleep(0.001)
        return exact_match(question, answer)

    result = await eval_empty()
    assert len(result.results) == 0


def test_foreach_sync_single_column():
    """Test with a single column dataset."""
    dataset = [("item1",), ("item2",), ("item3",)]

    @foreach("item", dataset)
    def eval_single_column(item):
        return exact_match(item, item)  # Always matches it

    result = eval_single_column()
    assert len(result.results) == 3
    for i, eval_result in enumerate(result.results):
        assert eval_result.item_data["item"] == f"item{i + 1}"


@pytest.mark.asyncio
async def test_foreach_async_single_column():
    """Test with a single column dataset."""
    dataset = [("item1",), ("item2",), ("item3",)]

    @foreach("item", dataset)
    async def eval_single_column(item):
        await asyncio.sleep(0.001)
        return exact_match(item, item)  # Always matches it

    result = await eval_single_column()
    assert len(result.results) == 3
    expected_items = [f"item{i + 1}" for i in range(len(result.results))]
    for i, eval_result in enumerate(result.results):
        assert eval_result.item_data["item"] in expected_items


def test_foreach_sync_many_columns():
    """Test with many columns."""
    dataset = [("a", "b", "c", "d", "e"), ("f", "g", "h", "i", "j")]

    @foreach("col1,col2,col3,col4,col5", dataset)
    def eval_many_columns(col1, col2, col3, col4, col5):
        combined = f"{col1}{col2}{col3}{col4}{col5}"
        return exact_match(combined, combined)  # Always matches

    result = eval_many_columns()
    assert len(result.results) == 2

    # Verify all columns are present
    first_result = result.results[0]
    assert first_result.item_data["col1"] == "a"
    assert first_result.item_data["col5"] == "e"


@pytest.mark.asyncio
async def test_foreach_async_many_columns():
    """Test with many columns."""
    dataset = [("a", "b", "c", "d", "e"), ("f", "g", "h", "i", "j")]

    @foreach("col1,col2,col3,col4,col5", dataset)
    async def eval_many_columns(col1, col2, col3, col4, col5):
        await asyncio.sleep(0.001)
        combined = f"{col1}{col2}{col3}{col4}{col5}"
        return exact_match(combined, combined)  # Always matches

    result = await eval_many_columns()
    assert len(result.results) == 2

    # Verify all columns are present
    first_result = result.results[0]
    assert first_result.item_data["col1"] in ["a", "f"]
    assert first_result.item_data["col5"] in ["e", "j"]
