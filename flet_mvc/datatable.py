"""Helpers for building and exporting current Flet ``DataTable`` controls."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, TypeAlias

import flet as ft

__all__ = ["DataTableAdapter"]

ColumnInput: TypeAlias = str | ft.DataColumn
RowInput: TypeAlias = ft.DataRow | Mapping[str, Any] | Sequence[Any]
CellFactory: TypeAlias = Callable[[Any], str | ft.Control]


class DataTableAdapter:
    """Build, mutate, and export an ``ft.DataTable`` safely.

    The adapter can own a new table or wrap one that already exists. The
    wrapped Flet control is available through :attr:`control`.
    """

    def __init__(
        self,
        table: ft.DataTable | None = None,
        *,
        file_picker: ft.FilePicker | None = None,
        cell_factory: CellFactory | None = None,
    ) -> None:
        selected_table = table
        if selected_table is None:
            # An empty DataTable can be configured before it is mounted.  Flet
            # correctly rejects it during update if no visible columns were
            # established first.
            selected_table = ft.DataTable(columns=[])
        if not isinstance(selected_table, ft.DataTable):
            raise TypeError(
                f"table must be an ft.DataTable, got {type(selected_table).__name__}"
            )
        if cell_factory is not None and not callable(cell_factory):
            raise TypeError("cell_factory must be callable")

        self._table = selected_table
        self._file_picker = file_picker
        self._cell_factory = cell_factory or self._default_cell_factory
        self._column_names = self._names_from_columns(selected_table.columns)
        self._managed_rows = list(selected_table.rows)
        self._row_values = [
            self._values_from_data_row(row) for row in selected_table.rows
        ]
        self._rendered_row_values = [
            self._values_from_data_row(row) for row in selected_table.rows
        ]

    @property
    def control(self) -> ft.DataTable:
        """The wrapped Flet control."""

        return self._table

    @property
    def columns(self) -> list[ft.DataColumn]:
        return self._table.columns

    @property
    def rows(self) -> list[ft.DataRow]:
        return self._table.rows

    @property
    def column_names(self) -> list[str]:
        """A copy of the export keys in display order."""

        return list(self._column_names)

    def set_columns(
        self,
        columns: Iterable[ColumnInput],
        *,
        numeric: str | int | Iterable[str | int] = (),
    ) -> DataTableAdapter:
        """Create or install table columns.

        ``numeric`` may contain a column name or zero-based index.  Existing
        rows are retained when the column count is unchanged; otherwise they
        are cleared so the DataTable cannot be left in an invalid state.
        """

        if isinstance(columns, (str, bytes)):
            raise TypeError(
                "columns must be an iterable of names or DataColumn objects"
            )
        try:
            requested = list(columns)
        except TypeError as exc:
            raise TypeError(
                "columns must be an iterable of names or DataColumn objects"
            ) from exc
        if not requested:
            raise ValueError("at least one column is required by ft.DataTable")

        if isinstance(numeric, (str, int)):
            numeric_items = {numeric}
        else:
            try:
                numeric_items = set(numeric)
            except TypeError as exc:
                raise TypeError(
                    "numeric must be a column name/index or an iterable of them"
                ) from exc
        built: list[ft.DataColumn] = []
        names: list[str] = []
        for index, item in enumerate(requested):
            if isinstance(item, ft.DataColumn):
                column = item
                name = self._name_from_column(column, index)
            elif isinstance(item, str):
                if not item:
                    raise ValueError(f"column {index} has an empty name")
                name = item
                column = ft.DataColumn(label=item)
            else:
                raise TypeError(
                    f"column {index} must be str or ft.DataColumn, "
                    f"got {type(item).__name__}"
                )
            built.append(column)
            names.append(name)

        self._ensure_unique_names(names)
        unknown_numeric = [
            item
            for item in numeric_items
            if not (
                isinstance(item, int)
                and not isinstance(item, bool)
                and 0 <= item < len(names)
                or isinstance(item, str)
                and item in names
            )
        ]
        if unknown_numeric:
            raise ValueError(
                f"numeric contains unknown column names/indices: {unknown_numeric!r}"
            )

        if not any(column.visible for column in built):
            raise ValueError("ft.DataTable requires at least one visible column")
        for index, (name, column) in enumerate(zip(names, built, strict=True)):
            if index in numeric_items or name in numeric_items:
                column.numeric = True

        old_count = len(self._table.columns)
        old_visibility = [column.visible for column in self._table.columns]
        new_visibility = [column.visible for column in built]
        self._table.columns = built
        self._column_names = names
        if (
            old_count != len(built) or old_visibility != new_visibility
        ) and self._table.rows:
            self._set_rows([], [])
        visible_count = sum(new_visibility)
        if (
            self._table.sort_column_index is not None
            and self._table.sort_column_index >= visible_count
        ):
            self._table.sort_column_index = None
        self._update_if_mounted()
        return self

    def set_rows(self, rows: Iterable[RowInput]) -> DataTableAdapter:
        """Create or install rows and validate their cell counts."""

        if isinstance(rows, (str, bytes, Mapping)):
            raise TypeError(
                "rows must be an iterable of DataRow, mapping, or sequence rows"
            )
        try:
            requested = list(rows)
        except TypeError as exc:
            raise TypeError(
                "rows must be an iterable of DataRow, mapping, or sequence rows"
            ) from exc

        if requested and not self._column_names:
            raise ValueError("set columns before adding rows")

        built_rows: list[ft.DataRow] = []
        raw_rows: list[list[Any]] = []
        for index, row in enumerate(requested):
            built, values = self._build_row(row, index=index)
            built_rows.append(built)
            raw_rows.append(values)

        self._set_rows(built_rows, raw_rows)
        self._update_if_mounted()
        return self

    def load_records(self, data: Sequence[Mapping[str, Any]]) -> DataTableAdapter:
        """Populate the table from records, preserving first-seen key order."""

        if isinstance(data, (str, bytes, Mapping)) or not isinstance(data, Sequence):
            raise TypeError(
                f"data must be a sequence of mappings, got {type(data).__name__}"
            )
        if not data:
            if not self._column_names:
                raise ValueError(
                    "cannot infer columns from an empty record list; "
                    "call set_columns() first"
                )
            self._set_rows([], [])
            self._update_if_mounted()
            return self

        names: list[str] = []
        seen: set[str] = set()
        for row_index, record in enumerate(data):
            if not isinstance(record, Mapping):
                raise TypeError(
                    f"record {row_index} must be a mapping, got {type(record).__name__}"
                )
            for key in record:
                if not isinstance(key, str):
                    raise TypeError(
                        f"record {row_index} has non-string key {key!r}; "
                        "DataTable column names must be strings"
                    )
                if not key:
                    raise ValueError(f"record {row_index} has an empty column name")
                if key not in seen:
                    seen.add(key)
                    names.append(key)
        if not names:
            raise ValueError("records must contain at least one column")

        built_columns = [ft.DataColumn(label=name) for name in names]
        built_rows: list[ft.DataRow] = []
        raw_rows: list[list[Any]] = []
        for record in data:
            values = [record.get(name) for name in names]
            built_rows.append(
                ft.DataRow(cells=[self._make_cell(value) for value in values])
            )
            raw_rows.append(values)

        # Assign columns and rows together before requesting an update, avoiding
        # an intermediate DataTable with mismatched cell counts.
        self._table.columns = built_columns
        self._column_names = names
        self._set_rows(built_rows, raw_rows)
        self._update_if_mounted()
        return self

    def load_dataframe(self, data: Any) -> DataTableAdapter:
        """Populate from a DataFrame-like object without importing pandas.

        Pandas-style ``to_dict(orient="records")`` and Polars-style
        ``to_dicts()`` objects are accepted structurally.
        """

        to_dict = getattr(data, "to_dict", None)
        to_dicts = getattr(data, "to_dicts", None)
        if not callable(to_dict) and not callable(to_dicts):
            raise TypeError(
                "data must be DataFrame-like and provide "
                "to_dict(orient='records') or to_dicts()"
            )

        try:
            raw_columns = list(data.columns)
        except (AttributeError, TypeError) as exc:
            raise TypeError(
                "data must be DataFrame-like and expose an iterable columns attribute"
            ) from exc

        names = [str(column) for column in raw_columns]
        if not names:
            raise ValueError("the DataFrame must contain at least one column")
        self._ensure_unique_names(names)

        if callable(to_dicts):
            try:
                converted = to_dicts()
            except Exception as exc:
                raise ValueError(
                    "could not convert DataFrame-like data with to_dicts()"
                ) from exc
        else:
            assert callable(to_dict)  # narrowed by the interface check above
            try:
                converted = to_dict(orient="records")
            except TypeError:
                # A few DataFrame-compatible implementations accept the orient
                # as a positional argument but expose the same records contract.
                try:
                    converted = to_dict("records")
                except Exception as exc:
                    raise TypeError(
                        "data.to_dict must support the 'records' orientation"
                    ) from exc
            except Exception as exc:
                raise ValueError(
                    "could not convert DataFrame-like data to records"
                ) from exc

        try:
            converted_records = list(converted)
        except TypeError as exc:
            raise TypeError(
                "data.to_dict(orient='records') must return an iterable"
            ) from exc

        normalized: list[dict[str, Any]] = []
        for index, record in enumerate(converted_records):
            if not isinstance(record, Mapping):
                raise TypeError(
                    f"DataFrame record {index} must be a mapping, "
                    f"got {type(record).__name__}"
                )
            normalized_record: dict[str, Any] = {}
            for raw_name, name in zip(raw_columns, names):
                normalized_record[name] = record.get(raw_name)
            normalized.append(normalized_record)

        if not normalized:
            self._table.columns = [ft.DataColumn(label=name) for name in names]
            self._column_names = names
            self._set_rows([], [])
            self._update_if_mounted()
            return self
        return self.load_records(normalized)

    def to_records(self) -> list[dict[str, Any]]:
        """Return table data as independent record dictionaries."""

        values = self._current_row_values()
        return [
            dict(zip(self._column_names, row_values, strict=True))
            for row_values in values
        ]

    def to_csv(
        self,
        *,
        index: bool = False,
        header: bool = True,
        include_header: bool | None = None,
        delimiter: str = ",",
        lineterminator: str = "\n",
    ) -> str:
        """Serialize records to CSV without requiring pandas."""

        if include_header is not None:
            header = include_header
        if not isinstance(delimiter, str) or len(delimiter) != 1:
            raise ValueError("delimiter must be exactly one character")

        output = io.StringIO(newline="")
        writer = csv.writer(
            output,
            delimiter=delimiter,
            lineterminator=lineterminator,
        )
        if header:
            writer.writerow(([""] if index else []) + self._column_names)
        for row_index, row in enumerate(self._current_row_values()):
            writer.writerow(
                ([row_index] if index else [])
                + [self._csv_value(value) for value in row]
            )
        return output.getvalue()

    def to_dataframe(self) -> Any:
        """Return a pandas DataFrame, with a clear optional-dependency error."""

        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "to_dataframe() requires the optional 'pandas' package; "
                "install it with `pip install pandas`"
            ) from exc
        return pd.DataFrame(self.to_records(), columns=self._column_names)

    async def save_csv(
        self,
        file_picker: ft.FilePicker | None = None,
        *,
        file_name: str = "data.csv",
        dialog_title: str | None = "Save table as CSV",
        encoding: str = "utf-8",
        index: bool = False,
        header: bool = True,
    ) -> str | None:
        """Open Flet's save/download dialog with the table encoded as CSV."""

        if not file_name:
            raise ValueError("file_name cannot be empty")
        picker = file_picker or self._file_picker or ft.FilePicker()
        save_file = getattr(picker, "save_file", None)
        if not callable(save_file):
            raise TypeError("file_picker must provide an async save_file() method")

        payload = self.to_csv(index=index, header=header).encode(encoding)
        result = save_file(
            dialog_title=dialog_title,
            file_name=file_name,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv"],
            src_bytes=payload,
        )
        if not hasattr(result, "__await__"):
            raise TypeError("FilePicker.save_file() must return an awaitable")
        return await result

    def _build_row(self, row: RowInput, *, index: int) -> tuple[ft.DataRow, list[Any]]:
        if isinstance(row, ft.DataRow):
            values = self._values_from_data_row(row)
            self._validate_cell_count(values, row_index=index)
            self._validate_visible_cell_count(row, row_index=index)
            return row, values

        if isinstance(row, Mapping):
            extras = [key for key in row if key not in self._column_names]
            if extras:
                raise ValueError(
                    f"row {index} contains columns not established in the table: "
                    f"{extras!r}"
                )
            values = [row.get(name) for name in self._column_names]
            return self._data_row_from_values(values), values

        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
            raise TypeError(
                f"row {index} must be ft.DataRow, mapping, or non-string sequence; "
                f"got {type(row).__name__}"
            )

        values = list(row)
        self._validate_cell_count(values, row_index=index)
        cells: list[ft.DataCell] = []
        raw_values: list[Any] = []
        for column_index, value in enumerate(values):
            if isinstance(value, ft.DataCell):
                cells.append(value)
                raw_values.append(self._value_from_cell(value))
            else:
                cells.append(
                    self._make_cell(
                        value,
                        visible=self._table.columns[column_index].visible,
                    )
                )
                raw_values.append(value)
        built = ft.DataRow(cells=cells)
        self._validate_visible_cell_count(built, row_index=index)
        return built, raw_values

    def _data_row_from_values(self, values: Sequence[Any]) -> ft.DataRow:
        self._validate_cell_count(values)
        return ft.DataRow(
            cells=[
                self._make_cell(value, visible=column.visible)
                for value, column in zip(
                    values,
                    self._table.columns,
                    strict=True,
                )
            ]
        )

    def _make_cell(self, value: Any, *, visible: bool = True) -> ft.DataCell:
        content = self._cell_factory(value)
        if not isinstance(content, (str, ft.Control)):
            raise TypeError(
                "cell_factory must return str or ft.Control, "
                f"got {type(content).__name__}"
            )
        return ft.DataCell(content=content, visible=visible)

    @staticmethod
    def _default_cell_factory(value: Any) -> str | ft.Control:
        if isinstance(value, ft.Control):
            return value
        return "" if value is None else str(value)

    def _validate_cell_count(
        self, values: Sequence[Any], *, row_index: int | None = None
    ) -> None:
        expected = len(self._column_names)
        actual = len(values)
        if actual != expected:
            location = "" if row_index is None else f" {row_index}"
            raise ValueError(
                f"row{location} contains {actual} cells; "
                f"ft.DataTable requires exactly {expected}"
            )

    def _validate_visible_cell_count(
        self,
        row: ft.DataRow,
        *,
        row_index: int,
    ) -> None:
        if not row.visible:
            return
        expected = sum(column.visible for column in self._table.columns)
        actual = sum(cell.visible for cell in row.cells)
        if actual != expected:
            raise ValueError(
                f"row {row_index} contains {actual} visible cells; "
                f"ft.DataTable requires exactly {expected} for the current columns"
            )

    def _set_rows(self, rows: list[ft.DataRow], values: list[list[Any]]) -> None:
        self._table.rows = rows
        self._managed_rows = list(rows)
        self._row_values = [list(row) for row in values]
        self._rendered_row_values = [self._values_from_data_row(row) for row in rows]

    def _current_row_values(self) -> list[list[Any]]:
        current_rows = self._table.rows
        if len(current_rows) == len(self._managed_rows) and all(
            current is managed
            for current, managed in zip(current_rows, self._managed_rows)
        ):
            rendered = [self._values_from_data_row(row) for row in current_rows]
            for index, row_values in enumerate(rendered):
                self._validate_cell_count(row_values, row_index=index)

            # Preserve original Python types for untouched cells (for example,
            # an int rendered as "42"), while reflecting edits performed
            # directly through the exposed DataTable.
            return [
                [
                    raw if current == snapshot else current
                    for raw, snapshot, current in zip(
                        raw_row,
                        snapshot_row,
                        current_row,
                        strict=True,
                    )
                ]
                for raw_row, snapshot_row, current_row in zip(
                    self._row_values,
                    self._rendered_row_values,
                    rendered,
                    strict=True,
                )
            ]

        values = [self._values_from_data_row(row) for row in current_rows]
        for index, row_values in enumerate(values):
            self._validate_cell_count(row_values, row_index=index)
        return values

    def _values_from_data_row(self, row: ft.DataRow) -> list[Any]:
        if not isinstance(row, ft.DataRow):
            raise TypeError(
                f"DataTable rows must be ft.DataRow, got {type(row).__name__}"
            )
        return [self._value_from_cell(cell) for cell in row.cells]

    @staticmethod
    def _value_from_cell(cell: ft.DataCell) -> Any:
        if not isinstance(cell, ft.DataCell):
            raise TypeError(
                f"DataRow cells must be ft.DataCell, got {type(cell).__name__}"
            )
        if cell.data is not None:
            return cell.data
        content = cell.content
        if isinstance(content, str):
            return content
        if isinstance(content, ft.Text):
            return content.value
        value = getattr(content, "value", None)
        return value if value is not None else str(content)

    @classmethod
    def _names_from_columns(cls, columns: Sequence[ft.DataColumn]) -> list[str]:
        names = [
            cls._name_from_column(column, index) for index, column in enumerate(columns)
        ]
        cls._ensure_unique_names(names)
        return names

    @staticmethod
    def _name_from_column(column: ft.DataColumn, index: int) -> str:
        if not isinstance(column, ft.DataColumn):
            raise TypeError(
                f"DataTable column {index} must be ft.DataColumn, "
                f"got {type(column).__name__}"
            )
        label = column.label
        if isinstance(label, str):
            name = label
        elif isinstance(label, ft.Text):
            name = label.value
        elif isinstance(column.data, str):
            name = column.data
        else:
            raise TypeError(
                f"cannot infer an export name for column {index}; use a string "
                "or ft.Text label, or set DataColumn.data to a string"
            )
        if not name:
            raise ValueError(f"column {index} has an empty export name")
        return name

    @staticmethod
    def _ensure_unique_names(names: Sequence[str]) -> None:
        seen: set[str] = set()
        duplicate: str | None = None
        for name in names:
            if name in seen:
                duplicate = name
                break
            seen.add(name)
        if duplicate is not None:
            raise ValueError(
                f"duplicate column name {duplicate!r}; record exports require "
                "unique names"
            )

    @staticmethod
    def _csv_value(value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, ft.Text):
            return value.value
        if isinstance(value, ft.Control):
            control_value = getattr(value, "value", None)
            return control_value if control_value is not None else str(value)
        return value

    def _update_if_mounted(self) -> None:
        try:
            _ = self._table.page
        except RuntimeError:
            # Configuration before insertion into a page is expected.
            return
        # Do not hide failures from an attached control, such as Flet's
        # "Frozen control cannot be updated" guard.
        self._table.update()
