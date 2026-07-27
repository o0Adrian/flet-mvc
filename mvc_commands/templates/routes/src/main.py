import flet as ft
from controllers.home import HomeController
from controllers.secondary import SecondaryController
from models.home import HomeModel
from models.secondary import SecondaryModel
from views.home import HomeView
from views.secondary import SecondaryView


def main(page: ft.Page) -> None:
    home_model = HomeModel()
    home_controller = HomeController(page, home_model)

    secondary_model = SecondaryModel()
    secondary_controller = SecondaryController(page, secondary_model)

    @ft.component
    def HomeRoute() -> ft.View:
        return ft.View(
            route="/",
            can_pop=False,
            appbar=ft.AppBar(title=ft.Text("Home")),
            controls=[HomeView(home_model, home_controller)],
            padding=24,
        )

    @ft.component
    def SecondaryRoute() -> ft.View:
        return ft.View(
            route="/secondary",
            appbar=ft.AppBar(title=ft.Text("Secondary")),
            controls=[SecondaryView(secondary_model, secondary_controller)],
            padding=24,
        )

    @ft.component
    def NotFound() -> ft.Control:
        return ft.Column(
            controls=[
                ft.Text("That page does not exist.", size=24),
                ft.Button(
                    content="Return home",
                    key="not-found-home",
                    on_click=lambda _event: page.navigate("/"),
                ),
            ],
            spacing=16,
        )

    @ft.component
    def App() -> ft.Control:
        return ft.Router(
            routes=[
                ft.Route(
                    component=HomeRoute,
                    children=[
                        ft.Route(
                            path="secondary",
                            component=SecondaryRoute,
                        ),
                    ],
                ),
            ],
            not_found=NotFound,
            manage_views=True,
        )

    page.title = "Flet MVC Routes"
    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
        )
    )
    page.render_views(App)


if __name__ == "__main__":
    ft.run(main)
