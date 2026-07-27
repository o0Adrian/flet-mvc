from __future__ import annotations

import ast
from pathlib import Path

import pytest
from click.testing import CliRunner

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

from mvc_commands.cli import cli

TEMPLATES = [
    pytest.param(
        "start",
        "basic",
        "flet-mvc-basic-app",
        {
            ".gitignore",
            "README.md",
            "pyproject.toml",
            "src/controllers/__init__.py",
            "src/controllers/main.py",
            "src/main.py",
            "src/models/__init__.py",
            "src/models/main.py",
            "src/views/__init__.py",
            "src/views/main.py",
            "tests/test_main.py",
        },
        id="basic",
    ),
    pytest.param(
        "routes",
        "routes",
        "flet-mvc-routes-app",
        {
            ".gitignore",
            "README.md",
            "pyproject.toml",
            "src/controllers/__init__.py",
            "src/controllers/home.py",
            "src/controllers/secondary.py",
            "src/main.py",
            "src/models/__init__.py",
            "src/models/home.py",
            "src/models/secondary.py",
            "src/views/__init__.py",
            "src/views/home.py",
            "src/views/secondary.py",
            "tests/test_main.py",
        },
        id="routes",
    ),
    pytest.param(
        "tabs",
        "tabs",
        "flet-mvc-tabs-app",
        {
            ".gitignore",
            "README.md",
            "pyproject.toml",
            "src/controllers/__init__.py",
            "src/controllers/index.py",
            "src/main.py",
            "src/models/__init__.py",
            "src/models/home.py",
            "src/models/index.py",
            "src/models/settings.py",
            "src/views/__init__.py",
            "src/views/home.py",
            "src/views/index.py",
            "src/views/settings.py",
            "tests/test_main.py",
        },
        id="tabs",
    ),
    pytest.param(
        "reactive",
        "reactive",
        "flet-mvc-reactive-app",
        {
            ".gitignore",
            "README.md",
            "pyproject.toml",
            "src/components/__init__.py",
            "src/components/counter.py",
            "src/main.py",
            "src/models/__init__.py",
            "src/models/counter.py",
            "tests/test_main.py",
        },
        id="reactive",
    ),
]


def generated_files(destination: Path) -> set[str]:
    return {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("command", "template_name", "project_name", "expected_files"),
    TEMPLATES,
)
def test_commands_generate_complete_standalone_projects(
    tmp_path: Path,
    command: str,
    template_name: str,
    project_name: str,
    expected_files: set[str],
) -> None:
    destination = tmp_path / template_name

    result = CliRunner().invoke(
        cli,
        [command, "--destination", str(destination)],
    )

    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert generated_files(destination) == expected_files
    assert f"Created '{template_name}' template" in result.output

    for source_path in destination.rglob("*.py"):
        ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )

    all_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((destination / "src").rglob("*.py"))
    )
    app_source = (destination / "src" / "main.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in app_source
    assert "ft.run(main)" in app_source
    assert "ft.app(" not in app_source
    assert "FletController" not in all_source
    assert "FletView" not in all_source
    assert "RouteHandler" not in all_source

    for controller_path in (destination / "src" / "controllers").glob("*.py"):
        if controller_path.name == "__init__.py":
            continue
        controller_source = controller_path.read_text(encoding="utf-8")
        assert "from dataclasses import dataclass" in controller_source
        assert "@dataclass" in controller_source
        assert "model:" in controller_source
        if template_name == "routes":
            assert "page: ft.Page" in controller_source
        else:
            assert "page: ft.Page" not in controller_source

    with (destination / "pyproject.toml").open("rb") as stream:
        generated_config = tomllib.load(stream)
    assert generated_config["project"]["name"] == project_name
    assert generated_config["project"]["readme"] == "README.md"
    assert generated_config["project"]["requires-python"] == ">=3.10"
    assert generated_config["project"]["dependencies"] == [
        "flet>=0.86.3,<0.87",
        "flet-mvc>=1.0,<2",
    ]
    assert generated_config["dependency-groups"]["dev"] == [
        "flet-cli>=0.86.3,<0.87",
        "flet-desktop>=0.86.3,<0.87",
        "flet-web>=0.86.3,<0.87",
        "flet[test]>=0.86.3,<0.87",
    ]
    assert generated_config["tool"]["pytest"]["ini_options"] == {
        "asyncio_mode": "auto",
        "testpaths": ["tests"],
    }
    assert generated_config["tool"]["flet"]["app"] == {"path": "src"}

    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "## 1. Install" in readme
    assert "## 2. Run" in readme
    assert "## 3. Test" in readme
    assert "## 4. File map" in readme
    assert "## 5. Next change" in readme
    assert "uv sync" in readme
    assert "uv run flet run" in readme
    assert "uv run pytest" in readme
    assert "src/main.py" in readme
    assert "python app.py" not in readme
    assert "pip install -e" not in readme


def test_routes_template_uses_native_declarative_router(tmp_path: Path) -> None:
    destination = tmp_path / "routes"

    result = CliRunner().invoke(cli, ["routes", "-d", str(destination)])

    assert result.exit_code == 0, result.output
    generated_source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(destination.rglob("*.py"))
    )
    assert "ft.Router(" in generated_source
    assert "ft.Route(" in generated_source
    assert "manage_views=True" in generated_source
    assert "page.render_views(App)" in generated_source
    assert "page.navigate(" in generated_source
    assert "RouteHandler" not in generated_source
    assert "page.on_route_change" not in generated_source
    assert "page.on_view_pop" not in generated_source
    assert "page.views.clear()" not in generated_source
    assert "page.go(" not in generated_source


