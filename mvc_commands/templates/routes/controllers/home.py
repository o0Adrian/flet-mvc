from flet_mvc import FletController


class HomeController(FletController):
    def navigate_secondary(self, e):
        """Example route change"""
        self.page.go("/secondary")
