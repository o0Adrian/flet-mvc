# **FLET MVC Architecture**

# Table of Contents
* [What is MVC?](#whatismvc)
* [Flet and MVC](#fletandmvc)
* [The flet-mvc package](#package)
    * [Installation](#installation)
    * [Usage – How to implement MVC to a Flet App?](#usage)
        * [Codebase structure:](#codebase)
        * [Basic structure](#structure)
        * [Explanation of the basic structure](#explanation)
        * [Controller Extra abilities](#extra)



<a name="whatismvc"></a>

# What is MVC?

MVC stands for Model-View-Controller. It is a design pattern that is used to create software applications with a clear separation of concerns.

- The Model represents the data and the business logic of the application. It is responsible for handling the data and performing any necessary computations.

- The View is responsible for displaying the data to the user. It receives updates from the Model and renders them on the screen.

- The Controller is responsible for handling user input and updating the Model and the View accordingly. It receives user input from the View and updates the Model with the new data, and then instructs the View to refresh the display with the new data.

The MVC pattern helps in separation of concern, **maintainability** and testability** of the application and also **making it scalable.**

In even simple terms:

- The Model updates de view when it’s values are changed by the controller

- The View is what you see and can interact with

- The Controller receives user input from the View and updates the Model with the new data, and then instructs the View to refresh the display with the new data.

Here is an image that explains this graphically:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.001.png)

Image taken from Wikipedia.org

<a name="fletandmvc"></a>

# Flet and MVC

In Flet you can build a whole running application in just one file. But “just because you can, doesn’t mean you should”.

Here two disadvantages of not using an architecture (any):

- Poor maintainability: A lack of separation of concerns can make it harder to maintain the codebase over time. This can lead to bugs and performance issues that are difficult to fix.

- Lack of scalability: Applications that are not designed using the MVC pattern can be harder to scale as the number of users or amount of data increases. This is because the codebase may become more complex and harder to understand as it grows.

- Just imagine receiving a +3000 lines of code app python file where every 100 lines a  new Flet Control is added to the view, methods all over the place and variables too. Good luck trying to fix a bug over there

**Flet-mvc** python package provides the necessary components to assimilate an implementation of the MVC architectural pattern in Flet.

<a name="package"></a>

# The flet-mvc package

<a name="installation"></a>

## Installation
```
python3 -m pip install flet-mvc
```
<a name="usage"></a>

## Usage – How to implement MVC to a Flet App?

<a name="codebase"></a>

### Codebase structure:
In the following image you will find a basic code base structure to start working in a new app. 

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.002.png)

This will keep the app maintenance and scalability on point.

**One more example**

Image an flet web app that looks like this:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.003.png)

This web app example has an index view, this index view contains a layer and a navigation menu that will allow the user to change the view to three different tabs: Home, Statistics and Dashboard. Each view containing unique logic.

How do we keep organized the code of this app? Using a similar MVC codebase structure. Something like this:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.004.png)

This way we can keep the project completely scalable and maintainable.

<a name="structure"></a>

### Basic structure

In the following paragraphs I will show you the basic template that each of the MVC python scripts contain. You can start building your app on top of these templates right away.

**NOTE**: I fully encourage you to create User snippets like *flet\_model*, *flet*\_*controller*, *flet\_view*, *flet\_app* to create each of the following blocks quicker.


**Model:**


Model -> ./models/main.py

```
from flet_mvc import data
import flet as ft

# Model
class Model():
    def __init__(self) -> None:
        """
        NOTE: __init__ method will be no longer needed
        in flet-mvc version 1.0.0. The ref objects can
        be created in a @data method like any datapoint.
        """
        self.ref_obj = ft.Ref[ft.Text]()
    @data
    def example(self):
        return ...
```
**View**

./views/main.py

```
from flet_mvc import FletView
import flet as ft

# View
class MainView(FletView):
    def __init__(self, controller, model):
        view = [
            ... # List of flet controls
        ]
        super().__init__(model, view, controller)
```


**Controller**

./controllers/main.py

```
from flet_mvc import FletController

# Controller
class Controller(FletController):
    ...
```


**App**

app.py

```
import flet as ft
from .controllers.main import Controller
from .views.main import MainView
from .models.main import Model

def main(page: ft.Page):
    # MVC set-up
    model = Model()
    controller = Controller(page, model)
    view = MainView(controller, model)
    
    # Settings
    page.title = ""

    # Run
    page.add(
        *view.content
    )

ft.app(target=main)
```

<a name="explanation"></a>

### Explanation of the basic structure:

**App**

Everything starts with the app.py, this script may be a little familiar to you if you have already worked with flet. Here you will:

- Set-up the MVC classes (I will explain each of them in a moment)
- Stablish the basic setting of your app (page), like the title, scroll, horizontal alignment, theme mode, etc. see <https://flet.dev/docs/controls/page/> for more page properties
- And finally run the app by reading the content of your View class.

Let’s continue to the view

**View**

Now let’s talk about the View class (which, as mentioned, I recommend having in the corresponding “views” folder).

Here we will inherit *FletView* base class and create it’s “content” attribute a list of all the flet controls that our app will contain. The *FletView* base class will have access to the model and controller. This way we can set the flet controls to use our controller methods when an event occurs, here is an example of a flet TextField control using a ref object from the model and a controller method in the “on\_click“ and “on\_submit” argument:

```
ft.TextField(
    hint_text="0.0",
    ref=model.text_field_ref,
    border=ft.InputBorder.NONE,
    filled=True,
    expand=True,
    keyboard_type="number",
    on_change=controller.check_digits_only,
    on_submit=controller.create_labels
),
```

**NOTE:** v.1.0.0 from flet-mvc will allow the usage of model datapoint as *Ref* objects. This will allow the developer to create a default value, access, edit, and restore the current value of a control **without the need of a real *Ref* object!** Stay tune for that!

Now let’s talk about the model before talking about the controller.

**Model**

The Model class doesn’t need to inherit any base class; but instead, create methods with the flet-mvc @data decorator. I like to call them datapoints.

In a VERY simple terms (maybe someone can get mad at me for saying this), the Model is a class that contains all the “variables” that the app will work with. These “variables” can have anything: from a Pandas DF obtained from SQL, Classes, Controls; to simple data types like strings, lists, int, etc. 

In order to create a “variable”/datapoint in the model, you only need to create a method, return it’s default value (can be computed with any logic that you want to use) and use the @data decorator in it.

The benefits of having a datapoint is that it can be accessed from the Controller and **can be used as any other python datatype**, but **additionally**: it will allow you to **set** **it’s value** in case it’s needed and most importantly **reset** **it’s value**!

\*\* As mentioned several times over this documentation, in the current flet version prior flet-mvc v.1.0.0., in order to create Ref objects in the model, you need to set the attributes in the class as:

```
self.ref_obj = ft.Ref[ft.Text]()
```

**Controller**

I like to think that the Controller is the most relevant class from an application because it handles all the interactions of the user within the app (events).

Essentially the controller class will inherit from flet-mvc *FletController* base class and in it you will define all the methods that *Flet controls* use to handle the events. (as mentioned in the View explanation)

I want to talk in space about all the possibilities that the FletController allows you to do:

- **Access a model datapoint:**

Let’s imagine in our Model we declare a “number” datapoint that return 0 by calculating 0+0:
```
@data
def number(self):
    return 0 + 0
```

now in our Controller we have a “clicked” method called when a button is clicked. And we want to print the “number” value. We will achieve this by doing the following:

```
class Controller(FletController):

    def clicked(self, e=None):
        print(self.model.number())  # will print: 0
```

\*notice how we call the datapoint by using the parethesis ()

- **Set a model datapoint with any other value:**

Now let’s say we want to set our “number” datapoint value to 1 after we click it. Then we will use the **set\_value** property of the datapoint:

```
class Controller(FletController):
    
    def clicked(self, e=None):
        print(self.model.number())  # will print: 0
        self.model.number.set_value(1)
        print(self.model.number())  # will print: 1
```
This number is saved and can be latter used by another other controller method or even other Controller class as long as it has the model instance reference:

```
    def clicked2(self, e=None):
        print(self.model.number())  # will print: 1

```

- Reset a model datapoint 

If we no longer need the set value and want to revert our change to this datapoint, it’s as easy as use the **reset** property:

```
class Controller(FletController):
    
    def clicked(self, e=None):
        print(self.model.number())  # will print: 0
        self.model.number.set_value(1)
        print(self.model.number())  # will print: 1
        self.model.number.reset()
        print(self.model.number())  # will print: 0 again after calculating 0+0 again.
```

- Access all controls properties by using the Ref objects declared in the model, it’s important to use the “current” property. 

```
        self.model.ref_obj.current.value = ""        
        self.model.ref_obj.current.value
        # plus any other property of the control
```

This will later be removed by the flet-mvc v1.0.0 as I have been promising since the start of the guide. It will be used as any other datapoint and it will be updated in the View the moment we set it’s value.

```
        # set value
        self.model.ref_obj.set_value("")
        
        # obtain value
        self.model.ref_obj()
        
        # possibility to reset
        self.model.ref_obj.reset()
```

**To have in mind:**

If we want to reset a datapoint and it contains a dependency with another datapoint, it won’t take the other datapoint current value, it will just take It’s default value. This dependencies will be provided in a later version of flet-mvc. Maybe v1.1.0

<a name="extra"></a>

### Controller Extra abilities

- The FletController base class also allows out app Controller to update the view, as we would do it with page.update() but just by running self.update() in a controller method, like this:

```
    def clicked(self, e=None):
        self.update()
```

- You can also access flet “page” by doing self.page
- Create alerts, you can send an alert whenever you need it as snackbar by using:

self.alert(“{your alert message}”, {alert type})


Example:
```
self.alert("Alert Message", alert.WARNING)  # from flet_mvc import alert
```

alert shown:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.005.png)

There are 5 different alerts, feel free to experiment with any of them.
```
WARNING = "warning"
ERROR = "error"
SUCCESS = "success"
INFO = "info"
ADVICE = "advice"
```

Hope this guide is useful, if not, please feel free to reach me out and I will further explain any topic that is not clear
