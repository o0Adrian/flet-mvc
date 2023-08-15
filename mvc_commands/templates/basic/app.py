import flet as ft
from controllers.main import Controller
from views.main import MainView
from models.main import Model

def main(page: ft.Page):
    # MVC set-up
    model = Model()
    controller = Controller(page, model)
    model.controller = controller
    view = MainView(controller, model)

    # Settings
    page.title = ""

    # Run
    page.add(
        *view.content
    )

ft.app(target=main)