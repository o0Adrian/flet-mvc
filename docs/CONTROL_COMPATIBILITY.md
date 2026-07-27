# Flet control binding compatibility

[Main guide](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Guía en español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md) ·
[Migration guide](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md)

This matrix documents flet-mvc 1.0 with Flet 0.86.3.

The short rule is:

- use automatic binding only for the 21 controls listed below;
- choose the field explicitly for every structural or custom binding;
- use `ft.Ref` when you need the control object, not its state.

The intentionally small registry is a safety feature. Current Flet controls
are sparse dataclasses and often expose many valid properties. Guessing the
first property that happens to exist can bind domain state to layout,
decoration, or child controls by accident.

## Three different tools

### 1. Bind a value automatically

Pass a mutable datapoint as a Flet `ref` when the control is in the matrix:

```python
import flet as ft

from flet_mvc import FletModel, data


class ProfileModel(FletModel):
    @data
    def name(self) -> str:
        return "Ada"


model = ProfileModel()
field = ft.TextField(ref=model.name)
label = ft.Text(ref=model.name)
```

Construction pushes `"Ada"` into both `value` fields. A later
`model.name.set("Grace")` updates both. A `TextField.on_change` event pulls the
edited value into the model and then calls the original application handler.

### 2. Bind a chosen field explicitly

Use explicit binding when the field is structural, the control is not in the
matrix, or the application intentionally wants a non-default field:

```python
class LayoutModel(FletModel):
    @data
    def cards(self) -> list[ft.Control]:
        return []

    @data
    def options(self) -> list[ft.DropdownOption]:
        return []


model = LayoutModel()
column = ft.Column()
model.cards.bind(column, "controls")

dropdown = ft.Dropdown()
model.options.bind(dropdown, "options")
```

This remains reactive, but the application owns the field choice.

### 3. Keep a reference to a control

Use native Flet `ft.Ref` when no model value should synchronize:

```python
field_ref = ft.Ref[ft.TextField]()
field = ft.TextField(ref=field_ref)


async def focus_field() -> None:
    if field_ref.current is not None:
        await field_ref.current.focus()
```

A control object is usually a UI concern, not domain state.

## Automatic bindings

These 21 core control classes have a single safe default in Flet 0.86.3.
Registrations use the real type and follow its MRO, so a normal subclass
inherits the same contract.

| Control | State field | Input event |
|---|---|---|
| `Checkbox` | `value` | `on_change` |
| `CupertinoCheckbox` | `value` | `on_change` |
| `CupertinoSlider` | `value` | `on_change` |
| `CupertinoSwitch` | `value` | `on_change` |
| `Dropdown` | `value` | `on_select` |
| `Icon` | `icon` | — |
| `IconButton` | `icon` | — |
| `Image` | `src` | — |
| `Markdown` | `value` | — |
| `NavigationBar` | `selected_index` | `on_change` |
| `NavigationRail` | `selected_index` | `on_change` |
| `ProgressBar` | `value` | — |
| `ProgressRing` | `value` | — |
| `RadioGroup` | `value` | `on_change` |
| `SearchBar` | `value` | `on_change` |
| `Slider` | `value` | `on_change` |
| `Switch` | `value` | `on_change` |
| `Tabs` | `selected_index` | `on_change` |
| `Text` | `value` | — |
| `TextField` | `value` | `on_change` |
| `TextSpan` | `text` | — |

An em dash means one-way model-to-control synchronization by default. The
field can still be pulled manually with `point.pull(control)` when the
application changes it outside a normal binding event.

## Why these defaults were chosen

### Dropdown

The model usually owns the selected key, so `Dropdown` binds `value` and pulls
through Flet 0.86's `on_select` event:

```python
class ColorModel(FletModel):
    @data
    def selected_color(self) -> str:
        return "blue"

    @data(bind="options")
    def color_options(self) -> list[ft.DropdownOption]:
        return [
            ft.DropdownOption(key="blue", text="Blue"),
            ft.DropdownOption(key="green", text="Green"),
        ]


model = ColorModel()
dropdown = ft.Dropdown(
    ref=model.selected_color,
    options=model.color_options.value,
)
```

`options` is structural and therefore explicit. `DropdownM2` is deprecated by
Flet for removal in 1.0 and is not registered.

### Tabs

`Tabs.selected_index` represents the selected state. The current tab
definitions and panels belong to separate structural controls:

- `TabBar.tabs`;
- `TabBarView.controls`;
- the layout held by `Tabs.content`.

Bind those fields explicitly only if the domain model truly owns the
structure. The number of tabs must still match the number of panels, and
`TabBarView` needs bounded layout space.

### Icons, images, and text

- `Icon` and `IconButton` bind their semantic `icon` field.
- `Image` binds its source string through `src`.
- `Text` and `Markdown` bind `value`.
- `TextSpan` binds `text`.

Button `content` is not treated as state. `ElevatedButton` is deprecated by
Flet for removal in 1.0 and has no compatibility registration; use
`ft.Button`.

### Selection and progress

