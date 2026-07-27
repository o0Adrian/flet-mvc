# Migrating to flet-mvc 1.0

[Main guide](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Guía en español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md) ·
[Control matrix](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md)

This guide covers both:

- applications upgrading from the published flet-mvc 0.1.5 release; and
- applications that used an earlier, unpublished version of the 1.0 branch.

Version 1.0 is an intentional API reset made before the stable release. The
library now focuses on an advanced reactive domain model and keeps MVC as an
optional project structure. Features that duplicate maintained Flet APIs were
removed.

## 1. Upgrade in a branch

The supported runtime is:

```text
Python >=3.10
flet-mvc >=1.0,<2
Flet >=0.86.3,<0.87
```

Create a clean environment so an old Flet installation cannot hide dependency
problems:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "flet-mvc>=1.0,<2"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

The `<0.87` Flet cap is deliberate. flet-mvc will widen it after the next
minor line has been audited and tested.

## 2. Understand the new boundary

Use flet-mvc for:

- mutable and computed domain state;
- dependency propagation;
- subscriptions, batches, snapshots, and restores;
- narrow or explicit control bindings;
- model-aware composite controls;
- a focused data-table adapter.

MVC remains available as an application directory structure. Controllers are
ordinary Python classes, functions, or service objects owned by the
application.

Use Flet itself for:

- controls and declarative `@ft.component` functions;
- `ft.View`, `ft.Router`, and `ft.Route`;
- dialogs, snack bars, dropdown options, and navigation;
- control-only references through `ft.Ref`;
- rendering and page lifecycle.

This boundary removes two competing ways to perform the same Flet operation.

## 3. Update imports first

The stable root API is intentionally small:

```python
from flet_mvc import (
    NO_CHANGE,
    DataTableAdapter,
    Datapoint,
    DatapointChange,
    FletComponent,
    FletModel,
    computed,
    data,
    receive,
    register_control_binding,
    send,
    use_datapoint,
)
```

Dependency and binding exceptions are also exported from `flet_mvc`.

The following names are gone:

| Removed API | Replacement |
|---|---|
| `DataPoint` | `Datapoint` |
| `Component` | `FletComponent` |
| `FletController` and `controller.py` | an application class or `@dataclass` |
| `FletView` and `view.py` | native controls, `ft.View`, or `@ft.component` |
| `RouteHandler`, route aliases, and `routing.py` | `ft.Router` and `ft.Route` |
| `RefOnly` and `@data.RefOnly` | `ft.Ref` for an object reference |
| alert constants, `AlertType`, and `alert.py` | native Flet dialog controls |
| controller alert/dropdown/update helpers | the corresponding Flet API |

Do not recreate these as local compatibility wrappers unless the application
has a separate domain-specific reason for them.

## 4. Separate mutable and computed state

Old models often used `@data` for both source and derived values:

```python
class OldOrder(FletModel):
    @data
    def quantity(self):
        return 1

    @data.depends_on("quantity")
    def doubled(self):
        return self.quantity() * 2
```

Use `@data` only for mutable source state and `@computed` for read-only derived
state:

```python
class Order(FletModel):
    @data
    def quantity(self) -> int:
        return 1

    @computed
    def doubled(self) -> int:
        return self.quantity.value * 2
```

Dependencies are inferred from `.value` reads. If the dependency is hidden
behind external code, declare it with
`@computed.depends_on("quantity")`.

Computed datapoints:

- cannot be passed as constructor overrides;
- reject `set()`, `update()`, `reset()`, and `pull()`;
- are omitted from snapshots;
- are recreated by restoring their source state.

## 5. Replace datapoint operations

| Old call | 1.0 call |
|---|---|
| `point()` | `point.value` |
| `point.set_value(value)` | `point.set(value)` |
| `point.append(item)` | `point.update(lambda items: [*items, item])` |
| `point.extend(values)` | `point.update(lambda items: [*items, *values])` |
| `point.remove(item)` | `point.update(...)` with application logic |
| `point.clear()` | `point.set([])` or another empty value |
| `model.transaction()` | `model.batch()` |
| `point.set_default(...)` | define the default in `@data` |
| `point.clear_default(...)` | define and restore explicit application state |
| `point.has_set_value()` | track the relevant state explicitly |
| direct model assignment | `point.set(value)` |

For collections, return a replacement instead of mutating `.value` in place:

