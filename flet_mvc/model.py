"""Reactive domain models with optional, explicit Flet control bindings.

``FletModel`` is also a public :class:`flet.Observable`, so it works directly
with Flet's declarative ``@component`` API. The ``@data`` and ``@computed``
descriptors add a deterministic dependency graph, snapshots, batches, and
imperative bindings for applications that need more than a plain observable.
"""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import logging
import threading
import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Mapping,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import flet as ft

logger = logging.getLogger(__name__)

__all__ = [
    "Datapoint",
    "DatapointBindingError",
    "DatapointChange",
    "DatapointDependencyError",
    "DatapointError",
    "DependencyCycleError",
    "FletModel",
    "UnsupportedControlError",
    "computed",
    "data",
    "register_control_binding",
]


class _Null:
    """Sentinel used for values that have not been initialized."""

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NULL"


NULL = _Null()


class DatapointError(RuntimeError):
    """Base error raised by datapoints."""


class DatapointBindingError(DatapointError):
    """A control could not be bound or synchronized atomically."""


class UnsupportedControlError(DatapointBindingError):
    """No default value attribute is registered for a control."""


class DatapointDependencyError(DatapointError):
    """A declared or inferred dependency is invalid."""


class DependencyCycleError(DatapointDependencyError):
    """A cycle was found in the datapoint dependency graph."""


ExpectedType = Optional[Union[Type[Any], Tuple[Type[Any], ...]]]
ValueT = TypeVar("ValueT")
DecoratedT = TypeVar("DecoratedT")
DataDescriptorT = TypeVar("DataDescriptorT", bound="data[Any]")


@dataclass(frozen=True)
class ControlBindingSpec:
    """Describes the state-bearing attribute of a Flet control."""

    attribute: str
    expected_type: ExpectedType = None
    event: Optional[str] = None


def _spec(
    attribute: str,
    expected_type: ExpectedType = None,
    event: Optional[str] = None,
) -> ControlBindingSpec:
    return ControlBindingSpec(attribute, expected_type, event)


# Keep automatic inference intentionally small. These controls have a clear,
# stable state property. Layout, content and extension controls must opt in
# with ``bind=...`` or ``register_control_binding()`` instead of relying on
# fragile class-name magic.
_CONTROL_BINDINGS: Dict[Type[Any], ControlBindingSpec] = {
    ft.Checkbox: _spec("value", event="on_change"),
    ft.CupertinoCheckbox: _spec("value", event="on_change"),
    ft.CupertinoSlider: _spec("value", event="on_change"),
    ft.CupertinoSwitch: _spec("value", event="on_change"),
    ft.Dropdown: _spec("value", event="on_select"),
    ft.Icon: _spec("icon"),
    ft.IconButton: _spec("icon"),
    ft.Image: _spec("src"),
    ft.Markdown: _spec("value"),
    ft.NavigationBar: _spec("selected_index", event="on_change"),
    ft.NavigationRail: _spec("selected_index", event="on_change"),
    ft.ProgressBar: _spec("value"),
    ft.ProgressRing: _spec("value"),
    ft.RadioGroup: _spec("value", event="on_change"),
    ft.SearchBar: _spec("value", event="on_change"),
    ft.Slider: _spec("value", event="on_change"),
    ft.Switch: _spec("value", event="on_change"),
    ft.Tabs: _spec("selected_index", event="on_change"),
    ft.Text: _spec("value"),
    ft.TextField: _spec("value", event="on_change"),
    ft.TextSpan: _spec("text"),
}


def register_control_binding(
    control_type: Type[Any],
    attribute: str,
    expected_type: ExpectedType = None,
    *,
    event: Optional[str] = None,
) -> None:
    """Register the default attribute used when a datapoint is passed as ``ref``.

    ``control_type`` must be the actual control class. MRO lookup means the
    registration also applies to its subclasses.
    """

    if not isinstance(control_type, type):
        raise TypeError("control_type must be a class")

    if not isinstance(attribute, str):
        raise TypeError("attribute must be a non-empty string")
    if not attribute.strip():
        raise ValueError("attribute must be a non-empty string")

    if expected_type is not None:
        if expected_type is Any or (
            isinstance(expected_type, tuple)
            and any(item is Any for item in expected_type)
        ):
            raise TypeError("expected_type entries must support isinstance()")
        expected_types: Tuple[Type[Any], ...]
        if isinstance(expected_type, type):
            expected_types = (expected_type,)
        elif (
            isinstance(expected_type, tuple)
            and bool(expected_type)
            and all(isinstance(item, type) for item in expected_type)
        ):
            expected_types = expected_type
        else:
            raise TypeError(
                "expected_type must be a type, a non-empty tuple of types, or None"
            )
        try:
            for item in expected_types:
                isinstance(None, item)
        except TypeError as exc:
            raise TypeError("expected_type entries must support isinstance()") from exc

    if event is not None:
        if not isinstance(event, str):
            raise TypeError("event must be a non-empty string or None")
        if not event.strip():
            raise ValueError("event must be a non-empty string or None")

    _CONTROL_BINDINGS[control_type] = ControlBindingSpec(
        attribute,
        expected_type,
        event,
    )


@dataclass(frozen=True)
class DatapointChange:
    """Immutable notification emitted after a datapoint changes."""

    datapoint: "Datapoint[Any]"
    old_value: Any
    new_value: Any
    source: str

    @property
    def model(self) -> "FletModel":
        return self.datapoint.model

    @property
    def name(self) -> str:
        return self.datapoint.name


