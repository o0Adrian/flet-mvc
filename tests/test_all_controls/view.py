import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from flet_mvc import FletView
import flet as ft
import math

class TestView(FletView):
    def __init__(self, controller, model):
        self.app_bar = ft.AppBar(
            ref=model.AppBar,
            leading=ft.Icon(ft.icons.PALETTE),
            leading_width=40,
            title=ft.Text("0. AppBar | This app contains all controls with refs"),
            center_title=False,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        self.audio = ft.Audio(ref=model.Audio)

        self.banner = ft.Banner(
            ref=model.Banner,
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=40),
            actions=[
                ft.TextButton("Retry", on_click=controller.close_banner),
                ft.TextButton("Ignore", on_click=controller.close_banner),
                ft.TextButton("Cancel", on_click=controller.close_banner),
            ],
        )

        self.bottom_sheet = ft.BottomSheet(
            ref=model.BottomSheet,
            open=False,
            on_dismiss=controller.bs_dismissed,
        )
        self.snack_bar = ft.SnackBar(
            ref=model.SnackBar,
            content=ft.Text("Hello, world!"),
            action="Alright!",
        )

        self.fab = ft.FloatingActionButton(
            ref=model.FloatingActionButton,
            icon=ft.icons.ADD,
            on_click=controller.fab_pressed,
            bgcolor=ft.colors.LIME_300,
            height=30,
            mini=True,
        )
        
        self.file_picker = ft.FilePicker(ref=model.FilePicker, on_result=controller.see_file)

        view = [
            ft.ListView(
                controls=[
                    # 1. AlertDialog
                    ft.Text("1. AlertDialog"),
                    ft.AlertDialog(ref=model.Dialog, title=ft.Text("Test Title")),
                    ft.ElevatedButton("Open Dialog", on_click=controller.open_dialog),

                    # 2. AnimatedSwitcher
                    ft.Text("\n2. Animated Switcher"),
                    ft.AnimatedSwitcher(
                        ref=model.AnimatedSwitcher,
                        transition=ft.AnimatedSwitcherTransition.SCALE,
                        duration=500,
                        reverse_duration=100,
                        switch_in_curve=ft.AnimationCurve.BOUNCE_OUT,
                        switch_out_curve=ft.AnimationCurve.BOUNCE_IN,
                    ),
                    ft.ElevatedButton("Animate!", on_click=controller.animate),

                    # 3. Audio
                    ft.Text("\n3. Audio"),
                    ft.ElevatedButton("Play", on_click=lambda _: self.audio.play()),
                    ft.ElevatedButton("Stop playing", on_click=lambda _: self.audio.pause()),

                    # 4. Banner
                    ft.Text("\n4. Banner"),
                    ft.ElevatedButton("Show Banner", on_click=controller.open_banner),

                    # 5. Bottom Sheet
                    ft.Text("\n5. Bottom Sheet"),
                    ft.ElevatedButton("Show Bottom Sheet", on_click=controller.open_bs),

                    # 6. Card
                    ft.Text("\n6. Card | 7. Checkbox | 10. Column | 11. Container | 26. Icon  | 30. ListTile | 45. Row | 54. Text | 55. TextButton"),
                    ft.Card(
                        ref=model.Card
                    ),

                    # 8. Circle Avatar
                    ft.Text("\n8. CircleAvatar | 51. Stack (overlap controls)"),
                    ft.Stack(
                        ref=model.Stack,
                        width=40,
                        height=40,
                    ),

                    # 12. DataTable
                    ft.Text("\n12. DataTable (only DataRow and DataTable supported)"),
                    # TODO: Create my own datatable that directly accepts a dataframe as input
                    # which of course is compatible with this library.
                    # TODO: Maybe create an controller function that makes that automaticalle
                    # given a ref of datatable + dataframe. <- I like this
                    # TODO: Create a download option given the datatable node.
                    ft.DataTable(
                        ref=model.DataTable,
                        columns=[
                            ft.DataColumn(ft.Text("First name")),
                            ft.DataColumn(ft.Text("Last name")),
                            ft.DataColumn(ft.Text("Age"), numeric=True),
                        ],
                    ),

                    # 13. Divider
                    ft.Text("\n13. Divider (RefOnly)"),
                    ft.Divider(ref=model.Divider),

                    # 14. Draggable
                    ft.Text("\n14. Draggable"),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Draggable(
                                        ref=model.Draggable,
                                        group="color",
                                        content_feedback=ft.Container(
                                            width=20,
                                            height=20,
                                            bgcolor=ft.colors.CYAN,
                                            border_radius=3,
                                        ),
                                    ),
                                    ft.Draggable(
                                        group="color",
                                        content=ft.Container(
                                            width=50,
                                            height=50,
                                            bgcolor=ft.colors.YELLOW,
                                            border_radius=5,
                                        ),
                                    ),
                                    ft.Draggable(
                                        group="color1",
                                        content=ft.Container(
                                            width=50,
                                            height=50,
                                            bgcolor=ft.colors.GREEN,
                                            border_radius=5,
                                        ),
                                    ),
                                ]
                            ),
                            ft.Container(width=100),
                            ft.Column(
                                [
                                    # 15. DragTarget
                                    ft.Text("\n15. DragTarget"),
                                    ft.DragTarget(
                                        ref=model.DragTarget,
                                        group="color",
                                        on_will_accept=controller.drag_will_accept,
                                        on_accept=controller.drag_accept,
                                        on_leave=controller.drag_leave,
                                    ),
                                ]
                            ),
                        ]
                    ),                    

                    # 16. Dropdown | 17. ElevatedButton | 50. Snackbar
                    ft.Text("\n16. Dropdown | 17. ElevatedButton | 50. Snackbar"),
                    ft.Dropdown(
                        ref=model.Dropdown,
                        width=100,
                    ),
                    ft.ElevatedButton(
                        ref=model.ElevatedButton,
                        on_click=controller.button_clicked
                    ),

                    # 18. FilePicker
                    ft.Text("\n18. FilePicker"),
                    ft.ElevatedButton(
                        "Choose file...",
                        on_click=lambda _: self.file_picker.pick_files(
                            allow_multiple=True
                        ),
                    ),
                    ft.ElevatedButton(
                        "See file on console",
                        on_click=controller.see_file
                    ),

                    # 19. FilledButton
                    ft.Text("\n19. FilledButton"),
                    ft.FilledButton(
                        ref=model.FilledButton,
                        disabled=True,
                        icon="add"
                    ),
                    

                    # 20. FilledTonalButton
                    ft.Text("\n20. FilledTonalButton"),
                    ft.FilledTonalButton(
                        ref=model.FilledTonalButton,
                        disabled=True, icon="add"
                    ),
                    

                    # 23. GestureDetector
                    ft.Text("\n23. GestureDetector"),
                    ft.Stack(
                        [
                            ft.GestureDetector(
                                ref=model.GestureDetector,
                                mouse_cursor=ft.MouseCursor.MOVE,
                                on_vertical_drag_update=controller.on_pan_update,
                                left=100,
                                top=100,
                            )
                        ],
                        height=200,
                    ),
                    

                    # 24. GridView
                    ft.Text("\n24. GridView"),
                    ft.GridView(
                        ref=model.GridView,
                        expand=1,
                        runs_count=5,
                        max_extent=150,
                        child_aspect_ratio=1.0,
                        spacing=5,
                        run_spacing=5,
                    ),                    

                    # 27. IconButton
                    ft.Text("\n27. IconButton"),
                    ft.Row(
                        [
                            ft.IconButton(
                                ref=model.IconButton,
                                icon=ft.icons.PLAY_CIRCLE_FILL_OUTLINED,
                                on_click=controller.icon_button_click,
                                data=0
                            ),
                        ]
                    ),

                    # 29. Ignore.

                    # 31. ListView
                    ft.Text("\n31. ListView"),
                    ft.Container(
                        content=ft.ListView(
                            ref=model.ListView,
                            expand=True,
                            spacing=10,
                        ),
                        height=100,
                    ),

                    # 32. Markdown
                    ft.Text("\n32. Markdown"),
                    ft.Markdown(
                        ref=model.Markdown,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        # on_tap_link=lambda e: self.page.launch_url(e.data),
                        code_theme="atom-one-dark",
                        code_style=ft.TextStyle(font_family="Roboto Mono"),
                    ),

                    # 33. MatplotlibChart | Tested, good.
                    ft.Text("\n33. MatplotlibChart | Tested."),

                    # 34. NavigationBar
                    ft.Text("\n34. NavigationBar | Tested."),

                    # 35. NavigationRail
                    ft.Text("\n35. NavigationRail | Tested."),

                    # 36. OutlinedButton
                    ft.Text("\n36. OutlinedButton"),
                    ft.OutlinedButton(ref=model.OutlinedButton, disabled=True),

                    # 37. PlotlyChart
                    ft.Text("\n37. PlotlyChart | Tested."),

                    # 40. ProgressBar
                    ft.Text("\n40. ProgressBar"),
                    ft.ProgressBar(
                        ref=model.ProgressBar,
                        width=400,
                        color="amber",
                        bgcolor="#eeeeee"
                    ),

                    # 41. ProgressRing
                    ft.Text("\n41. ProgressRing"),
                    ft.Row(
                        [
                            ft.ProgressRing(
                                ref=model.ProgressRing,
                                width=16,
                                height=16,
                                stroke_width = 2
                            ),
                            ft.Text("Stuck at 75%...")
                        ]
                    ),

                    # 42. Radio
                    ft.Text("\n42. Radio | 43. RadioGroup"),
                    ft.RadioGroup(
                        ref=model.RadioGroup,
                        content=ft.Column(
                            [
                                ft.Radio(ref=model.Radio, label="Red"),
                                ft.Radio(value="green", label="Green"),
                                ft.Radio(value="blue", label="Blue")
                            ]
                        )
                    ),

                    # 44. ResponsiveRow
                    ft.Text("\n44. ResponsiveRow"),
                    ft.ResponsiveRow(ref=model.ResponsiveRow),                    

                    # 47. ShaderMask
                    ft.Text("\n47. ShaderMask"),
                    ft.Row(
                        [
                            ft.ShaderMask(
                                ref=model.ShaderMask,
                                blend_mode=ft.BlendMode.MULTIPLY,
                                shader=ft.RadialGradient(
                                    center=ft.alignment.center,
                                    radius=2.0,
                                    colors=[ft.colors.WHITE, ft.colors.PINK],
                                    tile_mode=ft.GradientTileMode.CLAMP,
                                ),
                            )
                        ]
                    ),

                    # 49. Slider
                    ft.Text("\n49. Slider"),
                    ft.Slider(
                        ref=model.Slider,
                        min=0,
                        max=100,
                        divisions=10,
                        label="{value}%",
                        # on_change=slider_changed
                    ),

                    # 52. Switch
                    ft.Text("\n52. Switch"),
                    ft.Switch(ref=model.Switch),

                    # 53. Tabs
                    ft.Text("\n53. Tabs"),
                    ft.Container(
                        ft.Tabs(
                            ref=model.Tabs,
                            selected_index=0,
                            animation_duration=0,  # No animation
                            expand=1,
                        ),
                        width=300,
                        height=300,
                    ),

                    # 56. Textfield
                    ft.Text("\n56. Textfield"),
                    ft.TextField(ref=model.TextField, label="TextField"),

                    # 57. TextSpan | 57.2 TextStyle (RefOnly)
                    ft.Text("\n57. TextSpan"),
                    ft.Text(
                        spans=[
                            ft.TextSpan(
                                ref=model.TextSpan,
                                style=ft.TextStyle(
                                    size=60,
                                    weight=ft.FontWeight.BOLD,
                                    foreground=ft.Paint(
                                        color=ft.colors.BLUE_700,
                                        stroke_width=6,
                                        stroke_join=ft.StrokeJoin.ROUND,
                                        style=ft.PaintingStyle.STROKE,
                                    ),
                                ),
                            ),
                        ],
                    ),

                    # 58. Tooltip
                    ft.Text("\n58. Tooltip"),
                    ft.Tooltip(
                        ref=model.Tooltip,
                        message="This is tooltip",
                        padding=20,
                        border_radius=10,
                        text_style=ft.TextStyle(size=20, color=ft.colors.WHITE),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.Alignment(0.8, 1),
                            colors=[
                                "0xff1f005c",
                                "0xff5b0060",
                                "0xff870160",
                                "0xffac255e",
                                "0xffca485c",
                                "0xffe16b5c",
                                "0xfff39060",
                                "0xffffb56b",
                            ],
                            tile_mode=ft.GradientTileMode.MIRROR,
                            rotation=math.pi / 3,
                        ),
                    ),

                    # 60. VerticalDivider
                    ft.Text("\n60. VerticalDivider | RefOnly"),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        bgcolor=ft.colors.ORANGE_300,
                                        alignment=ft.alignment.center,
                                        expand=True,
                                    ),
                                    ft.VerticalDivider(),
                                    ft.Container(
                                        bgcolor=ft.colors.BROWN_400,
                                        alignment=ft.alignment.center,
                                        expand=True,
                                    ),
                                    ft.VerticalDivider(
                                        ref=model.VerticalDivider,
                                        width=1,
                                        color="white"
                                    ),
                                    ft.Container(
                                        bgcolor=ft.colors.BLUE_300,
                                        alignment=ft.alignment.center,
                                        expand=True,
                                    ),
                                    ft.VerticalDivider(width=9, thickness=3),
                                    ft.Container(
                                        bgcolor=ft.colors.GREEN_300,
                                        alignment=ft.alignment.center,
                                        expand=True,
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        height=300,
                    ),

                    # 61. WindowDragArea
                    ft.Text("\n61. WindowDragArea"),
                    ft.WindowDragArea(
                        ref=model.WindowDragArea,
                        expand=True
                    ),

                    # 62. Canvas
                    ft.Text("\n62. Canvas"),
                    ft.Container(
                        ft.canvas.Canvas(
                            ref=model.Canvas,
                            width=float("inf"),
                            expand=True,
                        ),
                        height=150,
                    ),

                    # 63. LineChart
                    ft.Text("\n63. LineChart"),
                    

                    # 64. BarChart
                    ft.Text("\n64. BarChart"),
                    

                    # 65. PieChart
                    ft.Text("\n65. PieChart"),
                    

                ],
                expand=True
            )
        ]
        super().__init__(model, view, controller)
