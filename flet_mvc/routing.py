import flet as ft


class RouteHandler:
    def __init__(self, page: ft.Page, fallback_content: list = None):
        self.page = page
        self.routes: dict[str, list] = {}
        self.fallback = fallback_content

    def register_route(self, route: str, view_content: list):
        self.routes[route] = view_content

    def route_change(self, e):
        self.page.views.clear()
        view_content = self.routes.get(e.route, self.fallback)
        self.page.views.append(ft.View(e.route, view_content))
        self.page.update()
