from flet_mvc import FletController


class HomeController(FletController):
    def navigate_secundary(self, e):
        """Example route change"""
        self.page.go("/secundary")
