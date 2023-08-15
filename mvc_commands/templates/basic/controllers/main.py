from flet_mvc import FletController


class Controller(FletController):
    def example_function(self, e=None):
        """Example of all the operations that you can perform on a model's datapoint"""
        self.model.example()  # value = "Hello World"
        self.model.example.set_value("Title")  # value = "Title"
        self.model.example.has_set_value()  # True
        self.model.example.reset()  # value = "Hello World"
        self.model.set_default("Hello Flet")  # value = "Hello World"
        self.model.example.reset()  # value = "Hello Flet"
        self.model.example.has_set_value()  # False

        self.update()  # flet page.update() command
