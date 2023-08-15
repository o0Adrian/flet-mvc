from flet_mvc import FletModel, data
import flet as ft


class Model(FletModel):
    @data
    def example_title(self):
        return "Hello World"
