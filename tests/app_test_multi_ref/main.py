from controller import TaskController
from view import TaskView
from model import TaskModel

import flet as ft

def main(page):
    # MVC set-up
    model = TaskModel()
    controller = TaskController(page, model)
    view = TaskView(controller, model)
    
    # model operations
    model.controller = controller
    # model.create_tasks()
    
    # Settings
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.on_keyboard_event = controller.on_keyboard
    page.theme_mode = "light"
    page.padding = 20
    page.window_width = 580
    page.window_always_on_top = True
    page.window_resizable = False
    page.window_height = 500
    
    # Run
    page.add(
        *view.content
    )

ft.app(target=main)
