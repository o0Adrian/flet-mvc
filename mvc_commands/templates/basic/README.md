# Basic Flet MVC app

This is the smallest template. The model owns the text, the controller changes
it, and the declarative view displays it.

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

Click **Toggle title** to see the model update the view.

## 3. Test

```bash
uv run pytest
```

The test opens the real Flet app, clicks the button, and checks the new title.

## 4. File map

- `src/main.py` creates and connects the three MVC objects.
- `src/models/main.py` defines the reactive `title` datapoint.
- `src/controllers/main.py` contains the button action.
- `src/views/main.py` contains the declarative Flet component.
- `tests/test_main.py` checks the visible behavior.
- `pyproject.toml` contains project and Flet build settings.

## 5. Next change

Change the default text in `src/models/main.py`, run the app again, and confirm
that the first title on screen changed.
