from dataclasses import dataclass

from models.main import Model


@dataclass
class Controller:
    model: Model

    def toggle_title(self, _event=None) -> None:
        """Toggle the title; the observable model re-renders the view."""
        title = (
            "Hello from Flet MVC!"
            if self.model.title.value == "Hello, World!"
            else "Hello, World!"
        )
        self.model.title.set(title)
