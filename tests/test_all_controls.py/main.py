from controller import TestController
from view import TestView
from model import TestModel

import flet as ft

def main(page):
    # MVC set-up
    model = TestModel()
    controller = TestController(page, model)
    model.controller = controller  # important to set controller in model (in needed) before view
    view = TestView(controller, model)
    
    # Settings
    
    # NOTE: adding in setting, but remember controller has access to page too; so
    # you can set this values in a function of the controller, which I recommend to do.
    page.appbar = view.app_bar
    page.overlay.append(view.audio)
    page.overlay.append(view.bottom_sheet)
    page.overlay.append(view.file_picker)
    page.banner = view.banner
    page.snack_bar = view.snack_bar
    page.floating_action_button = view.fab
    
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.on_keyboard_event = controller.on_keyboard
    page.theme_mode = "light"
    page.padding = 20
    page.window_width = 600
    page.window_always_on_top = True
    page.window_resizable = False
    page.window_height = 500
    
    # Run
    page.add(
        *view.content
    )

ft.app(target=main)