```python
model.items.update(lambda items: [*items, new_item])
model.tags.update(lambda tags: {*tags, "important"})
model.settings.update(lambda settings: {**settings, "theme": "dark"})
```

There is no separate “has been set” mode in 1.0. A datapoint always has its
current value. If the distinction matters to the domain, model it:

```python
class FormModel(FletModel):
    @data
    def title(self) -> str:
        return ""

    @data
    def title_was_edited(self) -> bool:
        return False

    def edit_title(self, title: str) -> None:
        with self.batch():
            self.title.set(title)
            self.title_was_edited.set(True)
```

## 6. Remove explicit initialization

`FletModel()` now initializes all datapoints eagerly and validates the
dependency graph. Remove calls such as:

```text
model.initialize()
model.sync_refs()
model.__hard_reset__()
```

Constructor values replace a later setup mutation:

```python
model = Order(quantity=4)
```

Unknown constructor names and attempts to initialize computed fields fail
immediately.

Create a model inside the Flet session entry point:

```python
def main(page: ft.Page) -> None:
    model = Order()
    page.render(OrderScreen, model)
```

This keeps state isolated between sessions.

## 7. Use atomic `batch()` commits, snapshots, and the graph

The canonical model operations are:

```python
with model.batch():
    model.quantity.set(2)
    model.unit_price.set(20.0)

saved = model.snapshot()
model.restore(saved)

print(model.dependency_graph)
print(model.dependency_dot())
```

`batch()` coalesces propagation and makes the outermost block one atomic
in-memory commit. Nested batches participate in that same transaction. If an
exception escapes the block, or a computed value or control binding fails
during propagation, flet-mvc restores mutable and computed values, bound
control properties, dependency edges, pending queues, and `model.revision`.
The failed commit publishes neither datapoint changes nor a native model
notification.

The transaction does not cover external database, file, or network side
effects. A `snapshot()` is still shallow, so copy mutable values when
persistence requires isolation; a snapshot is not required for automatic
batch rollback.

## 8. Adopt native Flet observability

`FletModel` now participates in Flet's native observable lifecycle. Its
`subscribe()` method is not a datapoint subscription:

| Subscription | Callback |
|---|---|
| `point.subscribe(callback)` | `callback(change: DatapointChange)` |
| `model.subscribe(callback)` | `callback(sender, field)` |

The model publishes one native notification after each stable datapoint
commit, with `field=None`. A whole outer `batch()` produces one commit.
`model.revision` counts those commits.

When a declarative component needs only one value, use the granular hook:

```python
from flet_mvc import use_datapoint


@ft.component
def QueryValue(point) -> ft.Control:
    query = use_datapoint(point)
    return ft.Text(query)
```

Call the hook unconditionally inside the component. It replaces its
subscription when `point` changes and disposes it on unmount.

## 9. Audit every implicit control binding

The old broad registry guessed structural fields such as `content`,
`controls`, `actions`, `options`, and `rows`. Those guesses were fragile after
Flet controls became sparse dataclasses.

Version 1.0 automatically binds only 21 core controls with one stable state
field. For example:

```python
field = ft.TextField(ref=model.query)
label = ft.Text(ref=model.query)
```

Input events pull the control value into mutable state and preserve the
application's original handler.

Structural state must be explicit:

```python
model.panels.bind(column, "controls")
model.options.bind(dropdown, "options")
model.rows.bind(table, "rows")
```

You can also declare a fixed field on the datapoint:

```python
class LayoutModel(FletModel):
    @data(bind="controls")
    def panels(self) -> list[ft.Control]:
        return []
```

For a custom class with one stable state contract:

```python
register_control_binding(
    MyControl,
    "selection",
    expected_type=str,
    event="on_change",
)
```

Unknown implicit bindings now raise `UnsupportedControlError`; they no longer
fall back to a first matching attribute. Review the complete
[21-control matrix](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md).

## 10. Replace `RefOnly` with `ft.Ref`

Use a native reference when the model does not own the control's value and you
only need to call a method on that control:

```python
field_ref = ft.Ref[ft.TextField]()
field = ft.TextField(ref=field_ref)


async def focus_field() -> None:
    if field_ref.current is not None:
        await field_ref.current.focus()
```

Use a normal `@data` datapoint plus `bind()` when the model does own a value.
Do not put a control object into domain state just to replace `RefOnly`.

