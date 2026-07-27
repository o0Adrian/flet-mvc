from __future__ import annotations

import inspect
from collections import defaultdict
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest
from flet.components.component import Component, Renderer
from flet.controls.context import _context_page

from flet_mvc import FletModel, data, use_datapoint


class HookModel(FletModel):
    @data
    def left(self):
        return 0

    @data
    def right(self):
        return 0


class _HeadlessSession:
    """Run real Flet component hooks without starting a Flutter client."""

    def __init__(self):
        self.pending_updates: set[Component] = set()
        self.pending_effects: list[tuple[Any, bool]] = []

    def schedule_update(self, component: Component) -> None:
        self.pending_updates.add(component)

    def schedule_effect(self, hook: Any, is_cleanup: bool) -> None:
        self.pending_effects.append((hook, is_cleanup))

    def patch_control(self, *args: Any, **kwargs: Any) -> None:
        pass

    def flush(self) -> None:
        for _ in range(20):
            if not (self.pending_updates or self.pending_effects):
                return

            updates = list(self.pending_updates)
            self.pending_updates.clear()
            for component in updates:
                component.update()

            effects = list(self.pending_effects)
            self.pending_effects.clear()
            for hook, is_cleanup in effects:
                callback = hook.cleanup if is_cleanup else hook.setup
                if not callable(callback):
                    continue
                result = callback()
                if inspect.isawaitable(result):
                    raise AssertionError("hook test effects must be synchronous")
                if not is_cleanup and callable(result):
                    hook.cleanup = result

        raise AssertionError("Flet's headless update queue did not settle")


@pytest.fixture
def headless_session():
    session = _HeadlessSession()
    token = _context_page.set(SimpleNamespace(session=session))
    try:
        yield session
    finally:
        _context_page.reset(token)


def _mount(
    session: _HeadlessSession,
    component: Any,
    *args: Any,
) -> Component:
    mounted = Renderer().render(component, *args)
    assert isinstance(mounted, Component)
    mounted.before_update()
    mounted.did_mount()
    session.flush()
    return mounted


def test_use_datapoint_rerenders_granularly_and_coalesces_batch(
    headless_session: _HeadlessSession,
):
    model = HookModel()
    renders: dict[str, list[int]] = defaultdict(list)

    @ft.component
    def Value(label: str, point: Any):
        value = use_datapoint(point)
        renders[label].append(value)
        return ft.Text(str(value))

    _mount(headless_session, Value, "left", model.left)
    _mount(headless_session, Value, "right", model.right)

    with model.batch():
        model.left.set(1)
        model.left.set(2)

    assert len(headless_session.pending_updates) == 1
    headless_session.flush()
    assert renders == {"left": [0, 2], "right": [0]}

    model.right.set(4)
    headless_session.flush()
    assert renders == {"left": [0, 2], "right": [0, 4]}


def test_use_datapoint_catches_change_between_render_and_effect(
    headless_session: _HeadlessSession,
):
    model = HookModel()
    renders: list[int] = []

    @ft.component
    def Value():
        value = use_datapoint(model.left)
        renders.append(value)
        return ft.Text(str(value))

    component = Renderer().render(Value)
    assert isinstance(component, Component)
    component.before_update()
    component.did_mount()

    # The first render has read the old value, but its effect has not subscribed
    # yet. This is the render-to-effect window that previously lost the change.
    assert renders == [0]
    assert len(model.left._subscribers) == 0
    model.left.set(1)
    assert not headless_session.pending_updates

    headless_session.flush()

    assert renders == [0, 1]
    assert len(model.left._subscribers) == 1


def test_use_datapoint_disposes_after_rerender_and_unmount(
    headless_session: _HeadlessSession,
):
    model = HookModel()
    renders: list[int] = []

    @ft.component
    def Value(point: Any):
        value = use_datapoint(point)
        renders.append(value)
        return ft.Text(str(value))

    component = _mount(headless_session, Value, model.left)
    assert len(model.left._subscribers) == 1

    model.left.set(1)
    headless_session.flush()
    assert renders == [0, 1]
    assert len(model.left._subscribers) == 1

    component.will_unmount()
    headless_session.flush()
    assert len(model.left._subscribers) == 0

    model.left.set(2)
    headless_session.flush()
    assert renders == [0, 1]


def test_use_datapoint_replaces_subscription_when_point_changes(
    headless_session: _HeadlessSession,
):
    model = HookModel()
    renders: list[int] = []

    @ft.component
    def Value(point: Any):
        value = use_datapoint(point)
        renders.append(value)
        return ft.Text(str(value))

    component = _mount(headless_session, Value, model.left)
    assert len(model.left._subscribers) == 1
    assert len(model.right._subscribers) == 0

    object.__setattr__(component, "args", (model.right,))
    component.before_update()
    headless_session.flush()

    assert len(model.left._subscribers) == 0
    assert len(model.right._subscribers) == 1
    assert renders == [0, 0]

    model.left.set(1)
    headless_session.flush()
    assert renders == [0, 0]

    model.right.set(2)
    headless_session.flush()
    assert renders == [0, 0, 2]


def test_use_datapoint_requires_a_subscription_disposer(
    headless_session: _HeadlessSession,
):
    class BrokenPoint:
        value = 0

        def subscribe(self, _callback, *, fire_immediately=False):
            return None

    @ft.component
    def Value():
        return ft.Text(str(use_datapoint(BrokenPoint())))

    with pytest.raises(
        TypeError,
        match=r"datapoint\.subscribe\(\) must return a disposer",
    ):
        _mount(headless_session, Value)


@pytest.mark.parametrize(
    "name",
    ["notify", "subscribe", "_notify", "__version__", "revision"],
)
def test_flet_model_rejects_observable_api_collisions(name: str):
    with pytest.raises(TypeError, match=name):
        type(
            f"Bad{name}",
            (FletModel,),
            {name: lambda self, *args: None},
        )