@dataclass
class _ControlBinding:
    control_ref: Callable[[], Any]
    spec: Optional[ControlBindingSpec]
    original_handler: Optional[Callable[..., Any]] = None
    wrapped_handler: Optional[Callable[..., Any]] = None

    @property
    def control(self) -> Any:
        return self.control_ref()


@dataclass(frozen=True)
class _DatapointCommitState:
    value: Any
    initialized: bool
    dependencies: frozenset["Datapoint[Any]"]
    dependents: frozenset["Datapoint[Any]"]


@dataclass(frozen=True)
class _ControlCommitState:
    control: Any
    attribute: str
    value: Any


@dataclass(frozen=True)
class _GraphCommitSnapshot:
    datapoints: Dict[str, "Datapoint[Any]"]
    states: Dict["Datapoint[Any]", _DatapointCommitState]
    controls: Tuple[_ControlCommitState, ...]
    revision: int


_evaluation_stack: contextvars.ContextVar[Tuple["Datapoint[Any]", ...]] = (
    contextvars.ContextVar("flet_mvc_evaluation_stack", default=())
)
_propagation_resolver: contextvars.ContextVar[
    Optional[Callable[["Datapoint[Any]"], None]]
] = contextvars.ContextVar("flet_mvc_propagation_resolver", default=None)
_OBSERVABLE_RESERVED_NAMES = frozenset(
    {"notify", "subscribe", "_notify", "__version__", "revision"}
)
_CONTROL_EVENT_OWNER_ATTR = "__flet_mvc_datapoint_owner__"


def _safe_equal(left: Any, right: Any) -> bool:
    if left is right:
        return True
    try:
        result = left == right
        if isinstance(result, bool):
            return result
        if hasattr(result, "all"):
            return bool(result.all())
        return bool(result)
    except (TypeError, ValueError):
        return False


def _weak_reference(value: Any) -> Callable[[], Any]:
    try:
        return weakref.ref(value)
    except TypeError:
        # Mostly useful for tiny test doubles. Flet controls support weak refs.
        return lambda: value


