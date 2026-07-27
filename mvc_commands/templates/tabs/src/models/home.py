from flet_mvc import FletModel, data


class HomeModel(FletModel):
    @data
    def content(self) -> str:
        return "This is the home tab."
