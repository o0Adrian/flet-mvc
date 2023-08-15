from flet_mvc import FletView
import flet as ft


class SettingsView(FletView):
    def __init__(self, controller, model):
        view = [
            ft.Text(ref=model.example_content),
        ]
        super().__init__(model, view, controller)
