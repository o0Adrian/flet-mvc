from flet_mvc import FletView
import flet as ft


class IndexView(FletView):
    """
    When working with tabs you can create an Index view that will orquestrate
    the tabs content. I would recommend the following approaches:

    1. You could add as many parameters as needed for all the views, into the index view
    class. That way you could personalize every tab individually. (nice for small
    amount of tabs)

    2. Another option would be to expect multiple views but without the need to add
    a parameter every time, just use *tab_views (unpacking).

    3. The third option is an extension of the above, where insead of expecting an
    undefined number of arguments/views, you could use a dictionary or maybe list of
    sets/dicts/tuples that contain the properites of all the tabs. Properties like
        - Tab name (text)
        - Tab icon (icon)
        - Tab style (tab_content)
        - Tab view (content)

    In this template I am using aproach 1 for simplicity (home_view and settings_view
    params). I would highly recommend approach 3.
    """

    def __init__(self, controller, model, home_view, settings_view):
        view = [
            ft.Text("Tabs template", size=30),
            ft.Tabs(
                tabs=[
                    # Remember tab's "content" property expects ONE control, not a list !!
                    # Here I am using Column and ListView to illustrate that, since the
                    # view's "content" property is a list. (unless your specify the contrary)
                    ft.Tab(
                        text="Home",
                        icon=ft.icons.HOME,
                        content=ft.ListView(home_view.content),
                    ),
                    ft.Tab(
                        text="Settings",
                        icon=ft.icons.SETTINGS,
                        content=ft.Column(settings_view.content),
                    ),
                    ft.Tab(
                        text="Other Tab",
                        icon=ft.icons.BUILD,
                        content=ft.Text("\n\n\tTab under construction!"),
                    ),
                ],
                selected_index=0,
                animation_duration=0,  # No animation
            ),
        ]
        super().__init__(model, view, controller)
