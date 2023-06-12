"""
Flet Base View Class
"""
from .controller import FletController


class FletView:
    def __init__(
        self, model=None, content: list = None, controller: FletController = None
    ):
        self.controller = controller
        self.model = model
        self.content = content

        # Flet sets the values/content of a control before it is actually instanciated [shown in ui],
        # that is why we call them again here so we can set the control with our default value.
        for ref_obj in self.model.ref_objs:
            ref_obj.reset()
