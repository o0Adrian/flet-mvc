# Routed Flet MVC app

This template has a home page, a secondary page, and a safe not-found page.
Flet's native `Router` keeps the view stack in sync with the current route.

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

Use **Go to secondary view**, then **Return home**, to test navigation.

## 3. Test

```bash
uv run pytest
```

The test follows the same route flow and checks both pages.

## 4. File map

- `src/main.py` creates both MVC groups and defines the native route tree.
- `src/models/` contains the state for each page.
- `src/controllers/` contains navigation actions.
- `src/views/` contains the declarative components shown on each page.
- `tests/test_main.py` checks navigation in a real Flet app.
- `pyproject.toml` contains project and Flet build settings.

## 5. Next change

Change the text returned by `src/models/secondary.py`, run the app again, and
open the secondary page to see where that model is used.
