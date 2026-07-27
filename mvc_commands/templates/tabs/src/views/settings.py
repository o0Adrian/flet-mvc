import flet as ft
from models.settings import SettingsModel


@ft.component
def SettingsView(model: SettingsModel) -> ft.Control:
    return ft.Text(model.content.value)
