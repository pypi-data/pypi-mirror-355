# doteval

LLM evaluation library that works like pytest.

## Overview

doteval lets you write LLM evaluations as pytest test functions. It handles progress tracking, resumption after crashes, and result storage automatically.

```python
from doteval import foreach
from doteval.evaluators import exact_match

@foreach("question,answer", dataset)
def eval_math_questions(question, answer, model):
    response = model.generate(question)
    return exact_match(response, answer)
```

`pytest` will collect all `eval_` functions in `eval_*.py` files and run them as an evaluation:

```bash
pytest eval_math_questions.py --session my_evaluation
```

## Installation

```bash
pip install doteval
```

## Basic Usage

### 1. Write an evaluation function

```python
# eval_sentiment.py
import pytest
from doteval import foreach
from doteval.evaluators import exact_match

@pytest.fixture
def model():
    return load_your_model()

data = [
    ("I love this!", "positive"),
    ("This is terrible", "negative"),
    ("It's okay", "neutral")
]

@foreach("text,label", data)
def eval_sentiment(text, label, model):
    prediction = model.classify(text)
    return exact_match(prediction, label)
```

### 2. Run the evaluation

```bash
pytest eval_sentiment.py --session sentiment_test
```

### 3. View results

```bash
doteval show sentiment_test
```

## Key Features

- **Automatic resumption**: Crashed evaluations continue where they left off
- **Session management**: Named experiments with persistent storage
- **pytest integration**: Use all pytest features (fixtures, parametrization, etc.)
- **Async support**: Built-in concurrency control for large-scale evaluations

## Examples

### Math Reasoning

```python
from datasets import load_dataset
from doteval import foreach
from doteval.evaluators import exact_match

def gsm8k_dataset():
    dataset = load_dataset("gsm8k", "main", split="test", streaming=True)
    for item in dataset:
        yield (item["question"], extract_answer(item["answer"]))

@foreach("question,answer", gsm8k_dataset())
def eval_math_reasoning(question, answer, model):
    response = model.solve(question)
    return exact_match(extract_number(response), answer)
```

### Async Evaluation

```python
@foreach("text,label", large_dataset)
async def eval_classification(text, label, async_model):
    prediction = await async_model.classify(text)
    return exact_match(prediction, label)
```

```bash
pytest eval_classification.py --session async_eval --max-concurrency 10
```

### Custom Evaluators

```python
from doteval.evaluators import evaluator

@evaluator
def semantic_similarity(response: str, expected: str) -> bool:
    embedding1 = get_embedding(response)
    embedding2 = get_embedding(expected)
    return cosine_similarity(embedding1, embedding2) > 0.8

@foreach("question,answer", dataset)
def eval_qa(question, answer, model):
    response = model.generate(question)
    return semantic_similarity(response, answer)
```

## CLI Commands

```bash
# List all evaluation sessions
doteval list

# Show results for a specific session
doteval show session_name

# Delete a session
doteval delete session_name

# Run with limited samples for testing
pytest eval_test.py --session eval_run --samples 10
```

## Session Management

Sessions automatically track:
- Evaluation progress and completion status
- Individual sample results and errors
- Timing and performance metrics
- Resumption state for interrupted runs

```bash
# Start named session
pytest eval_math.py --session math_baseline

# Resume if interrupted
pytest eval_math.py --session math_baseline  # Continues from last completed sample

# Use different storage backend
pytest eval_math.py --session math_baseline --storage sqlite://results.db
```

## Storage Backends

doteval supports multiple storage backends and allows you to implement custom ones:

```python
# Built-in backends
from doteval.sessions import SessionManager

# JSON storage (default)
manager = SessionManager(storage_path="json://evals")

# SQLite storage with query capabilities
manager = SessionManager(storage_path="sqlite://evaluations.db")

# Custom backend
from doteval.storage import Storage, register

class MyStorage(Storage):
    # Implement abstract methods...
    pass

register("mybackend", MyStorage)
manager = SessionManager(storage_path="mybackend://config")
```
