import flet as ft
from models.counter import CounterModel

from flet_mvc import FletComponent, receive, send


@ft.control
class CounterComponent(FletComponent):
    """A control that reads from and writes to the model."""

    def init(self) -> None:
        super().init()
        self.count_text = ft.Text(size=40)
        self.controls = [
            self.count_text,
            ft.Button(
                content="Add one",
                icon=ft.Icons.ADD,
                key="increment",
                on_click=self.increment,
            ),
        ]

    @receive(CounterModel.count)
    def show_count(self, value: int) -> None:
        """Run whenever the count datapoint changes."""
        self.count_text.value = str(value)

    @send(CounterModel.count)
    def increment(self, _event=None) -> int:
        """Return the next value; @send publishes it to the model."""
        return self.model.count.value + 1
