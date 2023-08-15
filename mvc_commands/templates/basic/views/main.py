from flet_mvc import FletView
import flet as ft


class MainView(FletView):
    def __init__(self, controller, model):
        view = [
            ft.Text(ref=model.example_title, size=30)
        ]  # List of flet controls
        super().__init__(model, view, controller)
