from __future__ import annotations

import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from .base import ValidationResult


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS = {"m": _MAIN_NS, "r": _REL_NS, "pr": _PKG_REL_NS}
_CELL_REF = re.compile(r"^([A-Z]+)([0-9]+)$")
_RANGE_REF = re.compile(r"^([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)$")


class WorkbookValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Cell:
    ref: str
    formula: str
    value: str
    has_formula: bool = False


class WorkbookValidator:
    """Inspect an XLSX workbook without requiring an Excel-only dependency.

    The validator reads the Open XML package directly. It intentionally checks
    durable workbook structures—sheets, formulas, filters, validation rules,
    tables, pivots, charts, and populated output ranges—rather than relying on
    application-specific UI state that may differ between Excel and Google
    Sheets exports.
    """

    def __init__(self, workbook_path: str | Path):
        self.path = Path(workbook_path).resolve()
        if not self.path.is_file():
            raise WorkbookValidationError(
                "The practice workbook does not exist yet. Open the workbook first, "
                "complete the task, save it, and then check your work."
            )
        try:
            self._zip = zipfile.ZipFile(self.path, "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise WorkbookValidationError(
                "The practice workbook could not be read. Close it, save it as an "
                ".xlsx file, and try again."
            ) from exc
        self._shared_strings = self._read_shared_strings()
        self._sheets = self._read_sheet_map()
        self._sheet_cache: dict[str, ET.Element] = {}
        self._cell_cache: dict[str, dict[str, _Cell]] = {}

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "WorkbookValidator":
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    @staticmethod
    def _normalize_target(base: str, target: str) -> str:
        target = str(target or "").replace("\\", "/")
        if target.startswith("/"):
            return target.lstrip("/")
        return str(PurePosixPath(base).joinpath(target))

    def _xml(self, member: str) -> ET.Element:
        try:
            return ET.fromstring(self._zip.read(member))
        except KeyError as exc:
            raise WorkbookValidationError(
                f"The workbook package is missing {member}."
            ) from exc
        except ET.ParseError as exc:
            raise WorkbookValidationError(
                f"The workbook package contains invalid XML in {member}."
            ) from exc

    def _read_shared_strings(self) -> tuple[str, ...]:
        try:
            root = ET.fromstring(self._zip.read("xl/sharedStrings.xml"))
        except KeyError:
            return ()
        result: list[str] = []
        for item in root.findall("m:si", _NS):
            texts = [node.text or "" for node in item.findall(".//m:t", _NS)]
            result.append("".join(texts))
        return tuple(result)

    def _read_sheet_map(self) -> dict[str, str]:
        workbook = self._xml("xl/workbook.xml")
        rels = self._xml("xl/_rels/workbook.xml.rels")
        targets = {
            str(item.attrib.get("Id") or ""): str(item.attrib.get("Target") or "")
            for item in rels.findall("pr:Relationship", _NS)
        }
        result: dict[str, str] = {}
        for sheet in workbook.findall("m:sheets/m:sheet", _NS):
            name = str(sheet.attrib.get("name") or "").strip()
            rel_id = str(sheet.attrib.get(f"{{{_REL_NS}}}id") or "")
            target = targets.get(rel_id, "")
            if name and target:
                result[name] = self._normalize_target("xl", target)
        return result

    @property
    def sheet_names(self) -> tuple[str, ...]:
        return tuple(self._sheets)

    def _sheet_root(self, sheet_name: str) -> ET.Element:
        if sheet_name not in self._sheets:
            raise WorkbookValidationError(
                f"The workbook is missing the required sheet “{sheet_name}”."
            )
        if sheet_name not in self._sheet_cache:
            self._sheet_cache[sheet_name] = self._xml(self._sheets[sheet_name])
        return self._sheet_cache[sheet_name]

    def _cells(self, sheet_name: str) -> dict[str, _Cell]:
        if sheet_name in self._cell_cache:
            return self._cell_cache[sheet_name]
        result: dict[str, _Cell] = {}
        root = self._sheet_root(sheet_name)
        for cell in root.findall(".//m:sheetData/m:row/m:c", _NS):
            ref = str(cell.attrib.get("r") or "").upper()
            if not ref:
                continue
            formula_node = cell.find("m:f", _NS)
            value_node = cell.find("m:v", _NS)
            formula = formula_node.text or "" if formula_node is not None else ""
            cell_type = str(cell.attrib.get("t") or "")
            value = value_node.text or "" if value_node is not None else ""
            if cell_type == "s" and value:
                try:
                    value = self._shared_strings[int(value)]
                except (ValueError, IndexError):
                    pass
            elif cell_type == "inlineStr":
                value = "".join(
                    node.text or "" for node in cell.findall(".//m:is/m:t", _NS)
                )
            result[ref] = _Cell(
                ref=ref,
                formula=formula,
                value=value,
                has_formula=formula_node is not None,
            )
        self._cell_cache[sheet_name] = result
        return result

    @staticmethod
    def _column_number(label: str) -> int:
        number = 0
        for char in label.upper():
            number = number * 26 + (ord(char) - 64)
        return number

    @staticmethod
    def _column_label(number: int) -> str:
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    @classmethod
    def _range_refs(cls, range_ref: str) -> tuple[str, ...]:
        text = str(range_ref or "").replace("$", "").upper().strip()
        single = _CELL_REF.fullmatch(text)
        if single:
            return (text,)
        match = _RANGE_REF.fullmatch(text)
        if not match:
            raise WorkbookValidationError(f"Invalid workbook range: {range_ref}")
        left_col, top_row, right_col, bottom_row = match.groups()
        start_col = cls._column_number(left_col)
        end_col = cls._column_number(right_col)
        start_row = int(top_row)
        end_row = int(bottom_row)
        return tuple(
            f"{cls._column_label(column)}{row}"
            for row in range(start_row, end_row + 1)
            for column in range(start_col, end_col + 1)
        )

    @staticmethod
    def _normalized_text(value: Any) -> str:
        return " ".join(str(value or "").strip().casefold().split())

    @classmethod
    def _sqref_contains(cls, sqref: str, target: str) -> bool:
        """Return whether an Open XML sqref fully covers a target range."""
        try:
            target_refs = set(cls._range_refs(target))
        except WorkbookValidationError:
            return False
        if not target_refs:
            return False
        for token in str(sqref or "").replace("$", "").upper().split():
            try:
                rule_refs = set(cls._range_refs(token))
            except WorkbookValidationError:
                continue
            if target_refs.issubset(rule_refs):
                return True
        return False

    @staticmethod
    def _number(value: Any) -> float | None:
        text = str(value or "").strip().replace(",", "").replace("$", "")
        try:
            return float(text)
        except ValueError:
            return None

    def _header_values(self, sheet_name: str, row: int) -> list[str]:
        cells = self._cells(sheet_name)
        headers: list[tuple[int, str]] = []
        for ref, cell in cells.items():
            match = _CELL_REF.fullmatch(ref)
            if not match or int(match.group(2)) != int(row):
                continue
            headers.append((self._column_number(match.group(1)), cell.value))
        return [value for _column, value in sorted(headers)]

    def _sheet_relationship_targets(self, sheet_name: str) -> tuple[str, ...]:
        sheet_path = PurePosixPath(self._sheets[sheet_name])
        rel_path = str(
            sheet_path.parent / "_rels" / f"{sheet_path.name}.rels"
        )
        try:
            root = ET.fromstring(self._zip.read(rel_path))
        except KeyError:
            return ()
        return tuple(
            str(item.attrib.get("Target") or "")
            for item in root.findall("pr:Relationship", _NS)
        )

    def _check(self, check: dict[str, Any], answer: str) -> tuple[bool, str]:
        kind = str(check.get("type") or "").strip().lower()
        sheet = str(check.get("sheet") or "").strip()

        if kind == "sheet_exists":
            passed = sheet in self._sheets
            return passed, (
                f"Found the {sheet} sheet."
                if passed
                else f"Create or restore the required sheet named {sheet}."
            )

        if kind == "headers":
            expected = [str(item) for item in check.get("expected", [])]
            actual = self._header_values(sheet, int(check.get("row", 1)))
            if bool(check.get("exact", False)):
                passed = [self._normalized_text(item) for item in actual] == [
                    self._normalized_text(item) for item in expected
                ]
            else:
                actual_set = {self._normalized_text(item) for item in actual}
                passed = all(self._normalized_text(item) in actual_set for item in expected)
            return passed, (
                "The required column headings are present."
                if passed
                else "Add the required headings: " + ", ".join(expected) + "."
            )

        if kind in {"formula_present", "formula_count"}:
            cells = self._cells(sheet)
            refs = self._range_refs(str(check.get("range") or check.get("cell") or ""))
            formula_cells = [
                cells[ref]
                for ref in refs
                if ref in cells and cells[ref].has_formula
            ]
            formulas = [cell.formula for cell in formula_cells if cell.formula]
            minimum = int(check.get("min_count", 1))
            passed = len(formula_cells) >= minimum
            contains_all = [str(item).casefold() for item in check.get("contains_all", [])]
            contains_any = [str(item).casefold() for item in check.get("contains_any", [])]
            searchable = "\n".join(formulas).casefold()
            if passed and contains_all:
                passed = all(item in searchable for item in contains_all)
            if passed and contains_any:
                passed = any(item in searchable for item in contains_any)
            return passed, (
                f"Found {len(formula_cells)} saved formula(s) in the required range."
                if passed
                else str(check.get("message") or "Enter and fill the required formula, then save the workbook.")
            )

        if kind == "cell_text":
            cell = self._cells(sheet).get(str(check.get("cell") or "").replace("$", "").upper())
            actual = cell.value if cell else ""
            expected = str(check.get("expected") or "")
            contains = [str(item) for item in check.get("contains", [])]
            normalized = self._normalized_text(actual)
            passed = (
                normalized == self._normalized_text(expected)
                if expected
                else all(self._normalized_text(item) in normalized for item in contains)
            )
            return passed, (
                f"The expected note is saved in {check.get('cell')}."
                if passed
                else str(check.get("message") or f"Update {check.get('cell')} with the requested text.")
            )

        if kind == "cell_number":
            cell = self._cells(sheet).get(str(check.get("cell") or "").replace("$", "").upper())
            actual = self._number(cell.value if cell else "")
            expected = float(check.get("expected", 0))
            tolerance = float(check.get("tolerance", 0.01))
            passed = actual is not None and math.isclose(actual, expected, abs_tol=tolerance)
            return passed, (
                f"The value in {check.get('cell')} matches the expected result."
                if passed
                else str(check.get("message") or f"Recheck the value in {check.get('cell')}.")
            )

        if kind in {"populated_range", "value_count"}:
            cells = self._cells(sheet)
            refs = self._range_refs(str(check.get("range") or ""))
            populated = [
                ref
                for ref in refs
                if ref in cells and (cells[ref].value != "" or cells[ref].has_formula)
            ]
            minimum = int(check.get("min_count", 1))
            passed = len(populated) >= minimum
            return passed, (
                f"Found {len(populated)} populated cells in the required output area."
                if passed
                else str(check.get("message") or "Complete the requested output area and save the workbook.")
            )

        if kind in {"auto_filter", "table_or_filter"}:
            root = self._sheet_root(sheet)
            has_filter = root.find("m:autoFilter", _NS) is not None
            has_table = root.find("m:tableParts", _NS) is not None
            passed = has_filter if kind == "auto_filter" else (has_filter or has_table)
            return passed, (
                "The data range has a saved filter or table."
                if passed
                else "Format the range as a table or add a filter, then save the workbook."
            )

        if kind == "data_validation":
            root = self._sheet_root(sheet)
            validations = root.findall("m:dataValidations/m:dataValidation", _NS)
            target = str(check.get("range") or "").replace("$", "").upper()
            passed = bool(validations)
            if passed and target:
                passed = any(
                    self._sqref_contains(
                        str(item.attrib.get("sqref") or ""),
                        target,
                    )
                    for item in validations
                )
            return passed, (
                "The requested data-validation rule is saved."
                if passed
                else "Add the requested drop-down or validation rule and save the workbook."
            )

        if kind == "conditional_formatting":
            root = self._sheet_root(sheet)
            rules = root.findall("m:conditionalFormatting", _NS)
            target = str(check.get("range") or "").replace("$", "").upper()
            passed = bool(rules)
            if passed and target:
                passed = any(
                    self._sqref_contains(
                        str(item.attrib.get("sqref") or ""),
                        target,
                    )
                    for item in rules
                )
            return passed, (
                "The requested conditional-formatting rule is saved."
                if passed
                else str(
                    check.get("message")
                    or "Add the requested conditional formatting and save the workbook."
                )
            )

        if kind in {"chart_present", "pivot_present", "chart_or_pivot"}:
            root = self._sheet_root(sheet)
            has_pivot = root.find("m:pivotTableParts", _NS) is not None
            targets = self._sheet_relationship_targets(sheet)
            has_chart = any("drawing" in target.casefold() for target in targets)
            passed = (
                has_chart
                if kind == "chart_present"
                else has_pivot
                if kind == "pivot_present"
                else (has_chart or has_pivot)
            )
            return passed, (
                "The requested analysis object is saved in the workbook."
                if passed
                else str(check.get("message") or "Create the requested pivot table or chart and save the workbook.")
            )

        if kind == "evidence_answer":
            expected_text = str(check.get("expected_answer") or "")
            if "expected_number" in check:
                actual = self._number(answer)
                expected = float(check.get("expected_number", 0))
                tolerance = float(check.get("tolerance", 0.01))
                passed = actual is not None and math.isclose(actual, expected, abs_tol=tolerance)
            else:
                passed = self._normalized_text(answer) == self._normalized_text(expected_text)
            return passed, (
                "Your evidence answer matches the workbook result."
                if passed
                else str(check.get("message") or "Recheck the requested workbook result and enter it exactly as shown.")
            )

        if kind == "any_of":
            options = [item for item in check.get("checks", []) if isinstance(item, dict)]
            messages: list[str] = []
            for option in options:
                passed, message = self._check(option, answer)
                messages.append(message)
                if passed:
                    return True, message
            return False, str(check.get("message") or "Complete at least one accepted workbook output. " + " ".join(messages))

        raise WorkbookValidationError(f"Unsupported workbook check: {kind or '<empty>'}")

    def validate(self, answer: str, config: dict[str, Any]) -> ValidationResult:
        checks = [item for item in config.get("checks", []) if isinstance(item, dict)]
        if not checks:
            return ValidationResult(
                False,
                "This workbook activity is missing its validation contract."
            )
        details: list[dict[str, Any]] = []
        failures: list[str] = []
        for check in checks:
            passed, message = self._check(check, answer)
            details.append(
                {
                    "type": str(check.get("type") or ""),
                    "passed": passed,
                    "message": message,
                }
            )
            if not passed:
                failures.append(message)
        if failures:
            return ValidationResult(
                False,
                "Not quite yet. " + " ".join(dict.fromkeys(failures)),
                details={"checks": details, "workbook": str(self.path)},
            )
        success = str(
            config.get("success_feedback")
            or "Workbook check passed. Your saved file contains the required result."
        )
        return ValidationResult(
            True,
            success,
            details={"checks": details, "workbook": str(self.path)},
        )
