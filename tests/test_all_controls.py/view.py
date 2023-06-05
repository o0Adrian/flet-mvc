import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletView
import flet as ft

class TaskView(FletView):
    def __init__(self, controller, model):
        self.app_bar = ft.AppBar(
            ref=model.AppBar,
            leading=ft.Icon(ft.icons.PALETTE),
            leading_width=40,
            title=ft.Text("0. AppBar | This app contains all controls with refs"),
            center_title=False,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        self.audio = ft.Audio(ref=model.Audio)
        
        self.banner = ft.Banner(
            ref=model.Banner,
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=40),
            actions=[
                ft.TextButton("Retry", on_click=controller.close_banner),
                ft.TextButton("Ignore", on_click=controller.close_banner),
                ft.TextButton("Cancel", on_click=controller.close_banner),
            ],
        )
        
        view = [
            ft.ListView(
                controls=[
                    # 1. AlertDialog
                    ft.Text("1. AlertDialog"),
                    ft.AlertDialog(ref=model.Dialog, title=ft.Text("Test Title")),
                    ft.ElevatedButton("Open Dialog", on_click=controller.open_dialog),

                    # 2. AnimatedSwitcher
                    ft.Text("\n2. Animated Switcher"),
                    ft.AnimatedSwitcher(
                        ref=model.AnimatedSwitcher,
                        transition=ft.AnimatedSwitcherTransition.SCALE,
                        duration=500,
                        reverse_duration=100,
                        switch_in_curve=ft.AnimationCurve.BOUNCE_OUT,
                        switch_out_curve=ft.AnimationCurve.BOUNCE_IN,
                    ),
                    ft.ElevatedButton("Animate!", on_click=controller.animate),
                    
                    # 3. Audio
                    ft.Text("\n3. Audio"),
                    ft.ElevatedButton("Play", on_click=lambda _: self.audio.play()),
                    ft.ElevatedButton("Stop playing", on_click=lambda _: self.audio.pause()),
                    
                    # 4. Banner
                    ft.Text("\n4. Banner"),
                    ft.ElevatedButton("Show Banner", on_click=controller.open_banner)
                    
                ],
                expand=True
            )
        ]
        super().__init__(model, view, controller)