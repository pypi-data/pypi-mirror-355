from doteval.metrics import accuracy
from doteval.models import EvaluationResult, EvaluationSummary, Score


def test_summary_empty_results():
    results = []
    summary = EvaluationSummary(results)
    assert isinstance(summary.summary, dict)
    assert len(summary.summary) == 0


def test_summary_simple():
    results = [
        EvaluationResult([Score("match", True, [accuracy()])], 1),
        EvaluationResult([Score("match", True, [accuracy()])], 2),
    ]
    summary = EvaluationSummary(results)
    assert isinstance(summary.summary, dict)
    assert summary.summary == {"match": {"accuracy": 1.0}}


def test_summary_two_scores_result():
    results = [
        EvaluationResult(
            [
                Score("match_1", True, [accuracy()]),
                Score("match_2", False, [accuracy()]),
            ],
            1,
        ),
        EvaluationResult(
            [
                Score("match_1", True, [accuracy()]),
                Score("match_2", False, [accuracy()]),
            ],
            2,
        ),
    ]
    summary = EvaluationSummary(results)
    assert isinstance(summary.summary, dict)
    assert summary.summary == {
        "match_1": {"accuracy": 1.0},
        "match_2": {"accuracy": 0.0},
    }