def test_tabs_template_uses_current_tabs_api(tmp_path: Path) -> None:
    destination = tmp_path / "tabs"

    result = CliRunner().invoke(cli, ["tabs", "-d", str(destination)])

    assert result.exit_code == 0, result.output
    index_view = (destination / "src" / "views" / "index.py").read_text(
        encoding="utf-8"
    )
    assert "ft.Tabs(" in index_view
    assert "ft.TabBar(" in index_view
    assert "ft.TabBarView(" in index_view
    assert "length=3" in index_view
    assert "model.selected_index.value" in index_view
    assert "on_change=controller.select_tab" in index_view


def test_reactive_template_shows_the_complete_reactive_flow(tmp_path: Path) -> None:
    destination = tmp_path / "reactive"

    result = CliRunner().invoke(cli, ["reactive", "-d", str(destination)])

    assert result.exit_code == 0, result.output
    model_source = (destination / "src" / "models" / "counter.py").read_text(
        encoding="utf-8"
    )
    component_source = (destination / "src" / "components" / "counter.py").read_text(
        encoding="utf-8"
    )
    app_source = (destination / "src" / "main.py").read_text(encoding="utf-8")

    assert "@data\n" in model_source
    assert "@computed\n" in model_source
    assert "self.count.value" in model_source
    assert "class CounterComponent(FletComponent):" in component_source
    assert "@receive(CounterModel.count)" in component_source
    assert "@send(CounterModel.count)" in component_source
    assert "self.model.count.value" in component_source
    assert "@ft.component" in app_source
    assert "model.message.value" in app_source
    assert "page.render(App, model)" in app_source
    assert "ft.run(main)" in app_source


def test_dry_run_reports_every_file_without_writing(tmp_path: Path) -> None:
    destination = tmp_path / "preview"

    result = CliRunner().invoke(
        cli,
        ["start", "--destination", str(destination), "--dry-run"],
    )

    assert result.exit_code == 0, result.output
    assert not destination.exists()
    assert "Would create 'basic' template" in result.output
    assert "(11 files)" in result.output
    assert "create  .gitignore" in result.output
    assert "create  README.md" in result.output
    assert "create  pyproject.toml" in result.output
    assert "create  src/main.py" in result.output
    assert "create  tests/test_main.py" in result.output


def test_collision_preflight_leaves_destination_unchanged(tmp_path: Path) -> None:
    destination = tmp_path / "existing"
    existing_app = destination / "src" / "main.py"
    existing_app.parent.mkdir(parents=True)
    existing_app.write_text("# user application\n", encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["start", "--destination", str(destination)],
    )

    assert result.exit_code == 1
    assert "Refusing to overwrite existing files" in result.output
    assert existing_app.read_text(encoding="utf-8") == "# user application\n"
    assert generated_files(destination) == {"src/main.py"}


def test_force_replaces_template_files_and_preserves_unrelated_files(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "existing"
    existing_app = destination / "src" / "main.py"
    existing_app.parent.mkdir(parents=True)
    existing_app.write_text("# obsolete\n", encoding="utf-8")
    unrelated = destination / "notes.txt"
    unrelated.write_text("keep me\n", encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["start", "--destination", str(destination), "--force"],
    )

    assert result.exit_code == 0, result.output
    assert "ft.run(main)" in existing_app.read_text(encoding="utf-8")
    assert unrelated.read_text(encoding="utf-8") == "keep me\n"


def test_force_rejects_structural_conflicts_without_partial_writes(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "structural-conflict"
    (destination / "src").mkdir(parents=True)
    controllers = destination / "src" / "controllers"
    controllers.write_text("not a directory\n", encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["start", "--destination", str(destination), "--force"],
    )

    assert result.exit_code == 1
    assert "non-directory parents" in result.output
    assert controllers.read_text(encoding="utf-8") == "not a directory\n"
    assert generated_files(destination) == {"src/controllers"}


def test_force_rejects_symlinked_directory_without_writing_outside_destination(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "project"
    outside = tmp_path / "outside"
    (destination / "src").mkdir(parents=True)
    outside.mkdir()
    (destination / "src" / "controllers").symlink_to(
        outside,
        target_is_directory=True,
    )

    result = CliRunner().invoke(
        cli,
        ["start", "--destination", str(destination), "--force"],
    )

    assert result.exit_code == 1
    assert "conflict" in result.output.lower()
    assert list(outside.iterdir()) == []


def test_destination_itself_cannot_be_a_symlink(tmp_path: Path) -> None:
    real_destination = tmp_path / "real"
    linked_destination = tmp_path / "linked"
    real_destination.mkdir()
    linked_destination.symlink_to(real_destination, target_is_directory=True)

    result = CliRunner().invoke(
        cli,
        ["start", "--destination", str(linked_destination), "--force"],
    )

    assert result.exit_code == 1
    assert "symbolic link" in result.output
    assert list(real_destination.iterdir()) == []


def test_destination_option_creates_missing_parent_directories(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "nested" / "project"

    result = CliRunner().invoke(cli, ["start", "-d", str(destination)])

    assert result.exit_code == 0, result.output
    assert (destination / "src" / "main.py").is_file()
    assert (destination / "src" / "controllers" / "__init__.py").is_file()


def test_default_destination_is_current_directory() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["start"])

        assert result.exit_code == 0, result.output
        assert Path("src/main.py").is_file()
        assert Path("tests/test_main.py").is_file()
        assert Path("pyproject.toml").is_file()


def test_version_option_reports_distribution_version() -> None:
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "flet-mvc, version 1.0.0"
