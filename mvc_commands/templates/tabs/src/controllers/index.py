from dataclasses import dataclass

import flet as ft
from models.index import IndexModel


@dataclass
class IndexController:
    model: IndexModel

    def select_tab(self, event: ft.Event[ft.Tabs]) -> None:
        """Keep the selected tab in the model."""
        self.model.selected_index.set(event.control.selected_index)
