from __future__ import annotations

import asyncio
from concurrent.futures import Future
from dataclasses import dataclass, field, fields
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest

from flet_mvc.component import (
    NO_CHANGE,
    FletComponent,
    receive,
    send,
)
from flet_mvc.model import FletModel, computed, data


@dataclass(frozen=True)
class FakeChange:
    new_value: Any


class FakeDatapoint:
    def __init__(self, value: Any):
        self.value = value
        self.set_values: list[Any] = []
        self.callbacks: list[Any] = []
        self.subscribe_calls: list[bool] = []
        self.unsubscribe_calls = 0

    def set(self, value: Any) -> None:
        self.value = value
        self.set_values.append(value)
        self.emit(value)

    def subscribe(self, callback, *, fire_immediately: bool = False):
        self.subscribe_calls.append(fire_immediately)
        self.callbacks.append(callback)
        if fire_immediately:
            callback(FakeChange(self.value))

        active = True

        def unsubscribe() -> None:
            nonlocal active
            if not active:
                return
            active = False
            self.unsubscribe_calls += 1
            self.callbacks.remove(callback)

        return unsubscribe

    def emit(self, value: Any) -> None:
        self.value = value
        for callback in tuple(self.callbacks):
            callback(FakeChange(value))

    def emit_change(self, change: Any) -> None:
        for callback in tuple(self.callbacks):
            callback(change)


class AsyncDatapoint(FakeDatapoint):
    async def set(self, value: Any) -> None:
        await asyncio.sleep(0)
        super().set(value)


class FakePage:
    def __init__(self):
        self.update_calls: list[tuple[Any, ...]] = []

    def update(self, *controls):
        self.update_calls.append(controls)

    def run_task(self, handler, *args, **kwargs):
        future = Future()
        try:
            future.set_result(asyncio.run(handler(*args, **kwargs)))
        except BaseException as exc:
            future.set_exception(exc)
        return future


def attach_page(monkeypatch, component, page):
    monkeypatch.setattr(
        type(component),
        "page",
        property(lambda _component: page),
    )


def skipped_field(*, default_factory=list):
    return field(
        default_factory=default_factory,
        init=False,
        repr=False,
        metadata={"skip": True},
    )


def test_component_is_a_real_flet_column_with_python_only_state():
    model = SimpleNamespace(value=FakeDatapoint(1))

    @ft.control
    class Demo(FletComponent):
        label: ft.Text | None = field(
            default=None,
            init=False,
            metadata={"skip": True},
        )

        def init(self):
            super().init()
            self.label = ft.Text("ready")
            self.controls = [self.label]

    component = Demo(model=model, spacing=17)

    assert isinstance(component, FletComponent)
    assert isinstance(component, ft.Column)
    assert component.controls == [component.label]
    assert component.spacing == 17
    assert component.model is model
    assert "model" not in component._values

    state_fields = {
        item.name: item.metadata.get("skip")
        for item in fields(component)
        if item.name
        in {"model", "_subscriptions", "_pending_tasks", "_bindings_active"}
    }
    assert state_fields == {
        "model": True,
        "_subscriptions": True,
        "_pending_tasks": True,
        "_bindings_active": True,
    }


def test_send_supports_direct_descriptor_and_callable_targets():
    direct = FakeDatapoint("direct")

    class Model(FletModel):
        @data
        def described(self):
            return "descriptor"

        @data
        def resolved(self):
            return "resolved"

    model = Model()

    @ft.control
    class Sender(FletComponent):
        @send(direct)
        def send_direct(self, value):
            return value

        @send(Model.described)
        def send_descriptor(self, value):
            return value

        @send(lambda component: component.model.resolved)
        def send_resolved(self, value):
            return value

    component = Sender(model=model)

    assert component.send_direct(1) == 1
    assert component.send_descriptor(2) == 2
    assert component.send_resolved(3) == 3
    assert direct.set_values == [1]
    assert model.described.value == 2
    assert model.resolved.value == 3


def test_send_distinguishes_none_from_no_change_and_preserves_metadata():
    point = FakeDatapoint("initial")

    @ft.control
    class Sender(FletComponent):
        @send(point)
        def publish_none(self):
            """A decorated method."""

            return None

        @send(point)
        def skip(self):
            return NO_CHANGE

    component = Sender()

    assert component.publish_none() is None
    assert point.set_values == [None]
    assert component.skip() is NO_CHANGE
    assert point.set_values == [None]
    assert repr(NO_CHANGE) == "NO_CHANGE"
    assert component.publish_none.__name__ == "publish_none"
    assert component.publish_none.__doc__ == "A decorated method."


