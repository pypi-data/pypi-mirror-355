import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from doteval.metrics import Metric


@dataclass
class Score:
    name: str
    value: Any
    metrics: list[Metric]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Results of a single evaluation step"""

    scores: list[Score]
    item_id: int
    item_data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class EvaluationSummary:
    """Aggregated results of a full evaluation"""

    def __init__(self, results: list[EvaluationResult]):
        self.results = results
        self.summary = self.compute_summary()

    def compute_summary(self):
        summary = defaultdict(dict)

        # Regorganize the results by evaluator and metric
        # TODO: Will break if the test function uses the same evaluator twice
        aggregated_results = defaultdict(lambda: defaultdict(list))
        for results in self.results:
            for score in results.scores:
                for metric in score.metrics:
                    aggregated_results[score.name][metric].append(score.value)

        for evaluator_name, metrics_values in aggregated_results.items():
            for metrics, values in metrics_values.items():
                summary[evaluator_name][metrics.__name__] = metrics(values)

        return summary