## 11. Use descriptor targets in components

String paths and the `Component` alias were pre-release conveniences. Use the
model descriptor so refactors are visible to Python and type-checkers:

```python
import flet as ft

from flet_mvc import FletComponent, FletModel, data, receive, send


class SearchModel(FletModel):
    @data
    def query(self) -> str:
        return ""


@ft.control
class SearchBox(FletComponent):
    def init(self) -> None:
        super().init()
        self.label = ft.Text()
        self.controls = [self.label]

    @receive(SearchModel.query)
    def show_query(self, value: str) -> None:
        self.label.value = value

    @send(SearchModel.query)
    def clear_query(self, _event=None) -> str:
        return ""
```

`@receive` subscribes during `did_mount()` and cleans up during
`will_unmount()`. Return `NO_CHANGE` from `@send` to skip publication; `None`
is a real value. For UI without send/receive lifecycle needs, use the native
`@ft.component` API.

An asynchronous send method must use `async def`:

```python
@send(SearchModel.query)
async def load_query(self, _event=None) -> str:
    return await load_default_query()
```

A synchronous `@send` method that returns an awaitable now raises `TypeError`;
Flet does not await coroutine objects returned by a regular event function.
Receivers update only their `FletComponent` subtree. They no longer force a
whole-page update after changing child controls.

## 12. Replace `FletView` with native UI

A view may now be:

- a function that returns `ft.Control`;
- an `@ft.component`;
- an `ft.View` for a navigation level; or
- a regular native control subclass.

A small imperative MVC view can be a plain builder:

```python
def build_profile(controller) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(ref=controller.model.name),
            ft.Button(content="Save", on_click=controller.save),
        ]
    )
```

Nothing needs to reset or initialize the model when the view is created.

## 13. Replace `RouteHandler` with Flet Router

Use Flet's maintained route matcher and rendering lifecycle:

```python
import flet as ft


@ft.component
def Home() -> ft.Control:
    return ft.Text("Home")


@ft.component
def Settings() -> ft.Control:
    return ft.Text("Settings")


@ft.component
def App() -> ft.Control:
    return ft.Router(
        routes=[
            ft.Route(index=True, component=Home),
            ft.Route(path="settings", component=Settings),
        ]
    )


def main(page: ft.Page) -> None:
    page.render(App)
```

Use `page.navigate("/settings")` in synchronous callbacks or
`await page.push_route("/settings")` in asynchronous code.

For a mobile view stack:

1. set `manage_views=True` on `ft.Router`;
2. return native `ft.View` objects from route components;
3. render with `page.render_views(App)`.

