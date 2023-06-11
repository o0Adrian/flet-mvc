import sys
import os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from flet_mvc import FletController, ADVICE
import flet as ft


class TestController(FletController):
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
        self.model.PopupMenuButton.set_value(
            [
                ft.PopupMenuItem(text="Changed Field"),
                ft.PopupMenuItem(),  # divider
                ft.PopupMenuItem(text="True Checked", checked=True),
            ]
        )
        self.update()

    def close_banner(self, e):
        """4. Banner"""
        self.page.banner.open = False
        self.update()

    def open_banner(self, e):
        """4. Banner"""
        self.page.banner.open = True
        self.update()

    def close_bs(self, e):
        """5. Bottom Sheet"""
        self.model.BottomSheet.current.open = False
        self.update()

    def open_bs(self, e):
        """5. Bottom Sheet"""
        self.model.BottomSheet.current.open = True
        self.update()

    def bs_dismissed(self, e):
        """5. Bottom Sheet"""
        print("Dismissed!")

    def drag_will_accept(self, e):
        """14. Draggable"""
        e.control.content.border = ft.border.all(
            2, ft.colors.BLACK45 if e.data == "true" else ft.colors.RED
        )
        e.control.update()

    def drag_accept(self, e: ft.DragTargetAcceptEvent):
        """14. Draggable"""
        src = self.page.get_control(e.src_id)
        e.control.content.bgcolor = src.content.bgcolor
        e.control.content.border = None
        e.control.update()

    def drag_leave(self, e):
        """14. Draggable"""
        e.control.content.border = None
        e.control.update()

    def button_clicked(self, e):
        """50. Snackbar"""
        self.model.SnackBar.set_value(
            ft.Text(f"Dropdown value is:  {self.model.Dropdown.current.value}")
        )
        self.page.snack_bar.open = True
        self.page.update()

    def see_file_on_close(self, e: ft.FilePickerResultEvent):
        """18. FilePicker"""
        print(e.files)

    def see_file(self, e):
        """18. FilePicker"""
        # Using the ref object
        # TODO: Maybe I could add all this methods in the datapoint (FilePicker.files),
        # and just raise exception if it's not a supported component to use that method.
        # others: icon, set_options, columns, rows, set_dataframe
        print(
            self.model.FilePicker.current.result.files
            if self.model.FilePicker.current.result
            else "No file selected"
        )

    def fab_pressed(self, e):
        """22. Floating Action Button"""
        self.alert("FAB Pressed", alert_type="info")

    def on_pan_update(self, e: ft.DragUpdateEvent):
        """23. Floating Action Button"""
        e.control.top = max(0, e.control.top + e.delta_y)
        e.control.left = max(0, e.control.left + e.delta_x)
        e.control.update()
        
    def icon_button_click(self, e):
        """27. Floating Action Button"""
        self.alert("Icon button Pressed", alert_type="info")