from flet_mvc import FletModel, data


class SecondaryModel(FletModel):
    @data
    def title(self) -> str:
        return "This is the secondary view."