def _invoke_event_handler(
    handler: Callable[..., Any],
    args: Tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> Any:
    """Call a Flet handler while preserving zero-argument handler support."""

    try:
        signature = inspect.signature(handler)
    except (TypeError, ValueError):
        return handler(*args, **dict(kwargs))

    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    has_varargs = any(
        parameter.kind == parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )
    if not positional and not has_varargs:
        return handler()
    return handler(*args, **dict(kwargs))


class data(Generic[ValueT]):
    """Declare mutable state owned by one :class:`FletModel` instance.

    Existing syntax remains valid::

        @data
        def title(self):
            return "Hello"

    New code can make an otherwise ambiguous binding explicit::

        @data(bind="value")
        def title(self):
            return "Hello"

    Dependencies are still inferred for backwards compatibility, but new code
    should use :class:`computed` for derived, read-only values.
    """

    def __init__(
        self,
        function: Optional[Callable[..., ValueT]] = None,
        *,
        bind: Optional[str] = None,
        dependencies: Sequence[str] = (),
        computed: bool = False,
    ):
        self.function = function
        self.binding_attribute = bind
        self.declared_dependencies = tuple(dependencies)
        self.computed = computed
        self.name = getattr(function, "__name__", "")
        self.owner: Optional[Type[Any]] = None

    def __call__(
        self,
        function: Callable[..., DecoratedT],
    ) -> "data[DecoratedT]":
        if self.function is not None:
            raise TypeError("A @data definition cannot decorate more than one function")
        if not callable(function):
            raise TypeError("@data must decorate a callable")
        # Configured decorators (for example ``@data(bind="value")``) are
        # created before mypy knows the decorated function's return type.
        # Returning the same runtime descriptor with a fresh type parameter
        # preserves that return type without changing descriptor semantics.
        self.function = cast(Callable[..., ValueT], function)
        self.name = function.__name__
        return cast("data[DecoratedT]", self)

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.owner = owner
        self.name = name

    @overload
    def __get__(
        self,
        instance: None,
        owner: Optional[Type[Any]] = None,
    ) -> "data[ValueT]": ...

    @overload
    def __get__(
        self,
        instance: "FletModel",
        owner: Optional[Type[Any]] = None,
    ) -> "Datapoint[ValueT]": ...

    def __get__(
        self,
        instance: Optional["FletModel"],
        owner: Optional[Type[Any]] = None,
    ) -> Union["data[ValueT]", "Datapoint[ValueT]"]:
        if instance is None:
            return self
        if self.function is None:
            raise DatapointError(f"Datapoint {self.name!r} has no function")
        return instance._get_datapoint(self)

    def __set__(self, instance: "FletModel", value: ValueT) -> None:
        raise AttributeError(
            f"Cannot assign {self.name!r} directly; use {self.name}.set(value)"
        )

    @classmethod
    def depends_on(
        cls: Type[DataDescriptorT],
        *names: str,
        bind: Optional[str] = None,
    ) -> DataDescriptorT:
        """Declare dependencies in addition to automatically inferred ones."""

        if not names or any(not isinstance(name, str) or not name for name in names):
            raise ValueError("depends_on() requires one or more datapoint names")
        return cls(bind=bind, dependencies=names)


class computed(data[ValueT], Generic[ValueT]):
    """Declare read-only state derived from other datapoints.

    Dependencies are inferred from datapoint reads and may additionally be
    declared with ``@computed.depends_on(...)``. Computed values are omitted
    from snapshots because restoring their source state recreates them.
    """

    def __init__(
        self,
        function: Optional[Callable[..., ValueT]] = None,
        *,
        bind: Optional[str] = None,
        dependencies: Sequence[str] = (),
    ):
        super().__init__(
            function,
            bind=bind,
            dependencies=dependencies,
            computed=True,
        )

    def __call__(
        self,
        function: Callable[..., DecoratedT],
    ) -> "computed[DecoratedT]":
        return cast("computed[DecoratedT]", super().__call__(function))

    @overload
    def __get__(
        self,
        instance: None,
        owner: Optional[Type[Any]] = None,
    ) -> "computed[ValueT]": ...

    @overload
    def __get__(
        self,
        instance: "FletModel",
        owner: Optional[Type[Any]] = None,
    ) -> "Datapoint[ValueT]": ...

    def __get__(
        self,
        instance: Optional["FletModel"],
        owner: Optional[Type[Any]] = None,
    ) -> Union["computed[ValueT]", "Datapoint[ValueT]"]:
        return cast(
            Union["computed[ValueT]", "Datapoint[ValueT]"],
            super().__get__(instance, owner),
        )


class Datapoint(ft.Ref[Any], Generic[ValueT]):
    """State and control bindings for one ``data`` definition and one model."""

    def __init__(self, model: "FletModel", definition: data[ValueT]):
        # Deliberately do not call Ref.__init__(): assigning its initial
        # ``current`` value would invoke our binding protocol. Flet only needs
        # the nominal Ref type and later assigns the mounted control through
        # this class's ``current`` setter.
        self.model = model
        self.definition = definition
        self.name = definition.name
        self._value: Any = NULL
        self._initialized = False
        self._evaluating = False
        self._bindings: List[_ControlBinding] = []
        self._subscribers: List[Callable[[DatapointChange], Any]] = []
        self.dependencies: Set["Datapoint[Any]"] = set()
        self.dependents: Set["Datapoint[Any]"] = set()

    # ------------------------------------------------------------------
    # Value lifecycle and dependency evaluation
    # ------------------------------------------------------------------
    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._value = self._evaluate_default()
        self._initialized = True

    def _evaluate_default(self) -> ValueT:
        if self._evaluating:
            cycle_path = " -> ".join(point.name for point in _evaluation_stack.get())
            raise DependencyCycleError(
                f"Dependency cycle while evaluating {self.name!r}: "
                f"{cycle_path} -> {self.name}"
            )

        old_dependencies = set(self.dependencies)
        self.model._clear_dependencies(self)
        self._evaluating = True
        evaluation_stack = _evaluation_stack.get()
        token = _evaluation_stack.set(evaluation_stack + (self,))
        try:
            for dependency_name in self.definition.declared_dependencies:
                descriptor = self.model._definition_for(dependency_name)
                if descriptor is None:
                    raise DatapointDependencyError(
                        f"Datapoint {self.name!r} declares unknown dependency "
                        f"{dependency_name!r}"
                    )
                dependency = self.model._get_datapoint(descriptor)
                self.model._register_dependency(self, dependency)
                dependency._ensure_initialized()
            return self.definition.function(self.model)  # type: ignore[misc]
        except Exception:
            self.model._clear_dependencies(self)
            for dependency in old_dependencies:
                self.model._link_dependency(self, dependency)
            raise
        finally:
            _evaluation_stack.reset(token)
            self._evaluating = False

    def _read(self) -> ValueT:
        stack = _evaluation_stack.get()
        if stack:
            dependent = stack[-1]
            if dependent is self:
                raise DependencyCycleError(f"Datapoint {self.name!r} depends on itself")
            self.model._register_dependency(dependent, self)
            resolver = _propagation_resolver.get()
            if resolver is not None:
                # During a batch, this datapoint may itself be waiting for
                # recomputation. Resolve it before returning its value so a
                # newly discovered dynamic edge cannot read stale state.
                resolver(self)

        self._ensure_initialized()
        return cast(ValueT, self._value)

    @property
    def value(self) -> ValueT:
        """Return the current value and register computed dependencies."""

        return self._read()

    def set(self, value: ValueT) -> None:
        """Set, synchronize and propagate a value atomically."""

        self._require_mutable("set")
        self._ensure_initialized()
        self._assign(value, source="set", propagate=True)

    def reset(self) -> None:
        """Re-evaluate and restore the value declared with ``@data``."""

        self._require_mutable("reset")
        self._ensure_initialized()
        # Mutable defaults may read other datapoints and therefore replace
        # dynamic dependency edges before ``_assign()`` gets a chance to open
        # a commit. Capture the stable graph first so a failing default factory
        # cannot leave those edges half-updated.
        started_commit = self.model._begin_graph_commit()
        try:
            new_value = self._evaluate_default()
            changed = self._assign(new_value, source="reset", propagate=True)
            if started_commit and not changed and self.model._mvc_batch_depth == 0:
                self.model._finish_graph_commit()
        except BaseException:
            if started_commit:
                self.model._rollback_graph_commit()
            raise

    def update(self, transform: Callable[[ValueT], ValueT]) -> ValueT:
        """Replace mutable state with ``transform(current_value)``."""

        self._require_mutable("update")
        if not callable(transform):
            raise TypeError("transform must be callable")
        value = transform(self.value)
        self.set(value)
        return value

    def _require_mutable(self, operation: str) -> None:
        if self.definition.computed:
            raise TypeError(
                f"Computed datapoint {self.name!r} is read-only; cannot {operation} it"
            )

    def _assign(
        self,
        value: ValueT,
        *,
        source: str,
        propagate: bool,
    ) -> bool:
        old_value = self._value
        changed = not _safe_equal(old_value, value)
        if not changed:
            return False

        started_commit = self.model._begin_graph_commit()
        try:
            # Synchronize first. If any control rejects the value, every
            # control is rolled back and the datapoint itself remains
            # unchanged.
            self._synchronize_bindings(value)
            self._value = value
            change = DatapointChange(self, old_value, value, source)
            self.model._queue_change(change, propagate=propagate)
            return True
        except BaseException:
            if started_commit:
                self.model._rollback_graph_commit()
            raise

    def _recompute(self) -> bool:
        new_value = self._evaluate_default()
        return self._assign(
            new_value,
            source="dependency",
            propagate=False,
        )

    # ------------------------------------------------------------------
    # Flet control binding
    # ------------------------------------------------------------------
    @property
    def current(self) -> Any:
        controls = [
            binding.control
            for binding in self._live_bindings()
            if binding.control is not None
        ]
        if not controls:
            return None
        return controls[0]

    @current.setter
    def current(self, control: Any) -> None:
        # This setter is the protocol used by Flet's ``ref=`` InitVar.
        if control is None:
            self.unbind()
        else:
            self.bind(control)

    def __call__(self) -> NoReturn:
        """Reject Flet Ref's callable shorthand, which is ambiguous here.

        A datapoint has two distinct values: domain state in ``.value`` and an
        optionally bound control in ``.current``. Requiring either name keeps
        reads explicit while the instance remains accepted by Flet's ``ref=``.
        """

        raise TypeError(
            "Datapoint is not callable; use '.value' for state or "
            "'.current' for the bound control"
        )

    @property
    def controls(self) -> Tuple[Any, ...]:
        """A stable tuple of all currently live referenced controls."""

        return tuple(
            binding.control
            for binding in self._live_bindings()
            if binding.control is not None
        )

    def bind(self, control: Any, attribute: Optional[str] = None) -> Any:
        """Bind to a control, optionally choosing its state attribute explicitly."""

        if control is None:
            raise DatapointBindingError("Cannot bind a datapoint to None")

        live = self._live_bindings()
        if any(binding.control is control for binding in live):
            return control

        self._ensure_initialized()
        spec = self._resolve_binding(control, attribute)
        self._validate_binding_value(spec, self._value)
        self._require_available_pull_handler(control, spec)

        try:
            previous_value = getattr(control, spec.attribute)
        except Exception as exc:
            raise DatapointBindingError(
                f"Could not read {type(control).__name__}.{spec.attribute} "
                f"before binding {self.name!r}: {exc}"
            ) from exc

        binding = _ControlBinding(_weak_reference(control), spec)
        try:
            setattr(control, spec.attribute, self._value)
            self._install_pull_handler(binding)
        except Exception as exc:
            self._restore_pull_handler(binding)
            try:
                setattr(control, spec.attribute, previous_value)
            except Exception:
                logger.exception(
                    "Failed to roll back %s.%s after binding %s",
                    type(control).__name__,
                    spec.attribute,
                    self.name,
                )
            raise DatapointBindingError(
                f"Could not bind {self.name!r} to "
                f"{type(control).__name__}.{spec.attribute}: {exc}"
            ) from exc

        self._bindings.append(binding)
        return control

    def _require_available_pull_handler(
        self,
        control: Any,
        spec: ControlBindingSpec,
    ) -> None:
        if spec.event is None or not hasattr(control, spec.event):
            return
        handler = getattr(control, spec.event)
        owner = getattr(handler, _CONTROL_EVENT_OWNER_ATTR, None)
        if isinstance(owner, Datapoint):
            raise DatapointBindingError(
                f"{type(control).__name__}.{spec.event} is already managed by "
                f"datapoint {owner.name!r}; cannot also bind datapoint "
                f"{self.name!r} to the same control event"
            )

    def unbind(self, control: Any = None) -> None:
        """Detach one control, or every control when omitted."""

        remaining: List[_ControlBinding] = []
        for binding in self._live_bindings():
            bound_control = binding.control
            should_remove = control is None or bound_control is control
            if should_remove:
                self._restore_pull_handler(binding)
            else:
                remaining.append(binding)
        self._bindings = remaining

    def pull(self, control: Any = None) -> ValueT:
        """Read a bound control attribute back into the model and propagate it."""

        self._require_mutable("pull a control value into")
        self._ensure_initialized()
        bindings = [
            binding
            for binding in self._live_bindings()
            if binding.spec is not None
            and (control is None or binding.control is control)
        ]
        if not bindings:
            return cast(ValueT, self._value)
        binding = bindings[0]
        bound_control = binding.control
        if bound_control is None or binding.spec is None:
            return cast(ValueT, self._value)
        new_value = getattr(bound_control, binding.spec.attribute)
        self._assign(
            new_value,
            source="control",
            propagate=True,
        )
        return cast(ValueT, self._value)

    def sync(self) -> None:
        """Push the current model value to every referenced control."""

        self._ensure_initialized()
        self._synchronize_bindings(self._value)

    def _resolve_binding(
        self,
        control: Any,
        attribute: Optional[str],
    ) -> ControlBindingSpec:
        selected_attribute = (
            attribute if attribute is not None else self.definition.binding_attribute
        )
        if selected_attribute is not None:
            if not hasattr(control, selected_attribute):
                raise UnsupportedControlError(
                    f"{type(control).__name__} has no attribute {selected_attribute!r}"
                )
            event = (
                None
                if self.definition.computed
                else self._infer_event(control, selected_attribute)
            )
            return ControlBindingSpec(selected_attribute, None, event)

        for control_class in type(control).__mro__:
            spec = _CONTROL_BINDINGS.get(control_class)
            if spec is not None:
                if not hasattr(control, spec.attribute):
                    raise UnsupportedControlError(
                        f"Registered binding {control_class.__qualname__}."
                        f"{spec.attribute} is not available in the installed "
                        "Flet version"
                    )
                return (
                    ControlBindingSpec(spec.attribute, spec.expected_type)
                    if self.definition.computed
                    else spec
                )

        raise UnsupportedControlError(
            f"No safe default binding is registered for "
            f"{type(control).__name__}. "
            "Use @data(bind='attribute'), datapoint.bind(control, 'attribute'), "
            "or register_control_binding()."
        )

    @staticmethod
    def _infer_event(control: Any, attribute: str) -> Optional[str]:
        if attribute != "value":
            return None
        if isinstance(control, ft.Dropdown) and hasattr(control, "on_select"):
            return "on_select"
        return "on_change" if hasattr(control, "on_change") else None

    def _validate_binding_value(
        self,
        spec: ControlBindingSpec,
        value: Any,
    ) -> None:
        expected = spec.expected_type
        if expected is not None and not isinstance(value, expected):
            expected_name = (
                expected.__name__
                if isinstance(expected, type)
                else " or ".join(item.__name__ for item in expected)
            )
            raise TypeError(
                f"Datapoint {self.name!r} value has type "
                f"{type(value).__name__}; {spec.attribute!r} expects "
                f"{expected_name}"
            )

    def _synchronize_bindings(self, value: Any) -> None:
        bindings = [
            binding
            for binding in self._live_bindings()
            if binding.spec is not None and binding.control is not None
        ]
        for binding in bindings:
            self._validate_binding_value(binding.spec, value)  # type: ignore[arg-type]

        previous: List[Tuple[Any, str, Any]] = []
        try:
            for binding in bindings:
                control = binding.control
                spec = binding.spec
                if control is None or spec is None:
                    continue
                previous.append(
                    (control, spec.attribute, getattr(control, spec.attribute))
                )
                setattr(control, spec.attribute, value)
        except Exception as exc:
            for old_control, old_attribute, old_value in reversed(previous):
                try:
                    setattr(old_control, old_attribute, old_value)
                except Exception:
                    logger.exception(
                        "Failed to roll back %s.%s",
                        type(old_control).__name__,
                        old_attribute,
                    )
            raise DatapointBindingError(
                f"Could not synchronize datapoint {self.name!r}: {exc}"
            ) from exc

    def _install_pull_handler(self, binding: _ControlBinding) -> None:
        if binding.spec is None or binding.spec.event is None:
            return
        control = binding.control
        if control is None or not hasattr(control, binding.spec.event):
            return

        event_name = binding.spec.event
        original = getattr(control, event_name)
        binding.original_handler = original

        if inspect.iscoroutinefunction(original):

            @wraps(original)
            async def async_handler(*args: Any, **kwargs: Any) -> Any:
                self.pull(control)
                return await _invoke_event_handler(original, args, kwargs)

            wrapped: Callable[..., Any] = async_handler
        else:

            def sync_handler(*args: Any, **kwargs: Any) -> Any:
                self.pull(control)
                if original is None:
                    return None
                return _invoke_event_handler(original, args, kwargs)

            wrapped = sync_handler
            if original is not None:
                wrapped = wraps(original)(wrapped)

        binding.wrapped_handler = wrapped
        setattr(wrapped, _CONTROL_EVENT_OWNER_ATTR, self)
        setattr(control, event_name, wrapped)

    @staticmethod
    def _restore_pull_handler(binding: _ControlBinding) -> None:
        if (
            binding.spec is None
            or binding.spec.event is None
            or binding.control is None
        ):
            return
        control = binding.control
        if getattr(control, binding.spec.event, None) is binding.wrapped_handler:
            setattr(control, binding.spec.event, binding.original_handler)

    def _live_bindings(self) -> List[_ControlBinding]:
        live = [binding for binding in self._bindings if binding.control is not None]
        if len(live) != len(self._bindings):
            self._bindings = live
        return live

    # ------------------------------------------------------------------
    # Observers
    # ------------------------------------------------------------------
    def subscribe(
        self,
        callback: Callable[[DatapointChange], Any],
        *,
        fire_immediately: bool = False,
    ) -> Callable[[], None]:
        """Subscribe to changes and return an idempotent unsubscribe callback."""

        if not callable(callback):
            raise TypeError("callback must be callable")
        # Computed datapoints need to establish their graph edges before an
        # upstream value can publish a change to this subscriber.
        self._ensure_initialized()
        if callback not in self._subscribers:
            self._subscribers.append(callback)
        if fire_immediately:
            current_value = self._value
            self._dispatch_callback(
                callback,
                DatapointChange(
                    self,
                    NULL,
                    current_value,
                    "subscribe",
                ),
            )

        active = True

        def unsubscribe() -> None:
            nonlocal active
            if not active:
                return
            active = False
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return unsubscribe

    def _notify(self, change: DatapointChange) -> None:
        for callback in tuple(self._subscribers):
            self._dispatch_callback(callback, change)

    @staticmethod
    def _dispatch_callback(
        callback: Callable[[DatapointChange], Any],
        change: DatapointChange,
    ) -> None:
        try:
            result = callback(change)
            if not inspect.isawaitable(result):
                return
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:

                async def run_subscriber() -> Any:
                    return await result

                asyncio.run(run_subscriber())
            else:

                async def run_subscriber() -> Any:
                    return await result

                task = loop.create_task(run_subscriber())
                change.model._track_subscriber_task(task, change)
        except Exception:
            logger.exception(
                "Subscriber failed for datapoint %s",
                change.name,
            )

    def __set__(self, instance: Any, value: Any) -> None:
        raise AttributeError("Use datapoint.set(value)")

    def __repr__(self) -> str:
        value = self._value if self._initialized else NULL
        kind = "computed" if self.definition.computed else "data"
        return f"<Datapoint name={self.name!r} kind={kind!r} value={value!r}>"


class FletModel(ft.Observable):
    """Observable model with isolated datapoints and a dependency graph.

    Passing an instance to a Flet ``@component`` (or storing it with
    ``ft.use_state``/``ft.use_context``) automatically re-renders that
    component after the dependency graph reaches a stable state.
    """

    _mvc_datapoints: Dict[str, Datapoint[Any]]
    _mvc_lock: Any
    _mvc_batch_depth: int
    _mvc_pending_sources: Set[Datapoint[Any]]
    _mvc_pending_changes: List[DatapointChange]
    _mvc_flushing_changes: bool
    _mvc_subscriber_tasks: Set[asyncio.Task[Any]]
    _mvc_revision: int
    _mvc_commit_snapshot: Optional[_GraphCommitSnapshot]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        collisions = _OBSERVABLE_RESERVED_NAMES.intersection(cls.__dict__)
        if collisions:
            joined = ", ".join(sorted(collisions))
            raise TypeError(
                f"FletModel subclasses cannot override Observable API names: {joined}"
            )

        datapoint_definitions = {
            name: definition
            for name, definition in cls.__dict__.items()
            if isinstance(definition, data)
        }
        internal_names = sorted(
            name for name in datapoint_definitions if name.startswith("_mvc_")
        )
        if internal_names:
            raise TypeError(
                "Datapoint names cannot use the reserved '_mvc_' prefix: "
                + ", ".join(internal_names)
            )

        api_collisions: list[str] = []
        for name in datapoint_definitions:
            for base in cls.__mro__[1:]:
                if name not in vars(base):
                    continue
                if not isinstance(vars(base)[name], data):
                    api_collisions.append(f"{name} ({base.__qualname__}.{name})")
                break
        if api_collisions:
            raise TypeError(
                "Datapoint definitions cannot override inherited model API members: "
                + ", ".join(sorted(api_collisions))
            )

    def __init__(self, **initial_values: Any):
        self._ensure_runtime()
        definitions = self._definitions()
        unknown = set(initial_values).difference(definitions)
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise TypeError(f"Unknown datapoint initial value(s): {joined}")
        read_only = {name for name in initial_values if definitions[name].computed}
        if read_only:
            joined = ", ".join(sorted(read_only))
            raise TypeError(
                f"Computed datapoint initial value(s) are read-only: {joined}"
            )
        for definition in definitions.values():
            self._get_datapoint(definition)._ensure_initialized()
        with self.batch():
            for name, value in initial_values.items():
                point = self._get_datapoint(definitions[name])
                point._ensure_initialized()
                point._assign(
                    value,
                    source="initial",
                    propagate=True,
                )

    def _ensure_runtime(self) -> None:
        namespace = object.__getattribute__(self, "__dict__")
        if "_mvc_datapoints" in namespace:
            return
        namespace["_mvc_datapoints"] = {}
        namespace["_mvc_lock"] = threading.RLock()
        namespace["_mvc_batch_depth"] = 0
        namespace["_mvc_pending_sources"] = set()
        namespace["_mvc_pending_changes"] = []
        namespace["_mvc_flushing_changes"] = False
        namespace["_mvc_subscriber_tasks"] = set()
        namespace["_mvc_revision"] = 0
        namespace["_mvc_commit_snapshot"] = None

    @property
    def revision(self) -> int:
        """Number of successful datapoint commits published by this model."""

        self._ensure_runtime()
        return self._mvc_revision

    @classmethod
    def _definitions(cls) -> Dict[str, data[Any]]:
        definitions: Dict[str, data[Any]] = {}
        for model_class in reversed(cls.__mro__):
            for name, value in vars(model_class).items():
                if isinstance(value, data):
                    definitions[name] = value
                elif name in definitions:
                    # Normal Python lookup allows a subclass to replace an
                    # inherited descriptor with any other attribute. Do not
                    # retain a hidden datapoint that is no longer reachable.
                    definitions.pop(name)
        return definitions

    def _definition_for(self, name: str) -> Optional[data[Any]]:
        return self._definitions().get(name)

    def _get_datapoint(
        self,
        definition: data[ValueT],
    ) -> Datapoint[ValueT]:
        self._ensure_runtime()
        with self._mvc_lock:
            point = self._mvc_datapoints.get(definition.name)
            if point is None:
                point = Datapoint(self, definition)
                self._mvc_datapoints[definition.name] = point
            return cast(Datapoint[ValueT], point)

    @property
    def datapoints(self) -> Mapping[str, Datapoint[Any]]:
        """All definitions as bound datapoints, in declaration order."""

        for definition in self._definitions().values():
            self._get_datapoint(definition)._ensure_initialized()
        return dict(self._mvc_datapoints)

    def reset_all(self) -> None:
        with self.batch():
            for point in self.datapoints.values():
                if not point.definition.computed:
                    point.reset()

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow snapshot of mutable state."""

        return {
            name: point.value
            for name, point in self.datapoints.items()
            if not point.definition.computed
        }

    def restore(
        self,
        values: Mapping[str, Any],
        *,
        strict: bool = True,
    ) -> None:
        definitions = self._definitions()
        unknown = set(values).difference(definitions)
        if strict and unknown:
            raise KeyError(f"Unknown datapoints: {', '.join(sorted(unknown))}")
        read_only = {
            name
            for name in values
            if name in definitions and definitions[name].computed
        }
        if strict and read_only:
            raise TypeError(
                "Computed datapoints cannot be restored: "
                + ", ".join(sorted(read_only))
            )
        with self.batch():
            for name, value in values.items():
                if name in definitions and not definitions[name].computed:
                    self._get_datapoint(definitions[name]).set(value)

    @contextmanager
    def batch(self) -> Iterator["FletModel"]:
        """Batch changes so each computed datapoint is recomputed only once."""

        self._ensure_runtime()
        with self._mvc_lock:
            if self._mvc_batch_depth == 0:
                self._begin_graph_commit()
            self._mvc_batch_depth += 1
        try:
            yield self
        except BaseException:
            rollback = False
            with self._mvc_lock:
                self._mvc_batch_depth -= 1
                rollback = self._mvc_batch_depth == 0
            if rollback:
                self._rollback_graph_commit()
            raise
        else:
            should_flush = False
            finished_batch = False
            with self._mvc_lock:
                self._mvc_batch_depth -= 1
                finished_batch = self._mvc_batch_depth == 0
                if finished_batch:
                    should_flush = bool(
                        self._mvc_pending_sources or self._mvc_pending_changes
                    )
            if should_flush:
                self._flush_changes()
            elif finished_batch:
                self._finish_graph_commit()

    def _queue_change(
        self,
        change: DatapointChange,
        *,
        propagate: bool,
    ) -> None:
        """Queue a change and publish it only after its graph is consistent."""

        should_flush = False
        with self._mvc_lock:
            self._mvc_pending_changes.append(change)
            if propagate:
                self._mvc_pending_sources.add(change.datapoint)
            should_flush = not self._mvc_batch_depth and not self._mvc_flushing_changes
        if should_flush:
            self._flush_changes()

    def _flush_changes(self) -> None:
        """Propagate queued sources and publish one native observable update."""

        with self._mvc_lock:
            if self._mvc_batch_depth or self._mvc_flushing_changes:
                return
            self._mvc_flushing_changes = True

        published_changes = False
        try:
            while True:
                with self._mvc_lock:
                    sources = set(self._mvc_pending_sources)
                    self._mvc_pending_sources.clear()

                if sources:
                    self._propagate_from(sources)

                with self._mvc_lock:
                    # A computed default may itself publish another source.
                    # Stabilize that graph before exposing any queued change.
                    if self._mvc_pending_sources:
                        continue
                    changes = list(self._mvc_pending_changes)
                    self._mvc_pending_changes.clear()

                for change in changes:
                    change.datapoint._notify(change)
                published_changes = published_changes or bool(changes)

                with self._mvc_lock:
                    if not (self._mvc_pending_sources or self._mvc_pending_changes):
                        self._mvc_flushing_changes = False
                        break
            if published_changes:
                namespace = object.__getattribute__(self, "__dict__")
                namespace["_mvc_revision"] += 1
                self._finish_graph_commit()
                self.notify()
            else:
                self._finish_graph_commit()
        except BaseException:
            self._rollback_graph_commit()
            raise

    def _begin_graph_commit(self) -> bool:
        """Capture the last stable graph before the first commit mutation."""

        self._ensure_runtime()
        with self._mvc_lock:
            if self._mvc_commit_snapshot is not None:
                return False

            datapoints = dict(self._mvc_datapoints)
            states = {
                point: _DatapointCommitState(
                    value=point._value,
                    initialized=point._initialized,
                    dependencies=frozenset(point.dependencies),
                    dependents=frozenset(point.dependents),
                )
                for point in datapoints.values()
            }
            controls: List[_ControlCommitState] = []
            seen_controls: Set[Tuple[int, str]] = set()
            for point in datapoints.values():
                for binding in point._live_bindings():
                    control = binding.control
                    spec = binding.spec
                    if control is None or spec is None:
                        continue
                    identity = (id(control), spec.attribute)
                    if identity in seen_controls:
                        continue
                    seen_controls.add(identity)
                    controls.append(
                        _ControlCommitState(
                            control=control,
                            attribute=spec.attribute,
                            value=getattr(control, spec.attribute),
                        )
                    )

            self._mvc_commit_snapshot = _GraphCommitSnapshot(
                datapoints=datapoints,
                states=states,
                controls=tuple(controls),
                revision=self._mvc_revision,
            )
            return True

    def _finish_graph_commit(self) -> None:
        with self._mvc_lock:
            self._mvc_commit_snapshot = None

    def _rollback_graph_commit(self) -> None:
        """Restore values, controls and edges captured before a failed commit."""

        with self._mvc_lock:
            snapshot = self._mvc_commit_snapshot
            self._mvc_commit_snapshot = None
            self._mvc_pending_sources.clear()
            self._mvc_pending_changes.clear()
            self._mvc_flushing_changes = False
            if snapshot is None:
                return

            current_points = set(self._mvc_datapoints.values())
            snapshot_points = set(snapshot.states)
            for point in current_points | snapshot_points:
                point.dependencies.clear()
                point.dependents.clear()

            namespace = object.__getattribute__(self, "__dict__")
            namespace["_mvc_datapoints"] = dict(snapshot.datapoints)
            namespace["_mvc_revision"] = snapshot.revision
            for point, state in snapshot.states.items():
                point._value = state.value
                point._initialized = state.initialized
                point._evaluating = False
                point.dependencies.update(state.dependencies)
                point.dependents.update(state.dependents)

            for control_state in snapshot.controls:
                try:
                    setattr(
                        control_state.control,
                        control_state.attribute,
                        control_state.value,
                    )
                except Exception:
                    logger.exception(
                        "Failed to roll back %s.%s",
                        type(control_state.control).__name__,
                        control_state.attribute,
                    )

    def _track_subscriber_task(
        self,
        task: asyncio.Task[Any],
        change: DatapointChange,
    ) -> None:
        """Retain an async subscriber and always consume its final exception."""

        with self._mvc_lock:
            self._mvc_subscriber_tasks.add(task)

        def completed(completed_task: asyncio.Task[Any]) -> None:
            with self._mvc_lock:
                self._mvc_subscriber_tasks.discard(completed_task)
            if completed_task.cancelled():
                return
            exception = completed_task.exception()
            if exception is not None:
                logger.error(
                    "Subscriber failed for datapoint %s",
                    change.name,
                    exc_info=(
                        type(exception),
                        exception,
                        exception.__traceback__,
                    ),
                )

        task.add_done_callback(completed)

    def _propagate_from(self, sources: Set[Datapoint[Any]]) -> None:
        with self._mvc_lock:
            affected: Set[Datapoint[Any]] = set()
            queue = list(sources)
            while queue:
                current = queue.pop(0)
                for dependent in tuple(current.dependents):
                    if dependent in sources or dependent in affected:
                        continue
                    affected.add(dependent)
                    queue.append(dependent)

            order = {name: index for index, name in enumerate(self._definitions())}
            remaining = set(affected)
            visiting: Set[Datapoint[Any]] = set()

            def recompute(point: Datapoint[Any]) -> None:
                if point not in remaining:
                    return
                if point in visiting:
                    names = " -> ".join(item.name for item in (*visiting, point))
                    raise DependencyCycleError(
                        f"Dependency cycle prevents propagation: {names}"
                    )

                visiting.add(point)
                try:
                    dependencies = sorted(
                        point.dependencies & remaining,
                        key=lambda dependency: (
                            order.get(dependency.name, 10**9),
                            dependency.name,
                        ),
                    )
                    for dependency in dependencies:
                        recompute(dependency)

                    # A dependency discovered while _recompute() evaluates a
                    # dynamic branch is resolved by Datapoint._read() through
                    # this same callback, before its value is returned.
                    point._recompute()
                    remaining.remove(point)
                finally:
                    visiting.discard(point)

            token = _propagation_resolver.set(recompute)
            try:
                for point in sorted(
                    affected,
                    key=lambda item: (order.get(item.name, 10**9), item.name),
                ):
                    recompute(point)
            finally:
                _propagation_resolver.reset(token)

    def _register_dependency(
        self,
        dependent: Datapoint[Any],
        dependency: Datapoint[Any],
    ) -> None:
        if dependent.model is not self or dependency.model is not self:
            raise DatapointDependencyError(
                "Datapoints from different model instances cannot be linked"
            )
        if dependent is dependency:
            raise DependencyCycleError(
                f"Datapoint {dependent.name!r} depends on itself"
            )
        path = self._dependency_path(dependency, dependent)
        if path is not None:
            cycle = [dependent.name] + [point.name for point in path]
            raise DependencyCycleError(
                "Dependency cycle detected: " + " -> ".join(cycle)
            )
        self._link_dependency(dependent, dependency)

    @staticmethod
    def _link_dependency(
        dependent: Datapoint[Any],
        dependency: Datapoint[Any],
    ) -> None:
        dependent.dependencies.add(dependency)
        dependency.dependents.add(dependent)

    @staticmethod
    def _dependency_path(
        start: Datapoint[Any],
        target: Datapoint[Any],
    ) -> Optional[List[Datapoint[Any]]]:
        stack: List[Tuple[Datapoint[Any], List[Datapoint[Any]]]] = [(start, [start])]
        visited: Set[Datapoint[Any]] = set()
        while stack:
            point, path = stack.pop()
            if point is target:
                return path
            if point in visited:
                continue
            visited.add(point)
            stack.extend(
                (dependency, path + [dependency]) for dependency in point.dependencies
            )
        return None

    @staticmethod
    def _clear_dependencies(point: Datapoint[Any]) -> None:
        for dependency in tuple(point.dependencies):
            dependency.dependents.discard(point)
        point.dependencies.clear()

    @property
    def dependency_graph(self) -> Mapping[str, Tuple[str, ...]]:
        """Map each datapoint to the names it depends on."""

        _ = self.datapoints
        return {
            name: tuple(sorted(dependency.name for dependency in point.dependencies))
            for name, point in self._mvc_datapoints.items()
        }

    def dependency_dot(self) -> str:
        """Render the dependency graph as Graphviz DOT."""

        graph = self.dependency_graph
        lines = ["digraph flet_mvc {"]
        for name in graph:
            lines.append(f'  "{name}";')
        for dependent, dependencies in graph.items():
            for dependency in dependencies:
                lines.append(f'  "{dependency}" -> "{dependent}";')
        lines.append("}")
        return "\n".join(lines)
