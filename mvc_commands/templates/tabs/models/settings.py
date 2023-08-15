from flet_mvc import FletModel, data
import flet as ft


class SettingsModel(FletModel):
    @data
    def example_content(self):
        return "\n\n\tThis is the settings tab!"
