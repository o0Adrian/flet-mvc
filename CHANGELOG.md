# Changelog

Notable project changes are recorded here. Versions follow semantic
versioning; dates use `YYYY-MM-DD`.

[Project guide](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Guía en español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md) ·
[Migration guide](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md)

## 1.0.0 - Unreleased

Version 1.0 is still being prepared. The API cleanup below happened before
the stable release so the project would not publish two competing public
designs.

### Project direction

- Repositioned flet-mvc around advanced reactive domain models.
- Made class-oriented MVC an optional project structure instead of a required
  runtime abstraction.
- Kept Flet as the source of truth for controls, declarative components,
  views, routing, dialogs, navigation, references, and rendering.
- Reduced the package root to the supported model, hook, component, table, and
  error APIs.

### Reactive model

- Reimplemented `@data` as mutable state isolated per model instance and
  session.
- Added `@computed` for read-only derived state.
- Added inferred and declared dependencies, dynamic edge replacement,
  deterministic propagation, diamond coalescing, and cycle detection.
- Made `point.value`, `point.set()`, `point.update()`, and `point.reset()` the
  canonical value lifecycle.
- Made `data[T]`, `computed[T]`, and `Datapoint[T]` generic, preserving return
  types through descriptors, values, updates, hooks, and Flet `ref=`.
- Added synchronous and asynchronous subscriptions with immutable
  `DatapointChange` notifications.
- Added nested `batch()` blocks with atomic outer commits. Failures in the
  block, computed propagation, or control synchronization restore datapoint
  values, controls, graph edges, pending queues, and `revision` without
  publishing notifications.
- Added shallow snapshots, strict or lenient restores, dependency inspection,
  and Graphviz DOT output.
- Made model construction eager and added validated mutable constructor
  overrides.
- Made `FletModel` inherit Flet's native `ft.Observable`, allowing direct use
  from `@ft.component`.
- Added `model.revision`, incremented once per stable datapoint commit or
  outer batch.
- Added `use_datapoint()` for granular declarative rerenders with automatic
  subscription replacement and unmount cleanup.
- Kept datapoint subscriptions (`DatapointChange`) distinct from the native
  model Observable callback (`sender, field`).
- Added atomic multi-control synchronization with rollback, weak binding
  references, explicit bind/unbind/pull/sync operations, and current Flet
  input events.
- Made initial binding atomic too: handler-installation failures restore the
  control's previous value and leave no partial binding.

### Control bindings

- Replaced broad first-match field guessing with a registry keyed by actual
  control types.
- Limited automatic binding to 21 current core controls with one stable state
  field.
- Changed `Dropdown`'s safe default to `value` with `on_select`.
- Required explicit bindings for structural fields such as `content`,
  `controls`, `actions`, `options`, and `rows`.
- Added `register_control_binding()` for explicit custom-control contracts.
- Removed automatic entries for deprecated controls, optional extension
  classes, and class-name-only matches.
- Added clear `UnsupportedControlError` failures instead of ambiguous
  fallbacks.

### Native Flet integration

- Adopted Flet 0.86's `ft.run`, `ft.Button`, `ft.Colors`, `ft.Icons`, current
  Tabs, services, dialogs, navigation, and control dataclasses.
- Moved declarative applications to Flet's `@ft.component`, `page.render()`,
  and observable lifecycle.
- Moved routing applications to the official `ft.Router`, `ft.Route`,
  `ft.View`, and `page.render_views()` APIs.
- Moved control-only references to native `ft.Ref`.
- Kept MVC controllers as ordinary application classes rather than a library
  base class.

### Model-aware controls

- Implemented `FletComponent` as a native `@ft.control` subclass of
  `ft.Column`.
- Added descriptor targets such as `@send(CounterModel.count)` and
  `@receive(CounterModel.count)`.
- Added synchronous and asynchronous send/receive flows, `NO_CHANGE`,
  component-subtree updates, subscription cleanup, and cancellation of
  outstanding work.
