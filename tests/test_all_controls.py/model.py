import sys
import os
import pandas
import math

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from flet_mvc import FletModel, data
import flet as ft


class TestModel(FletModel):
    @data
    def AppBar(self):
        """0. App Bar | Attribute: actions"""
        return [
            ft.IconButton(ft.icons.WB_SUNNY_OUTLINED),
            ft.IconButton(ft.icons.FILTER_3),
            ft.PopupMenuButton(ref=self.PopupMenuButton),
        ]

    # NOTE: When the attribute of a Cotnrol is content, sometimes can be a list
    # sometimes a single control, and sometimes both. Inconsistency of flet.
    @data
    def Dialog(self):
        """1. Dialog datapoint | Attribute: content"""
        return []

    @data
    def AnimatedSwitcher(self):
        """2. Animated Switcher | Attribute: content"""
        return ft.Container(
            ft.Text("Hello!", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            alignment=ft.alignment.center,
            width=200,
            height=200,
            bgcolor=ft.colors.GREEN,
        )

    @data
    def Audio(self):
        """3. Audio | Attribute: src"""
        return "https://luan.xyz/files/audio/ambient_c_motion.mp3"

    @data
    def Banner(self):
        """4. Banner | Attribute: content"""
        return ft.Text(
            "4. Banner. Imagine this is an error. What would you like me to do?"
        )

    @data
    def BottomSheet(self):
        """5. Bottom Sheet | Attribute: content"""
        return ft.Container(
            ft.Column(
                [
                    ft.Text("This is sheet's content!"),
                    ft.ElevatedButton(
                        "Close bottom sheet", on_click=self.controller.close_bs
                    ),
                ],
                tight=True,
            ),
            padding=10,
            width=680,
        )

    @data
    def Card(self):
        """6. Card | Attribute: content"""
        return ft.Container(
            ref=self.Container,
            width=400,
            padding=10,
        )

    @data
    def Checkbox(self):
        """7. Checkbox | Attribute: value"""
        return False

    @data
    def CircleAvatar(self):
        """8. CircleAvatar | Attribute: content"""
        return ft.Text("CA")

    @data
    def Column(self):
        """10. Column | Attribute: controls"""
        return [
            ft.ListTile(
                ref=self.ListTile,
                leading=ft.Icon(ref=self.Icon),
                subtitle=ft.Text("Music by Julie Gable. Lyrics by Sidney Stein."),
            ),
            ft.Row(
                ref=self.Row,
                alignment=ft.MainAxisAlignment.END,
            ),
        ]

    @data
    def Container(self):
        """11. Container | Attribute: content"""
        return ft.Column(ref=self.Column)

    @data
    def DataTable(self):
        """12. DataTable | Attribute: rows"""

        def createRows():
            """
            This is an example of a function that creates rows from a dataframe
            This could be used in a function of the controller and then set the value
            of this node (set_value) with the result of that function for the datatable
            to be interactive.
            Keep in mind this is a RefNode, so you can also access the columns in the controller
            with 'self.model.DataTable.current.columns = $yourNewColumns'
            """
            df = pandas.DataFrame(
                [
                    {"First name": "John", "Last name": "Smith", "Age": "43"},
                    {"First name": "Jack", "Last name": "Brown", "Age": "19"},
                    {"First name": "Alice", "Last name": "Wong", "Age": "25"},
                ]
            )
            return [
                ft.DataRow(cells=[ft.DataCell(ft.Text(value)) for value in row])
                for row in df.values.tolist()
            ]

        rows = createRows()
        rows.append(
            ft.DataRow(
                ref=self.DataRow,
                selected=True,
                on_select_changed=lambda e: print(f"row select changed: {e.data}"),
            ),
        )
        return rows

    @data
    def DataRow(self):
        """12.1 DataRow | Attribute: cells (DataCell and Column not supported)"""
        return [
            ft.DataCell(ft.Text("Adrián")),
            ft.DataCell(ft.Text("Monroy")),
            ft.DataCell(ft.Text("23")),
        ]

    @data.RefOnly
    def Divider(self):
        """13. Divider | Attribute: NONE"""
        return None

    @data
    def Draggable(self):
        """14. Draggable | Attribute: content"""
        return ft.Container(
            width=50,
            height=50,
            bgcolor=ft.colors.CYAN,
            border_radius=5,
        )

    @data
    def DragTarget(self):
        """15. DragTarget | Attribute: content"""
        return ft.Container(
            width=50,
            height=50,
            bgcolor=ft.colors.BLUE_GREY_100,
            border_radius=5,
        )

    @data
    def Dropdown(self):
        """16. Dropdown | Attribute: options"""

        def set_options(
            options,
        ) -> list:  #  TODO: This could live in the controller or datapoint.
            return [ft.dropdown.Option(option) for option in options]

        return set_options(options=["Red", "Green", "Blue"])

    @data
    def ElevatedButton(self):
        """17. ElevatedButton | Attribute: text"""
        return "Submit"

    @data.RefOnly
    def FilePicker(self):
        """18. FilePicker | Attribute: None"""
        return None

    @data
    def FilledButton(self):
        """19. FilledButton | Attribute: text"""
        return "Disabled Button"

    @data
    def FilledTonalButton(self):
        """20. FilledTonalButton | Attribute: text"""
        return "Disabled Button"

    # 21. FletApp | Ignore

    @data
    def FloatingActionButton(self):
        """22. FloatingActionButton | Attribute: text"""
        return "22. FAB"

    @data
    def GestureDetector(self):
        """23. GestureDetector | Attribute: content"""
        return ft.Container(
            content=ft.Text("23", style=ft.TextThemeStyle.LABEL_LARGE),
            bgcolor=ft.colors.BLUE,
            alignment=ft.alignment.center,
            width=50,
            height=50,
            border_radius=5,
        )

    @data
    def GridView(self):
        """24. GridView | Attribute: controls"""
        images = []
        for i in range(0, 7):
            images.append(
                ft.Image(
                    src=f"https://picsum.photos/150/150?{i}",
                    fit=ft.ImageFit.NONE,
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    border_radius=ft.border_radius.all(10),
                )
            )
        images.append(
            ft.Image(
                ref=self.Image,
                fit=ft.ImageFit.NONE,
                repeat=ft.ImageRepeat.NO_REPEAT,
                border_radius=ft.border_radius.all(10),
            )
        )
        return images

    # 25. HapticFeedback | Ignore | can still have ref though.

    @data.RefOnly
    def IconButton(self):
        """27. IconButton | Attribute: content * Use RefOnly Please"""
        return None

    @data
    def Image(self):
        """28. Image | Attribute: src"""
        return "https://picsum.photos/150/150?8"

    # 29. Ignore

    @data
    def ListView(self):
        """31. ListView | Attribute: controls"""
        items = []
        for i in range(100):
            items.append(ft.Text(f"Line {i}"))
        return items

    @data
    def Markdown(self):
        """32. Markdown | Attribute: value"""
        return """
## Tables

|Syntax                                 |Result                               |
|---------------------------------------|-------------------------------------|
|`*italic 1*`                           |*italic 1*                           |
|`_italic 2_`                           | _italic 2_                          |
|`**bold 1**`                           |**bold 1**                           |
|`__bold 2__`                           |__bold 2__                           |
|`This is a ~~strikethrough~~`          |This is a ~~strikethrough~~          |
|`***italic bold 1***`                  |***italic bold 1***                  |
|`___italic bold 2___`                  |___italic bold 2___                  |
|`***~~italic bold strikethrough 1~~***`|***~~italic bold strikethrough 1~~***|
|`~~***italic bold strikethrough 2***~~`|~~***italic bold strikethrough 2***~~|

## Styling

Style text as _italic_, __bold__, ~~strikethrough~~, or `inline code`.

- Use bulleted lists
- To better clarify
- Your points

## Code blocks

Formatted Dart code looks really pretty too:

```dart
import 'package:flet/flet.dart';
import 'package:flutter/material.dart';

void main() async {
  await setupDesktop();
  runApp(const MyApp());
}
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: 'Flet Flutter Demo',
      home: FletApp(pageUrl: "http://localhost:8550"),
    );
  }
}
```
"""

    # TEST COMPLETE:
    # @data
    # def MatplotlibChart(self):
    #     """33. MatplotlibChart | Attribute: figure"""
    #     return None

    # @data
    # def NavigationBar(self):
    #     """34. NavigationBar | Attribute: destinations"""
    #     return None

    # @data
    # def NavigationRail(self):
    #     """35. NavigationRail | Attribute: destinations"""
    #     return None

    # @data
    # def NavigationDestination(self):
    #     """34.5 NavigationDestination | Attribute: label"""
    #     return None

    @data
    def OutlinedButton(self):
        """36. OutlinedButton | Attribute: text"""
        return "Disabled button"

    @data
    def PlotlyChart(self):
        """37. PlotlyChart | Attribute: figure"""
        return None

    @data
    def ProgressBar(self):
        """40. ProgressBar | Attribute: value"""
        return 0.5

    @data
    def ProgressRing(self):
        """41. ProgressRing | Attribute: value"""
        return 0.75

    @data
    def Radio(self):
        """42. Radio | Attribute: value"""
        return "red"

    @data
    def RadioGroup(self):
        """43. RadioGroup | Attribute: value (current selection, not content!)"""
        return "blue"

    @data
    def ResponsiveRow(self):
        """44. ResponsiveRow | Attribute: controls"""
        return [
            ft.Container(
                ft.Text("Column 1"),
                padding=5,
                bgcolor=ft.colors.YELLOW,
                col={"sm": 6, "md": 4, "xl": 2},
            ),
            ft.Container(
                ft.Text("Column 2"),
                padding=5,
                bgcolor=ft.colors.GREEN,
                col={"sm": 6, "md": 4, "xl": 2},
            ),
            ft.Container(
                ft.Text("Column 3"),
                padding=5,
                bgcolor=ft.colors.BLUE,
                col={"sm": 6, "md": 4, "xl": 2},
            ),
            ft.Container(
                ft.Text("Column 4"),
                padding=5,
                bgcolor=ft.colors.PINK_300,
                col={"sm": 6, "md": 4, "xl": 2},
            ),
        ]

    # 46. Semantics? | Ignore | label

    @data
    def ShaderMask(self):
        """47. ShaderMask | Attribute: content"""
        return ft.Image(
            src="https://picsum.photos/200/200?1",
            width=200,
            height=200,
            fit=ft.ImageFit.FILL,
        )

    # 48. ShakeDetector | Attribute: UNSOPPORTED UNTIL THERE'S AN USE CASE"""

    @data
    def Slider(self):
        """49. Slider | Attribute: value"""
        return 25

    @data
    def SnackBar(self):
        """50. SnackBar | Attribute: content *not automatically set"""
        # NOTE: This is not supported to be automatically set, but can still be used
        # as normal ref, like DataColumn or DataCell, but if you are going to use this
        # I recommend using it as @data.RefOnly instead. but showing that can still work
        # with set valueon the controller at button_clicked method.
        # Actually just use flet-mvc alert instead.
        return None

    @data
    def Switch(self):
        """52. Switch | Attribute: value"""
        return True

    @data
    def Tabs(self):
        """53. Tabs | Attribute: tabs"""
        return [
            ft.Tab(
                ref=self.Tab,
                content=ft.Container(
                    content=ft.Text("This is Tab 1"), alignment=ft.alignment.center
                ),
            ),
            ft.Tab(
                tab_content=ft.Icon(ft.icons.SEARCH),
                content=ft.Text("This is Tab 2"),
            ),
            ft.Tab(
                text="Tab 3",
                icon=ft.icons.SETTINGS,
                content=ft.Text("This is Tab 3"),
            ),
        ]

    @data
    def Tab(self):
        """53.1 Tab | Attribute: text"""
        return "Tab 1"

    @data
    def TextField(self):
        """56. TextField | Attribute: value"""
        return "Initial text value"

    @data
    def TextSpan(self):
        """57. TextSpan | Attribute: text"""
        return "Greetings, planet!"

    @data
    def Tooltip(self):
        """58. Tooltip | Attribute: content"""
        return ft.Text("Hover to see tooltip", weight=ft.FontWeight.W_100)

    # 59. TransparentPointer | See Flet docs | content

    @data.RefOnly
    def VerticalDivider(self):
        """60. VerticalDivider | Attribute: None"""
        return None

    @data
    def WindowDragArea(self):
        """61. WindowDragArea | Attribute: content"""
        return ft.Container(
            ft.Text("Drag this area to move, maximize and restore application window."),
            bgcolor=ft.colors.AMBER_300,
            padding=10,
        )

    @data
    def Canvas(self):
        """62. Canvas | Attribute: shapes"""
        return [
            ft.canvas.Circle(100, 100, 50, self.PaintStroke()),
            ft.canvas.Circle(80, 90, 10, self.PaintStroke()),
            ft.canvas.Circle(84, 87, 5, self.PaintFill()),
            ft.canvas.Circle(120, 90, 10, self.PaintStroke()),
            ft.canvas.Circle(124, 87, 5, self.PaintFill()),
            ft.canvas.Arc(70, 95, 60, 40, 0, math.pi, paint=self.PaintStroke()),
        ]

    def PaintStroke(self):
        return ft.Paint(stroke_width=2, style=ft.PaintingStyle.STROKE)

    def PaintFill(self):
        return ft.Paint(style=ft.PaintingStyle.FILL)

    @data
    def LineChart(self):
        """63. LineChart | Attribute: MISSING"""
        return None

    @data
    def BarChart(self):
        """64. BarChart | Attribute: MISSING"""
        return None

    @data
    def PieChart(self):
        """65. PieChart | Attribute: MISSING"""
        return None

    ###

    @data
    def Icon(self):
        """26. Icon | Attribute: name"""
        return ft.icons.ALBUM

    @data
    def ListTile(self):
        """30. ListTile | Attribute: title"""
        return ft.Text(ref=self.Text)

    @data
    def Row(self):
        """45. Row | Attribute: controls"""
        return [
            ft.Checkbox(ref=self.Checkbox, label="7. Checkbox"),
            ft.TextButton(ref=self.TextButton),
        ]

    @data
    def Stack(self):
        """51. Stack | Attribute: controls"""
        return [
            ft.CircleAvatar(ref=self.CircleAvatar),
            ft.Container(
                content=ft.CircleAvatar(bgcolor=ft.colors.GREEN, radius=5),
                alignment=ft.alignment.bottom_left,
            ),
        ]

    @data
    def Text(self):
        """54. Text | Attribute: value"""
        return "54. Text | The Enchanted Nightingale"

    @data
    def TextButton(self):
        """55. TextButton | Attribute: text"""
        return "55. TextButton"

    @data
    def PopupMenuButton(self):
        """39. PopupMenuButton | Attribute: items"""
        return [
            ft.PopupMenuItem(text="39. PopupMenuButton"),
            ft.PopupMenuItem(),  # divider
            ft.PopupMenuItem(content=ft.TextField()),
            ft.PopupMenuItem(ref=self.PopupMenuItem, checked=False),
        ]

    @data
    def PopupMenuItem(self):
        """38. PopupMenuItem | Attribute: text"""
        return "38. PopupMenuItem"
