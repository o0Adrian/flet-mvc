import flet as ft
from controllers.main import Controller
from models.main import Model


@ft.component
def MainView(model: Model, controller: Controller) -> ft.Control:
    """Render again whenever the observable model changes."""
    return ft.Column(
        controls=[
            ft.Text(model.title.value, size=30),
            ft.Button(
                content="Toggle title",
                icon=ft.Icons.REFRESH,
                key="toggle-title",
                on_click=controller.toggle_title,
            ),
        ],
        spacing=16,
    )
