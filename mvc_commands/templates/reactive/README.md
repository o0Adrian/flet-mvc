# Reactive Flet MVC app

This template shows one complete reactive flow: a button changes `count`, the
component receives it, and the derived `message` updates automatically.

## 1. Install

Install [uv](https://docs.astral.sh/uv/) and run this command from the project
directory:

```bash
uv sync
```

This creates an isolated environment and installs the app and test tools.

## 2. Run

```bash
uv run flet run
```

Click **Add one** and watch both the number and message change.

## 3. Test

```bash
uv run pytest
```

The test clicks the counter and checks both reactive outputs.

## 4. File map

- `src/main.py` renders the model as a native Flet component.
- `src/models/counter.py` defines `count` and its computed `message`.
- `src/components/counter.py` receives the count and sends the next value.
- `tests/test_main.py` checks the complete click-to-render flow.
- `pyproject.toml` contains project and Flet build settings.

## 5. Next change

Add a `decrement()` method beside `increment()` in
`src/components/counter.py`, decorate it with `@send(CounterModel.count)`, and
connect it to a second button.
