from __future__ import annotations

import builtins
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest

from flet_mvc import DataTableAdapter


def test_adapter_owns_or_wraps_exactly_one_control() -> None:
    owned = DataTableAdapter()
    table = ft.DataTable(columns=[ft.DataColumn(label="Name")])
    wrapped = DataTableAdapter(table)

    assert isinstance(owned.control, ft.DataTable)
    assert wrapped.control is table
    assert not hasattr(wrapped, "table")
    assert not hasattr(wrapped, "current")


def test_update_errors_from_an_attached_control_are_not_hidden(monkeypatch) -> None:
    adapter = DataTableAdapter().set_columns(["name"])
    monkeypatch.setattr(
        type(adapter.control),
        "page",
        property(lambda _control: object()),
    )
    adapter.control._frozen = True

    with pytest.raises(RuntimeError, match="Frozen control"):
        adapter.set_rows([["Ada"]])


def test_set_columns_accepts_names_controls_and_numeric_selectors() -> None:
    custom = ft.DataColumn(label="Score")
    adapter = DataTableAdapter().set_columns(
        ["name", custom],
        numeric=["Score"],
    )

    assert adapter.column_names == ["name", "Score"]
    assert isinstance(adapter.columns[0], ft.DataColumn)
    assert adapter.columns[1] is custom
    assert adapter.columns[0].numeric is False
    assert adapter.columns[1].numeric is True

    adapter.set_columns(["first", "second"], numeric=1)
    assert adapter.column_names == ["first", "second"]
    assert adapter.columns[1].numeric is True


def test_set_rows_accepts_sequences_mappings_data_rows_and_cells() -> None:
    existing_cell = ft.DataCell(content="existing")
    existing_row = ft.DataRow(
        cells=[ft.DataCell(content="ready"), ft.DataCell(content="9")]
    )
    adapter = DataTableAdapter().set_columns(["name", "value"])

    result = adapter.set_rows(
        [
            ["Ada", 1],
            {"name": "Grace", "value": 2},
            [existing_cell, 3],
            existing_row,
        ]
    )

    assert result is adapter
    assert len(adapter.rows) == 4
    assert adapter.rows[2].cells[0] is existing_cell
    assert adapter.rows[3] is existing_row
    assert adapter.to_records() == [
        {"name": "Ada", "value": 1},
        {"name": "Grace", "value": 2},
        {"name": "existing", "value": 3},
        {"name": "ready", "value": "9"},
    ]


def test_visibility_applies_to_cells_and_schema_changes_clear_rows() -> None:
    hidden = ft.DataColumn(label="secret", visible=False)
    adapter = (
        DataTableAdapter().set_columns(["shown", hidden]).set_rows([["yes", "hidden"]])
    )

    assert adapter.rows[0].cells[0].visible is True
    assert adapter.rows[0].cells[1].visible is False

    adapter.set_columns(["replacement"])
    assert adapter.rows == []
    assert adapter.to_records() == []


def test_custom_rows_must_match_visible_columns() -> None:
    adapter = DataTableAdapter().set_columns(
        ["shown", ft.DataColumn(label="hidden", visible=False)]
    )
    invalid = ft.DataRow(
        cells=[
            ft.DataCell(content="one"),
            ft.DataCell(content="two", visible=True),
        ]
    )
    with pytest.raises(ValueError, match="visible"):
        adapter.set_rows([invalid])

    valid = ft.DataRow(
        cells=[
            ft.DataCell(content="one"),
            ft.DataCell(content="two", visible=False),
        ]
    )
    adapter.set_rows([valid])
    assert adapter.rows == [valid]


def test_load_records_uses_first_seen_union_and_missing_none() -> None:
    adapter = DataTableAdapter().load_records(
        [
            {"name": "Ada", "score": 98},
            {"score": 100, "language": "COBOL"},
        ]
    )

    assert adapter.column_names == ["name", "score", "language"]
    assert adapter.to_records() == [
        {"name": "Ada", "score": 98, "language": None},
        {"name": None, "score": 100, "language": "COBOL"},
    ]


def test_empty_records_clear_rows_when_schema_exists() -> None:
    adapter = (
        DataTableAdapter().set_columns(["name"]).set_rows([["Ada"]]).load_records([])
    )

    assert adapter.column_names == ["name"]
    assert adapter.rows == []


