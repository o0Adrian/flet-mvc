"""
Flet Base View Class
"""
from .controller import FletController

class FletView():
    def __init__(self, model = None, content = [], controller: FletController = None):
        self.controller = controller
        self.model = model
        self.content = content