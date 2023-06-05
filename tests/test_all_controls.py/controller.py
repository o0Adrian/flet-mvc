import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletController, ADVICE
import flet as ft

class TaskController(FletController):
    def on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "D" and e.alt and e.shift:
            self.page.show_semantics_debugger = not self.page.show_semantics_debugger
            self.page.update()
            
    def open_dialog(self, e):
        """1. AlertDialog"""
        self.page.Dialog = self.model.Dialog.current
        self.model.Dialog.current.open = True
        self.page.update()
        
    def animate(self, e):
        """2. Animated Switcher"""
        if self.model.AnimatedSwitcher.has_changed():
            self.model.AnimatedSwitcher.reset()
        else:
            self.model.AnimatedSwitcher.set_value(
                ft.Container(
                    ft.Text("Bye!", size=50),
                    alignment=ft.alignment.center,
                    width=200,
                    height=200,
                    bgcolor=ft.colors.YELLOW,
                )
            )
            
        # This shouldn't be here, but just testing that a refdatapoint can change when containing other refdatapoint
        self.model.PopupMenuButton.set_value([
            ft.PopupMenuItem(text="Changed Field"),
            ft.PopupMenuItem(),  # divider
            ft.PopupMenuItem(
                text="True Checked", checked=True
            ),
        ])
        self.update()
        
    def close_banner(self, e):
        """4. Banner"""
        self.page.banner.open = False
        self.update()
        
    def open_banner(self, e):
        """4. Banner"""
        self.page.banner.open = True
        self.update()