def test_load_records_is_atomic_when_cell_factory_fails() -> None:
    fail = False

    def cell_factory(value: Any):
        if fail and value == "bad":
            raise ValueError("bad cell")
        return str(value)

    adapter = DataTableAdapter(cell_factory=cell_factory).load_records(
        [{"name": "original"}]
    )
    previous_columns = list(adapter.columns)
    previous_rows = list(adapter.rows)
    fail = True

    with pytest.raises(ValueError, match="bad cell"):
        adapter.load_records([{"other": "bad"}])

    assert adapter.columns == previous_columns
    assert adapter.rows == previous_rows
    assert adapter.to_records() == [{"name": "original"}]


def test_control_cells_and_direct_control_mutations_are_exported() -> None:
    text = ft.Text("initial")
    adapter = (
        DataTableAdapter()
        .set_columns(["number", "none", "control"])
        .set_rows([[42, None, text]])
    )

    text.value = "changed"
    adapter.rows[0].cells[0].content = "43"

    assert adapter.to_records() == [
        {"number": "43", "none": None, "control": "changed"}
    ]


def test_custom_cell_factory_must_return_supported_content() -> None:
    adapter = DataTableAdapter(
        cell_factory=lambda value: ft.Text(f"value={value}")
    ).set_columns(["value"])
    adapter.set_rows([[1]])
    assert adapter.rows[0].cells[0].content.value == "value=1"

    bad = DataTableAdapter(cell_factory=lambda _value: object()).set_columns(["value"])
    with pytest.raises(TypeError, match="str or ft.Control"):
        bad.set_rows([[1]])


class PandasStyleFrame:
    columns = ["name", "score"]

    def to_dict(self, orient=None):
        assert orient == "records"
        return [{"name": "Ada", "score": 98}]


class PositionalFrame:
    columns = ["name"]

    def to_dict(self, orient, /):
        assert orient == "records"
        return [{"name": "Grace"}]


class PolarsStyleFrame:
    columns = ["name"]

    def to_dicts(self):
        return [{"name": "Linus"}]


@pytest.mark.parametrize(
    ("frame", "expected"),
    [
        (PandasStyleFrame(), [{"name": "Ada", "score": 98}]),
        (PositionalFrame(), [{"name": "Grace"}]),
        (PolarsStyleFrame(), [{"name": "Linus"}]),
    ],
)
def test_load_dataframe_is_structural(frame, expected) -> None:
    adapter = DataTableAdapter().load_dataframe(frame)
    assert adapter.to_records() == expected


def test_empty_dataframe_preserves_declared_columns() -> None:
    frame = SimpleNamespace(
        columns=["name", "score"],
        to_dict=lambda orient: [],
    )

    adapter = DataTableAdapter().load_dataframe(frame)

    assert adapter.column_names == ["name", "score"]
    assert adapter.rows == []


def test_to_dataframe_uses_optional_pandas() -> None:
    pd = pytest.importorskip("pandas")
    adapter = DataTableAdapter().load_records([{"name": "Ada", "score": 98}])

    frame = adapter.to_dataframe()

    assert isinstance(frame, pd.DataFrame)
    assert frame.to_dict(orient="records") == [{"name": "Ada", "score": 98}]


def test_to_dataframe_has_clear_optional_dependency_error(monkeypatch) -> None:
    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    with pytest.raises(ImportError, match="optional 'pandas'"):
        DataTableAdapter().set_columns(["value"]).to_dataframe()


def test_csv_handles_escaping_headers_and_index() -> None:
    adapter = DataTableAdapter().load_records(
        [{"name": 'Ada, "Countess"', "note": None}]
    )

    assert adapter.to_csv() == 'name,note\n"Ada, ""Countess""",\n'
    assert adapter.to_csv(index=True, include_header=False) == (
        '0,"Ada, ""Countess""",\n'
    )
    assert adapter.to_csv(delimiter=";") == ('name;note\n"Ada, ""Countess""";\n')


