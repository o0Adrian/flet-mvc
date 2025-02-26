<h1 align="center">
  <br>
  [DEPRECATED, NO LONGER UPDATED DUE WORK + CHANGED TO REACT FOR PERSONAL PROJECTS, BUT STILL: FEEL FREE TO COLLABORATE]
  <br>
  <br>
  [LOGO IN PROGRESS]
  <br>
  <br>
  <strong>Flet-MVC</strong>
  <br>
</h1>

<h4 align="center">The coding best practices for <a href="https://flet.dev/" target="_blank">Flet</a>. (Works with Flet v0.9.0)</h4>

<p align="center">
    <img src=https://img.shields.io/pypi/pyversions/flet-mvc>
    <img src=https://img.shields.io/pypi/dm/flet-mvc>
    <img src=https://badge.fury.io/py/flet-mvc.svg>
</p>
<br>

# Content
* [Quick Start](#quick-start)
* [What's next?](#next-updates)
* [Before we start](#before)
* [What is MVC?](#whatismvc)
* [Flet and MVC](#fletandmvc)
* [The flet-mvc package](#package)
    * [Installation](#installation)
    * [Usage – How to implement MVC to a Flet App?](#usage)
        * [Codebase structure:](#codebase)
        * [Basic structure](#structure)
        * [Explanation of the basic structure](#explanation)
        * [Controller Extra abilities](#extra)
    * [Datapoints](#datapoints)
        * [Supported Controls](#controls)
* [Common Mistakes](#common-mistakes)


<a name="quick-start"></a>

# Quick Start: `flet-mvc` cli
Flet-mvc v.0.1.5 now includes new **quick start** commands that you can use in the **terminal**. They will allow you to start developing right away, without the need of going though the effort of: looking for examples, copying old code as guidance, creating snippets or even reading this documentation every time you are in the need of starting a new Flet project with the MVC structure.

**The commands:**

- `flet-mvc start`: Creates the most basic MVC template for a flet app. It also includes the most basic usage of [Datapoints](#datapoints).
- `flet-mvc routes`: Creates the basic MVC template for a routed flet app.
- `flet-mvc tabs`: Creates the basic MVC template for a flet app that uses tabs. (advanced)

NOTE: The `flet-mvc tabs` command includes a concept of inheriting a modal inside other modal. This would illustrate **one** solution when in the need of making a View interact/modify other views. Remember that these are just templates, feel free to modify as needed.


# Version History
### **Flet-mvc v0.1.5 - The template update:**
- Bug fixes
- Added new flet-mvc cli. See "Quick Start: flet-mvc cli" [STABLE VERSION]

### **Flet-mvc v0.1.1 - v0.1.4 - Unstable versions!:**
- Bug fixes
- Added new flet-mvc cli [ERRORS FOUND]


### **Flet-mvc v0.1.0 - The datapoint update:**

- Added Ref Datapoints:<br>Creating Ref objects is no longer a pain, the need of using `__init__` and attributes in the model has been removed. It's now as easy as creating a new datapoint and setting it up inside a flet control: `ft.Text(ref=model.MyRefDatapoint)`.<br>They will show the returned value to the flet Control automatically and change it's value whenever a value is set to this datapoints. For more information see  [Datapoints](#datapoints).
- Added RefOnly Datapoints: <br> This datapoins can be using by declaring the following decorator: `@data.RefOnly`, the difference between the normal Ref datapoints is that this won't set any value to it's control by default, instead you will use it as any normal flet ref obj by calling `.current` and any needed attribute.
- Added `.has_set_value()` method to the datapoint object, which returns a boolean whenever a datapoint has a value set after using ".set_value()". Resets to false after calling `.reset()`
- Added unit tests and an app that tests all supported controls at: `/tests/test_all_controls/main.py`
- Added Dependancy between refs datapoints. If you create a datapoint with a certain Ref Object which default value is another flet control, to which you add another ref datapoint, the parent control will be updated when the child control does.
- Important Notes:
    - Memory: After testing the impact in the usage of this library seem to be minimal almost null. Still, more testing will be in progress.
    - See all supported controls and their corresponding default values at [Supported Controls](#controls)

<br>

<a name="next-updates"></a>

# What's next?

The flet-mvc 0.1.0 it's a very stable and complete versions of this library. But we are still a few steps away from making it the real flet-mvc v1.0.0 package. Below you will find the topic for the next updates and what will they consist of:

1. **The User's Control update**: This will cover the creation of a Flet User Control using the flet-mvc best practices and the corresponding send/receive decorator to comunicate between controls.
2. **The Controller update**: This will include new controller functions that will make flet develpment and building controls easier; more alerts, options for dropdowns maybe, etc. (suggestions are very well received)
3. **The DataTable update**: This will include practical controller functions that will allow the developer creating tables faster. Methods like:
    - stablish_columns(columns: List[str])
    - stablish_rows(rows: List[str])
    - create_from_df(data=pd.DataFrame)
    - create_from_dict(data=List[dict])
    - download_df()
    
    *These method names are not official and will be part of the datapoints methods.
    
    Also some styling maybe, and pretty much everything realted to DataTables.
4. **The Depancy Graph update**: This will be the biggest update and may take months of develoment. Were datapoints can depend on other datapoints (without the need of being ref objects) and can automatically affect the node/root values whenever the leaf changes. This will mark the era of the flet-mvc v1.0.0 (in the meantime use refs/datapoints for simple dependancies)


- **bug-fixes-updates**: simple bug-fixes, better typing exceptions, etc...

<br>

<a name="before"></a>
# Before we start
In case you want to go to a straighforward code example, please see the flet app where I am testing almost all flet controls with this library, and of course, following the strucure described here. The app is at:
`/tests/test_all_controls/main.py`

**KEEP IN MIND**, that it is a testing app, of course you don't need to add refdatapoints to every control in the ui. It's just showing the possibilities for all supported controls.

**SPECIAL NOTE**: I made this library with love <3 - I really hope you can find this guide is useful! in case it's not, please feel free to reach me out and I will further explain any topic that is not clear or add the necessary changes to the code and documentation.

You can find me in the Flet discort chanel which can be found in it's page: <a href="https://flet.dev/" target="_blank">Flet</a> at `third-party-packaged/flet-mvc`

<br>
<br>
<a name="whatismvc"></a>

# What is MVC?

MVC stands for Model-View-Controller. It is a design pattern that is used to create software applications with a clear separation of concerns.

- The Model represents the data and the business logic of the application. It is responsible for handling the data and performing any necessary computations.

- The View is responsible for displaying the data to the user. It receives updates from the Model and renders them on the screen.

- The Controller is responsible for handling user input and updating the Model and the View accordingly. It receives user input from the View and updates the Model with the new data, and then instructs the View to refresh the display with the new data.

The MVC pattern helps in separation of concern, **maintainability** and testability** of the application and also **making it scalable.**

In even simple terms:

- The Model can update the view when it’s values are changed by the controller. or just a "container" of data used in the app.

- The View is what you see and can interact with

- The Controller receives user input from the View and updates the Model with the new data, and then instructs the View to refresh the display with the new data.

Here is an image that explains this graphically:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.001.png)

Image taken from Wikipedia.org

<a name="fletandmvc"></a>
<br>
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

Imagine a flet app that looks like this:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.003.png)

This app example has an index view, this index view contains a layer and a navigation menu that will allow the user to change the view to three different tabs: Home, Statistics and Dashboard. Each view containing unique logic.

How do we keep organized the code of this app? Using a similar MVC codebase structure. Something like this:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.004.png)

This way we can keep the project completely scalable and maintainable.

<a name="structure"></a>

### Basic structure

In the following paragraphs I will show you the basic template that each of the MVC python scripts contain. You can start building your app on top of these templates right away.

**NOTE**: You can now get the basic template when creating a new flet project by running the command `flet-mvc start` on v.0.1.5 - I would also encourage you to create User snippets.


**Model:**


Model -> ./models/main.py

```python
from flet_mvc import FletModel, data
import flet as ft

# Model
class Model(FletModel):
    @data
    def example(self):
        return ...
```
**View**

./views/main.py

```python
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

```python
from flet_mvc import FletController

# Controller
class Controller(FletController):
    ...
```


**App**

app.py

```python
import flet as ft
from .controllers.main import Controller
from .views.main import MainView
from .models.main import Model

def main(page: ft.Page):
    # MVC set-up
    model = Model()
    controller = Controller(page, model)
    model.controller = controller  # Optional, in case controller it's needed in the model.
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

One of the question that you may have is, *how do I add controls to the page properties like banner or overlay?* The answer to that question is that you will add every control into a view attributes and set them up in the "Settings" section. example:

```python
    # Settings
    page.overlay.append(view.audio)
    page.overlay.append(view.bottom_sheet)
    page.overlay.append(view.file_picker)
    page.appbar = view.app_bar
    page.banner = view.banner
    page.snack_bar = view.snack_bar
    page.floating_action_button = view.fab

```

Just keep in mind that if you want to dinamically change them, you will be doing this set-up in the controller like:

```python
    # Inside a controller function
    self.page.banner = self.model.Banner.current  # <- ref datapoint
```

Let’s continue to the view

**View**

Now let’s talk about the View class (which, as mentioned, I recommend having in the corresponding “views” folder).

Here we will inherit *FletView* base class and create it’s “content” attribute as list of all the flet controls that our app will contain. <br>The *FletView* base class will have access to the model and controller. This way we can set the flet controls to use our controller methods when an event occurs. <br> Here is an example of a flet TextField control using a ref object from the model and a controller method in the “on\_click“ and “on\_submit” argument:

```python
ft.TextField(
    hint_text="0.0",
    ref=model.TextFieldDatapoint,  # Setting the ref obj
    border=ft.InputBorder.NONE,
    filled=True,
    expand=True,
    keyboard_type="number",
    on_change=controller.check_digits_only,  # Setting the function
    on_submit=controller.create_labels,  # Setting the function
),
```

**NOTE:** Keep in mind that datapoints have default values which will be set in the controls automaitcally. In this case, the value of TextFieldDatapoint will modify the attribute "value" of the TextField control. To learn more about this see [Datapoints](#datapoints).

Also, as we mentioned in the **App** section, in the view we can declare the controls that can be added to the flet page object. In this case we will need to add them into separate attributes. Following the example of the banner we mentioned before, the banner will look like this in the view:

```python
class MainView(FletView):
    def __init__(self, controller, model):
        self.banner = ft.Banner(  # <--
            ref=model.Banner,
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=40),
            actions=[
                ...
            ],
        )

        view = [
            ... # List of "normal" flet controls
        ]
        super().__init__(model, view, controller)
```

and that is how now the banner could be set to the page by using the datapoint in the controller.py or by using this attribute in the app.py at the "Settings" section.

Now let’s talk about the model before talking about the controller.

**Model**

The Model class inherit the *FletModel* base class. Here is where we create methods with the flet-mvc @data decorator, which I like to call: **Datapoints**.

In a VERY simple terms (maybe someone can get mad at me for saying this), the Model is a class that contains all the “variables” that the app will work with. These “variables” can have anything: from a Pandas DF obtained from SQL, Classes, Controls; to simple data types like strings, lists, int, etc. 

In order to create a “variable”/datapoint in the model, you only need to create a method, return it’s default value (can be computed with any logic that you want to use) and use the @data decorator in it.

The benefits of having a datapoint is that it can be accessed from the Controller and **can be used as any other python datatype**, but **additionally**: it will allow you to **set** **it’s value** in case it’s needed and most importantly **reset** **it’s value**!

\*\* Since version *0.1.0: The datapoint update*,  Datapoint can also work as Flet Ref objects. For more information see: [Datapoints](#datapoints)


**Controller**

I like to think that the Controller is the most relevant class from an application because it handles all the interactions of the user within the app (events).

Essentially the controller class will inherit from flet-mvc *FletController* base class and in it you will define all the methods that *Flet controls* use to handle the events. (as mentioned in the View explanation)

Let's talk about all the possibilities that the FletController allows you to do:

- **Access a model datapoint:**

Let’s imagine in our Model we declare a “number” datapoint that return 5 by calculating 2+3:
```python
@data
def number(self):
    return 2 + 3
```

now in our Controller we have a “clicked” method (which we assume is called when a button is clicked), and we want to print the “number” value. We will achieve this by doing the following:

```python
class Controller(FletController):

    def clicked(self, e=None):
        print(self.model.number())  # will print: 5
```

\*Notice how we call the datapoint by using the parethesis (), this returns the current value of the datapoint.

- **Set a model datapoint with any other value:**

Now let’s say we want to set our “number” datapoint value to 1 after we "click" it. Then we will use the **set\_value** property of the datapoint:

```python
class Controller(FletController):
    
    def clicked(self, e=None):
        print(self.model.number())  # will print: 5
        self.model.number.set_value(1)
        print(self.model.number())  # will print: 1
```
This number is saved and can be latter used by another other controller method or even other Controller class as long as it has the model instance reference:

```python
    def clicked2(self, e=None):
        print(self.model.number())  # will print: 1

```

- Reset a model datapoint 

If we no longer need the set value and want to revert our change to this datapoint, it’s as easy as use the **reset** property:

```python
class Controller(FletController):
    
    def clicked(self, e=None):
        print(self.model.number())  # will print: 5
        self.model.number.set_value(1)
        print(self.model.number())  # will print: 1
        self.model.number.reset()
        print(self.model.number())  # will print: 5 again after calculating 2+3 again.
```

- Set the default value of a datapoint

If by any chance we want to set a new default value whenever we reset a datapoint, we will use **set_default** property:

```python
class Controller(FletController):
    
    def clicked(self, e=None):
        print(self.model.number())  # will print: 5
        self.model.number.set_value(1)
        print(self.model.number())  # will print: 1
        self.model.number.set_default(3)
        self.model.number.reset()
        print(self.model.number())  # will print: 3 which is the new default
```

To learn more about datapoints please see [Datapoints](#datapoints).


<a name="extra"></a>

### Controller Extra abilities

- The FletController base class also allows out app Controller to update the view, as we would do it with page.update() but just by running self.update() in a controller method, like this:

```python
    def clicked(self, e=None):
        self.update()
```

- You can also access flet “page” by doing self.page
- Create alerts, you can send an alert whenever you need it as snackbar by using:

self.alert(“{your alert message}”, {alert type})


Example:
```python
self.alert("Alert Message", alert.WARNING)  # from flet_mvc import alert
```

alert shown:

![](imgs/Aspose.Words.efcdc9e9-d587-4000-ba2a-a36665e1390e.005.png)

There are 5 different alerts, feel free to experiment with any of them.
```python
WARNING = "warning"
ERROR = "error"
SUCCESS = "success"
INFO = "info"
ADVICE = "advice"
```

<a name="datapoints"></a>

# Datapoints


The data decorator in the Flet MVC framework is a powerful tool for defining Datapoints within a model. These datapoints form the backbone of your model's state and can be used to track, manipulate, and reference important data throughout the lifecycle of the Flet app.

I recommend using PascalCase to define your datapoints. ()

It's important to mention that there are three types of datapoints:

- <u>Normal Datapoint</u>: This Datapoints are used as normal "variables" that can be used at any time of the App lifecycle, they can be any type of data that you need: Pandas Dataframes, objects, integers, strings, etc. The way to define this datapoints is simply by creating a method in the model with the @data decorator:

    ```python
    class Model(FletModel):
        @data
        def Example(self):
            return "string type"
    ```

- <u>Normal Reference Data Points</u>: Normal reference data points are used when you want a Datapoint to affect the state of a Flet Control whenever these datapoints change their value. Also the returned type of this datapoint will be set to a specific attribute of the control, depending which one is it. Please see the section "Supported Flet Controls" below to learn more about the attributes affected. The way to define these datapoints is by declaring a normal datapoint, but adding it to a flet control `ref` attribute:

    ```python
    class Model(FletModel):
        @data
        def Example(self):
            return "string type value"

    class MainView(FletView):
        def __init__(self, controller, model):
            view = [
                ft.Text(ref=model.Example)  # This converts the datapoint automatically to a Ref Obj
            ]
            super().__init__(model, view, controller)
    ```

- <u>Reference-Only Datapoints (RefOnly)</u>: Lastly, RefOnly Datapoints are meant to be used only for referencing. They cannot be directly set, reset, appended to, or retrieved like normal data points; also they should return a None value since it's returned value don't affect the state of the Flet Control. Any attempts to directly interact with a RefOnly data point will raise a TypeError.

    Essentially they will fully work as normal Flet Ref Obj and in order to access the attributes of a control you will need to invoke the `.current` property. Don't forget to add it to the `ref` attribute of a Flet Control. The way to define them is by using the `@data.RefOnly` decorator:

     ```python
    class Model(FletModel):
        @data.RefOnly  # <--
        def Example(self):
            return None  # Any other value will result in useless logic

    class MainView(FletView):
        def __init__(self, controller, model):
            view = [
                ft.Text(ref=model.Example, value="RefOnly") # Assigning
            ]
            super().__init__(model, view, controller)
    ```


As seen in the Controller section, here are some of the functionalities of the data decorator:

## 1. Setting and Getting Data Point Values

Once a data point is defined, its value can be set using the `set_value()` function, and retrieved simply by calling the data point as a function. For example:

```python
model = MockModel()
model.datapoint.set_value("Test Value")
print(model.datapoint())  # Prints: Test Value
```
If the Datapoint is a ref obj datapoint, it will only accept the expected type of the control. For example, seting a string value for a datapoint that needs an integer for it's defined attributes (see *Supported flet controls* section below), will raise an exception. Same error will be applied if the default returned value is not consintent with the control.
## 2. Resetting Data Point Values

The value of a data point can be reset to its initial value using the `reset()` function. For example:

```python
model.datapoint.reset()
print(model.datapoint())  # Resets to it's initial defined value (unless it's set to a new default)
```

## 3. Setting a new default value

In the case that you need to set a new default for a datapoint, you can always use the `set_default` function. For Example:

```python
print(model.datapoint()) # Initial declared value
model.datapoint.set_default("new value")
model.datapoint.reset()
print(model.datapoint())  # Shows "new value"
```


## 4. Appending to List Data Points

If a data point is a list, values can be appended to it using the `append()` function. Note that a normal append operation won't modify the `has_set_value` attribute of the data point.

```python
model.datapoint_list().append("Test Value")
print(model.datapoint_list())  # Prints: ["Test Value"]
```
In case the Datapoint is a ref value with a data type of list (usually list of controls), then the append method can be directly called from the datapoint, it won't work otherwise.

```python
model.datapoint_list.append(ft.Text()"Test Value"))
print(model.datapoint_list())  # Shows the full list of controls that the datapoint has.
```

## 5. Check if it has a value set

Sometime you may want to see if a datapoint has changed of state and a value has been set. In order to solve that you can use the `has_set_value()` function, which will return a bool when the state has been set.

```python
print(model.datapoint.has_set_value()) # False
model.datapoint.set_value(None)
print(model.datapoint.has_set_value()) # True
model.datapoint.reset()
print(model.datapoint.has_set_value()) # False
```

## 6. Hard Reset (WARNING)

There is also a hard reset method called `__hard_reset__()` which will completely reset the datapoint to a state where it was never assigned to any flet Control, loosing all reference and being in the limbo. I have been using this to test the same datapoint in multiple flet controls by losing reference of the previous ones.

## 7. Multireference

A Datapoint can save the reference of multiple controls at the same time, in other words, we are assinging the same datapoint to multiple controls (that's why in order to assign a datapoint to another control you first need to call the __hard__reset__() method as mentioned above). This should be only used when you are sure the controls have the same attribute to be set by the ref datapoint. This can be useful when you have multiple copies of the same control. Not sure if it's needed but added this possibility.

## 8. Current property

The `.current` property can only be used by Ref Datapoints, either normal ones or RefOnly datapoints. The value returned by this property it's the referenced flet Control itself. This way you can access all the attributes of a control in the controller.

## 9. Control Dependencies

This is where the magic can happen. Let's say you have a dialog component:


```python
ft.AlertDialog(ref=model.Dialog, title=ft.Text("Title"))
```

If you look at the section below you will see that the Ref Datapoint will affect the content of the Dialog, but not the title, but what if we also what to have the text of the title in another datapoint so that it can change of state depending on a controller event? Well, we could define another ref datapoint to this text!

```python
ft.AlertDialog(ref=model.Dialog, title=ft.Text(ref=model.Text))
```

Hence our model datapoint will look like this:

```python
@data
def Text(self):
    return "Title"

@data
def Dialog(self):
    return ft.Text("This is my dialog content")
```

but as you can see there is even more levels to the Dialog datapoint, so we can even add more ref objects from the "self" model.

```python
@data
def Text(self):
    return "Title"

@data
def Dialog(self):
    return ft.Text(ref=self.DialogContentText)

@data
def DialogContentText(self):
    return "This is my dialog content"
```
you see where I am going? I know this example is a little useless, but it can illustrate the power of ref datapoint, and even more because if we do a `self.model.Text.set_value("new_title")` in the controller, it will automatically affect the root Control which will be the AlertDialog.

Just for the record, another way to do this will be the following:

```python
dialog = ft.AlertDialog(content=ft.Text(ref=model.DialogContentText) title=ft.Text(ref=model.Text)) 

# assigned to variable so I can set it in the page dialog attribute. *See the banner example at the View Section above.
```
this way I am only using two datapoint instead of three, but sometimes have that third one is useful.

<br>

## Supported flet controls:

| Control                 | Attribute    | Type       |
|-------------------------|--------------|------------|
| ft.TextField            | value        | str        |
| ft.AlertDialog          | content      | Control    |
| ft.AnimatedSwitcher     | content      | Control    |
| ft.AppBar               | actions      | list       |
| ft.Audio                | src          | str        |
| ft.Banner               | content      | Control    |
| ft.BottomSheet          | content      | Control    |
| ft.Card                 | content      | Control    |
| ft.Checkbox             | value        | Bool       |
| ft.CircleAvatar         | content      | Control    |
| ft.Column               | controls     | list       |
| ft.Container            | content      | Control(s?)|
| ft.DataTable            | rows         | list       |
| ft.DataRow              | cells        | list       |
| ft.Draggable            | content      | Control    |
| ft.DragTarget           | content      | Control    |
| ft.Dropdown             | options      | list       |
| ft.ElevatedButton       | text         | str        |
| ft.FilledButton         | text         | str        |
| ft.FilledTonalButton    | text         | str        |
| ft.FloatingActionButton | text         | str        |
| ft.GestureDetector      | content      | Control    |
| ft.GridView             | controls     | list       |
| ft.Icon                 | name         | str        |
| ft.Image                | src          | str        |
| ft.ListTile             | title        | Control    |
| ft.ListView             | controls     | list       |
| ft.Markdown             | value        | str        |
| ft.NavigationBar        | destinations | list       |
| ft.NavigationRail       | destinations | list       |
| ft.OutlinedButton       | text         | str        |
| ft.PopupMenuItem        | text         | str        |
| ft.PopupMenuButton      | items        | list       |
| ft.ProgressBar          | value        | float      |
| ft.ProgressRing         | value        | float      |
| ft.Radio                | value        | str        |
| ft.RadioGroup           | value        | str        |
| ft.ResponsiveRow        | controls     | list       |
| ft.Row                  | controls     | list       |
| ft.ShaderMask           | content      | Control    |
| ft.Slider               | value        | int        |
| ft.Stack                | controls     | list       |
| ft.Switch               | value        | bool       |
| ft.Tabs                 | tabs         | list       |
| ft.Text                 | value        | str        |
| ft.TextButton           | text         | str        |
| ft.TextField            | value        | str        |
| ft.TextSpan             | text         | str        |
| ft.Tooltip              | content      | Control    |
| ft.TransparentPointer   | content      | ----       |
| ft.WindowDragArea       | content      | Control    |
| ft.canvas.Canvas        | shapes       | list       |


Other supported controls are, but I would recommend using them as RefOnly datapoints:

| Control                |
|------------------------|
| ft.DataColumn          |
| ft.Divider             |
| ft.DataCell            |
| ft.FilePicker          |
| ft.HapticFeedback      |
| ft.IconButton          |
| ft.InlineSpan          |
| ft.Semantics           |
| ft.ShakeDetector       |
| ft.SnackBar            |
| ft.VerticalDivider     |


MatplotlibChart, PlotlyChart, LineChart, BarChart, PieChart Controls are still missing some testing.

<a name="common-mistakes"></a>

# Common Mistakes
If you have any issues in your code is possible that these are the possible mistakes:

1. <u>Forget to add the Ref-Datapoint to a Flet Control</u>: Keep in consideration that if you want to use a model datapoint as Ref-Object or RefOnly-Object **you need to assign it to a Flet control!** Else you won't be seeing any change being made in the UI.

    Example:

    ```python
    ft.Text(ref=model.MyRefDatapoint)
    ```

2. <u>Forget to use current attribute of a Ref-Object Datapoint in the Controller:</u> When working with Ref-Object Datatpoints, it's possible to forget using the *current* property. This one will actually return the Flet Control that you are referencing. So it's important to call current when accessing any other arrtribute of a Control.

    Example:
    ```python
    # Inside a controller function:
    self.model.MyRefDatatpoint.current.icon
    ```

3. <u>Calling the model datapoints and controller functions in the Flet controls:</u> In order to attach a datapoint to a Flet control, or adding the function to be triggered by an event of a flet control, it's important to specify only the object! not calling it!

    Example:
    ```python
    # Wrong:
    ft.ElevatedButton(ft.model.ButtonDatapoint(), on_click=controller.button_click())
    # Correct (no parenthesis):
    ft.ElevatedButton(ft.model.ButtonDatapoint, on_click=controller.button_click)
    ```
