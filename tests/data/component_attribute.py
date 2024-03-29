import flet as ft
from flet.matplotlib_chart import MatplotlibChart
from flet.plotly_chart import PlotlyChart

component_value_attr_map = {
    ft.TextField: "value",
    ft.AlertDialog: "content",
    ft.AnimatedSwitcher: "content",
    ft.AppBar: "actions",
    ft.Audio: "src",
    ft.Banner: "content",
    ft.BottomSheet: "content",
    ft.Card: "content",
    ft.Checkbox: "value",
    ft.CircleAvatar: "content",
    ft.Column: "controls",
    ft.Container: "content",
    ft.DataTable: "rows",
    ft.DataCell: "content",
    # ft.DataColumn: None,
    ft.DataRow: "cells",
    # ft.Divider: None,
    ft.Draggable: "content",
    ft.DragTarget: "content",
    ft.Dropdown: "options",
    ft.ElevatedButton: "text",
    # ft.FilePicker: None,
    ft.FilledButton: "text",
    ft.FilledTonalButton: "text",
    ft.FloatingActionButton: "text",
    ft.GestureDetector: "content",
    ft.GridView: "controls",
    # ft.HapticFeedback: None,
    ft.Icon: "name",
    ft.IconButton: "content",
    ft.Image: "src",
    # ft.InlineSpan: None,
    ft.ListTile: "title",
    ft.ListView: "controls",
    ft.Markdown: "value",
    ft.NavigationBar: "destinations",
    ft.NavigationRail: "destinations",
    ft.OutlinedButton: "text",
    # MatplotlibChart: "figure", ******** MISSING TESTING
    # PlotlyChart: "figure",  ******** MISSING TESTING
    # LineChart. ******** MISSING TESTING
    # BarChart, ******** MISSING TESTING
    # PieChart, ******** MISSING TESTING
    ft.PopupMenuItem: "text",
    ft.PopupMenuButton: "items",
    ft.ProgressBar: "value",
    ft.ProgressRing: "value",
    ft.Radio: "value",
    ft.RadioGroup: "value",
    ft.ResponsiveRow: "controls",
    ft.Row: "controls",
    # ft.Semantics: None,
    ft.ShaderMask: "content",
    # ft.ShakeDetector: None,
    ft.Slider: "value",
    ft.SnackBar: "content",
    ft.Stack: "controls",
    ft.Switch: "value",
    ft.Tabs: "tabs",
    ft.Text: "value",
    ft.TextButton: "text",
    ft.TextField: "value",
    ft.TextSpan: "text",
    ft.Tooltip: "content",
    ft.TransparentPointer: "content",
    # ft.VerticalDivider: None,
    ft.WindowDragArea: "content",
    ft.canvas.Canvas: "shapes",
}

potential_attributes = {
    "options": list,
    "value": None,
    "label": str,
    "src": str,
    "text": str,
    "name": str,
    "items": list,
    "shapes": list,
    "content": None,
    "actions": list,
    "controls": list,
    "figure": None,
    "title": None,
    "rows": list,
    "cells": list,
    "destinations": list,
    "tabs": list,
    "paint": None,
}
