from __future__ import annotations

from typing import Any

import flet as ft
import pytest

from flet_mvc import FletModel, computed, data
from flet_mvc.model import _CONTROL_BINDINGS


def _values(control_type: type[Any], attribute: str) -> tuple[Any, Any]:
    if attribute == "value":
        if control_type in {
            ft.Checkbox,
            ft.CupertinoCheckbox,
            ft.CupertinoSwitch,
            ft.Switch,
        }:
            return False, True
        if control_type in {
            ft.CupertinoSlider,
            ft.ProgressBar,
            ft.ProgressRing,
            ft.Slider,
        }:
            return 0.25, 0.75
        return "initial", "replacement"
    if attribute == "selected_index":
        return 0, 1
    if attribute == "icon":
        return ft.Icons.ADD, ft.Icons.REMOVE
    if attribute == "src":
        return "initial.png", "replacement.png"
    if attribute == "text":
        return "initial", "replacement"
    raise AssertionError(f"Missing values for {control_type.__name__}.{attribute}")


def _tab_content(label: str) -> ft.Column:
    return ft.Column(
        [
            ft.TabBar(tabs=[ft.Tab(label=label), ft.Tab(label="Other")]),
            ft.TabBarView([ft.Text(label), ft.Text("Other")]),
        ]
    )


def _build(control_type: type[Any], ref: Any) -> Any:
    kwargs: dict[str, Any] = {}
    if control_type is ft.Dropdown:
        kwargs["options"] = [
            ft.DropdownOption(key="initial", text="Initial"),
            ft.DropdownOption(key="replacement", text="Replacement"),
        ]
    elif control_type is ft.Image:
        kwargs["src"] = "placeholder.png"
    elif control_type is ft.Icon:
        kwargs["icon"] = ft.Icons.INFO
    elif control_type is ft.RadioGroup:
        kwargs["content"] = ft.Column()
    elif control_type is ft.Tabs:
        kwargs.update(length=2, content=_tab_content("Initial"))
    return control_type(ref=ref, **kwargs)


@pytest.mark.parametrize(
    "control_type",
    sorted(_CONTROL_BINDINGS, key=lambda item: item.__name__),
)
def test_every_safe_default_binding_sets_and_resets(
    control_type: type[Any],
) -> None:
    spec = _CONTROL_BINDINGS[control_type]
    initial, replacement = _values(control_type, spec.attribute)

    class Model(FletModel):
        @data
        def state(self):
            return initial

    model = Model()
    control = _build(control_type, model.state)

    assert getattr(control, spec.attribute) == initial
    assert model.state.current is control

    model.state.set(replacement)
    assert getattr(control, spec.attribute) == replacement
    assert model.state.value == replacement

    model.state.reset()
    assert getattr(control, spec.attribute) == initial
    assert model.state.value == initial


def test_default_matrix_is_small_and_contains_only_state_or_leaf_data() -> None:
    assert len(_CONTROL_BINDINGS) == 21
    assert {control.__name__ for control in _CONTROL_BINDINGS} == {
        "Checkbox",
        "CupertinoCheckbox",
        "CupertinoSlider",
        "CupertinoSwitch",
        "Dropdown",
        "Icon",
        "IconButton",
        "Image",
        "Markdown",
        "NavigationBar",
        "NavigationRail",
        "ProgressBar",
        "ProgressRing",
        "RadioGroup",
        "SearchBar",
        "Slider",
        "Switch",
        "Tabs",
        "Text",
        "TextField",
        "TextSpan",
    }


@pytest.mark.parametrize(
    "control_type",
    [
        control_type
        for control_type, spec in _CONTROL_BINDINGS.items()
        if spec.event is not None
    ],
)
def test_registered_input_events_pull_state_and_preserve_handler(
    control_type: type[Any],
) -> None:
    spec = _CONTROL_BINDINGS[control_type]
    initial, replacement = _values(control_type, spec.attribute)
    calls: list[bool] = []

    class Model(FletModel):
        @data
        def state(self):
            return initial

    model = Model()
    control = _build(control_type, None)
    setattr(control, spec.event, lambda: calls.append(True))
    model.state.bind(control)
    setattr(control, spec.attribute, replacement)
    getattr(control, spec.event)()

    assert model.state.value == replacement
    assert calls == [True]


def test_dropdown_defaults_to_selected_value_not_options() -> None:
    class Model(FletModel):
        @data
        def selected(self) -> str:
            return "red"

    model = Model()
    options = [
        ft.DropdownOption(key="red", text="Red"),
        ft.DropdownOption(key="blue", text="Blue"),
    ]
    dropdown = ft.Dropdown(options=options, ref=model.selected)

    dropdown.value = "blue"
    dropdown.on_select()

    assert model.selected.value == "blue"
    assert dropdown.options is options


def test_datapoint_is_a_real_flet_ref_with_explicit_read_semantics() -> None:
    class Model(FletModel):
        @data
        def title(self) -> str:
            return "Hello"

    model = Model()
    field = ft.TextField(ref=model.title)

    assert isinstance(model.title, ft.Ref)
    assert model.title.current is field
    assert model.title.value == "Hello"
    assert field.value == "Hello"
    with pytest.raises(
        TypeError,
        match=r"use '\.value' for state or '\.current' for the bound control",
    ):
        model.title()


def test_computed_bindings_are_one_way_even_on_input_controls() -> None:
    class Model(FletModel):
        @data
        def source(self) -> str:
            return "derived"

        @computed
        def output(self) -> str:
            return self.source.value.upper()

    calls: list[str] = []
    model = Model()
    field = ft.TextField(on_change=lambda: calls.append("changed"))
    model.output.bind(field)

    assert field.value == "DERIVED"
    assert field.on_change is not None
    field.value = "user"
    field.on_change()

    assert calls == ["changed"]
    assert model.output.value == "DERIVED"


def test_structural_tree_bindings_must_be_explicit() -> None:
    class Model(FletModel):
        @data
        def children(self) -> list[ft.Control]:
            return [ft.Text("One")]

    model = Model()
    column = ft.Column()

    with pytest.raises(Exception, match="No safe default"):
        model.children.bind(column)

    model.children.bind(column, "controls")
    assert column.controls == model.children.value


def test_registered_mro_applies_to_control_subclasses() -> None:
    @ft.control
    class CustomDropdown(ft.Dropdown):
        pass

    class Model(FletModel):
        @data
        def selected(self) -> str:
            return "red"

    model = Model()
    dropdown = CustomDropdown(
        options=[ft.DropdownOption(key="red", text="Red")],
        ref=model.selected,
    )

    dropdown.value = "blue"
    dropdown.on_select()

    assert model.selected.value == "blue"
