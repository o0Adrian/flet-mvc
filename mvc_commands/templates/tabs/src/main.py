import flet as ft
from controllers.index import IndexController
from models.home import HomeModel
from models.index import IndexModel
from models.settings import SettingsModel
from views.index import IndexView


def main(page: ft.Page) -> None:
    index_model = IndexModel()
    index_controller = IndexController(index_model)
    home_model = HomeModel()
    settings_model = SettingsModel()

    page.title = "Flet MVC Tabs"
    page.padding = 24
    page.render(
        IndexView,
        index_model,
        index_controller,
        home_model,
        settings_model,
    )


if __name__ == "__main__":
    ft.run(main)
