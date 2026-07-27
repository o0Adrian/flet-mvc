from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import flet as ft

import flet_mvc
from flet_mvc import FletModel, data


class DemoModel(FletModel):
    @data
    def title(self) -> str:
        return "Hello"


@dataclass
class DemoController:
    page: object
    model: DemoModel


def test_applications_can_use_plain_python_controllers() -> None:
    page = object()
    model = DemoModel()

    controller = DemoController(page, model)

    assert controller.page is page
    assert controller.model is model


def test_plain_controller_does_not_wrap_native_flet_features() -> None:
    controller = DemoController(object(), DemoModel())

    for removed in (
        "update",
        "alert",
        "error",
        "success",
        "warning",
        "info",
        "advice",
        "dropdown_option",
        "dropdown_options",
    ):
        assert not hasattr(controller, removed)


def test_root_api_is_small_and_intentional() -> None:
    assert set(flet_mvc.__all__) == {
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
    }


def test_removed_framework_layers_are_not_shipped() -> None:
    package = Path(flet_mvc.__file__).parent

    assert not (package / "alert.py").exists()
    assert not (package / "controller.py").exists()
    assert not (package / "routing.py").exists()
    assert not (package / "view.py").exists()
    assert not hasattr(flet_mvc, "FletController")
    assert not hasattr(flet_mvc, "RouteHandler")
    assert not hasattr(flet_mvc, "FletView")


def test_flet_native_types_remain_the_application_primitives() -> None:
    assert ft.View is not None
    assert ft.Router is not None
    assert ft.Observable is not None
