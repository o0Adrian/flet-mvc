"""
Notice how I am not importing index model. (controller is unused)
I am using the model in the home model, so that the home model can have
access to the index model.

It's no neccesary but showing the possibility in case you want to have
control of the index view inside the Home tab. Like a button that adds
tabs which only leaves in the home tab.

You could easily use normal setup, but that would mean that views cannot
interact with each other (which in most cases, is the expected behaivour) 
"""
import flet as ft

# Models
from models.home import HomeModel
from models.settings import SettingsModel

# Views
from views.index import IndexView
from views.home import HomeView
from views.settings import SettingsView

# Controllers

from controllers.home import HomeController
from controllers.settings import SettingsController


def main(page: ft.Page):
    ### MVC set-up ###

    # Models
    home_model = HomeModel()
    settings_model = SettingsModel()

    # Controllers
    home_controller = HomeController(page, home_model)
    settings_controller = SettingsController(page, settings_model)

    # Views
    home_view = HomeView(home_controller, home_model)
    settings_view = SettingsView(settings_controller, settings_model)

    # Lastly set up index view
    
        # Here you could add the index controller and model in case you want the normal set-up
        # but as mentioned, using this weird approach to show that it's possible and that you can connect two models.
    index_view = IndexView(home_controller, home_model, home_view, settings_view)

    ### Page Settings ###
    page.title = ""

    # Run
    page.add(*index_view.content)


ft.app(target=main)
