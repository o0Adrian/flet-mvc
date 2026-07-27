from flet_mvc import FletModel, data


class IndexModel(FletModel):
    @data
    def title(self) -> str:
        return "Tabs template"

    @data
    def selected_index(self) -> int:
        return 0
