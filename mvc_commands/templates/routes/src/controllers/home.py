from dataclasses import dataclass

import flet as ft
from models.home import HomeModel


@dataclass
class HomeController:
    page: ft.Page
    model: HomeModel

    def navigate_secondary(self, _event=None) -> None:
        self.page.navigate("/secondary")
