import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletView
import flet as ft

class TaskView(FletView):
    def __init__(self, controller, model):
        view = [
            ft.Text(
                "Task List",
                size=36,
                weight="w700",
            ),
            ft.ListView(
                ref=model.tasks,
                expand=True
            ),
            ft.ListView(
                ref=model.tasks,
                expand=True
            ),
            ft.ListView(
                expand=True
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        ref=model.new_task,
                        hint_text="Enter new task",
                        border=ft.InputBorder.NONE,
                        filled=True,
                        expand=True,
                        on_submit=controller.add_task
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("Add Task", size=18, weight="w700"),
                        on_click=controller.add_task,
                        bgcolor="#f7ce7c",
                        color="black",
                        width=220,
                        height=50,
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
        ]
        super().__init__(model, view, controller)
