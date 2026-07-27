# flet-mvc

Advanced reactive domain models for Flet, with an optional MVC project
structure.

[English](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md)

> The upcoming flet-mvc 1.0 targets Flet `>=0.86.3,<0.87` and Python 3.10 or
> newer. The upper bound is intentional: a new Flet minor release is audited
> before the range is widened.

flet-mvc gives a domain model a little more structure than a plain observable:

- `@data` declares mutable state;
- `@computed` declares read-only derived state;
- dependencies form a deterministic graph;
- batches, snapshots, subscriptions, and control bindings are built in;
- `FletModel` is a native `ft.Observable`, so it works with `@ft.component`.

MVC is available when separating models, views, and controllers makes a
project easier to maintain. It is not mandatory. Flet remains responsible for
controls, `ft.View`, `ft.Router`, dialogs, navigation, rendering, and
application lifecycle.

## Choose a path

- To build something now, follow [Quick start](#quick-start).
- To learn the state API, read [Model state](#model-state).
- To use class-oriented MVC, open [Optional MVC structure](#optional-mvc-structure).
- To migrate old code, use the
  [migration guide](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md).
- To bind a control, check the
  [control matrix](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md).
- To review the Flet upgrade, read the
  [release audit](https://github.com/o0Adrian/flet-mvc/blob/master/docs/FLET_RELEASE_AUDIT.md).

## Install

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install flet-mvc:

```bash
python -m pip install --upgrade pip
python -m pip install "flet-mvc>=1.0,<2"
```

The package installs its tested Flet range automatically.

| flet-mvc | Flet | Python | Status |
|---|---|---|---|
| 1.0.x | `>=0.86.3,<0.87` | 3.10–3.14 | Current target |
| 0.1.5 | 0.9.0 in practice | Historical | Legacy |

## Quick start

This first application uses a flet-mvc model directly from Flet's declarative
UI. There is no controller or custom view class to understand yet.

Create `app.py`:

```python
import flet as ft

from flet_mvc import FletModel, computed, data


class CounterModel(FletModel):
    @data
    def count(self) -> int:
        return 0

    @computed
    def message(self) -> str:
        return f"Count: {self.count.value}"


@ft.component
def Counter(model: CounterModel) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(model.message.value, size=28),
            ft.Button(
                content="Add one",
                icon=ft.Icons.ADD,
                on_click=lambda: model.count.update(lambda value: value + 1),
            ),
        ]
    )


def main(page: ft.Page) -> None:
    page.title = "Reactive counter"
    page.render(Counter, CounterModel())


if __name__ == "__main__":
    ft.run(main)
```

Run it:

```bash
python app.py
```

Each click follows one predictable flow:

```text
Button event
  → count.update(...)
  → count changes
  → message is recomputed
  → Flet observes the model
  → Counter renders the new values
```

No `page.update()` is needed in this declarative example.

## Model state

### Mutable state with `@data`

The decorated method supplies the default value. Every model instance owns
independent datapoints.

```python
from flet_mvc import FletModel, data


class OrderModel(FletModel):
    @data
    def quantity(self) -> int:
        return 1

    @data
    def unit_price(self) -> float:
        return 9.50


first = OrderModel()
second = OrderModel(quantity=3)

assert first.quantity.value == 1
assert second.quantity.value == 3

first.quantity.set(2)
first.quantity.update(lambda quantity: quantity + 1)
assert first.quantity.value == 3

first.quantity.reset()
assert first.quantity.value == 1
```

Use:

- `point.value` to read;
- `point.set(value)` to replace a value;
- `point.update(transform)` to derive the next value from the current one;
- `point.reset()` to evaluate its `@data` method again.

Do not assign `model.quantity = 2`; the descriptor rejects direct assignment
so changes cannot bypass propagation.

The descriptors are generic. A method returning `int` becomes a
`Datapoint[int]`, so type checkers validate `.value`, `set()`, `update()`, and
`use_datapoint()` without extra annotations.

### Derived state with `@computed`

A computed datapoint is read-only. flet-mvc records which datapoints it reads
and recomputes it after any dependency changes.

```python
from flet_mvc import FletModel, computed, data


class OrderModel(FletModel):
    @data
    def quantity(self) -> int:
        return 1

    @data
    def unit_price(self) -> float:
        return 9.50

    @computed
    def total(self) -> float:
        return self.quantity.value * self.unit_price.value


model = OrderModel()
assert model.total.value == 9.50

model.quantity.set(4)
assert model.total.value == 38.0
```

Calling `set()`, `update()`, or `reset()` on `total` raises `TypeError`.
Change its source data instead.

Dependencies can change at runtime. For example, a computed property may read
`personal_price` in one branch and `business_price` in another. The graph
removes stale edges when the active branch changes.

If a dependency is hidden behind code that does not read the datapoint during
evaluation, declare it:

```python
class SearchModel(FletModel):
    @data
    def query(self) -> str:
        return ""

    @computed.depends_on("query")
    def normalized_query(self) -> str:
        return normalize_external_query(self.query.value)
```

`normalize_external_query` is an application function in this example.
Unknown dependencies and cycles fail with a specific dependency error.

### Replace collections instead of mutating them silently

Use `update()` to return a new collection:

```python
from flet_mvc import FletModel, data


class WorkspaceModel(FletModel):
    @data
    def items(self) -> list[dict]:
        return []

    @data
    def filters(self) -> dict:
        return {}


model = WorkspaceModel()
new_item = {"id": 3, "name": "Document"}
model.items.update(lambda items: [*items, new_item])
model.filters.update(lambda filters: {**filters, "active": True})
```

An in-place mutation such as `model.items.value.append(new_item)` changes the
Python list without telling the dependency graph. Prefer immutable-style
updates like the example above.

### Subscribe to changes

Subscribers receive an immutable `DatapointChange`. The returned function
unsubscribes safely, even when called more than once.

```python
def report(change) -> None:
    print(change.name, change.old_value, change.new_value, change.source)


unsubscribe = model.total.subscribe(report, fire_immediately=True)
model.quantity.set(2)
unsubscribe()
```

Synchronous and asynchronous subscribers are supported. Notifications run
after the dependency graph has reached a consistent state.

### Batch related changes

`batch()` delays propagation until the outermost block exits. Each affected
computed datapoint is evaluated once with the final source values.

```python
with model.batch():
    model.quantity.set(2)
    model.unit_price.set(20.0)

assert model.total.value == 40.0
```

Nested batches join the same outer transaction. The outermost `batch()` is an
atomic commit boundary: if an exception escapes its body, or a computed value
or control binding fails while the graph is stabilizing, flet-mvc restores the
previous mutable and computed values, bound control properties, dependency
edges, pending queues, and `model.revision`. Datapoint subscribers and the
native model observable are not notified about the failed commit.

This rollback protects the in-memory model graph; it cannot undo database,
file, network, or other side effects performed by application code.

### Save and restore model state

```python
saved = model.snapshot()

model.quantity.set(99)
model.restore(saved)

assert model.quantity.value == saved["quantity"]
```

Snapshots are shallow dictionaries containing mutable `@data` values.
Computed values are omitted because restoring their dependencies recreates
them. `restore(values, strict=False)` ignores unknown keys, which is useful
when loading older saved data. Snapshots are useful for persistence and manual
state capture; `batch()` does not require one to roll back a failed commit.

### Inspect the dependency graph

```python
print(model.dependency_graph)
print(model.dependency_dot())
```

`dependency_graph` maps each datapoint to the names it depends on.
`dependency_dot()` returns Graphviz DOT for debugging or visualization.

## Use the model with native Flet

### Declarative components

`FletModel` inherits `ft.Observable`. Pass a model to `@ft.component`, read
its datapoint values while rendering, and let Flet schedule the rerender.
This is the recommended starting point for new declarative applications.

```python
@ft.component
def OrderSummary(model: OrderModel) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(f"Quantity: {model.quantity.value}"),
            ft.Text(f"Total: ${model.total.value:.2f}"),
            ft.Button(
                content="Add item",
                on_click=lambda: model.quantity.update(lambda value: value + 1),
            ),
        ]
    )
```

Use Flet hooks, contexts, and routers normally. flet-mvc does not introduce a
second rendering system.

Passing the whole model makes the component observe model commits. For a
smaller rerender boundary, `use_datapoint(point)` subscribes only to that
datapoint and disposes the subscription when the component unmounts:

```python
from flet_mvc import use_datapoint


@ft.component
def QuantityValue(point) -> ft.Control:
    quantity = use_datapoint(point)
    return ft.Text(f"Quantity: {quantity}")
```

Like every Flet hook, call `use_datapoint()` unconditionally and only inside
an `@ft.component` body.

There are two intentionally different subscription contracts:

| API | Callback receives | Use |
|---|---|---|
| `point.subscribe(...)` | one `DatapointChange` | Observe a specific value |
| `model.subscribe(...)` | `(sender, field)` | Native `ft.Observable` contract |

A stable datapoint commit notifies the model once with `field=None`.
`model.revision` increments once for each such commit, including one increment
for a whole outer `batch()`; no-op assignments do not increment it. Regular
public attributes on the model retain normal Flet Observable notifications
with their field name.

### Imperative control bindings

Bindings are useful in an imperative screen or when a specific control should
receive updates without rebuilding a larger component.

```python
class ProfileModel(FletModel):
    @data
    def name(self) -> str:
        return "Ada"


model = ProfileModel()
field = ft.TextField(ref=model.name, label="Name")
preview = ft.Text(ref=model.name)

model.name.set("Grace")
assert field.value == "Grace"
assert preview.value == "Grace"
```

For a registered input control, flet-mvc also wraps its current change event.
Typing into `field` pulls `field.value` into the model, preserves the original
event handler, and propagates the result.

Automatic inference is deliberately limited to 21 controls with one stable
state field. Structural properties such as `controls`, `content`, `actions`,
`options`, and `rows` are never guessed. Bind those explicitly:

```python
class BoardModel(FletModel):
    @data
    def cards(self) -> list[ft.Control]:
        return []


model = BoardModel()
board = ft.Column()
model.cards.bind(board, "controls")

model.cards.set([ft.Text("First"), ft.Text("Second")])
model.cards.sync()
model.cards.pull(board)
model.cards.unbind(board)
```

The complete fields and events are in
[`docs/CONTROL_COMPATIBILITY.md`](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md).

For a custom control class with one stable state field, register the contract
once:

```python
register_control_binding(
    MyControl,
    "selection",
    expected_type=str,
    event="on_change",
)
```

For only one instance, prefer
`point.bind(control, "selection")`. An unsafe or unknown implicit binding
raises `UnsupportedControlError` with instructions instead of guessing.

### Control references

Use Flet's own `ft.Ref` when you need the control object rather than a reactive
value:

```python
name_ref = ft.Ref[ft.TextField]()


async def focus_name() -> None:
    if name_ref.current is not None:
        await name_ref.current.focus()


field = ft.TextField(ref=name_ref, label="Name")
```

Keep this reference beside the UI that owns the control.

## Model-aware composite controls

`FletComponent` is a native `@ft.control` subclass of `ft.Column`. Use it when
a reusable control needs lifecycle-managed communication with a model.

`@send(Model.field)` publishes the method's return value.
`@receive(Model.field)` subscribes on mount and unsubscribes on unmount.

```python
import flet as ft

from flet_mvc import FletComponent, FletModel, data, receive, send


class CounterModel(FletModel):
    @data
    def count(self) -> int:
        return 0


@ft.control
class CounterPanel(FletComponent):
    def init(self) -> None:
        super().init()
        self.count_text = ft.Text(size=32)
        self.controls = [
            self.count_text,
            ft.Button(content="Add one", on_click=self.increment),
        ]

    @receive(CounterModel.count)
    def show_count(self, value: int) -> None:
        self.count_text.value = str(value)

    @send(CounterModel.count)
    def increment(self, _event=None) -> int:
        return self.model.count.value + 1


panel = CounterPanel(model=CounterModel())
```

Both decorators accept synchronous and asynchronous methods.
`@receive` fires immediately by default; pass `fire_immediately=False` when
only later changes matter. Return `NO_CHANGE` from a `@send` method when an
event should leave the target untouched. Returning `None` deliberately sets
the datapoint to `None`.

An asynchronous `@send` method must be declared with `async def`. A regular
`def` that returns an awaitable raises `TypeError`, matching Flet's event
contract instead of silently dropping the coroutine.

After a receiver changes child controls, `FletComponent` updates only its own
subtree. Declarative components and controls bound elsewhere keep their own
Flet update lifecycle; a receiver does not force a whole-page update.

For ordinary UI composition, prefer Flet's lighter `@ft.component`. Use
`FletComponent` specifically when send/receive and mount cleanup are useful.

## Optional MVC structure

MVC is a directory and responsibility boundary, not a required runtime layer:

```text
my_app/
├── app.py
├── controllers/
│   └── todo.py
├── models/
│   └── todo.py
└── views/
    └── todo.py
```

- The **Model** owns domain state and rules.
- The **View** returns native Flet controls, an `ft.View`, or a component.
- The **Controller** translates UI actions into model operations.
- `app.py` creates fresh session objects and connects them.

`models/todo.py`:

```python
from flet_mvc import FletModel, data


class TodoModel(FletModel):
    @data
    def title(self) -> str:
        return "Learn Flet MVC"
```

`controllers/todo.py`:

```python
from dataclasses import dataclass

from models.todo import TodoModel


@dataclass
class TodoController:
    model: TodoModel

    def rename(self, _event=None) -> None:
        self.model.title.set("Build the application")
```

`views/todo.py`:

```python
import flet as ft

from controllers.todo import TodoController


def build_view(controller: TodoController) -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text(ref=controller.model.title, size=28),
            ft.Button(content="Rename", on_click=controller.rename),
        ]
    )
```

`app.py`:

```python
import flet as ft

from controllers.todo import TodoController
from models.todo import TodoModel
from views.todo import build_view


def main(page: ft.Page) -> None:
    model = TodoModel()
    controller = TodoController(model)
    page.add(build_view(controller))


if __name__ == "__main__":
    ft.run(main)
```

Create the model inside `main()`. Flet invokes `main()` for each session, so
module-level models would accidentally share state between users.

The controller is an ordinary application class; `@dataclass` only removes
boilerplate. A function or service object works just as well. flet-mvc exports
no controller base. Pass `page` into a controller only when that controller
actually navigates or opens a Flet service. Dialogs, dropdown options, updates,
and navigation use Flet directly.

## Native routing and views

Use the official `ft.Router`, `ft.Route`, `ft.View`, and `@ft.component`.
flet-mvc does not maintain a parallel route handler.

```python
import flet as ft


@ft.component
def Home() -> ft.Control:
    return ft.Text("Home", size=28)


@ft.component
def About() -> ft.Control:
    return ft.Text("About", size=28)


@ft.component
def App() -> ft.Control:
    page = ft.context.page
    return ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Button(content="Home", on_click=lambda: page.navigate("/")),
                    ft.Button(
                        content="About",
                        on_click=lambda: page.navigate("/about"),
                    ),
                ]
            ),
            ft.Router(
                routes=[
                    ft.Route(index=True, component=Home),
                    ft.Route(path="about", component=About),
                ]
            ),
        ]
    )


def main(page: ft.Page) -> None:
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
```

For mobile back gestures and a real view stack, set
`ft.Router(..., manage_views=True)`, return `ft.View` objects from route
components, and call `page.render_views(App)`. See Flet's official
[Router guide](https://flet.dev/docs/controls/router/).

## Data tables

`DataTableAdapter` builds and exports a native `ft.DataTable`. The Flet control
is always available through `adapter.control`.

### Load records

```python
import flet as ft

from flet_mvc import DataTableAdapter


adapter = DataTableAdapter().load_records(
    [
        {"name": "Ada", "score": 98},
        {"name": "Grace", "score": 95},
    ]
)

table_control = adapter.control
assert isinstance(table_control, ft.DataTable)
print(adapter.to_records())
print(adapter.to_csv())
```

Keys are collected in first-seen order. Missing values become `None`.

### Set a schema and rows

```python
adapter = DataTableAdapter()
adapter.set_columns(["name", "score"], numeric="score")
adapter.set_rows(
    [
        ["Ada", 98],
        {"name": "Grace", "score": 95},
    ]
)
```

Rows may be sequences, mappings, or existing `ft.DataRow` objects. Column and
visible-cell counts are validated before the table is updated.

### DataFrames and CSV files

```python
adapter.load_dataframe(frame)
frame_copy = adapter.to_dataframe()


async def export_table() -> None:
    await adapter.save_csv(file_name="scores.csv")
```

`load_dataframe()` accepts pandas-style `to_dict(orient="records")` and
Polars-style `to_dicts()` objects without importing either library.
`to_dataframe()` requires pandas:

```bash
python -m pip install "flet-mvc[dataframe]>=1.0,<2"
```

`save_csv()` uses Flet's current asynchronous `FilePicker.save_file()` and
sends CSV bytes for desktop or web download.

The canonical adapter API is:

| Purpose | API |
|---|---|
| Native table | `control` |
| Define content | `set_columns()`, `set_rows()` |
| Import | `load_records()`, `load_dataframe()` |
| Export in memory | `to_records()`, `to_csv()`, `to_dataframe()` |
| Save or download | `save_csv()` |

## Project templates

The CLI provides four runnable starting points:

| Command | What it demonstrates |
|---|---|
| `flet-mvc start -d my_app` | Small class-oriented MVC project |
| `flet-mvc reactive -d my_app` | Computed state and `FletComponent` |
| `flet-mvc routes -d my_app` | Official Flet Router and native views |
| `flet-mvc tabs -d my_app` | Current `Tabs`, `TabBar`, and `TabBarView` |

Preview every file without writing:

```bash
flet-mvc reactive --destination my_app --dry-run
```

Existing files are not overwritten by default. After reviewing the
destination, `--force` replaces template files:

```bash
flet-mvc reactive --destination my_app --force
```

Each template includes a short local README and its own `pyproject.toml`.

## Public API at a glance

| Area | Public names |
|---|---|
| Model | `FletModel`, `Datapoint`, `DatapointChange`, `data`, `computed` |
| Declarative hook | `use_datapoint` |
| Binding | `register_control_binding` and binding exceptions |
| Components | `FletComponent`, `send`, `receive`, `NO_CHANGE` |
| Tables | `DataTableAdapter` |

The main errors are:

- `DatapointError`: base reactive-state error;
- `DatapointBindingError`: binding or atomic synchronization failed;
- `UnsupportedControlError`: no safe default field is registered;
- `DatapointDependencyError`: dependency declaration is invalid;
- `DependencyCycleError`: the graph contains a cycle.

Pre-1.0 compatibility aliases and duplicate Flet layers were removed before
the stable API was published. The exact replacements are in
[`MIGRATION.md`](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md).

## Development

Install the repository with development dependencies:

```bash
git clone https://github.com/o0Adrian/flet-mvc.git
cd flet-mvc
python -m pip install -e ".[dev]"
```

Run the fast checks:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

The repository also contains real Flet browser, Pyodide, generated-template,
and packaged integration checks. See
[`CONTRIBUTING.md`](https://github.com/o0Adrian/flet-mvc/blob/master/CONTRIBUTING.md)
for the complete workflow.

## License

MIT. See [LICENSE](https://github.com/o0Adrian/flet-mvc/blob/master/LICENSE).