def test_send_supports_async_methods_and_async_setters():
    normal = FakeDatapoint(0)
    asynchronous = AsyncDatapoint(0)

    @ft.control
    class AsyncSender(FletComponent):
        @send(normal)
        async def publish_async(self, value):
            await asyncio.sleep(0)
            return value

        @send(asynchronous)
        def publish_to_async_setter(self, value):
            return value

        @send(normal)
        def invalid_sync_awaitable(self, value):
            async def resolve():
                await asyncio.sleep(0)
                return value

            return resolve()

        @send(normal)
        async def skip_async(self):
            await asyncio.sleep(0)
            return NO_CHANGE

    component = AsyncSender()

    assert asyncio.run(component.publish_async(4)) == 4
    assert normal.set_values == [4]
    assert component.publish_to_async_setter(5) == 5
    assert asynchronous.set_values == [5]
    with pytest.raises(TypeError, match="declare the method with 'async def'"):
        component.invalid_sync_awaitable(6)
    assert normal.set_values == [4]
    assert asyncio.run(component.skip_async()) is NO_CHANGE
    assert normal.set_values == [4]


def test_receive_targets_fire_immediately_and_auto_update(monkeypatch):
    direct = FakeDatapoint("direct")

    class Model(FletModel):
        @data
        def described(self):
            return "descriptor"

        @data
        def resolved(self):
            return "resolved"

    model = Model()

    @ft.control
    class Receiver(FletComponent):
        events: list[tuple[str, Any]] = skipped_field()

        @receive(direct)
        def direct_changed(self, value):
            self.events.append(("direct", value))

        @receive(Model.described, fire_immediately=False)
        def descriptor_changed(self, value):
            self.events.append(("descriptor", value))

        @receive(lambda component: component.model.resolved)
        def resolved_changed(self, value):
            self.events.append(("resolved", value))

    component = Receiver(model=model)
    page = FakePage()
    attach_page(monkeypatch, component, page)
    updates: list[str] = []
    monkeypatch.setattr(component, "update", lambda: updates.append("update"))

    component.did_mount()

    assert component.events == [
        ("direct", "direct"),
        ("resolved", "resolved"),
    ]
    assert updates == ["update", "update"]
    assert page.update_calls == []
    assert direct.subscribe_calls == [True]

    direct.emit(1)
    model.described.set(2)
    model.resolved.set(3)
    assert component.events[-3:] == [
        ("direct", 1),
        ("descriptor", 2),
        ("resolved", 3),
    ]
    assert updates == ["update"] * 5
    assert page.update_calls == []


def test_receive_async_handler_updates_after_completion(monkeypatch):
    point = FakeDatapoint(1)

    @ft.control
    class Receiver(FletComponent):
        events: list[Any] = skipped_field()

        @receive(point)
        async def changed(self, value):
            await asyncio.sleep(0)
            self.events.append(value)

    component = Receiver()
    page = FakePage()
    attach_page(monkeypatch, component, page)
    updates: list[str] = []
    monkeypatch.setattr(component, "update", lambda: updates.append("update"))

    component.did_mount()
    point.emit(2)

    assert component.events == [1, 2]
    assert updates == ["update", "update"]
    assert page.update_calls == []
    component.will_unmount()


def test_mount_is_idempotent_and_unmount_cleans_up_then_allows_remount():
    point = FakeDatapoint(1)

    @ft.control
    class Receiver(FletComponent):
        events: list[Any] = skipped_field()

        @receive(point)
        def changed(self, value):
            self.events.append(value)

    component = Receiver()
    component.did_mount()
    component.did_mount()

    assert point.subscribe_calls == [True]
    assert len(point.callbacks) == 1

    component.will_unmount()
    component.will_unmount()
    assert point.unsubscribe_calls == 1
    assert point.callbacks == []

    point.emit(2)
    assert component.events == [1]

    component.did_mount()
    assert component.events == [1, 2]
    assert len(point.callbacks) == 1
    component.will_unmount()


