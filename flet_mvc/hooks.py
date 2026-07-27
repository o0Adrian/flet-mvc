"""Declarative Flet hooks for model datapoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, TypeVar

import flet as ft

from .model import DatapointChange, _safe_equal

ValueT = TypeVar("ValueT", covariant=True)


class _DatapointLike(Protocol[ValueT]):
    @property
    def value(self) -> ValueT: ...

    def subscribe(
        self,
        callback: Callable[[DatapointChange], Any],
        *,
        fire_immediately: bool = False,
    ) -> Callable[[], None]: ...


@dataclass
class _SubscriptionState:
    disposer: Callable[[], None] | None = None
    point: object | None = None
    observed_value: Any = None


def use_datapoint(point: _DatapointLike[ValueT]) -> ValueT:
    """Read a datapoint and re-render only the consuming component.

    The subscription is established after mount, replaced if ``point`` changes,
    and disposed when the component unmounts. As with every Flet hook, this
    function must be called unconditionally from an ``@ft.component`` body.
    """

    value = point.value
    _, set_revision = ft.use_state(0)
    subscription, _ = ft.use_state(_SubscriptionState())

    # Effects run after rendering. Keep the exact snapshot rendered for the
    # active point so an immediate subscription event can distinguish an
    # unchanged initial value from a change in the render-to-effect window.
    subscription.point = point
    subscription.observed_value = value

    def changed(change: DatapointChange) -> None:
        if subscription.point is not point:
            return
        if _safe_equal(change.new_value, subscription.observed_value):
            return
        subscription.observed_value = change.new_value
        set_revision(lambda revision: revision + 1)

    def cleanup() -> None:
        disposer = subscription.disposer
        subscription.disposer = None
        if disposer is not None:
            disposer()

    def setup() -> None:
        cleanup()
        disposer = point.subscribe(changed, fire_immediately=True)
        if not callable(disposer):
            raise TypeError("datapoint.subscribe() must return a disposer")
        subscription.disposer = disposer

    # Passing cleanup explicitly keeps it attached across component re-renders.
    ft.use_effect(setup, dependencies=[point], cleanup=cleanup)
    return value


__all__ = ["use_datapoint"]
