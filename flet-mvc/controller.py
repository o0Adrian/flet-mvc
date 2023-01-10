"""
Flet Base Controller Class
"""

import flet as ft

class FletController():
    def __init__(self, page: ft.Page, model):
        self.page = page
        self.model = model
        
    # def append_control(self, component, control):
    #     """ Appends control to a container control """
    #     component.current.controls.append(control)
        
    def update(self):
        """ Updates the page by using self.update() instead of self.page.update() """
        self.page.update()
        
    # def focus(self, control):
    #     """ Gives focus to a control """
    #     getattr(self.model, control).current.focus()
