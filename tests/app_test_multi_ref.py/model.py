import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletModel, data
import flet as ft

class TaskModel(FletModel):
    @data
    def new_task(self):
        return ""

    @data
    def tasks(self):
        return []

    @data.RefOnly
    def title(self):
        return "title"
    
    @data
    def check(self):
        return False