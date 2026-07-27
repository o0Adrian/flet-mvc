"""Command-line project generator for Flet MVC."""

from __future__ import annotations

import os
import shutil
import tempfile
from importlib import resources
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import click

_PACKAGE_NAME = "flet-mvc"
_SOURCE_VERSION = "1.0.0"


def _package_version() -> str:
    try:
        return version(_PACKAGE_NAME)
    except PackageNotFoundError:
        return _SOURCE_VERSION


def _template_files(template_name: str) -> list[tuple[PurePosixPath, Any]]:
    """Return every file in a packaged template in deterministic order."""
    template = (
        resources.files("mvc_commands").joinpath("templates").joinpath(template_name)
    )
    if not template.is_dir():
        raise click.ClickException(
            "The packaged templates are missing. Reinstall flet-mvc and try again."
        )

    files: list[tuple[PurePosixPath, Any]] = []

    def walk(directory: Any, relative: PurePosixPath) -> None:
        for item in sorted(directory.iterdir(), key=lambda child: child.name):
            if item.name == "__pycache__" or item.name.endswith((".pyc", ".pyo")):
                continue
            item_relative = relative / item.name
            if item.is_dir():
                walk(item, item_relative)
            elif item.is_file():
                files.append((item_relative, item))

    walk(template, PurePosixPath())
    return files


def _structural_conflict(destination: Path, relative: PurePosixPath) -> Path | None:
    """Find a path that prevents a template file from being created safely."""
    current = destination
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return current
    target = destination.joinpath(*relative.parts)
    if target.exists() and target.is_dir():
        return target
    return None


def _format_paths(paths: Iterable[Path], destination: Path) -> str:
    return "\n".join(f"  - {path.relative_to(destination)}" for path in sorted(paths))


def _stage_template(files: list[tuple[PurePosixPath, Any]], stage: Path) -> None:
    for relative, source in files:
        target = stage.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as source_file, target.open("wb") as target_file:
            shutil.copyfileobj(source_file, target_file)


def _merge_staged_template(
    stage: Path,
    destination: Path,
    relative_files: list[PurePosixPath],
) -> None:
    """Merge staged files, restoring the destination if a write fails."""
    backup_root = Path(
        tempfile.mkdtemp(prefix=".flet-mvc-backup-", dir=destination.parent)
    )
    installed: list[Path] = []
    backed_up: list[tuple[Path, Path]] = []
    created_directories: list[Path] = []

    try:
        for relative in relative_files:
            source = stage.joinpath(*relative.parts)
            target = destination.joinpath(*relative.parts)

            missing_parents: list[Path] = []
            parent = target.parent
            while parent != destination and not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            target.parent.mkdir(parents=True, exist_ok=True)
            created_directories.extend(reversed(missing_parents))

            if target.exists() or target.is_symlink():
                backup = backup_root.joinpath(*relative.parts)
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, backup)
                backed_up.append((target, backup))

            os.replace(source, target)
            installed.append(target)
    except Exception:
        for target in reversed(installed):
            if target.is_file() or target.is_symlink():
                target.unlink()
        for target, backup in reversed(backed_up):
            if backup.exists() or backup.is_symlink():
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(backup, target)
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def _copy_template_files(
    template_name: str,
    destination: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Copy a packaged template after a complete collision preflight."""
    destination = destination.expanduser().absolute()
    files = _template_files(template_name)
    relative_files = [relative for relative, _ in files]

    if destination.is_symlink():
        raise click.ClickException(
            f"Destination cannot be a symbolic link: {destination}"
        )
    if destination.exists() and not destination.is_dir():
        raise click.ClickException(
            f"Destination exists and is not a directory: {destination}"
        )

    structural_conflicts = {
        conflict
        for relative in relative_files
        if (conflict := _structural_conflict(destination, relative)) is not None
    }
    if structural_conflicts:
        raise click.ClickException(
            "Template paths conflict with existing directories or non-directory "
            f"parents:\n{_format_paths(structural_conflicts, destination)}"
        )

    collisions = [
        destination.joinpath(*relative.parts)
        for relative in relative_files
        if destination.joinpath(*relative.parts).exists()
        or destination.joinpath(*relative.parts).is_symlink()
    ]
    if collisions and not force:
        raise click.ClickException(
            "Refusing to overwrite existing files. Use --force to replace them:\n"
            f"{_format_paths(collisions, destination)}"
        )

    if dry_run:
        action = "replace" if collisions else "create"
        click.echo(
            f"Would {action} {template_name!r} template in {destination} "
            f"({len(relative_files)} files)."
        )
        for relative in relative_files:
            target = destination.joinpath(*relative.parts)
            marker = "replace" if target.exists() or target.is_symlink() else "create"
            click.echo(f"  {marker:7} {relative}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".flet-mvc-stage-", dir=destination.parent
    ) as temporary_directory:
        stage = Path(temporary_directory) / "project"
        stage.mkdir()
        _stage_template(files, stage)

        if not destination.exists():
            os.replace(stage, destination)
        else:
            _merge_staged_template(stage, destination, relative_files)

    click.echo(
        f"Created {template_name!r} template in {destination} "
        f"({len(relative_files)} files)."
    )


def _template_options(command):
    command = click.option(
        "--dry-run",
        is_flag=True,
        help="Show the files that would be written without changing anything.",
    )(command)
    command = click.option(
        "--force",
        is_flag=True,
        help="Replace template files that already exist.",
    )(command)
    command = click.option(
        "-d",
        "--destination",
        type=click.Path(path_type=Path, file_okay=False),
        default=Path("."),
        show_default=True,
        help="Directory in which to create the project.",
    )(command)
    return command


@click.command()
@_template_options
def start(destination: Path, force: bool, dry_run: bool) -> None:
    """Create a basic Flet MVC project."""
    _copy_template_files("basic", destination, force=force, dry_run=dry_run)


@click.command()
@_template_options
def routes(destination: Path, force: bool, dry_run: bool) -> None:
    """Create a Flet MVC project with route-based navigation."""
    _copy_template_files("routes", destination, force=force, dry_run=dry_run)


@click.command()
@_template_options
def tabs(destination: Path, force: bool, dry_run: bool) -> None:
    """Create a Flet MVC project with tab-based navigation."""
    _copy_template_files("tabs", destination, force=force, dry_run=dry_run)


@click.command()
@_template_options
def reactive(destination: Path, force: bool, dry_run: bool) -> None:
    """Create a small project that demonstrates reactive state."""
    _copy_template_files("reactive", destination, force=force, dry_run=dry_run)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=_package_version(), prog_name=_PACKAGE_NAME)
def cli() -> None:
    """Generate ready-to-run Flet MVC projects."""


cli.add_command(start)
cli.add_command(routes)
cli.add_command(tabs)
cli.add_command(reactive)


if __name__ == "__main__":
    cli()
