from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import flet as ft

from flet_mvc import (
    DataTableAdapter,
    FletComponent,
    FletModel,
    computed,
    data,
    send,
    use_datapoint,
)


class IntegrationModel(FletModel):
    @data
    def query(self):
        return "initial"

    @data
    def count(self):
        return 0

    @computed
    def summary(self):
        return f"{self.query.value}:{self.count.value}"


@ft.control
class CounterComponent(FletComponent):
    def init(self):
        super().init()
        self.controls = [
            ft.Text("FletComponent ready", key="component-ready"),
            ft.Button(
                content="Component +1",
                key="component-increment",
                on_click=self.increment,
            ),
        ]

    @send(IntegrationModel.count)
    def increment(self, _event=None):
        return self.model.count.value + 1


@dataclass(frozen=True)
class _Resources:
    model: IntegrationModel


_resources_context: Any = ft.create_context(None)


def _resources() -> _Resources:
    resources = ft.use_context(_resources_context)
    if resources is None:
        raise RuntimeError("Integration resources provider is missing")
    return resources


@ft.component
def QueryField(point):
    value = use_datapoint(point)
    return ft.TextField(
        value=value,
        key="query",
        on_change=lambda event: point.set(event.control.value),
    )


@ft.component
def Summary(point):
    return ft.Text(use_datapoint(point), key="summary")


@ft.component
def DeclarativeReady():
    ready, set_ready = ft.use_state(False)
    ft.use_effect(lambda: set_ready(True), dependencies=[])
    return ft.Text("Declarative ready", visible=ready, key="declarative-ready")


@ft.component
def Home():
    page = ft.context.page
    resources = _resources()
    table, _ = ft.use_state(
        lambda: DataTableAdapter().load_records(
            [
                {"name": "Ada", "score": 98},
                {"name": "Grace", "score": 100},
            ]
        )
    )
    tabs = ft.Tabs(
        length=2,
        height=160,
        content=ft.Column(
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="State"),
                        ft.Tab(label="About"),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Text("State panel"),
                        ft.Text("Integration ready"),
                    ],
                ),
            ]
        ),
    )
    return ft.Column(
        controls=[
            QueryField(resources.model.query),
            Summary(resources.model.summary),
            ft.Button(
                content="Set from model",
                key="set-from-model",
                on_click=lambda _event: resources.model.query.set("server"),
            ),
            CounterComponent(model=resources.model),
            table.control,
            tabs,
            ft.Button(
                content="Open details",
                key="open-details",
                on_click=lambda _event: page.navigate("/details"),
            ),
            DeclarativeReady(),
        ]
    )


@ft.component
def Details():
    page = ft.context.page
    return ft.Column(
        controls=[
            ft.Text("Details route", key="details-title"),
            ft.Button(
                content="Return home",
                key="return-home",
                on_click=lambda _event: page.navigate("/"),
            ),
        ]
    )


_routes = [
    ft.Route(index=True, component=Home),
    ft.Route(path="details", component=Details),
]


@ft.component
def App():
    resources, _ = ft.use_state(lambda: _Resources(IntegrationModel()))
    return _resources_context(resources, lambda: ft.Router(_routes))


def main(page: ft.Page):
    page.title = "flet-mvc integration"
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
