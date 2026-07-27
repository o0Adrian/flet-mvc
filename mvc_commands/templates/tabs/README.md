# Tabbed Flet MVC app

This template places separate home and settings views inside Flet's current
`Tabs`, `TabBar`, and `TabBarView` controls. The selected index lives in the
model, and the controller updates it.

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

Select **Settings** and **About** to verify all three tabs.

## 3. Test

```bash
uv run pytest
```

The test selects the Settings tab and checks its visible content.

## 4. File map

- `src/main.py` creates the models and controller for one session.
- `src/views/index.py` defines the tab bar and its three panels.
- `src/models/index.py` stores the selected tab.
- `src/models/home.py` and `src/models/settings.py` hold each tab's text.
- `src/views/home.py` and `src/views/settings.py` display those datapoints.
- `tests/test_main.py` checks the tab interaction.
- `pyproject.toml` contains project and Flet build settings.

## 5. Next change

Replace **Add your next view here.** in `src/views/index.py` with your own
About content, then reload the app.