- Required asynchronous `@send` work to use `async def`; a synchronous send
  method returning an awaitable raises `TypeError`.

### Data tables

- Added `DataTableAdapter` around the current native `ft.DataTable`.
- Added the canonical `control`, `set_columns()`, `set_rows()`,
  `load_records()`, `load_dataframe()`, `to_records()`, `to_csv()`,
  `to_dataframe()`, and `save_csv()` API.
- Added schema, visibility, row-width, cell-content, and export validation.
- Added pandas-style and Polars-style ingestion without a mandatory DataFrame
  dependency.
- Added current asynchronous `FilePicker.save_file()` export with CSV bytes.

### CLI and templates

- Rebuilt template generation with packaged resources, complete collision
  preflight, staged writes, rollback, `--dry-run`, `--destination`, and
  explicit `--force`.
- Kept `start`, `reactive`, `routes`, and `tabs` as focused runnable examples.
- Updated templates to the canonical datapoint API and current Flet controls.
- Updated the routing template to use Flet's official Router.
- Added independent project metadata and a local walkthrough to every
  template.

### Removed before the stable release

- Removed `DataPoint` and `Component` aliases.
- Removed `point()`, `set_value()`, collection helper methods,
  `set_default()`, `clear_default()`, `has_set_value()`, and
  `__hard_reset__()`.
- Removed the `transaction()` alias; use `batch()`.
- Removed `RefOnly`; use `ft.Ref` for object references.
- Removed `FletView` and `view.py`; use native Flet controls, components, and
  views.
- Removed `RouteHandler`, route type aliases, and `routing.py`; use
  `ft.Router`.
- Removed alert constants, alert helpers, and `alert.py`; use native Flet
  dialogs.
- Removed `FletController` and `controller.py`; MVC controllers are ordinary
  application classes, functions, or services.
- Removed controller wrappers for updates, alerts, dropdown options, and
  navigation.
- Removed DataTable aliases, old misspelled methods, and datapoint table
  proxies.
- Removed magic structural bindings and deprecated `DropdownM2` /
  `ElevatedButton` compatibility.

### Compatibility and packaging

- Replaced the historical unbounded Flet dependency with
  `flet>=0.86.3,<0.87`.
- Raised the minimum Python version to 3.10 and added Python 3.10–3.14 CI.
- Moved packaging from `setup.py` to PEP 517/621 `pyproject.toml`.
- Added typed-package metadata and a focused optional `dataframe` dependency
  group.
- Kept media/chart extension selection in applications instead of turning
  flet-mvc into an extension dependency aggregator.
- Added wheel/source-distribution validation, clean-wheel smoke tests, bounded
  locks, and package metadata checks.

### Verification

- Replaced historical scripts with focused model, hook, binding, component,
  public-boundary, table, CLI, documentation, and type-checking tests.
- Added real Flutter Web tests for a server-backed app and a static Pyodide
  build.
- Added rendered interaction checks for all generated templates.
- Added packaged desktop/device testing with Flet's integration runner.
- Added Ruff, formatting, mypy, coverage, Python-version, build, Twine, and
  installation checks in CI.

### Documentation

- Rewrote the English and Spanish guides as equivalent, linear walkthroughs.
- Added a pre-1.0 migration map for every removed API.
- Added a 21-control compatibility matrix and explicit-binding guide.
- Audited every official Flet release heading from 0.9.0 through 0.86.3.
- Added contributor, template, testing, packaging, and troubleshooting
  documentation.
- Added tests that compile Python examples and verify local documentation
  links and README example parity.

## 0.1.5

- Added the original `start`, `routes`, and `tabs` CLI templates.
- Fixed template packaging issues.

## 0.1.0

- Added the original datapoint-as-reference experiment.
- Added `RefOnly`, multi-reference support, reset/default operations, and
  early control tests.

Earlier 0.1.x versions were experimental packaging and template iterations.
