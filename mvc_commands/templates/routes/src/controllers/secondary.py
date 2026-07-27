from dataclasses import dataclass

import flet as ft
from models.secondary import SecondaryModel


@dataclass
class SecondaryController:
    page: ft.Page
    model: SecondaryModel

    def return_home(self, _event=None) -> None:
        self.page.navigate("/")
