from __future__ import annotations

import asyncio
import gc
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Any
from weakref import ref

import flet as ft
import pytest

from flet_mvc import (
    DatapointBindingError,
    DependencyCycleError,
    FletModel,
    UnsupportedControlError,
    computed,
    data,
    register_control_binding,
)
from flet_mvc.model import _CONTROL_BINDINGS, NULL


class ReactiveModel(FletModel):
    @data
    def first(self) -> int:
        return 2

    @computed
    def second(self) -> int:
        return self.first.value + 3

    @computed
    def total(self) -> int:
        return self.first.value + self.second.value

    @data
    def items(self) -> list[str]:
        return []


def test_datapoints_are_isolated_per_model_instance() -> None:
    first = ReactiveModel()
    second = ReactiveModel()

    assert first.first is not second.first
    first.first.set(10)

    assert first.first.value == 10
    assert first.second.value == 13
    assert first.total.value == 23
    assert second.first.value == 2
    assert second.second.value == 5
    assert second.total.value == 7


def test_default_factory_uses_the_correct_instance() -> None:
    class NamedModel(FletModel):
        def __init__(self, name: str):
            self.name = name
            super().__init__()

        @data
        def label(self) -> str:
            return f"model:{self.name}"

    assert NamedModel("one").label.value == "model:one"
    assert NamedModel("two").label.value == "model:two"
    assert isinstance(NamedModel.label, data)


def test_inheritance_and_concurrent_instances_remain_isolated() -> None:
    class Base(FletModel):
        def __init__(self, number: int):
            self.number = number
            super().__init__()

        @data
        def value(self) -> int:
            return self.number

    class Child(Base):
        @computed
        def doubled(self) -> int:
            return self.value.value * 2

    def build(number: int) -> tuple[int, int]:
        model = Child(number)
        model.value.set(number + 1)
        return model.value.value, model.doubled.value

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(build, range(30)))

    assert results == [(number + 1, (number + 1) * 2) for number in range(30)]


def test_subclass_can_replace_inherited_datapoint() -> None:
    class Base(FletModel):
        @data
        def state(self) -> str:
            return "base"

    class Child(Base):
        state = "child"

    model = Child()

    assert model.state == "child"
    assert model.snapshot() == {}
    assert model.dependency_graph == {}


def test_subclass_can_override_an_inherited_datapoint_definition() -> None:
    class Base(FletModel):
        @data
        def state(self) -> str:
            return "base"

    class Child(Base):
        @computed
        def state(self) -> str:
            return "child"

    model = Child()

    assert model.state.value == "child"
    assert model.snapshot() == {}


