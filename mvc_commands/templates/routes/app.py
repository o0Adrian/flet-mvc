import flet as ft
from flet_mvc import RouteHandler

# Models
from models.home import HomeModel
from models.secundary import SecundaryModel

# Views
from views.home import HomeView
from views.secundary import SecundaryView

# Controllers
from controllers.home import HomeController
from controllers.secundary import SecundaryController


def main(page: ft.Page):
    ### MVC set-up ###
    routes_handler = RouteHandler(page)

    # main view
    home_model = HomeModel()
    home_controller = HomeController(page, home_model)
    home_model.controller = home_controller
    home_view = HomeView(home_controller, home_model)
    routes_handler.register_route("/", home_view.content)

    # secundary view
    secundary_model = SecundaryModel()
    secundary_controller = SecundaryController(page, secundary_model)
    secundary_model.controller = secundary_controller
    secundary_view = SecundaryView(secundary_controller, secundary_model)
    routes_handler.register_route("/secundary", secundary_view.content)

    ### Page Settings ###
    theme = ft.Theme()
    platforms = ["android", "ios", "macos", "linux", "windows"]
    for platform in platforms:  # Removing animation on route change.
        setattr(theme.page_transitions, platform, ft.PageTransitionTheme.NONE)

    page.title = ""
    page.theme = theme
    page.on_route_change = routes_handler.route_change  # route change

    # Run
    page.go(page.route)


ft.app(target=main)
