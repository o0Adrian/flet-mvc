from flet_mvc import data
from .index import IndexModel
import flet as ft


class HomeModel(IndexModel):
    @data
    def example_content(self):
        return "\n\n\tThis is the Home Tab!"
