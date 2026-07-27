"""Public API for flet-mvc."""

from importlib.metadata import PackageNotFoundError, version

from .component import NO_CHANGE, FletComponent, receive, send
from .datatable import DataTableAdapter
from .hooks import use_datapoint
from .model import (
    Datapoint,
    DatapointBindingError,
    DatapointChange,
    DatapointDependencyError,
    DatapointError,
    DependencyCycleError,
    FletModel,
    UnsupportedControlError,
    computed,
    data,
    register_control_binding,
)

try:
    __version__ = version("flet-mvc")
except PackageNotFoundError:  # pragma: no cover - source tree without metadata
    __version__ = "1.0.0"

__all__ = [
    "NO_CHANGE",
    "DataTableAdapter",
    "Datapoint",
    "DatapointBindingError",
    "DatapointChange",
    "DatapointDependencyError",
    "DatapointError",
    "DependencyCycleError",
    "FletComponent",
    "FletModel",
    "UnsupportedControlError",
    "__version__",
    "computed",
    "data",
    "receive",
    "register_control_binding",
    "send",
    "use_datapoint",
]
