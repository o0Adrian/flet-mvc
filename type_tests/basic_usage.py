"""Consumer-side typing contract checked by mypy, not executed by pytest."""

from dataclasses import dataclass

import flet as ft
from typing_extensions import assert_type

from flet_mvc import (
    Datapoint,
    FletComponent,
    FletModel,
    computed,
    data,
    receive,
    send,
    use_datapoint,
)


class TypedModel(FletModel):
    @data
    def count(self) -> int:
        return 1

    @data(bind="value")
    def title(self) -> str:
        return "Typed"

    @data.depends_on("count")
    def ratio(self) -> float:
        return float(self.count.value)

    @computed
    def doubled(self) -> int:
        return self.count.value * 2

    @computed(bind="value")
    def summary(self) -> str:
        return f"{self.title.value}: {self.doubled.value}"

    @computed.depends_on("count")
    def parity(self) -> bool:
        return self.count.value % 2 == 0


model = TypedModel()
point: Datapoint[int] = model.count
assert_type(model.count, Datapoint[int])
assert_type(model.title, Datapoint[str])
assert_type(model.ratio, Datapoint[float])
assert_type(model.doubled, Datapoint[int])
assert_type(model.summary, Datapoint[str])
assert_type(model.parity, Datapoint[bool])

assert_type(model.count.value, int)
assert_type(model.count.set(2), None)
assert_type(model.count.update(lambda value: value + 1), int)
assert_type(use_datapoint(model.count), int)
model.count.set("invalid")  # type: ignore[arg-type]

assert_type(TypedModel.count, data[int])
assert_type(TypedModel.title, data[str])
assert_type(TypedModel.ratio, data[float])
assert_type(TypedModel.doubled, computed[int])
assert_type(TypedModel.summary, computed[str])
assert_type(TypedModel.parity, computed[bool])

text_ref: ft.Ref[ft.BaseControl] = model.title
field = ft.TextField(ref=model.title)
assert_type(field, ft.TextField)


@dataclass
class TypedController:
    page: ft.Page
    model: TypedModel

    def increment(self, _event=None) -> None:
        self.model.count.set(self.model.count.value + 1)


def create_controller(page: ft.Page) -> TypedController:
    return TypedController(page, model)


@ft.component
def TypedView(model: TypedModel) -> ft.Control:
    return ft.Text(str(model.doubled.value))


@ft.control
class TypedComponent(FletComponent):
    @send(TypedModel.count)
    def increment(self, _event=None) -> int:
        return self.model.count.value + 1

    @receive(TypedModel.doubled)
    def show_doubled(self, value: int) -> None:
        pass