def test_cleanup_logs_unsubscribe_failures_and_stale_callbacks_are_inert(caplog):
    point = FakeDatapoint(1)

    def broken_subscribe(callback, *, fire_immediately=False):
        unsubscribe = FakeDatapoint.subscribe(
            point,
            callback,
            fire_immediately=fire_immediately,
        )

        def broken_unsubscribe():
            unsubscribe()
            raise RuntimeError("cleanup failed")

        return broken_unsubscribe

    point.subscribe = broken_subscribe

    @ft.control
    class Receiver(FletComponent):
        events: list[Any] = skipped_field()

        @receive(point)
        def changed(self, value):
            self.events.append(value)

    component = Receiver()
    component.did_mount()
    stale_callback = point.callbacks[0]

    component.will_unmount()
    stale_callback(FakeChange(2))

    assert component.events == [1]
    assert point.callbacks == []
    assert "Failed to unsubscribe" in caplog.text


def test_unmount_cancels_pending_async_receivers_without_late_update(monkeypatch):
    point = FakeDatapoint(1)

    @ft.control
    class Receiver(FletComponent):
        events: list[Any] = skipped_field()

        @receive(point, fire_immediately=False)
        async def changed(self, value):
            await asyncio.sleep(60)
            self.events.append(value)

    async def scenario():
        component = Receiver()
        updates: list[str] = []
        monkeypatch.setattr(component, "update", lambda: updates.append("update"))
        component.did_mount()
        point.emit(2)
        assert len(component._pending_tasks) == 1

        component.will_unmount()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert component._pending_tasks == set()
        assert component.events == []
        assert updates == []
        assert point.callbacks == []

    asyncio.run(scenario())


@pytest.mark.asyncio
async def test_async_receiver_exceptions_are_consumed_and_logged(caplog):
    point = FakeDatapoint(1)
    started = asyncio.Event()
    release = asyncio.Event()
    unhandled_contexts = []
    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()

    @ft.control
    class Receiver(FletComponent):
        @receive(point, fire_immediately=False)
        async def changed(self, _value):
            started.set()
            await release.wait()
            raise LookupError("receiver exploded")

    component = Receiver()
    loop.set_exception_handler(
        lambda _loop, context: unhandled_contexts.append(context)
    )
    try:
        component.did_mount()
        with caplog.at_level("ERROR", logger="flet_mvc.component"):
            point.emit(2)
            await started.wait()
            assert len(component._pending_tasks) == 1

            release.set()
            await asyncio.sleep(0)
            await asyncio.sleep(0)
    finally:
        component.will_unmount()
        loop.set_exception_handler(previous_handler)

    assert component._pending_tasks == set()
    assert unhandled_contexts == []
    assert "Component task failed for Receiver" in caplog.text
    assert "LookupError: receiver exploded" in caplog.text


def test_receive_override_suppresses_base_binding_and_decorated_override_replaces_it():
    first = FakeDatapoint("first")
    second = FakeDatapoint("second")

    @ft.control
    class Base(FletComponent):
        events: list[Any] = skipped_field()

        @receive(first)
        def changed(self, value):
            self.events.append(("base", value))

    @ft.control
    class UndecoratedOverride(Base):
        def changed(self, value):
            self.events.append(("plain", value))

    @ft.control
    class DecoratedOverride(Base):
        @receive(second)
        def changed(self, value):
            self.events.append(("child", value))

    undecorated = UndecoratedOverride()
    undecorated.did_mount()
    assert first.callbacks == []
    assert undecorated.events == []

    decorated = DecoratedOverride()
    decorated.did_mount()
    assert decorated.events == [("child", "second")]
    assert len(first.callbacks) == 0
    assert len(second.callbacks) == 1

    undecorated.will_unmount()
    decorated.will_unmount()


def test_stacked_receive_decorators_subscribe_one_method_to_multiple_points():
    first = FakeDatapoint(1)
    second = FakeDatapoint(2)

    @ft.control
    class Receiver(FletComponent):
        values: list[Any] = skipped_field()

        @receive(first)
        @receive(second)
        def changed(self, value):
            self.values.append(value)

    component = Receiver()
    component.did_mount()

    assert component.values == [2, 1]
    first.emit(3)
    second.emit(4)
    assert component.values == [2, 1, 3, 4]
    component.will_unmount()


def test_component_integrates_with_real_model_datapoints():
    class Model(FletModel):
        @data
        def count(self):
            return 1

    @ft.control
    class Counter(FletComponent):
        values: list[int] = skipped_field()

        @receive(Model.count)
        def changed(self, value):
            self.values.append(value)

        @send(Model.count)
        def publish(self, value):
            return value

    model = Model()
    component = Counter(model=model)
    component.did_mount()

    assert component.values == [1]
    component.publish(7)
    assert model.count.value == 7
    assert component.values == [1, 7]

    component.will_unmount()
    model.count.set(8)
    assert component.values == [1, 7]


