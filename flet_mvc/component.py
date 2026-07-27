"""Reactive, composite controls for Flet MVC applications.

Flet removed the old ``UserControl`` abstraction in favour of subclassing an
existing control.  :class:`FletComponent` follows that model: it is a real
``ft.Column`` decorated with ``@ft.control`` and can therefore be composed,
styled, and updated like any other Flet control.

The :func:`send` and :func:`receive` decorators provide a deliberately small
bridge between a component and a model datapoint:

* ``send`` publishes the decorated method's return value.
* ``receive`` subscribes on mount and passes ``change.new_value`` to the
  decorated method.

Both decorators support synchronous and asynchronous methods.  Subscriptions
and background work are released when the component is unmounted.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Final, Generic, Protocol, TypeAlias, TypeVar, cast

import flet as ft

from .model import data

__all__ = [
    "NO_CHANGE",
    "FletComponent",
    "receive",
    "send",
]

logger = logging.getLogger(__name__)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
F = TypeVar("F", bound=Callable[..., Any])


class Change(Protocol, Generic[T_co]):
    """The part of a datapoint change consumed by :func:`receive`."""

    @property
    def new_value(self) -> T_co:
        """Value after the datapoint changed."""


Unsubscribe: TypeAlias = Callable[[], None]


class DatapointLike(Protocol, Generic[T]):
    """Structural interface required by component bindings."""

    def set(self, value: T) -> Any:
        """Set the datapoint value.

        Implementations may return an awaitable, although normal model
        datapoints update synchronously.
        """

    def subscribe(
        self,
        callback: Callable[[Change[T]], Any],
        *,
        fire_immediately: bool = False,
    ) -> Unsubscribe:
        """Subscribe to changes and return an unsubscribe callback."""


# A callable target receives the component. This permits bindings such as
# ``lambda component: component.model.selected_user.name``.
DatapointTarget: TypeAlias = (
    data | DatapointLike[Any] | Callable[[Any], DatapointLike[Any]]
)


class _NoChange:
    __slots__ = ()

    def __repr__(self) -> str:
        return "NO_CHANGE"


NO_CHANGE: Final = _NoChange()
"""Return this from a ``@send`` method to leave its datapoint unchanged."""


@dataclass(frozen=True)
class _ReceiveBinding:
    target: DatapointTarget
    fire_immediately: bool


_RECEIVE_BINDINGS_ATTR = "__flet_mvc_receive_bindings__"


def send(target: DatapointTarget) -> Callable[[F], F]:
    """Publish a method's return value to a model datapoint.

    ``target`` can be a model's ``data`` descriptor, a datapoint instance, or
    a callable receiving the component and returning a datapoint. Returning
    :data:`NO_CHANGE` skips the publication; ``None`` is a normal value.

    The wrapper keeps synchronous methods synchronous and asynchronous methods
    asynchronous. A synchronous method must return a concrete value; declare
    it with ``async def`` when computing the value requires awaiting. A
    synchronous method whose datapoint has an asynchronous ``set`` schedules
    that setter on the component's Flet page.
    """

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(
                component: FletComponent, *args: Any, **kwargs: Any
            ):
                _require_component(component, decorator_name="send")
                value = await func(component, *args, **kwargs)
                if value is not NO_CHANGE:
                    result = component._publish(target, value)
                    if inspect.isawaitable(result):
                        await result
                return value

            return cast(F, async_wrapper)

        @wraps(func)
        def sync_wrapper(component: FletComponent, *args: Any, **kwargs: Any):
            _require_component(component, decorator_name="send")
            value = func(component, *args, **kwargs)

            if inspect.isawaitable(value):
                # Flet decides whether to await an event handler by inspecting
                # the handler itself. It does not await an awaitable returned
                # from a regular function, so accepting this shape would work
                # in direct calls but silently fail in a real Flet event.
                close = getattr(value, "close", None)
                if callable(close):
                    close()
                raise TypeError(
                    f"@send method {func.__qualname__} returned an awaitable "
                    "from a synchronous function; declare the method with "
                    "'async def'"
                )

            if value is not NO_CHANGE:
                published = component._publish(target, value)
                if inspect.isawaitable(published):
                    component._schedule(published)
            return value

        return cast(F, sync_wrapper)

    return decorator


def receive(
    target: DatapointTarget,
    *,
    fire_immediately: bool = True,
) -> Callable[[F], F]:
    """Call a method when a model datapoint changes.

    The decorated method receives ``change.new_value``.  Its subscription is
    created in :meth:`FletComponent.did_mount` and removed in
    :meth:`FletComponent.will_unmount`.  Multiple ``@receive`` decorators can
    be stacked on one method.
    """

    if not isinstance(fire_immediately, bool):
        raise TypeError("fire_immediately must be a bool")

    def decorator(func: F) -> F:
        bindings = list(
            cast(tuple[_ReceiveBinding, ...], getattr(func, _RECEIVE_BINDINGS_ATTR, ()))
        )
        bindings.append(
            _ReceiveBinding(target=target, fire_immediately=fire_immediately)
        )
        setattr(func, _RECEIVE_BINDINGS_ATTR, tuple(bindings))
        return func

    return decorator


@ft.control
class FletComponent(ft.Column):
    """Base class for model-aware composite Flet controls.

    Subclasses should also use ``@ft.control`` and override ``init()`` to build
    their child controls.  Call ``super().init()`` before assigning component
    state:

    .. code-block:: python

        @ft.control
        class Counter(FletComponent):
            def init(self):
                super().init()
                self.label = ft.Text()
                self.controls = [self.label]

            @receive(CounterModel.count)
            def show_count(self, value):
                self.label.value = str(value)

            @send(CounterModel.count)
            def increment(self, _event):
                return self.model.count.value + 1
    """

    # These are Python-side concerns, not Dart properties.  ``skip`` is
    # essential with Flet's sparse property machinery: without it, ``model``
    # would be serialized as an unknown Column property.
    model: Any = field(
        default=None,
        kw_only=True,
        repr=False,
        metadata={"skip": True},
    )
    _subscriptions: list[Unsubscribe] = field(
        default_factory=list,
        init=False,
        repr=False,
        metadata={"skip": True},
    )
    _pending_tasks: set[Any] = field(
        default_factory=set,
        init=False,
        repr=False,
        metadata={"skip": True},
    )
    _bindings_active: bool = field(
        default=False,
        init=False,
        repr=False,
        metadata={"skip": True},
    )

    def init(self) -> None:
        """Initialize Column internals and component lifecycle state."""

        super().init()
        # Explicitly reset these fields for subclasses that call ``init`` while
        # being reconstructed by Flet's dataclass machinery.
        self._subscriptions = []
        self._pending_tasks = set()
        self._bindings_active = False

    def did_mount(self) -> None:
        """Subscribe all ``@receive`` methods after attachment to a page."""

        super().did_mount()
        if self._bindings_active:
            return

        self._bindings_active = True
        try:
            self._subscribe_receivers()
        except Exception:
            self._dispose_bindings()
            raise

    def will_unmount(self) -> None:
        """Unsubscribe receivers and cancel outstanding asynchronous work."""

        self._dispose_bindings()
        super().will_unmount()

    def _publish(self, target: DatapointTarget, value: Any) -> Any:
        datapoint = self._resolve_datapoint(target, operation="send")
        setter = getattr(datapoint, "set", None)
        if not callable(setter):
            raise TypeError(
                f"{target!r} cannot be used with @send: resolved object "
                f"{datapoint!r} has no callable set(value)"
            )
        return setter(value)

    def _resolve_datapoint(
        self, target: DatapointTarget, *, operation: str
    ) -> DatapointLike[Any]:
        if isinstance(target, data):
            if self.model is None:
                raise RuntimeError(
                    f"{type(self).__name__} needs a model before @{operation}"
                    f"({target.name}) can be used"
                )
            if target.owner is not None and not isinstance(self.model, target.owner):
                raise TypeError(
                    f"@{operation} target {target.owner.__name__}.{target.name} "
                    f"cannot be resolved on {type(self.model).__name__}"
                )
            return cast(DatapointLike[Any], getattr(self.model, target.name))

        # Datapoints can themselves be callable, so structural datapoints must
        # be recognized before treating a target as a resolver.
        if callable(getattr(target, "set", None)) or callable(
            getattr(target, "subscribe", None)
        ):
            return cast(DatapointLike[Any], target)

        if callable(target):
            try:
                resolved = target(self)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to resolve @{operation} datapoint with {target!r}"
                ) from exc
            if resolved is None:
                raise TypeError(
                    f"@{operation} datapoint resolver {target!r} returned None"
                )
            return resolved

        raise TypeError(
            f"@{operation} target must be a data descriptor, datapoint, or resolver; "
            f"got {type(target).__name__}"
        )

    def _subscribe_receivers(self) -> None:
        for method, binding in self._iter_receiver_bindings():
            datapoint = self._resolve_datapoint(binding.target, operation="receive")
            subscriber = getattr(datapoint, "subscribe", None)
            if not callable(subscriber):
                raise TypeError(
                    f"{binding.target!r} cannot be used with @receive: resolved "
                    f"object {datapoint!r} has no callable subscribe(...)"
                )

            def changed(
                change: Change[Any],
                *,
                receiver: Callable[[Any], Any] = method,
                source: DatapointTarget = binding.target,
            ) -> None:
                # An unsubscribe racing with a notification must not restart
                # work after ``will_unmount`` has begun.
                if not self._bindings_active:
                    return
                if not hasattr(change, "new_value"):
                    raise TypeError(
                        f"Subscription for {source!r} emitted "
                        f"{type(change).__name__}, expected an object with new_value"
                    )
                result = receiver(change.new_value)
                if inspect.isawaitable(result):
                    self._schedule(result, update_after=True)
                else:
                    self._update_if_mounted()

            unsubscribe = subscriber(changed, fire_immediately=binding.fire_immediately)
            if not callable(unsubscribe):
                raise TypeError(
                    f"subscribe() for {binding.target!r} must return an "
                    "unsubscribe callback"
                )
            self._subscriptions.append(unsubscribe)

    def _iter_receiver_bindings(
        self,
    ) -> list[tuple[Callable[[Any], Any], _ReceiveBinding]]:
        # Build the effective class namespace so an override suppresses a base
        # implementation rather than registering both.
        effective_members: dict[str, Any] = {}
        for cls in reversed(type(self).mro()):
            effective_members.update(vars(cls))

        found: list[tuple[Callable[[Any], Any], _ReceiveBinding]] = []
        for name, member in effective_members.items():
            bindings = cast(
                tuple[_ReceiveBinding, ...],
                getattr(member, _RECEIVE_BINDINGS_ATTR, ()),
            )
            if not bindings:
                continue
            method = getattr(self, name)
            if not callable(method):
                raise TypeError(f"@receive member {name!r} is no longer callable")
            found.extend((method, binding) for binding in bindings)
        return found

    def _schedule(
        self,
        awaitable: Awaitable[Any],
        *,
        update_after: bool = False,
    ) -> Any:
        """Schedule an awaitable and retain a cancellable handle."""

        async def runner() -> Any:
            result = await awaitable
            if update_after:
                self._update_if_mounted()
            return result

        try:
            page = self.page
        except RuntimeError:
            page = None

        handle: Any
        if page is not None:
            handle = page.run_task(runner)
        else:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Lifecycle callbacks normally have an attached page.  This
                # fallback keeps manual/headless lifecycle tests deterministic.
                return asyncio.run(runner())
            handle = loop.create_task(runner())

        self._pending_tasks.add(handle)

        def discard(completed: Any) -> None:
            self._pending_tasks.discard(completed)
            if completed.cancelled():
                # A task canceled before ``runner`` gets its first time slice
                # never awaits the original coroutine.  Close it explicitly to
                # release its frame and avoid "coroutine was never awaited".
                close = getattr(awaitable, "close", None)
                if callable(close):
                    close()
                return

            # Retrieving the exception is required for tasks created directly
            # on an asyncio loop; otherwise a failed async receiver produces a
            # delayed "Task exception was never retrieved" warning.
            exception = completed.exception()
            if exception is not None:
                logger.error(
                    "Component task failed for %s",
                    type(self).__name__,
                    exc_info=(
                        type(exception),
                        exception,
                        exception.__traceback__,
                    ),
                )

        handle.add_done_callback(discard)
        return handle

    def _update_if_mounted(self) -> None:
        if not self._bindings_active:
            return
        try:
            _ = self.page
        except RuntimeError:
            # Detachment may race with an asynchronous receiver completing.
            return
        # Receivers mutate this composite control. Keep the update scoped to
        # its subtree; declarative consumers and other explicitly bound
        # controls own their own Flet update lifecycle. Runtime errors from an
        # attached control (for example, updating a frozen control) must remain
        # visible to the application.
        self.update()

    def _dispose_bindings(self) -> None:
        self._bindings_active = False

        subscriptions, self._subscriptions = self._subscriptions, []
        for unsubscribe in reversed(subscriptions):
            try:
                unsubscribe()
            except Exception:
                logger.exception("Failed to unsubscribe a component receiver")

        pending, self._pending_tasks = self._pending_tasks, set()
        for handle in pending:
            cancel = getattr(handle, "cancel", None)
            if callable(cancel):
                cancel()


def _require_component(value: Any, *, decorator_name: str) -> None:
    if not isinstance(value, FletComponent):
        raise TypeError(
            f"@{decorator_name} can only decorate FletComponent methods; "
            f"got {type(value).__name__}"
        )
