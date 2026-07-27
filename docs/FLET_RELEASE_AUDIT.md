# Flet compatibility audit: 0.9.0 to 0.86.3

[Project guide](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Guía en español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md) ·
[Migration guide](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md) ·
[Control matrix](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md)

This document records how flet-mvc moved from the Flet line used by release
0.1.5 to its 1.0 compatibility target.

Primary sources:

- Flet's official
  [changelog](https://github.com/flet-dev/flet/blob/main/CHANGELOG.md);
- Flet's
  [breaking-change index](https://flet.dev/docs/updates/breaking-changes/);
- the official [Router guide](https://flet.dev/docs/controls/router/);
- the upstream
  [0.70/1.0 migration issue](https://github.com/flet-dev/flet/issues/5238).

## Final compatibility contract

- **Flet dependency:** `>=0.86.3,<0.87`.
- **Python dependency:** `>=3.10`; CI covers 3.10–3.14.
- **Reactive core:** mutable `@data`, read-only `@computed`, deterministic
  propagation, subscriptions, batches, snapshots, and graph inspection.
- **Native observability:** `FletModel` is an `ft.Observable`;
  `use_datapoint()` provides a granular declarative subscription.
- **Control binding:** 21 non-deprecated core controls have a safe automatic
  state field; every structural, extension, or ambiguous field is explicit.
- **Native Flet boundary:** Flet owns `@ft.component`, `ft.Ref`, `ft.View`,
  `ft.Router`, dialogs, services, navigation, and rendering.
- **Custom controls:** `FletComponent` is a current `@ft.control` subclass and
  uses descriptor targets for send/receive.
- **Data tables:** `DataTableAdapter` wraps a current native `ft.DataTable` and
  uses the current asynchronous FilePicker contract.

There is no compatibility layer for deprecated buttons or DropdownM2, no
class-name-based extension registry, and no parallel alert, view, or router
framework. MVC controllers remain ordinary application code; the core exports
no controller base.

## Audit method

1. Use Flet 0.9.0 as the historical baseline documented by flet-mvc 0.1.5.
2. Read every later release heading in the official changelog through 0.86.3.
3. Inspect breaking-change guides for APIs used by runtime, templates, tests,
   packaging, or documentation.
4. Inspect the installed Flet 0.86.3 types and signatures directly.
5. Remove duplicated or deprecated abstractions before stabilizing the 1.0
   public API.
6. Test Python behavior, real Flutter rendering, static Pyodide, generated
   projects, and a packaged app.
7. Cap the dependency before the next unaudited Flet minor line.

The table follows official changelog headings. It does not invent headings
for versions absent from that file. In particular, the official history has
no 0.28.1 heading and jumps from 0.28.3 to 0.70.0, then to 0.80.0.

“No direct change” means the release was reviewed but did not change an API
owned or called by flet-mvc. Applications may use other Flet features affected
by that release.

## Release-by-release review

| Flet release | Impact on the flet-mvc 1.0 core |
|---|---|
| 0.9.0 | Historical compatibility baseline for flet-mvc 0.1.5. |
| 0.10.0 | DataTable row-height changes were reviewed. The new adapter does not set the removed styling fields and validates current columns/cells. |
| 0.10.1 | No direct change. |
| 0.10.2 | FilledButton patch only; no direct change. |
| 0.10.3 | No direct change. |
| 0.11.0 | Python 3.12 support was noted; no direct API change. |
| 0.12.0 | Audio and FilePicker fixes were reviewed; no historical service API was retained. |
| 0.12.1 | Dialog, BottomSheet, and window fixes were reviewed; no direct change. |
| 0.12.2 | Control representation changes reinforced avoiding control internals; no direct code change. |
| 0.13.0 | New controls only; no direct change. |
| 0.14.0 | New controls only; no direct change. |
| 0.15.0 | Added properties and dialog fixes were reviewed; no direct change. |
| 0.16.0 | Cupertino controls and Tabs fixes were reviewed. Current safe Cupertino state controls are registered by actual type. |
| 0.17.0 | New controls only; no direct change. |
| 0.18.0 | TextStyle and dialog changes were reviewed; no direct change. |
| 0.19.0 | Dialog/adaptive additions were reviewed; no direct change. |
| 0.20.0 | Audio, AudioRecorder, Video, and WebView moved to extension packages. The final core neither imports nor automatically registers extension classes; applications install and bind them explicitly. |
| 0.20.1 | `Control.on_update` became `before_update`. Runtime and adapter code use current control lifecycle APIs and do not keep an old hook shim. |
| 0.20.2 | Adaptive/dialog patches were reviewed; no direct change. |
| 0.21.0 | Cupertino and media additions were reviewed; only unambiguous current core value controls entered the final registry. |
| 0.21.1 | No direct change. |
| 0.21.2 | Python 3.12 cleanup and build fixes; no direct change. |
| 0.22.0 | Control enhancements were reviewed; no direct change. |
| 0.22.1 | Chart and Dropdown patches were reviewed; no direct change. |
| 0.23.0 | Window/browser properties moved to objects such as `page.window`. Runtime and templates contain no removed flat window wrappers. |
| 0.23.1 | Window encapsulation follow-up; no direct change. |
| 0.23.2 | Resize and dialog fixes were reviewed; no direct change. |
| 0.24.0 | `Tooltip` became a value dataclass. It is not treated as a visual control or ref binding target. |
| 0.24.1 | Tooltip patch reviewed; no direct change. |
| 0.25.0 | Application code moved to `Colors`/`Icons`, current icon fields, and current button content. Button content is structural and is not an automatic datapoint binding. |
| 0.25.1 | No direct change. |
| 0.25.2 | Tooltip/control-state fixes were reviewed; no direct change. |
| 0.26.0 | Deprecated page dialog/snackbar/banner and window-era APIs were removed. flet-mvc removed its alert/controller facade and documents native `page.show_dialog()` instead. |
| 0.27.0 | Removal of 0.24 deprecations confirmed that Tooltip must remain outside the binding matrix. |
| 0.27.1 | No direct change. |
| 0.27.2 | `Control.build()` restoration was reviewed; flet-mvc does not depend on the historical implementation. |
| 0.27.3 | No direct change. |
| 0.27.4 | No direct change. |
| 0.27.5 | No direct change. |
| 0.27.6 | `update_async` was removed. No controller/update compatibility wrapper is shipped. |
| 0.28.0 | Removal of 0.25 deprecations confirmed the enum/icon migration. |
| 0.28.2 | No direct change. |
| 0.28.3 | FilePicker save fixes were reviewed; the adapter targets the later 0.86 async bytes API. |
| 0.70.0 | Major sparse-dataclass control rewrite. The old first-property heuristic was discarded; the final registry is keyed by real types, contains 21 semantic state fields, and requires explicit structural/extension bindings. Native `ft.Ref` owns object references. |
| 0.80.0 | Major API redesign. Runtime/templates moved to `ft.run`, `ft.Button`, current Tabs, current alignment/value objects, async services, `@ft.control`, and declarative component APIs. Duplicate view, route, alert, and controller layers were removed in favor of native Flet. |
| 0.80.1 | Migration regressions and fixes were reviewed; no additional compatibility shim was added. |
| 0.80.2 | Patch release reviewed against the current control model. |
| 0.80.3 | Patch release reviewed; no direct change. |
| 0.80.4 | Patch release reviewed; no direct change. |
| 0.80.5 | Patch release reviewed; no direct change. |
| 0.81.0 | Protocol/control improvements were reviewed; no public flet-mvc change. |
| 0.82.0 | Runtime, component, and packaging changes were reviewed; native component integration remained valid. |
| 0.82.2 | Patch release reviewed; no direct change. |
| 0.83.0 | Runtime/build changes were reviewed; templates remained on current APIs. |
| 0.83.1 | Patch release reviewed; no direct change. |
| 0.84.0 | Control/runtime changes were reviewed; no direct change. |
| 0.85.0 | Deprecated spacing and border helpers were removed. Runtime and templates use current value objects and enums. |
| 0.85.1 | Patch release reviewed; no direct change. |
| 0.85.2 | Patch release reviewed; no direct change. |
| 0.85.3 | Patch release reviewed; no direct change. |
| 0.86.0 | Python 3.14 became the default packaged runtime; app files/storage, Android packaging, Pyodide resolution, protocol framing, and DataChannel changed. Build metadata, entry-point guards, storage assumptions, static-web tests, and packaged integration were reviewed against this line. |
| 0.86.1 | Top-level component/hook API documentation and build fixes were reviewed. `use_datapoint()` composes only public Flet hooks. |
| 0.86.2 | Components-mode session isolation and auto-update fixes directly affect mixed declarative/imperative apps. Real multi-session and rendered event tests target the fixed behavior; no local workaround is shipped. |
| 0.86.3 | Exact verified target. Embedded transport, Back navigation, windows, modal lifecycle, build assets, and Matplotlib fixes were reviewed. Native Router/View/dialog ownership lets applications receive these fixes without a duplicate flet-mvc layer. |

## Decisions derived from the audit

### Bound the dependency

The historical `flet>=0.7.4` requirement could resolve across multiple known
breaking redesigns. `flet>=0.86.3,<0.87` converts compatibility from an
assumption into a declared contract.

The cap is not a claim that 0.87 will be incompatible. It means 0.87 is
unknown until the same audit and test layers pass.

### Keep domain reactivity, reuse native UI

The durable flet-mvc contribution is its domain-state graph:

- isolated mutable datapoints;
- computed dependencies;
- deterministic batching;
- change events and snapshots;
- safe bindings where an imperative bridge is useful.

Flet now has maintained primitives for declarative rendering, observables,
hooks, references, views, routing, dialogs, and services. The final 1.0 API
integrates with those primitives instead of shadowing them.

MVC may still organize application files into model, view, and controller
responsibilities. That organization does not require a framework base class:
an application controller can be a dataclass, ordinary class, function, or
service.

### Honor both observable contracts

`FletModel` subclasses `ft.Observable`. After a datapoint graph stabilizes it
publishes one native notification with `field=None`, and `model.revision`
increments once. An outer batch is one commit. Normal public model attributes
still use Flet's usual field-specific notification.

Datapoint commits are atomic. If an outer batch body, computed evaluation, or
control binding fails, the runtime restores datapoint values, bound controls,
dependency edges, pending queues, and the prior revision. No datapoint or
native model notification is published for that failed commit. Nested batches
share the outer transaction; shallow snapshots remain a persistence and manual
state-capture API, not a prerequisite for rollback.

The APIs remain distinct:

- `point.subscribe(callback)` sends a `DatapointChange`;
- `model.subscribe(callback)` follows Flet's `(sender, field)` signature;
- `use_datapoint(point)` uses a Flet effect and state hook to rerender only the
  consuming component, replace the subscription if the point changes, and
  dispose it on unmount.

### Make automatic bindings small and semantic

The old broad heuristic became unsafe when controls acquired many sparse
dataclass fields. The final registry:

- is keyed by actual core control types;
- follows MRO for normal subclasses;
- contains only 21 current non-deprecated state controls;
- uses current two-way events;
- never guesses layout or child structure;
- raises a specific error for unknown controls.

`Dropdown` binds its selected `value` through `on_select`; it does not bind
`options`. `Tabs` binds `selected_index`; `TabBar.tabs`,
`TabBarView.controls`, and `Tabs.content` are explicit structural choices.
See the exact
[compatibility matrix](https://github.com/o0Adrian/flet-mvc/blob/master/docs/CONTROL_COMPATIBILITY.md).

### Do not aggregate Flet extensions

The flet-mvc core does not import, register, or install media/chart extension
families on behalf of an application. An application chooses its extension
package, imports the real control type, and binds a field explicitly when
needed.

The only feature extra owned by flet-mvc is `dataframe`, for pandas output from
`DataTableAdapter`. Development tooling remains in the `dev` extra.

### Use native references

Flet 0.86 provides a generic weak `ft.Ref.current` protocol. Maintaining a
second reference-only descriptor would duplicate its lifecycle and typing.
Datapoints represent values; native `ft.Ref` represents a control object.

`Datapoint.current` remains the Flet `ref=` binding protocol and returns the
first bound value control. It is not a replacement for a standalone
`ft.Ref`.

### Use current custom controls and components

The removed `UserControl` roadmap item became `FletComponent`, a real
`@ft.control` subclass of `ft.Column`. Python-only model/subscription fields
are skipped from Flet serialization.

Descriptor targets such as `@send(Model.field)` avoid the refactor hazards of
string paths. Mount establishes receivers; unmount disposes subscriptions and
cancels pending async work. A receiver updates only its component subtree.
Async send work must be declared with `async def`; returning an awaitable from
a synchronous send raises `TypeError` so it cannot be silently lost by Flet's
event dispatcher. Ordinary declarative UI continues to use `@ft.component`.

### Use Flet Router and native View

The official Router already owns route matching, nested layouts, dynamic
segments, navigation subscriptions, not-found rendering, managed view stacks,
Back behavior, and cleanup.

Maintaining another route stack would prevent applications from inheriting
upstream fixes such as the 0.86.3 Back/modal corrections. flet-mvc therefore
ships no route handler or view wrapper. Templates use `ft.Router`, `ft.Route`,
`ft.View`, `page.render()`, and `page.render_views()` directly.

### Keep tabs structural

Current Flet tabs divide responsibility among:

- `Tabs`, including `selected_index` and overall content;
- `TabBar.tabs`;
- `TabBarView.controls`.

Only selected state is automatic. Definitions, panels, and layout stay native
and explicit. This prevents the old `Tabs.tabs` assumption from returning.

### Keep DataTable adaptation separate from model state

`DataTableAdapter` wraps one native control and provides explicit
construction/import/export methods. Datapoints hold application records and
may update an adapter through a normal subscription or component.

This separation removes table-specific proxy methods from the reactive model
and keeps Flet DataTable validation close to the control.

## Verification layers

The compatibility claim uses several kinds of evidence:

| Layer | What it checks |
|---|---|
| Unit tests | Model isolation, computed graphs, batching, errors, bindings, components, adapter, public boundary, and CLI |
| Hook renderer tests | Real Flet hook scheduling, granular rerenders, replacement, and cleanup |
| Type tests | Public imports, descriptors, hooks, and downstream use |
| Dynamic browser tests | Serialization, mount, input pull, model push, components, tables, tabs, and Router in Flutter Web |
| Static Pyodide tests | The same core flow after a real `flet build web` |
| Template browser tests | All four generated projects render and respond |
| Packaged integration | The checkout is bundled and driven through Flet's official test runner |
| Python/packaging CI | Python 3.10–3.14, Ruff, mypy, distributions, clean-wheel install, and template smoke checks |

The packaged integration project points Flet at this checkout as a development
package. Without that setting, packaging could install flet-mvc 0.1.5 from
PyPI and test the wrong code.

## Checklist for the next Flet minor line

Before changing `<0.87`:

1. read every new official changelog and breaking-change entry;
2. inspect `Observable`, component hooks, Router/View, control refs, events,
   FilePicker, DataTable, Tabs, and `@ft.control`;
3. construct and push/pull all 21 automatic binding types;
4. confirm deprecated classes have not entered runtime or templates;
5. run the complete Python matrix and type checks;
6. run dynamic web, static Pyodide, template, and packaged integration tests;
7. rebuild the wheel and source distribution from the tested commit;
8. update this audit, the control matrix, both READMEs, migration guide,
   changelog, locks, and dependency cap.
