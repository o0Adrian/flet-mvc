from flet_mvc import FletModel, data


class SettingsModel(FletModel):
    @data
    def content(self) -> str:
        return "This is the settings tab."
