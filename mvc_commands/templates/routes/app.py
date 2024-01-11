import flet as ft
from flet_mvc import RouteHandler

# Models
from models.home import HomeModel
from models.secondary import SecondaryModel

# Views
from views.home import HomeView
from views.secondary import SecondaryView

# Controllers
from controllers.home import HomeController
from controllers.secondary import SecondaryController


def main(page: ft.Page):
    ### MVC set-up ###
    routes_handler = RouteHandler(page)

    # main view
    home_model = HomeModel()
    home_controller = HomeController(page, home_model)
    home_model.controller = home_controller
    home_view = HomeView(home_controller, home_model)
    routes_handler.register_route("/", home_view.content)

    # secondary view
    secondary_model = SecondaryModel()
    secondary_controller = SecondaryController(page, secondary_model)
    secondary_model.controller = secondary_controller
    secondary_view = SecondaryView(secondary_controller, secondary_model)
    routes_handler.register_route("/secondary", secondary_view.content)

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
