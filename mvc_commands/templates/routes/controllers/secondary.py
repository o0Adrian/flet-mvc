from flet_mvc import FletController


class SecondaryController(FletController):
    def return_home(self, e):
        """Example route change"""
        self.page.go("/")
