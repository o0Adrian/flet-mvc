import flet as ft
from models.home import HomeModel


@ft.component
def HomeView(model: HomeModel) -> ft.Control:
    return ft.Text(model.content.value)
