from flet_mvc import FletController


class SecundaryController(FletController):
    def return_home(self, e):
        """Example route change"""
        self.page.go("/")