The official [Router guide](https://flet.dev/docs/controls/router/) covers
nested routes, parameters, outlets, loaders, not-found components, and Back
navigation.

## 14. Replace `FletController` with an application class

`FletController` and `controller.py` were removed. Once the duplicate dialog,
dropdown, navigation, and update helpers were gone, the base class added no
behavior beyond assigning `page` and `model`.

Use a normal class. `@dataclass` is a concise option:

```python
from dataclasses import dataclass

import flet as ft


@dataclass
class OrderController:
    page: ft.Page
    model: Order

    def mark_saved(self, _event=None) -> None:
        self.page.show_dialog(ft.SnackBar(content=ft.Text("Saved")))
```

A function or domain service may be simpler when no object needs both values.
Replace historical convenience methods directly:

| Removed helper | Native replacement |
|---|---|
| `controller.update(...)` | normal event update, control update, or `page.update()` |
| `alert()`, `error()`, `success()`, `warning()`, `info()`, `advice()` | construct the desired Flet dialog |
| `show_error()` and other alert aliases | construct the desired Flet dialog |
| `dropdown_option(...)` | `ft.DropdownOption(...)` |
| `dropdown_options(...)` | a normal list of `ft.DropdownOption` |
| controller navigation wrappers | `page.navigate()` or `await page.push_route()` |

For example:

```python
page.show_dialog(ft.SnackBar(content=ft.Text("Saved")))

options = [
    ft.DropdownOption(key="draft", text="Draft"),
    ft.DropdownOption(key="published", text="Published"),
]
```

Flet automatically schedules normal control changes made in event handlers.
Call `page.update()` only when the native Flet lifecycle requires an explicit
update.

## 15. Rename DataTable adapter operations

The adapter is no longer exposed through datapoint proxy methods.

| Old API | 1.0 API |
|---|---|
| `adapter.table` or `adapter.current` | `adapter.control` |
| `stablish_columns()` / `establish_columns()` | `set_columns()` |
| `stablish_rows()` / `establish_rows()` | `set_rows()` |
| `create_from_dict()` | `load_records()` |
| `create_from_df()` | `load_dataframe()` |
| `records()` | `to_records()` |
| `download_df()` | `save_csv()` |

New code:

```python
adapter = DataTableAdapter()
adapter.set_columns(["name", "score"], numeric="score")
adapter.set_rows([["Ada", 98]])

page.add(adapter.control)
records = adapter.to_records()
csv_text = adapter.to_csv()
```

Or let records define the schema:

```python
adapter.load_records(
    [
        {"name": "Ada", "score": 98},
        {"name": "Grace", "score": 95},
    ]
)
```

Keep model state and the adapter as separate objects:

```python
adapter = DataTableAdapter().load_records(model.records.value)
unsubscribe = model.records.subscribe(
    lambda change: adapter.load_records(change.new_value)
)
```

Call `unsubscribe()` when the owner of this manual subscription is disposed.

For DataFrames and files, use:

```python
adapter.load_dataframe(frame)
frame_copy = adapter.to_dataframe()


async def export() -> None:
    await adapter.save_csv(file_name="records.csv")
```

## 16. Update Flet 0.9-era UI code

The library migration does not automatically rewrite application controls.
Common Flet changes include:

| Historical code | Current Flet 0.86 code |
|---|---|
| `ft.app(target=main)` | `ft.run(main)` |
| `ft.ElevatedButton(...)` | `ft.Button(...)` |
| lowercase color/icon constants | `ft.Colors` and `ft.Icons` enums |
| old `UserControl` | `@ft.control` subclass or `@ft.component` |
| old `Tabs(tabs=[...])` | `Tabs` with `TabBar` and `TabBarView` |
| `page.go(...)` | `page.navigate(...)` or `await page.push_route(...)` |
| flat page window properties | `page.window` |
| old page dialog fields | `page.show_dialog(...)` |

Audio, charts, video, and web views may live in Flet extension packages.
Install only the extensions the application uses. See the complete
[0.9.0 → 0.86.3 audit](https://github.com/o0Adrian/flet-mvc/blob/master/docs/FLET_RELEASE_AUDIT.md)
and Flet's
[breaking-change index](https://flet.dev/docs/updates/breaking-changes/).

## 17. Regenerate or compare templates

The 1.0 templates demonstrate the supported architecture:

```bash
flet-mvc start --destination /tmp/basic
flet-mvc reactive --destination /tmp/reactive
flet-mvc routes --destination /tmp/routes
flet-mvc tabs --destination /tmp/tabs
```

Do not point `--force` at an existing application until you have reviewed the
generated files. A safer migration is to generate beside the application and
compare each model, controller, view/component, and `pyproject.toml`.

## 18. Verify behavior, not only imports

Before considering the migration complete, test:

1. every mutable datapoint with `set()`, `update()`, and `reset()`;
2. each computed chain after one change and one `batch()`;
3. dynamic dependency branches and cycle errors;
4. every implicit and explicit control binding in both directions;
5. component mount, receive, send, async work, and unmount;
6. direct links, reload, Back, and not-found routes;
7. table import, rendering, in-memory export, and file download;
8. two simultaneous Flet sessions for state isolation;
9. desktop or device packaging;
10. dynamic web and static Pyodide builds if the application targets web.

The repository's own fast suite can be run with:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

## Troubleshooting

| Symptom | Check |
|---|---|
| `TypeError: Datapoint is not callable` | Replace `point()` with `point.value` |
| A computed value cannot be set | Change its mutable dependencies |
| `UnsupportedControlError` | Choose an explicit field or register the control type |
| A list changed but dependents did not | Replace it through `update()` |
| A component target cannot resolve | Use `@send(Model.field)` / `@receive(Model.field)` and pass the matching model |
| A route does not render | Verify `ft.Route` paths and `page.render(...)` / `render_views(...)` |
| A table has a cell-count error | Set columns before rows and match visible columns |
| Two users share state | Construct the model inside `main(page)` |
| Installation selected an incompatible Flet | Recreate the environment and inspect `python -m pip check` |
