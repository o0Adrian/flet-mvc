from __future__ import annotations

import ast
import re
from pathlib import Path
from urllib.parse import unquote

import pytest

from flet_mvc.model import _CONTROL_BINDINGS

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION = (
    ROOT / "README.md",
    ROOT / "README.es.md",
    ROOT / "MIGRATION.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CHANGELOG.md",
    *sorted((ROOT / "docs").glob("*.md")),
    *sorted((ROOT / "mvc_commands" / "templates").glob("*/README.md")),
)
PYTHON_FENCE = re.compile(r"```python[^\n]*\n(.*?)```", re.DOTALL)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
REPOSITORY_BLOB_PREFIX = "https://github.com/o0Adrian/flet-mvc/blob/master/"
FLET_RELEASE_ROW = re.compile(r"^\| (\d+\.\d+\.\d+) \|", re.MULTILINE)
CONTROL_MATRIX_ROW = re.compile(
    r"^\| `(?P<control>[^`]+)` \| `(?P<attribute>[^`]+)` \| "
    r"(?P<event>`[^`]+`|—) \|$",
    re.MULTILINE,
)
AUDITED_FLET_RELEASES = (
    "0.9.0",
    "0.10.0",
    "0.10.1",
    "0.10.2",
    "0.10.3",
    "0.11.0",
    "0.12.0",
    "0.12.1",
    "0.12.2",
    "0.13.0",
    "0.14.0",
    "0.15.0",
    "0.16.0",
    "0.17.0",
    "0.18.0",
    "0.19.0",
    "0.20.0",
    "0.20.1",
    "0.20.2",
    "0.21.0",
    "0.21.1",
    "0.21.2",
    "0.22.0",
    "0.22.1",
    "0.23.0",
    "0.23.1",
    "0.23.2",
    "0.24.0",
    "0.24.1",
    "0.25.0",
    "0.25.1",
    "0.25.2",
    "0.26.0",
    "0.27.0",
    "0.27.1",
    "0.27.2",
    "0.27.3",
    "0.27.4",
    "0.27.5",
    "0.27.6",
    "0.28.0",
    "0.28.2",
    "0.28.3",
    "0.70.0",
    "0.80.0",
    "0.80.1",
    "0.80.2",
    "0.80.3",
    "0.80.4",
    "0.80.5",
    "0.81.0",
    "0.82.0",
    "0.82.2",
    "0.83.0",
    "0.83.1",
    "0.84.0",
    "0.85.0",
    "0.85.1",
    "0.85.2",
    "0.85.3",
    "0.86.0",
    "0.86.1",
    "0.86.2",
    "0.86.3",
)


def _relative_name(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


@pytest.mark.parametrize("document", DOCUMENTATION, ids=_relative_name)
def test_python_examples_are_syntactically_valid(document: Path) -> None:
    source = document.read_text(encoding="utf-8")

    for index, example in enumerate(PYTHON_FENCE.findall(source), start=1):
        compile(
            example,
            f"{_relative_name(document)}:python-example-{index}",
            "exec",
            flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            dont_inherit=True,
        )


@pytest.mark.parametrize("document", DOCUMENTATION, ids=_relative_name)
def test_relative_documentation_links_exist(document: Path) -> None:
    source = document.read_text(encoding="utf-8")

    for raw_target in MARKDOWN_LINK.findall(source):
        target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
        if target.startswith(REPOSITORY_BLOB_PREFIX):
            repository_path = unquote(
                target.removeprefix(REPOSITORY_BLOB_PREFIX).split("#", 1)[0]
            )
            assert (ROOT / repository_path).exists(), (
                f"{_relative_name(document)} links to missing repository path "
                f"{repository_path!r}"
            )
            continue
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        path_text = unquote(target.split("#", 1)[0])
        assert (document.parent / path_text).exists(), (
            f"{_relative_name(document)} links to missing path {path_text!r}"
        )


def test_english_and_spanish_readme_examples_stay_in_sync() -> None:
    english = PYTHON_FENCE.findall((ROOT / "README.md").read_text(encoding="utf-8"))
    spanish = PYTHON_FENCE.findall((ROOT / "README.es.md").read_text(encoding="utf-8"))

    assert len(english) == len(spanish)
    for index, (english_example, spanish_example) in enumerate(
        zip(english, spanish, strict=True),
        start=1,
    ):
        assert ast.dump(ast.parse(english_example)) == ast.dump(
            ast.parse(spanish_example)
        ), f"Python example {index} differs between README.md and README.es.md"


def test_release_audit_covers_every_official_stable_heading() -> None:
    source = (ROOT / "docs" / "FLET_RELEASE_AUDIT.md").read_text(encoding="utf-8")
    documented = tuple(FLET_RELEASE_ROW.findall(source))

    assert len(documented) == 64
    assert documented == AUDITED_FLET_RELEASES


def test_control_matrix_matches_runtime_registry() -> None:
    source = (ROOT / "docs" / "CONTROL_COMPATIBILITY.md").read_text(encoding="utf-8")
    documented = {
        match.group("control"): (
            match.group("attribute"),
            None if match.group("event") == "—" else match.group("event").strip("`"),
        )
        for match in CONTROL_MATRIX_ROW.finditer(source)
    }
    registered = {
        control_type.__name__: (spec.attribute, spec.event)
        for control_type, spec in _CONTROL_BINDINGS.items()
    }

    assert len(documented) == 21
    assert documented == registered
