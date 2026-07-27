import flet as ft
from controllers.main import Controller
from models.main import Model
from views.main import MainView


def main(page: ft.Page) -> None:
    model = Model()
    controller = Controller(model)

    page.title = "Flet MVC"
    page.padding = 24
    page.render(MainView, model, controller)


if __name__ == "__main__":
    ft.run(main)