Navigation controls and Tabs bind the selected index. Checkbox, switch,
slider, radio, search, and dropdown inputs use their current value event.
Progress controls are output-only by default.

## Fields that are never guessed

The following categories require an explicit field:

- child structure: `content`, `controls`, `actions`, `tabs`, `rows`, `cells`;
- data choices: `options`, `items`, `destinations`, chart series or shapes;
- layout and styling: size, alignment, padding, color, decoration, visibility;
- services and methods: file picking, storage, clipboard, focus, navigation;
- optional extension controls;
- ambiguous custom controls.

This means an unsupported control produces `UnsupportedControlError` even if
it happens to expose a property named `value`. The error protects the
application from accidental contracts.

## Explicit binding patterns

### A fixed field for one datapoint

Use `bind=` when every control attached to that datapoint uses the same field:

```python
class BoardModel(FletModel):
    @data(bind="controls")
    def cards(self) -> list[ft.Control]:
        return []
```

Then Flet's `ref=` syntax can still be used:

```python
model = BoardModel()
board = ft.Column(ref=model.cards)
```

### One control instance

Choose the field when binding:

```python
model.cards.bind(board, "controls")
model.cards.set([ft.Text("One"), ft.Text("Two")])
```

This is the best option when only one site has the special contract.

### Every instance of a custom class

Register the actual type:

```python
register_control_binding(
    SelectionControl,
    "selection",
    expected_type=str,
    event="on_change",
)
```

`expected_type` is optional. When present, flet-mvc validates values before
changing any bound control. `event` is also optional and must name the current
Flet event that signals a user-side change.

The registry follows the control's method resolution order. A subclass of
`SelectionControl` inherits this registration unless its exact type gets a
more specific one.

## Binding lifecycle

For a mutable datapoint:

1. `point.bind(control, field)` validates the contract and pushes the current
   value.
2. A registered input event calls `point.pull(control)` before the original
   event handler.
3. `point.set(value)` or `point.update(transform)` pushes to every live
   binding.
4. `point.sync()` pushes the unchanged current value again.
5. `point.pull(control)` reads one chosen control into the model.
6. `point.unbind(control)` restores the original event handler and detaches
   that control.
7. `point.unbind()` detaches all controls.

Bindings keep weak references when the control type supports them. Discarded
controls do not remain alive because of a datapoint.

Synchronization is atomic across live controls. flet-mvc validates the value
first. If an assignment still fails, earlier assignments are rolled back and
the datapoint remains unchanged.

The same failure also aborts the surrounding datapoint commit or outer
`batch()`. Values from other datapoints, computed results, control properties,
dependency edges, pending queues, and `model.revision` return to their
pre-commit state, and subscribers are not notified.

Computed datapoints may be bound for one-way output, but they never install a
pull event and reject manual `pull()` because they are read-only.

### Inspect live bindings

`point.current` returns the first live bound control, or `None`. This property
also implements the protocol Flet's `ref=` constructor uses. When a datapoint
is bound to several controls, `point.controls` returns all live controls as a
tuple.

These properties inspect value bindings; they are not a general reference
container. Use `ft.Ref` when accessing the control object itself is the goal.

## Existing input handlers

An automatic input binding preserves the handler already assigned by the
application:

```python
events = []
field = ft.TextField(
    ref=model.name,
    on_change=lambda: events.append(model.name.value),
)
```

When `on_change` runs, flet-mvc first pulls `field.value`; the original handler
therefore reads the new model value. Both zero-argument and event-argument
handlers are supported, including asynchronous handlers.

Unbinding restores the original handler only if the installed wrapper is
still present. If the application replaced the handler later, flet-mvc does
not overwrite that newer choice.

## DataTable guidance

`DataTable.rows` is structural and not automatic. Prefer
`DataTableAdapter` when building a tabular view:

```python
from flet_mvc import DataTableAdapter


adapter = DataTableAdapter().load_records(
    [
        {"name": "Ada", "score": 98},
        {"name": "Grace", "score": 95},
    ]
)
table_control = adapter.control
```

Keep domain records in a normal datapoint and update the adapter from a
subscription or declarative component.

## Optional and third-party controls

Audio, charts, video, web views, and other extensions are not imported into
the automatic registry. This keeps their packages optional and avoids
class-name collisions.

Choose the relevant state field in the application:

```python
model.audio_source.bind(audio_control, "src")
```

Or register the imported extension class explicitly if the whole application
uses one contract:

```python
register_control_binding(AudioControl, "src")
```

Value objects such as `Tooltip` are not controls and should not be used as a
Flet `ref` target.

## Adding a default binding to flet-mvc

A contribution must demonstrate that:

1. the control is current, core, and non-deprecated in the required Flet line;
2. one non-structural property is clearly its semantic state;
3. its current input event is known, if applicable;
4. an existing handler is preserved;
5. subclass MRO lookup is safe;
6. push, pull, reset, unbind, weak cleanup, and atomic failure are tested;
7. a real rendered test covers behavior that construction cannot prove.

If any point is ambiguous, explicit application binding is the correct
answer.
