import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletModel, data
import flet as ft

class TaskModel(FletModel):
    @data
    def AppBar(self):
        """0. App Bar | Attribute: actions """
        return [
            ft.IconButton(ft.icons.WB_SUNNY_OUTLINED),
            ft.IconButton(ft.icons.FILTER_3),
            ft.PopupMenuButton(
                ref=self.PopupMenuButton
            ),
        ]

    # NOTE: When the attribute of a Cotnrol is content, sometimes can be a list
    # sometimes a single control, and sometimes both. Inconsistency of flet.
    @data
    def Dialog(self):
        """1. Dialog datapoint | Attribute: content"""
        return []
    
    @data
    def AnimatedSwitcher(self):
        """2. Animated Switcher | Attribute: content"""
        return ft.Container(
            ft.Text("Hello!", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            alignment=ft.alignment.center,
            width=200,
            height=200,
            bgcolor=ft.colors.GREEN,
        )
    
    @data
    def Audio(self):
        """3. Audio | Attribute: src"""
        return "https://luan.xyz/files/audio/ambient_c_motion.mp3"
    
    @data
    def Banner(self):
        """3. Banner | Attribute: content"""
        return ft.Text(
            "4. Banner. Imagine this is an error. What would you like me to do?"
        )
        
    @data
    def PopupMenuButton(self):
        """39. PopupMenuButton | Attribute: items"""
        return [
            ft.PopupMenuItem(text="39. PopupMenuButton"),
            ft.PopupMenuItem(),  # divider
            ft.PopupMenuItem(
                ref=self.PopupMenuItem, checked=False
            ),
        ]
        
    @data
    def PopupMenuItem(self):
        """38. PopupMenuItem | Attribute: text"""
        return "38. PopupMenuItem"