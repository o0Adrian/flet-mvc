import flet as ft
from controllers.index import IndexController
from models.home import HomeModel
from models.index import IndexModel
from models.settings import SettingsModel

from views.home import HomeView
from views.settings import SettingsView


@ft.component
def IndexView(
    model: IndexModel,
    controller: IndexController,
    home_model: HomeModel,
    settings_model: SettingsModel,
) -> ft.Control:
    tabs = ft.Tabs(
        length=3,
        selected_index=model.selected_index.value,
        animation_duration=200,
        expand=True,
        on_change=controller.select_tab,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    scrollable=False,
                    tab_alignment=ft.TabAlignment.FILL,
                    tabs=[
                        ft.Tab(label="Home", icon=ft.Icons.HOME, key="home-tab"),
                        ft.Tab(
                            label="Settings",
                            icon=ft.Icons.SETTINGS,
                            key="settings-tab",
                        ),
                        ft.Tab(
                            label="About",
                            icon=ft.Icons.INFO_OUTLINE,
                            key="about-tab",
                        ),
                    ],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(
                            padding=24,
                            content=HomeView(home_model),
                        ),
                        ft.Container(
                            padding=24,
                            content=SettingsView(settings_model),
                        ),
                        ft.Container(
                            padding=24,
                            content=ft.Text("Add your next view here."),
                        ),
                    ],
                ),
            ],
        ),
    )
    return ft.Column(
        expand=True,
        controls=[
            ft.Text(model.title.value, size=30),
            tabs,
        ],
    )
