"""
Flet Base Controller Class
"""

from typing import Type
import flet as ft
from .alert import ERROR, WARNING, SUCCESS, ADVICE, INFO
from .model import FletModel


class FletController:
    def __init__(self, page: ft.Page, model: Type[FletModel]):
        self.page = page
        self.model = model

    def update(self):
        """Updates the page by using self.update() instead of self.page.update()"""
        self.page.update()

    def alert(self, msg="", alert_type=ERROR):
        """Show Alert"""
        if alert_type == ERROR:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.colors.WHITE),
                        ft.Text(msg),
                    ],
                ),
                bgcolor=ft.colors.ERROR,
            )
            self.page.snack_bar.open = True
            self.update()

        elif alert_type == SUCCESS:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.WHITE),
                        ft.Text(msg),
                    ],
                ),
                action="OK",
                action_color=ft.colors.BLACK,
                bgcolor=ft.colors.GREEN_300,
            )
            self.page.snack_bar.open = True
            self.update()

        elif alert_type == ADVICE:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(msg),
                action="Understood",
                action_color=ft.colors.BLUE_200,
            )
            self.page.snack_bar.open = True
            self.update()

        elif alert_type == INFO:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.INFO_OUTLINED, color=ft.colors.WHITE),
                        ft.Text(msg),
                    ],
                ),
                bgcolor=ft.colors.BLUE_200,
            )
            self.page.snack_bar.open = True
            self.update()

        elif alert_type == WARNING:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.WHITE),
                        ft.Text(msg),
                    ],
                ),
                action="OK",
                action_color=ft.colors.BLACK,
                bgcolor=ft.colors.AMBER,
            )
            self.page.snack_bar.open = True
            self.update()