@pytest.mark.parametrize(
    ("name", "definition", "message"),
    [
        ("batch", data(lambda self: None), "inherited model API.*batch"),
        ("snapshot", computed(lambda self: None), "inherited model API.*snapshot"),
        ("datapoints", data(lambda self: None), "inherited model API.*datapoints"),
        ("_definitions", data(lambda self: None), "inherited model API.*_definitions"),
        ("_mvc_lock", data(lambda self: None), "reserved '_mvc_' prefix"),
    ],
)
def test_datapoint_names_cannot_shadow_model_runtime(
    name: str,
    definition: data,
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        type("InvalidModel", (FletModel,), {name: definition})


def test_dependency_graph_propagates_diamond_once() -> None:
    model = ReactiveModel()
    changes = []
    model.total.subscribe(changes.append)

    with model.batch():
        model.first.set(4)
        model.first.set(5)

    assert model.second.value == 8
    assert model.total.value == 13
    assert [(change.new_value, change.source) for change in changes] == [
        (13, "dependency")
    ]
    assert model.dependency_graph == {
        "first": (),
        "second": ("first",),
        "total": ("first", "second"),
        "items": (),
    }
    assert '"first" -> "second";' in model.dependency_dot()
    assert '"second" -> "total";' in model.dependency_dot()


def test_subscribers_see_a_fully_stabilized_graph() -> None:
    model = ReactiveModel()
    observations: list[tuple[int, int, int]] = []
    model.first.subscribe(
        lambda change: observations.append(
            (change.new_value, model.second.value, model.total.value)
        )
    )

    model.first.set(10)

    assert observations == [(10, 13, 23)]


@pytest.mark.asyncio
async def test_async_subscriber_tasks_are_retained_and_exceptions_consumed(
    caplog,
) -> None:
    model = ReactiveModel()
    started = asyncio.Event()
    release = asyncio.Event()
    unhandled_contexts: list[dict[str, Any]] = []
    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()

    async def failing_subscriber(_change) -> None:
        started.set()
        await release.wait()
        raise LookupError("subscriber exploded")

    loop.set_exception_handler(
        lambda _loop, context: unhandled_contexts.append(context)
    )
    try:
        model.first.subscribe(failing_subscriber)
        with caplog.at_level("ERROR", logger="flet_mvc.model"):
            model.first.set(4)
            await started.wait()
            assert len(model._mvc_subscriber_tasks) == 1
            release.set()
            await asyncio.sleep(0)
            await asyncio.sleep(0)
    finally:
        loop.set_exception_handler(previous_handler)

    assert model._mvc_subscriber_tasks == set()
    assert unhandled_contexts == []
    assert "Subscriber failed for datapoint first" in caplog.text
    assert "LookupError: subscriber exploded" in caplog.text


def test_dynamic_dependencies_follow_the_selected_branch() -> None:
    class Dynamic(FletModel):
        @data
        def use_left(self) -> bool:
            return True

        @data
        def left(self) -> str:
            return "L"

        @data
        def right(self) -> str:
            return "R"

        @computed
        def selected(self) -> str:
            return self.left.value if self.use_left.value else self.right.value

    model = Dynamic()
    assert model.selected.value == "L"
    assert model.dependency_graph["selected"] == ("left", "use_left")

    model.use_left.set(False)
    assert model.selected.value == "R"
    assert model.dependency_graph["selected"] == ("right", "use_left")

    model.left.set("ignored")
    assert model.selected.value == "R"
    model.right.set("changed")
    assert model.selected.value == "changed"


def test_batch_orders_new_dynamic_dependency_before_its_dependent() -> None:
    evaluations = {"right": 0, "selected": 0}

    class DynamicBatch(FletModel):
        @data
        def use_left(self) -> bool:
            return True

        @data
        def source(self) -> int:
            return 1

        @data
        def left(self) -> int:
            return 100

        @computed
        def selected(self) -> int:
            evaluations["selected"] += 1
            return self.left.value if self.use_left.value else self.right.value

        @computed
        def right(self) -> int:
            evaluations["right"] += 1
            return self.source.value * 10

    model = DynamicBatch()
    evaluations = dict.fromkeys(evaluations, 0)
    changes = []
    model.selected.subscribe(changes.append)

    with model.batch():
        model.source.set(2)
        model.use_left.set(False)

    assert model.right.value == 20
    assert model.selected.value == 20
    assert model.dependency_graph["selected"] == ("right", "use_left")
    assert [change.new_value for change in changes] == [20]
    assert evaluations == {"right": 1, "selected": 1}


def test_declared_dependencies_and_cycles() -> None:
    class Declared(FletModel):
        @data
        def amount(self) -> int:
            return 3

        @computed.depends_on("amount")
        def doubled(self) -> int:
            return self.amount.value * 2

    model = Declared()
    assert model.doubled.value == 6
    model.amount.set(8)
    assert model.doubled.value == 16

    class Cyclic(FletModel):
        @computed
        def left(self) -> int:
            return self.right.value

        @computed
        def right(self) -> int:
            return self.left.value

    with pytest.raises(DependencyCycleError, match="cycle"):
        Cyclic()


def test_computed_values_are_explicitly_read_only() -> None:
    model = ReactiveModel()

    for operation in (
        lambda: model.total.set(99),
        lambda: model.total.update(lambda value: value + 1),
        model.total.reset,
        model.total.pull,
    ):
        with pytest.raises(TypeError, match="read-only"):
            operation()

    with pytest.raises(TypeError, match="initial value"):
        ReactiveModel(total=99)


def test_reset_update_snapshot_and_restore_only_mutable_state() -> None:
    model = ReactiveModel()

    model.first.set(9)
    model.first.reset()
    assert model.first.value == 2

    result = model.items.update(lambda items: [*items, "a", "c"])
    assert result == ["a", "c"]
    assert model.items.value == ["a", "c"]

    model.restore({"first": 20, "items": ["x"]})
    assert model.snapshot() == {"first": 20, "items": ["x"]}
    assert model.total.value == 43

    with pytest.raises(KeyError, match="unknown"):
        model.restore({"unknown": 1})
    with pytest.raises(TypeError, match="Computed"):
        model.restore({"total": 1})

    model.restore({"unknown": 1, "total": 1}, strict=False)
    assert model.snapshot() == {"first": 20, "items": ["x"]}


def test_subscribe_immediate_and_idempotent_unsubscribe() -> None:
    model = ReactiveModel()
    changes = []
    unsubscribe = model.first.subscribe(changes.append, fire_immediately=True)

    model.first.set(6)
    unsubscribe()
    unsubscribe()
    model.first.set(7)

    assert changes[0].old_value is NULL
    assert changes[0].new_value == 2
    assert changes[0].source == "subscribe"
    assert changes[1].old_value == 2
    assert changes[1].new_value == 6


def test_flet_observable_notifies_once_per_stable_commit_and_batch() -> None:
    model = ReactiveModel()
    observations: list[tuple[int, int | None]] = []

    def listener(sender: ft.Observable, field: str | None) -> None:
        observations.append((sender.total.value, field))  # type: ignore[attr-defined]

    dispose = model.subscribe(listener)
    model.first.set(4)
    with model.batch():
        model.first.set(5)
        model.first.set(6)
    model.first.set(6)
    dispose()

    assert isinstance(model, ft.Observable)
    assert observations == [(11, None), (15, None)]
    assert model.revision == 2


def test_failed_immediate_computed_commit_rolls_back_entire_graph() -> None:
    class AtomicModel(FletModel):
        @data
        def use_alternative(self) -> bool:
            return False

        @data
        def source(self) -> int:
            return 1

        @data
        def alternative(self) -> int:
            return 10

        @computed
        def selected(self) -> int:
            if self.use_alternative.value:
                return self.alternative.value
            return self.source.value * 2

        @computed
        def fragile(self) -> int:
            selected = self.selected.value
            if self.use_alternative.value:
                raise RuntimeError("computed exploded")
            return selected + 1

    model = AtomicModel()
    source_control = SimpleNamespace(value=None)
    selected_control = SimpleNamespace(value=None)
    fragile_control = SimpleNamespace(value=None)
    model.use_alternative.bind(source_control, "value")
    model.selected.bind(selected_control, "value")
    model.fragile.bind(fragile_control, "value")

    graph_before = dict(model.dependency_graph)
    published: list[tuple[str, Any]] = []
    observable_updates: list[tuple[int, int]] = []

    def record_change(change) -> None:
        published.append((change.name, change.new_value))

    for point in model.datapoints.values():
        point.subscribe(record_change)

    def record_observable(sender, _field) -> None:
        observable_updates.append((sender.selected.value, sender.revision))

    dispose = model.subscribe(record_observable)
    with pytest.raises(RuntimeError, match="computed exploded"):
        model.use_alternative.set(True)

    assert model.use_alternative.value is False
    assert model.source.value == 1
    assert model.selected.value == 2
    assert model.fragile.value == 3
    assert source_control.value is False
    assert selected_control.value == 2
    assert fragile_control.value == 3
    assert model.dependency_graph == graph_before
    assert published == []
    assert observable_updates == []
    assert model.revision == 0

    model.source.set(4)
    dispose()

    assert model.selected.value == 8
    assert model.fragile.value == 9
    assert selected_control.value == 8
    assert fragile_control.value == 9
    assert published == [("source", 4), ("selected", 8), ("fragile", 9)]
    assert observable_updates == [(8, 1)]
    assert model.revision == 1


def test_failed_batch_computed_binding_rolls_back_entire_commit() -> None:
    class RejectingControl:
        def __init__(self, value: int) -> None:
            self._value = value
            self.rejected_value: int | None = None

        @property
        def value(self) -> int:
            return self._value

        @value.setter
        def value(self, value: int) -> None:
            if value == self.rejected_value:
                raise ValueError("binding exploded")
            self._value = value

    class AtomicBatchModel(FletModel):
        @data
        def left(self) -> int:
            return 1

        @data
        def right(self) -> int:
            return 10

        @computed
        def doubled(self) -> int:
            return self.left.value * 2

        @computed
        def total(self) -> int:
            return self.doubled.value + self.right.value

    model = AtomicBatchModel()
    left_control = SimpleNamespace(value=None)
    right_control = SimpleNamespace(value=None)
    doubled_control = SimpleNamespace(value=None)
    total_control = RejectingControl(model.total.value)
    model.left.bind(left_control, "value")
    model.right.bind(right_control, "value")
    model.doubled.bind(doubled_control, "value")
    model.total.bind(total_control, "value")
    total_control.rejected_value = 26

    graph_before = dict(model.dependency_graph)
    published: list[tuple[str, Any]] = []
    observable_updates: list[tuple[int, int]] = []

    def record_change(change) -> None:
        published.append((change.name, change.new_value))

    for point in model.datapoints.values():
        point.subscribe(record_change)

    def record_observable(sender, _field) -> None:
        observable_updates.append((sender.total.value, sender.revision))

    dispose = model.subscribe(record_observable)
    with pytest.raises(DatapointBindingError, match="binding exploded"):
        with model.batch():
            model.left.set(3)
            model.right.set(20)

    assert model.left.value == 1
    assert model.right.value == 10
    assert model.doubled.value == 2
    assert model.total.value == 12
    assert left_control.value == 1
    assert right_control.value == 10
    assert doubled_control.value == 2
    assert total_control.value == 12
    assert model.dependency_graph == graph_before
    assert published == []
    assert observable_updates == []
    assert model.revision == 0

    total_control.rejected_value = None
    with model.batch():
        model.left.set(4)
        model.right.set(30)
    dispose()

    assert model.doubled.value == 8
    assert model.total.value == 38
    assert doubled_control.value == 8
    assert total_control.value == 38
    assert published == [
        ("left", 4),
        ("right", 30),
        ("doubled", 8),
        ("total", 38),
    ]
    assert observable_updates == [(38, 1)]
    assert model.revision == 1


def test_batch_body_exception_rolls_back_values_controls_and_notifications() -> None:
    model = ReactiveModel()
    first_control = SimpleNamespace(value=None)
    total_control = SimpleNamespace(value=None)
    model.first.bind(first_control, "value")
    model.total.bind(total_control, "value")
    graph_before = dict(model.dependency_graph)
    published = []
    observable_updates = []
    model.first.subscribe(published.append)
    dispose = model.subscribe(
        lambda sender, _field: observable_updates.append(sender.revision)
    )

    with pytest.raises(RuntimeError, match="abort transaction"):
        with model.batch():
            model.first.set(10)
            assert first_control.value == 10
            raise RuntimeError("abort transaction")

    dispose()
    assert model.first.value == 2
    assert model.second.value == 5
    assert model.total.value == 7
    assert first_control.value == 2
    assert total_control.value == 7
    assert model.dependency_graph == graph_before
    assert published == []
    assert observable_updates == []
    assert model.revision == 0


def test_failed_reset_restores_dynamic_dependencies_and_stable_value() -> None:
    class ResetModel(FletModel):
        fail = False
        use_alternative = False

        @data
        def primary(self) -> int:
            return 2

        @data
        def alternative(self) -> int:
            return 20

        @data
        def selected(self) -> int:
            value = (
                self.alternative.value if self.use_alternative else self.primary.value
            )
            if self.fail:
                raise RuntimeError("default exploded")
            return value

    model = ResetModel()
    selected_control = SimpleNamespace(value=None)
    model.selected.bind(selected_control, "value")
    graph_before = dict(model.dependency_graph)
    model.use_alternative = True
    model.fail = True
    published = []
    observable_updates = []
    model.selected.subscribe(published.append)
    dispose = model.subscribe(
        lambda sender, _field: observable_updates.append(sender.revision)
    )

    with pytest.raises(RuntimeError, match="default exploded"):
        model.selected.reset()

    dispose()
    assert model.selected.value == 2
    assert selected_control.value == 2
    assert model.dependency_graph == graph_before
    assert published == []
    assert observable_updates == []
    assert model.revision == 0


def test_regular_public_fields_keep_native_observable_behavior() -> None:
    class Mixed(FletModel):
        def __init__(self) -> None:
            self.label = "before"
            super().__init__()

        @data
        def count(self) -> int:
            return 0

    model = Mixed()
    fields: list[str | None] = []

    def listener(_sender, field) -> None:
        fields.append(field)

    dispose = model.subscribe(listener)
    model.label = "after"
    dispose()

    assert fields == ["label"]
    assert model.revision == 0


@pytest.mark.parametrize(
    "reserved",
    ["notify", "subscribe", "_notify", "__version__", "revision"],
)
def test_observable_api_names_are_reserved(reserved: str) -> None:
    with pytest.raises(TypeError, match="Observable API"):
        type(
            "InvalidModel",
            (FletModel,),
            {reserved: lambda self: None},
        )


def test_control_to_model_to_dependencies_and_multiple_bindings() -> None:
    model = ReactiveModel()
    calls: list[int] = []

    def original_handler() -> None:
        calls.append(model.first.value)

    slider = ft.Slider(ref=model.first, on_change=original_handler)
    progress = ft.ProgressBar(ref=model.first)

    assert slider.value == 2
    assert progress.value == 2

    slider.value = 12
    slider.on_change(SimpleNamespace(control=slider))

    assert calls == [12]
    assert model.first.value == 12
    assert model.second.value == 15
    assert model.total.value == 27
    assert progress.value == 12
    assert model.first.current is slider
    assert model.first.controls == (slider, progress)

    model.first.unbind(slider)
    assert model.first.current is progress
    assert model.first.controls == (progress,)


def test_two_datapoints_cannot_manage_the_same_control_event() -> None:
    class BindingModel(FletModel):
        @data
        def first(self) -> str:
            return "first"

        @data
        def second(self) -> str:
            return "second"

    model = BindingModel()
    calls: list[str] = []

    def original_handler() -> None:
        calls.append("original")

    field = ft.TextField(value="outside", on_change=original_handler)
    model.first.bind(field)
    first_wrapper = field.on_change

    with pytest.raises(
        DatapointBindingError,
        match="already managed by datapoint 'first'.*datapoint 'second'",
    ):
        model.second.bind(field)

    assert field.value == "first"
    assert field.on_change is first_wrapper
    assert model.first.controls == (field,)
    assert model.second.controls == ()

    model.first.unbind(field)

    assert field.on_change is original_handler
    field.on_change()
    assert calls == ["original"]


def test_bind_rolls_back_control_value_if_event_handler_installation_fails() -> None:
    def original_handler() -> None:
        return None

    class RejectingHandlerControl:
        def __init__(self) -> None:
            self.value = "outside"
            self._handler = original_handler

        @property
        def on_change(self):
            return self._handler

        @on_change.setter
        def on_change(self, _handler) -> None:
            raise RuntimeError("handler rejected")

    class BindingModel(FletModel):
        @data
        def state(self) -> str:
            return "inside"

    model = BindingModel()
    control = RejectingHandlerControl()

    with pytest.raises(DatapointBindingError, match="handler rejected"):
        model.state.bind(control, "value")

    assert control.value == "outside"
    assert control.on_change is original_handler
    assert model.state.value == "inside"
    assert model.state.controls == ()


def test_bindings_are_weak_and_can_be_explicit() -> None:
    class Explicit(FletModel):
        @data(bind="payload")
        def state(self) -> str:
            return "ready"

    class Custom:
        def __init__(self) -> None:
            self.payload = None

    model = Explicit()
    control = Custom()
    control_ref = ref(control)
    model.state.bind(control)
    assert control.payload == "ready"

    model.state.set("done")
    assert control.payload == "done"

    del control
    gc.collect()
    assert control_ref() is None
    assert model.state.controls == ()


def test_unknown_controls_require_an_explicit_binding() -> None:
    control = SimpleNamespace(value=None, content=None)

    with pytest.raises(UnsupportedControlError, match="No safe default"):
        ReactiveModel().first.bind(control)

    model = ReactiveModel()
    model.first.bind(control, "value")
    assert control.value == 2


@pytest.mark.parametrize(
    ("control_type", "attribute", "expected_type", "event", "error", "message"),
    [
        (42, "value", None, None, TypeError, "control_type"),
        (object, 42, None, None, TypeError, "attribute"),
        (object, "  ", None, None, ValueError, "attribute"),
        (object, "value", "text", None, TypeError, "expected_type"),
        (object, "value", Any, None, TypeError, "isinstance"),
        (object, "value", (), None, TypeError, "expected_type"),
        (object, "value", (str, "text"), None, TypeError, "expected_type"),
        (object, "value", None, 42, TypeError, "event"),
        (object, "value", None, "  ", ValueError, "event"),
    ],
)
def test_register_control_binding_rejects_invalid_contracts(
    control_type,
    attribute,
    expected_type,
    event,
    error,
    message,
) -> None:
    with pytest.raises(error, match=message):
        register_control_binding(
            control_type,
            attribute,
            expected_type,
            event=event,
        )


def test_register_control_binding_uses_real_classes_and_mro() -> None:
    class RegisteredControl:
        def __init__(self) -> None:
            self.value = None
            self.on_change = None

    class ChildControl(RegisteredControl):
        pass

    assert RegisteredControl not in _CONTROL_BINDINGS
    try:
        register_control_binding(
            RegisteredControl,
            "value",
            (str, type(None)),
            event="on_change",
        )
        model = ReactiveModel(first=3)
        control = ChildControl()
        with pytest.raises(TypeError, match="expects"):
            model.first.bind(control)

        string_model = type(
            "StringModel",
            (FletModel,),
            {"state": data(lambda self: "ready")},
        )()
        string_model.state.bind(control)
        assert control.value == "ready"
    finally:
        _CONTROL_BINDINGS.pop(RegisteredControl, None)


def test_multibinding_failure_rolls_back_controls_and_model() -> None:
    class Rejecting:
        def __init__(self) -> None:
            self._value = 2
            self.reject = False

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, value):
            if self.reject and value == 99:
                raise ValueError("rejected")
            self._value = value

    model = ReactiveModel()
    first = SimpleNamespace(value=2)
    second = Rejecting()
    model.first.bind(first, "value")
    model.first.bind(second, "value")
    second.reject = True

    with pytest.raises(DatapointBindingError, match="synchronize"):
        model.first.set(99)

    assert model.first.value == 2
    assert first.value == 2
    assert second.value == 2
