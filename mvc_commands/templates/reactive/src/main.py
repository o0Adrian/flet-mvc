import flet as ft
from components.counter import CounterComponent
from models.counter import CounterModel


@ft.component
def App(model: CounterModel) -> ft.Control:
    """Combine a class-based component with a declarative computed value."""
    return ft.Column(
        controls=[
            ft.Text("Reactive counter", size=30, weight=ft.FontWeight.BOLD),
            CounterComponent(model=model),
            ft.Text(model.message.value, size=18, color=ft.Colors.BLUE),
        ],
        spacing=16,
    )


def main(page: ft.Page) -> None:
    model = CounterModel()

    page.title = "Flet MVC Reactive"
    page.padding = 24
    page.render(App, model)


if __name__ == "__main__":
    ft.run(main)
