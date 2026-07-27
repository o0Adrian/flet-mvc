from flet_mvc import FletModel, data


class HomeModel(FletModel):
    @data
    def title(self) -> str:
        return "This is the home view."
