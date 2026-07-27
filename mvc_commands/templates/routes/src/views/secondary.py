import flet as ft
from controllers.secondary import SecondaryController
from models.secondary import SecondaryModel


@ft.component
def SecondaryView(
    model: SecondaryModel,
    controller: SecondaryController,
) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(model.title.value, size=30),
            ft.Button(
                content="Return home",
                icon=ft.Icons.ARROW_BACK,
                key="return-home",
                on_click=controller.return_home,
            ),
        ],
        spacing=16,
    )