class Picker:
    def __init__(self, result: str | None = "/tmp/data.csv") -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    async def save_file(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


@pytest.mark.asyncio
async def test_save_csv_uses_async_file_picker_and_src_bytes() -> None:
    picker = Picker()
    adapter = DataTableAdapter(file_picker=picker).load_records(
        [{"name": "Ada", "score": 98}]
    )

    result = await adapter.save_csv(file_name="people.csv")

    assert result == "/tmp/data.csv"
    assert picker.calls == [
        {
            "dialog_title": "Save table as CSV",
            "file_name": "people.csv",
            "file_type": ft.FilePickerFileType.CUSTOM,
            "allowed_extensions": ["csv"],
            "src_bytes": b"name,score\nAda,98\n",
        }
    ]


@pytest.mark.asyncio
async def test_save_csv_can_report_cancel() -> None:
    picker = Picker(None)
    adapter = DataTableAdapter().set_columns(["value"])
    assert await adapter.save_csv(picker) is None


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (lambda: DataTableAdapter(table=object()), "ft.DataTable"),
        (lambda: DataTableAdapter(cell_factory=object()), "cell_factory"),
        (lambda: DataTableAdapter().set_columns("name"), "iterable"),
        (lambda: DataTableAdapter().set_columns(1), "iterable"),
        (lambda: DataTableAdapter().set_columns([]), "at least one"),
        (lambda: DataTableAdapter().set_columns([1]), "str or ft.DataColumn"),
        (lambda: DataTableAdapter().set_columns([""]), "empty name"),
        (lambda: DataTableAdapter().set_columns(["x", "x"]), "duplicate"),
        (
            lambda: DataTableAdapter().set_columns(["x"], numeric="missing"),
            "unknown",
        ),
        (lambda: DataTableAdapter().set_rows([[1]]), "set columns"),
        (
            lambda: DataTableAdapter().set_columns(["x"]).set_rows("row"),
            "iterable",
        ),
        (
            lambda: DataTableAdapter().set_columns(["x"]).set_rows([[1, 2]]),
            "contains 2 cells",
        ),
        (lambda: DataTableAdapter().load_records([]), "cannot infer"),
        (lambda: DataTableAdapter().load_records({"x": 1}), "sequence"),
        (lambda: DataTableAdapter().load_records([1]), "must be a mapping"),
        (
            lambda: DataTableAdapter().load_records([{1: "x"}]),
            "non-string key",
        ),
        (lambda: DataTableAdapter().to_csv(delimiter="::"), "one character"),
    ],
)
def test_validation_errors(operation, message) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        operation()


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (object(), "to_dict"),
        (SimpleNamespace(to_dict=lambda orient: []), "columns attribute"),
        (
            SimpleNamespace(columns=[], to_dict=lambda orient: []),
            "at least one column",
        ),
        (
            SimpleNamespace(
                columns=["x", "x"],
                to_dict=lambda orient: [],
            ),
            "duplicate column",
        ),
        (
            SimpleNamespace(columns=["x"], to_dict=lambda orient: 1),
            "must return an iterable",
        ),
        (
            SimpleNamespace(columns=["x"], to_dict=lambda orient: [1]),
            "must be a mapping",
        ),
    ],
)
def test_dataframe_contract_errors(frame, message) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        DataTableAdapter().load_dataframe(frame)


def test_existing_table_requires_exportable_unique_column_names() -> None:
    unnamed = ft.DataTable(columns=[ft.DataColumn(label=ft.Icon(ft.Icons.ADD))])
    with pytest.raises(TypeError, match="cannot infer"):
        DataTableAdapter(unnamed)

    duplicates = ft.DataTable(
        columns=[ft.DataColumn(label="x"), ft.DataColumn(label="x")]
    )
    with pytest.raises(ValueError, match="duplicate"):
        DataTableAdapter(duplicates)


@pytest.mark.asyncio
async def test_save_csv_validation_errors() -> None:
    adapter = DataTableAdapter().set_columns(["value"])
    with pytest.raises(ValueError, match="file_name"):
        await adapter.save_csv(Picker(), file_name="")
    with pytest.raises(TypeError, match="save_file"):
        await adapter.save_csv(object())

    class SyncPicker:
        def save_file(self, **_kwargs):
            return "not-awaitable"

    with pytest.raises(TypeError, match="awaitable"):
        await adapter.save_csv(SyncPicker())
