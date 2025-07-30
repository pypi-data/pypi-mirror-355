"""Dataset management and discovery for doteval."""

from doteval.datasets.base import _registry


def list_available() -> list[str]:
    """List all available datasets that can be used with foreach.dataset_name()"""
    return _registry.list_datasets()


def get_dataset_info(name: str) -> dict:
    """Get information about a specific dataset"""
    dataset_class = _registry.get_dataset_class(name)
    return {
        "name": dataset_class.name,
        "splits": dataset_class.splits,
        "columns": dataset_class.columns,
        "num_rows": getattr(dataset_class, "num_rows", None),
    }


# Import dataset loaders to register them
try:
    from . import gsm8k
except ImportError:
    pass  # Dataset dependencies might not be installed
