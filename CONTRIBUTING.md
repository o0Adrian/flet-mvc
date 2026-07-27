# Contributing to flet-mvc

[Project guide](https://github.com/o0Adrian/flet-mvc/blob/master/README.md) ·
[Guía en español](https://github.com/o0Adrian/flet-mvc/blob/master/README.es.md) ·
[Migration guide](https://github.com/o0Adrian/flet-mvc/blob/master/MIGRATION.md)

Thank you for improving flet-mvc. The project is preparing its first stable
API, so a contribution should keep the library small, predictable, and
aligned with native Flet.

## 1. Know the project boundary

flet-mvc owns:

- advanced reactive domain state;
- dependency propagation, subscriptions, batches, and snapshots;
- safe or explicit control binding;
- model-aware composite controls;
- a focused DataTable adapter and project templates.

Flet owns controls, `@ft.component`, `ft.View`, `ft.Router`, dialogs,
navigation, `ft.Ref`, updates, and rendering. Avoid adding a second wrapper
when current Flet already provides the feature.

MVC is an optional application structure. A controller belongs to the
generated/application code as a normal class, function, or service; flet-mvc
does not own a controller base.

The main runtime files are:

| Path | Responsibility |
|---|---|
| `flet_mvc/model.py` | Datapoints, graphs, observability, and bindings |
| `flet_mvc/hooks.py` | Granular `use_datapoint` declarative hook |
| `flet_mvc/component.py` | `FletComponent`, `send`, and `receive` |
| `flet_mvc/datatable.py` | Native DataTable construction and export |
| `mvc_commands/cli.py` | Safe project generation |
| `mvc_commands/templates/` | Runnable learning projects |

## 2. Create a development environment

Use Python 3.10 or newer. Compatibility work must use exactly Flet 0.86.3.

With `venv` and pip:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "flet==0.86.3" -e ".[dev]"
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

With uv:

```bash
uv sync --extra dev
```

Confirm the resolved versions before debugging:

```bash
python -c "import importlib.metadata as m; print(m.version('flet'))"
python -m pip check
```

The first command must print `0.86.3`.

## 3. Run the fast checks

Run from the repository root:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest
```

For a behavior change, include coverage:

```bash
python -m pytest \
  --cov=flet_mvc \
  --cov=mvc_commands \
  --cov-report=term-missing
```

Test layers:

| Path | What it proves |
|---|---|
| `tests/test_model.py` | State, propagation, batches, snapshots, and errors |
| `tests/test_hooks.py` | Granular rerenders and hook cleanup |
| `tests/test_control_bindings.py` | Every safe binding and two-way event |
| `tests/test_component.py` | Component targets, lifecycle, and async cleanup |
| `tests/test_datatable.py` | Table construction, validation, and export |
| `tests/test_mvc_shell.py` | Small root API and public/native boundary |
| `tests/test_cli.py` | Generator safety and packaged templates |
| `tests/test_documentation.py` | Examples, links, and EN/ES parity |
| `type_tests/` | Downstream public API checked by mypy |
| `integration/web_tests/` | Real Flutter Web and static Pyodide behavior |
| `integration/tests/` | Packaged Flet integration behavior |

Prefer a small regression test that fails for the original bug. Add a rendered
test when construction alone cannot prove the behavior.

## 4. Test real Flet behavior when needed

Python-side construction cannot prove that Flutter can serialize, mount,
render, receive an event, and update a control.

Run integration tests for changes to:

- control bindings or input events;
- Flet observability and declarative rendering;
- `FletComponent` mount/unmount or async work;
- native Router, views, or tabs;
- DataTable rendering and file services;
- templates, Flet packaging, or Pyodide.

Set up the integration project:

```bash
cd integration
uv sync
```

Run the browser suite:

```bash
uv run pytest web_tests
```

It exercises a server-backed Flet Web session, a static Pyodide build, and
all generated projects in Chrome. Chrome must be installed. Set
`FLET_MVC_CHROME_PATH` if Playwright cannot find the normal `chrome` channel.

Run a packaged native suite on a configured target:

```bash
uv run flet test macos --yes --no-rich-output
```

Replace `macos` with the target under test. This requires that platform's
Flutter and native build toolchain.

Keep the integration project's Flet development-package entry pointed at
`..`. Otherwise packaging may install the historical PyPI release instead of
the checkout being tested.

## 5. Rules for reactive model changes

The stable model vocabulary is:

- mutable `@data`;
- read-only `@computed`;
- `point.value`, `set()`, `update()`, and `reset()`;
- `subscribe()`, `bind()`, `unbind()`, `pull()`, and `sync()`;
- `batch()`, `snapshot()`, `restore()`, `dependency_graph`, and
  `dependency_dot()`;
- native model observability, `revision`, and `use_datapoint()`.

Preserve these invariants:

- A descriptor never stores instance or session state.
- Construction eagerly validates every definition.
- A computed datapoint cannot be mutated or restored directly.
- Dependency propagation is deterministic and cycle-safe.
- Subscribers see a fully consistent graph.
- Nested batches share one atomic outer commit and recompute each affected
  node once at that boundary.
- An exception from the outer batch body, computed propagation, or control
  synchronization restores values, controls, graph edges, queues, and
  `revision`; the failed commit publishes no notification.
- A failed control synchronization leaves datapoint and controls unchanged.
- Async subscriber work is retained and exceptions are consumed or logged.
- `FletModel` continues to honor the `ft.Observable` contract.
- Datapoint subscribers receive `DatapointChange`; model subscribers retain
  Flet's `(sender, field)` callback.
- `revision` and native model notification advance once per stable datapoint
  commit, including once for an outer batch.
- `use_datapoint` replaces subscriptions when its point changes and disposes
  them on component unmount.

Do not reintroduce pre-1.0 aliases merely to avoid changing tests. This is the
window in which the public surface is deliberately being cleaned.

## 6. Rules for control bindings

Automatic binding is intentionally narrow. A new default entry is acceptable
only when all of these are true:

1. the class is a non-deprecated control in the required core Flet package;
2. one property clearly represents its application state;
3. the property is not structural UI such as `content`, `controls`, `actions`,
   `options`, or `rows`;
4. the control type is used as the registry key, not only its class name;
5. any two-way event uses the current Flet event and preserves an existing
   handler;
6. construction, push, pull, reset, unbind, and garbage collection are tested;
7. the compatibility matrix is updated.

Prefer `point.bind(control, "field")` or
`register_control_binding(ControlType, "field")` when any criterion is
uncertain. Unknown bindings must fail clearly instead of guessing.

Keep optional extension packages optional at import time. Do not add
class-name matching to avoid an import; require an explicit binding in the
application instead.

## 7. Rules for native Flet integration

- Use `@ft.component` for normal declarative UI.
- Use `use_datapoint(point)` for a granular rerender boundary.
- Use `FletComponent` only for its send/receive lifecycle.
- Component documentation and templates use descriptor targets such as
  `@send(Model.field)`.
- A receiver updates only its `FletComponent` subtree, never the whole page.
- A synchronous `@send` method returns a concrete value. Awaiting work must be
  declared with `async def`; do not accept a coroutine returned by regular
  `def`.
- Use `ft.Ref` for a reference to a control object.
- Use `ft.View`, `ft.Router`, and `ft.Route` for navigation.
- Use Flet's dialog, service, and update APIs directly.
- Keep runtime code and templates free of deprecation warnings.

If a feature belongs in Flet, link to the Flet API instead of adding a local
facade.

## 8. Check generated projects

When changing the CLI, templates, or package data, generate all templates into
empty directories:

```bash
flet-mvc start -d /tmp/flet-mvc-basic
flet-mvc reactive -d /tmp/flet-mvc-reactive
flet-mvc routes -d /tmp/flet-mvc-routes
flet-mvc tabs -d /tmp/flet-mvc-tabs
```

Compile each project and run the browser integration suite for UI or event
changes.

Also exercise collision handling:

```bash
flet-mvc start -d /tmp/flet-mvc-basic --dry-run
```

The generator must never silently overwrite a user file, follow a destination
symlink, or leave a partly copied project after failure.

## 9. Check distributions

Build the artifacts:

```bash
python -m build
python -m twine check dist/*
```

Install the wheel into a new environment and verify:

1. `import flet_mvc` loads from the wheel;
2. Flet resolves inside `>=0.86.3,<0.87`;
3. `flet-mvc --version` matches distribution metadata;
4. all four templates are packaged and compile;
5. `py.typed` is present;
6. the source distribution contains both READMEs, migration, changelog,
   contributor guide, and the two documents under `docs/`.

Do not mark 1.0 as released until clean-wheel and packaged integration checks
pass from the exact release commit.

## 10. Update documentation with behavior

For a public behavior change:

1. update the simplest relevant example in `README.md`;
2. make the equivalent change in `README.es.md`;
3. update `MIGRATION.md` if an application must change;
4. update `docs/CONTROL_COMPATIBILITY.md` for any binding decision;
5. update the unreleased section of `CHANGELOG.md`;
6. update `docs/FLET_RELEASE_AUDIT.md` for a Flet compatibility decision;
7. run `python -m pytest tests/test_documentation.py`.

The English and Spanish README files must have the same Python examples in
the same order. The documentation test compares their syntax trees.

Use absolute GitHub links from top-level guides when the link must also work
on PyPI. Keep each example focused on one idea and use the canonical API only.

## 11. Raising the Flet range

Never change the `<0.87` cap based only on a successful import.

For a new Flet line:

1. read every intervening official changelog heading and breaking-change note;
2. inspect every Flet type and event used by runtime and templates;
3. run the complete fast suite on Python 3.10–3.14;
4. run dynamic web, static Pyodide, generated-template, and packaged tests;
5. confirm no deprecation warnings;
6. update dependency groups and both lock files;
7. update the release audit, control matrix, READMEs, and changelog.

Record exact evidence and keep the upper bound until all layers pass.

## Pull request checklist

- The change stays inside the project boundary.
- Runtime behavior has a focused test.
- Real rendering is tested when Python objects are insufficient evidence.
- The canonical API is used; removed aliases are not restored.
- English and Spanish examples remain aligned.
- Ruff, formatting, mypy, and pytest pass.
- Generated projects and distributions were checked when affected.
- Compatibility decisions are explained in the pull request.
- Generated builds, environments, caches, and personal paths are not included.
