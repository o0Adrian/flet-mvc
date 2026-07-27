import flet as ft
from controllers.home import HomeController
from models.home import HomeModel


@ft.component
def HomeView(model: HomeModel, controller: HomeController) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(model.title.value, size=30),
            ft.Button(
                content="Go to secondary view",
                icon=ft.Icons.ARROW_FORWARD,
                key="go-secondary",
                on_click=controller.navigate_secondary,
            ),
        ],
        spacing=16,
    )
