import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletController, ADVICE
import flet as ft

class TaskController(FletController):
    def add_task(self, e):
        new_task = self.model.new_task()
        if new_task.strip() == "":
            self.alert("Task can't be empty!!", ADVICE)
            return
        self.model.tasks.append(
            ft.Row(
                controls=[
                    ft.Checkbox(ref=self.model.check),
                    ft.Text(new_task, size=18),
                ]
            ),
        )
        # IMPORTANT: Check changes it's value and modifies the node, but to change the UI we still need to modify the older
        # checkboxes, a possible solition would be iterating over self.model.check.current which will return a list of currents.
        # and then set the value self.model.check.current.value = self.model.check(). Also.. there is already an on_change method...
        self.model.check.set_value(self.model.check())
        self.model.new_task.set_value("")
        self.update()

    def on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "D" and e.alt and e.shift:
            self.page.show_semantics_debugger = not self.page.show_semantics_debugger
            self.page.update()
