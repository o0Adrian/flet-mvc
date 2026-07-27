from flet_mvc import FletModel, data


class Model(FletModel):
    @data
    def title(self) -> str:
        return "Hello, World!"