def test_receive_updates_only_its_component_subtree(
    monkeypatch,
):
    class Model(FletModel):
        @data
        def count(self):
            return 1

        @computed
        def summary(self):
            return f"Count: {self.count.value}"

    @ft.control
    class Counter(FletComponent):
        label: ft.Text | None = field(
            default=None,
            init=False,
            metadata={"skip": True},
        )

        def init(self):
            super().init()
            self.label = ft.Text()
            self.controls = [self.label]

        @receive(Model.count)
        def show_count(self, value):
            self.label.value = str(value)

        @send(Model.count)
        def increment(self):
            return self.model.count.value + 1

    model = Model()
    # This binding intentionally lives outside the component subtree.
    external_summary = ft.Text(ref=model.summary)
    component = Counter(model=model)
    page = FakePage()
    attach_page(monkeypatch, component, page)
    updates: list[str] = []
    monkeypatch.setattr(component, "update", lambda: updates.append("update"))

    component.did_mount()
    updates.clear()
    assert component.increment() == 2

    assert component.label.value == "2"
    assert external_summary.value == "Count: 2"
    assert updates == ["update"]
    assert page.update_calls == []
    component.will_unmount()


def test_send_resolution_and_contract_errors():
    class Model(FletModel):
        @data
        def value(self):
            return 0

    class OtherModel(FletModel):
        pass

    class NoSetter:
        pass

    def exploding_resolver(_component):
        raise LookupError("boom")

    @ft.control
    class Sender(FletComponent):
        @send(Model.value)
        def no_model(self):
            return 1

        @send(Model.value)
        def wrong_model(self):
            return 1

        @send(lambda _component: None)
        def none_resolver(self):
            return 1

        @send(exploding_resolver)
        def exploding(self):
            return 1

        @send(lambda _component: NoSetter())
        def no_setter(self):
            return 1

        @send(42)  # type: ignore[arg-type]
        def invalid_target(self):
            return 1

    with pytest.raises(RuntimeError, match="needs a model"):
        Sender().no_model()
    with pytest.raises(TypeError, match="cannot be resolved"):
        Sender(model=OtherModel()).wrong_model()
    with pytest.raises(TypeError, match="returned None"):
        Sender().none_resolver()
    with pytest.raises(RuntimeError, match="Failed to resolve"):
        Sender().exploding()
    with pytest.raises(TypeError, match="no callable set"):
        Sender().no_setter()
    with pytest.raises(TypeError, match="data descriptor, datapoint, or resolver"):
        Sender().invalid_target()


def test_receive_contract_errors_and_partial_mount_cleanup():
    good = FakeDatapoint(1)

    class NoSubscriber:
        pass

    class BrokenSubscriber:
        def subscribe(self, _callback, *, fire_immediately=False):
            return None

    @ft.control
    class MissingSubscriber(FletComponent):
        @receive(lambda _component: NoSubscriber())
        def changed(self, _value):
            pass

    @ft.control
    class BadUnsubscribe(FletComponent):
        @receive(BrokenSubscriber())
        def changed(self, _value):
            pass

    @ft.control
    class PartialFailure(FletComponent):
        @receive(good)
        def first(self, _value):
            pass

        @receive(lambda _component: NoSubscriber())
        def second(self, _value):
            pass

    with pytest.raises(TypeError, match="no callable subscribe"):
        MissingSubscriber().did_mount()
    with pytest.raises(TypeError, match="must return an unsubscribe"):
        BadUnsubscribe().did_mount()
    with pytest.raises(TypeError, match="no callable subscribe"):
        PartialFailure().did_mount()

    assert good.callbacks == []
    assert good.unsubscribe_calls == 1


def test_receive_rejects_changes_without_new_value():
    point = FakeDatapoint(1)

    @ft.control
    class Receiver(FletComponent):
        @receive(point, fire_immediately=False)
        def changed(self, _value):
            pass

    component = Receiver()
    component.did_mount()
    with pytest.raises(TypeError, match="expected an object with new_value"):
        point.emit_change(object())
    component.will_unmount()


def test_receive_decorator_and_send_owner_validation():
    point = FakeDatapoint(1)
    with pytest.raises(TypeError, match="fire_immediately must be a bool"):
        receive(point, fire_immediately=1)  # type: ignore[arg-type]

    class NotAComponent:
        @send(FakeDatapoint(1))
        def publish(self):
            return 2

    with pytest.raises(TypeError, match="only decorate FletComponent"):
        NotAComponent().publish()
