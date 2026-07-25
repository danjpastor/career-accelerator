"""VS Code-inspired assistance for Career Accelerator code editors.

The component intentionally stays local and deterministic.  It provides
contextual completions, paired-character editing, indentation, and line-comment
shortcuts without sending learner code to an external service.
"""

from __future__ import annotations

import builtins
import csv
from dataclasses import dataclass, field
import keyword
from pathlib import Path
import re
from typing import Iterable

from PySide6.QtCore import QEvent, QPoint, QRect, QStringListModel, Qt, QTimer
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import QApplication, QCompleter, QPlainTextEdit, QTextEdit


_SQL_KEYWORDS = (
    "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
    "OFFSET", "DISTINCT", "AS", "JOIN", "INNER JOIN", "LEFT JOIN",
    "RIGHT JOIN", "FULL JOIN", "CROSS JOIN", "ON", "USING", "UNION",
    "UNION ALL", "INTERSECT", "EXCEPT", "WITH", "RECURSIVE", "CASE",
    "WHEN", "THEN", "ELSE", "END", "AND", "OR", "NOT", "IN", "BETWEEN",
    "LIKE", "ILIKE", "IS NULL", "IS NOT NULL", "NULLS FIRST", "NULLS LAST",
    "ASC", "DESC", "OVER", "PARTITION BY", "ROWS", "RANGE", "CURRENT ROW",
    "UNBOUNDED PRECEDING", "UNBOUNDED FOLLOWING", "QUALIFY", "PIVOT",
    "UNPIVOT", "CREATE TABLE", "CREATE VIEW", "CREATE OR REPLACE VIEW",
    "INSERT INTO", "UPDATE", "DELETE FROM", "ALTER TABLE", "DROP TABLE",
    "COPY", "DESCRIBE", "EXPLAIN", "VALUES", "TRUE", "FALSE", "NULL",
)

_SQL_FUNCTIONS = (
    "COUNT", "COUNT_IF", "SUM", "AVG", "MIN", "MAX", "MEDIAN", "MODE",
    "STDDEV", "STDDEV_POP", "STDDEV_SAMP", "VAR_POP", "VAR_SAMP",
    "APPROX_COUNT_DISTINCT", "STRING_AGG", "LIST", "ARRAY_AGG", "FIRST",
    "LAST", "COALESCE", "NULLIF", "IFNULL", "GREATEST", "LEAST", "CAST",
    "TRY_CAST", "ROUND", "CEIL", "FLOOR", "ABS", "POWER", "SQRT", "MOD",
    "LOWER", "UPPER", "TRIM", "LTRIM", "RTRIM", "LENGTH", "REPLACE",
    "CONCAT", "CONCAT_WS", "SUBSTRING", "SPLIT_PART", "REGEXP_REPLACE",
    "REGEXP_MATCHES", "STRPTIME", "STRFTIME", "DATE_TRUNC", "DATE_PART",
    "DATEDIFF", "DATEADD", "CURRENT_DATE", "CURRENT_TIMESTAMP", "EXTRACT",
    "ROW_NUMBER", "RANK", "DENSE_RANK", "NTILE", "LAG", "LEAD",
    "FIRST_VALUE", "LAST_VALUE", "PERCENT_RANK", "CUME_DIST", "FILTER",
    "READ_CSV", "READ_CSV_AUTO", "READ_PARQUET", "READ_JSON_AUTO",
)

_PYTHON_WORDS = tuple(sorted(set(keyword.kwlist) | set(dir(builtins))))

_PYTHON_COMMON = (
    "pd", "np", "Path", "DataFrame", "Series", "read_csv", "read_parquet",
    "read_excel", "read_json", "to_csv", "to_parquet", "head", "tail",
    "shape", "columns", "dtypes", "info", "describe", "isna", "notna",
    "fillna", "dropna", "drop_duplicates", "duplicated", "astype", "rename",
    "replace", "map", "apply", "assign", "query", "loc", "iloc", "groupby",
    "agg", "transform", "merge", "join", "concat", "pivot_table", "melt",
    "sort_values", "sort_index", "value_counts", "nunique", "unique",
    "reset_index", "set_index", "copy", "str", "dt", "plot", "hist",
)

_PANDAS_MEMBERS = (
    "read_csv", "read_parquet", "read_excel", "read_json", "read_sql",
    "DataFrame", "Series", "concat", "merge", "to_datetime", "isna",
    "notna", "cut", "qcut", "crosstab", "pivot_table", "date_range",
)

_DATAFRAME_MEMBERS = (
    "head", "tail", "sample", "shape", "columns", "dtypes", "info",
    "describe", "isna", "notna", "fillna", "dropna", "duplicated",
    "drop_duplicates", "astype", "rename", "replace", "assign", "query",
    "loc", "iloc", "groupby", "agg", "transform", "merge", "join",
    "pivot_table", "melt", "sort_values", "sort_index", "value_counts",
    "nunique", "unique", "reset_index", "set_index", "copy", "to_csv",
    "to_parquet", "to_excel", "plot", "hist", "corr", "select_dtypes",
)

_PATH_MEMBERS = (
    "exists", "is_file", "is_dir", "mkdir", "glob", "rglob", "iterdir",
    "read_text", "write_text", "open", "resolve", "relative_to", "parent",
    "name", "stem", "suffix", "with_suffix", "as_posix", "unlink", "rename",
)

_WORD_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_DOTTED_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]*$")
_SQL_ALIAS_PATTERN = re.compile(
    r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_\.]*)"
    r"(?:\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?",
    re.IGNORECASE,
)


@dataclass
class CompletionContext:
    tables: dict[str, tuple[str, ...]] = field(default_factory=dict)
    columns: set[str] = field(default_factory=set)
    extra_words: set[str] = field(default_factory=set)

    def merge(
        self,
        *,
        tables: dict[str, Iterable[str]] | None = None,
        columns: Iterable[str] | None = None,
        extra_words: Iterable[str] | None = None,
    ) -> None:
        if tables:
            for table, values in tables.items():
                clean_table = str(table or "").strip()
                if not clean_table:
                    continue
                clean_columns = tuple(
                    dict.fromkeys(
                        str(value or "").strip()
                        for value in values
                        if str(value or "").strip()
                    )
                )
                self.tables[clean_table] = clean_columns
                self.columns.update(clean_columns)
        if columns:
            self.columns.update(
                str(value or "").strip()
                for value in columns
                if str(value or "").strip()
            )
        if extra_words:
            self.extra_words.update(
                str(value or "").strip()
                for value in extra_words
                if str(value or "").strip()
            )


def project_completion_context(project_dir: Path | None) -> CompletionContext:
    """Read lightweight table and column context without opening a database."""
    context = CompletionContext()
    if project_dir is None:
        return context
    root = Path(project_dir)
    if not root.exists():
        return context

    dictionary = root / "documentation" / "data_dictionary.csv"
    if dictionary.is_file():
        try:
            with dictionary.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            grouped: dict[str, list[str]] = {}
            for row in rows:
                table = str(row.get("table") or "").strip()
                column = str(row.get("column") or "").strip()
                if table and column:
                    grouped.setdefault(table, []).append(column)
            context.merge(tables=grouped)
        except (OSError, UnicodeError, csv.Error):
            pass

    candidates: list[Path] = []
    for relative in (
        "data/raw",
        "data/processed",
        "data/staging",
        "datasets",
    ):
        folder = root / relative
        if folder.exists():
            candidates.extend(sorted(folder.rglob("*.csv"))[:80])
    for path in candidates[:120]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                columns = next(csv.reader(handle), [])
        except (OSError, UnicodeError, csv.Error):
            continue
        table = re.sub(r"[^A-Za-z0-9_]+", "_", path.stem).strip("_")
        if table and columns:
            context.merge(tables={table: columns})
    return context


def detect_notebook_language(source: str, fallback: str = "python") -> str:
    text = str(source or "").replace("\r\n", "\n").replace("\r", "\n")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.casefold()
        if lowered.startswith("%%sql") or lowered.startswith("%sql"):
            return "sql"
        if lowered.startswith("%%bash") or lowered.startswith("%%sh"):
            return "shell"
        if stripped.startswith("#") or stripped.startswith("--"):
            continue
        if re.match(
            r"^(?:SELECT|WITH|CREATE|INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|"
            r"DESCRIBE|DESC|SHOW|PRAGMA|EXPLAIN|COPY|VALUES|CALL|EXPORT|"
            r"IMPORT|ATTACH|DETACH|INSTALL|LOAD|PIVOT|UNPIVOT)\b",
            stripped,
            flags=re.IGNORECASE,
        ):
            return "sql"
        break
    return fallback


def _document_identifiers(text: str) -> set[str]:
    return {
        word
        for word in _WORD_PATTERN.findall(str(text or ""))
        if len(word) >= 2 and not word.isdigit()
    }


def _sql_aliases(text: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table, alias in _SQL_ALIAS_PATTERN.findall(str(text or "")):
        clean_table = table.split(".")[-1]
        if alias and alias.upper() not in _SQL_KEYWORDS:
            aliases[alias] = clean_table
        aliases.setdefault(clean_table, clean_table)
    return aliases


class EditorAssistMixin:
    """Mixin used by QTextEdit and QPlainTextEdit code editors."""

    def _init_editor_assist(
        self,
        *,
        language: str = "plain",
        project_dir: Path | None = None,
    ) -> None:
        self._assist_language = str(language or "plain").casefold()
        self._assist_context = project_completion_context(project_dir)
        self._assist_peer_text = ""
        self._assist_suppressed = False
        self._completion_start = 0
        self._completion_model = QStringListModel(self)
        self._completer = QCompleter(self._completion_model, self)
        self._completer.setWidget(self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setModelSorting(QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        self._completer.setMaxVisibleItems(12)
        self._completer.activated[str].connect(self._insert_completion)
        self._completer.popup().setStyleSheet(
            "QListView {background:#111A2D;color:#F4F7FF;border:1px solid #4C5C78;"
            "selection-background-color:#6F49C9;selection-color:white;padding:3px;}"
            "QListView::item {padding:5px 8px;}"
        )
        self._completion_timer = QTimer(self)
        self._completion_timer.setSingleShot(True)
        self._completion_timer.setInterval(45)
        self._completion_timer.timeout.connect(self._show_context_completion)
        self._comment_chord_active = False
        self._comment_chord_timer = QTimer(self)
        self._comment_chord_timer.setSingleShot(True)
        self._comment_chord_timer.setInterval(1600)
        self._comment_chord_timer.timeout.connect(self._clear_comment_chord)

    def set_language(self, language: str) -> None:
        language = str(language or "plain").casefold()
        if language != self._assist_language:
            self._assist_language = language
            self._completer.popup().hide()

    def language(self) -> str:
        return self._assist_language

    def set_project_context(self, project_dir: Path | None) -> None:
        self._assist_context = project_completion_context(project_dir)

    def set_completion_context(
        self,
        *,
        tables: dict[str, Iterable[str]] | None = None,
        columns: Iterable[str] | None = None,
        extra_words: Iterable[str] | None = None,
    ) -> None:
        self._assist_context.merge(
            tables=tables,
            columns=columns,
            extra_words=extra_words,
        )

    def set_peer_text(self, text: str) -> None:
        self._assist_peer_text = str(text or "")

    def trigger_completion(self) -> None:
        self._show_context_completion(force=True)

    def _clear_comment_chord(self) -> None:
        self._comment_chord_active = False

    def _comment_prefix(self) -> str | None:
        if self._assist_language == "sql":
            return "--"
        if self._assist_language in {"python", "shell"}:
            return "#"
        return None

    def _selected_line_numbers(self) -> tuple[int, int, bool]:
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        had_selection = cursor.hasSelection()
        if had_selection and end > start:
            block = self.document().findBlock(end)
            if block.isValid() and end == block.position():
                end -= 1
        first = self.document().findBlock(start)
        last = self.document().findBlock(max(start, end))
        return max(0, first.blockNumber()), max(0, last.blockNumber()), had_selection

    def _apply_line_comment(self, action: str) -> bool:
        prefix = self._comment_prefix()
        if not prefix:
            return False
        current = self.textCursor()
        original_block = current.blockNumber()
        original_column = current.positionInBlock()
        first_number, last_number, had_selection = self._selected_line_numbers()
        all_commented = True
        any_content = False
        for number in range(first_number, last_number + 1):
            block = self.document().findBlockByNumber(number)
            stripped = block.text().lstrip(" \t") if block.isValid() else ""
            if not stripped:
                continue
            any_content = True
            if not stripped.startswith(prefix):
                all_commented = False
        if action == "toggle":
            action = "uncomment" if any_content and all_commented else "comment"

        editor = QTextCursor(self.document())
        editor.beginEditBlock()
        cursor_delta = 0
        try:
            for number in range(last_number, first_number - 1, -1):
                block = self.document().findBlockByNumber(number)
                if not block.isValid():
                    continue
                line = block.text()
                indent = len(line) - len(line.lstrip(" \t"))
                stripped = line[indent:]
                position = block.position() + indent
                if action == "comment":
                    addition = prefix + " "
                    editor.setPosition(position)
                    editor.insertText(addition)
                    if number == original_block:
                        cursor_delta += len(addition)
                else:
                    if stripped.startswith(prefix + " "):
                        remove_count = len(prefix) + 1
                    elif stripped.startswith(prefix):
                        remove_count = len(prefix)
                    else:
                        continue
                    editor.setPosition(position)
                    editor.setPosition(position + remove_count, QTextCursor.MoveMode.KeepAnchor)
                    editor.removeSelectedText()
                    if number == original_block:
                        cursor_delta -= remove_count
        finally:
            editor.endEditBlock()

        restored = QTextCursor(self.document())
        if had_selection:
            first = self.document().findBlockByNumber(first_number)
            last = self.document().findBlockByNumber(last_number)
            if first.isValid() and last.isValid():
                restored.setPosition(first.position())
                restored.setPosition(
                    last.position() + len(last.text()),
                    QTextCursor.MoveMode.KeepAnchor,
                )
        else:
            block = self.document().findBlockByNumber(original_block)
            if block.isValid():
                column = max(0, min(len(block.text()), original_column + cursor_delta))
                restored.setPosition(block.position() + column)
        self.setTextCursor(restored)
        return True

    def _indent_selection(self, dedent: bool = False) -> bool:
        cursor = self.textCursor()
        if not cursor.hasSelection() and dedent:
            first = last = cursor.blockNumber()
        elif not cursor.hasSelection():
            cursor.insertText("    ")
            return True
        else:
            first, last, _ = self._selected_line_numbers()
        editor = QTextCursor(self.document())
        editor.beginEditBlock()
        try:
            for number in range(last, first - 1, -1):
                block = self.document().findBlockByNumber(number)
                if not block.isValid():
                    continue
                editor.setPosition(block.position())
                if dedent:
                    text = block.text()
                    remove_count = 1 if text.startswith("\t") else min(4, len(text) - len(text.lstrip(" ")))
                    if remove_count:
                        editor.setPosition(block.position() + remove_count, QTextCursor.MoveMode.KeepAnchor)
                        editor.removeSelectedText()
                else:
                    editor.insertText("    ")
        finally:
            editor.endEditBlock()
        return True

    def _insert_pair(self, opening: str, closing: str) -> None:
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().replace("\u2029", "\n")
            cursor.insertText(opening + selected + closing)
            cursor.setPosition(cursor.position() - len(closing))
            self.setTextCursor(cursor)
            return
        cursor.insertText(opening + closing)
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(closing))
        self.setTextCursor(cursor)

    def _character_after_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        return cursor.selectedText()

    def _character_before_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
        return cursor.selectedText()

    def _paired_enter(self) -> bool:
        before = self._character_before_cursor()
        after = self._character_after_cursor()
        pairs = {"(": ")", "[": "]", "{": "}"}
        if pairs.get(before) != after:
            return False
        cursor = self.textCursor()
        block_text = cursor.block().text()
        indent = block_text[: len(block_text) - len(block_text.lstrip(" \t"))]
        inner = indent + "    "
        cursor.insertText("\n" + inner + "\n" + indent)
        cursor.movePosition(QTextCursor.MoveOperation.Up)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.setTextCursor(cursor)
        return True

    def _normal_enter(self) -> None:
        cursor = self.textCursor()
        before = cursor.block().text()[: cursor.positionInBlock()]
        indent = before[: len(before) - len(before.lstrip(" \t"))]
        stripped = before.rstrip()
        if self._assist_language == "python" and stripped.endswith(":"):
            indent += "    "
        elif stripped.endswith(("(", "[", "{")):
            indent += "    "
        cursor.insertText("\n" + indent)
        self.setTextCursor(cursor)

    def _completion_prefix(self) -> tuple[str, str, int]:
        cursor = self.textCursor()
        text = self.toPlainText()[: cursor.position()]
        match = _DOTTED_PATTERN.search(text)
        full = match.group(0) if match else ""
        segment = full.rsplit(".", 1)[-1]
        return full, segment, cursor.position() - len(segment)

    def _sql_candidates(self, full_prefix: str, before_cursor: str) -> set[str]:
        context = self._assist_context
        candidates = set(_SQL_KEYWORDS) | set(_SQL_FUNCTIONS)
        candidates.update(context.tables)
        candidates.update(context.columns)
        candidates.update(context.extra_words)
        candidates.update(_document_identifiers(self.toPlainText()))
        candidates.update(_document_identifiers(self._assist_peer_text))

        aliases = _sql_aliases(self.toPlainText())
        if "." in full_prefix:
            owner = full_prefix.rsplit(".", 1)[0].split(".")[-1]
            table = aliases.get(owner, owner)
            for table_name, columns in context.tables.items():
                if table_name.casefold() == table.casefold():
                    return set(columns)
            return set(context.columns)

        upper = before_cursor.upper()
        if re.search(r"\b(?:FROM|JOIN|UPDATE|INTO|TABLE)\s+[A-Z0-9_\.]*$", upper):
            return set(context.tables) | {"SELECT", "VALUES"}
        if re.search(r"\b(?:SELECT|WHERE|ON|HAVING|QUALIFY|BY)\s+[A-Z0-9_\.]*$", upper):
            return set(context.columns) | set(_SQL_FUNCTIONS) | set(aliases)
        return candidates

    def _python_candidates(self, full_prefix: str) -> set[str]:
        context = self._assist_context
        if "." in full_prefix:
            owner = full_prefix.rsplit(".", 1)[0].split(".")[-1]
            owner_lower = owner.casefold()
            if owner_lower in {"pd", "pandas"}:
                return set(_PANDAS_MEMBERS)
            if owner_lower in {"path", "project_dir", "raw_path", "processed_path"}:
                return set(_PATH_MEMBERS)
            if owner_lower.endswith(("df", "dataframe")) or owner_lower in {
                "raw_df", "clean_df", "df",
            }:
                return set(_DATAFRAME_MEMBERS) | set(context.columns)
            return set(_DATAFRAME_MEMBERS) | set(_PATH_MEMBERS)
        candidates = set(_PYTHON_WORDS) | set(_PYTHON_COMMON)
        candidates.update(context.tables)
        candidates.update(context.columns)
        candidates.update(context.extra_words)
        candidates.update(_document_identifiers(self.toPlainText()))
        candidates.update(_document_identifiers(self._assist_peer_text))
        return candidates

    def _candidate_list(self, full_prefix: str, segment: str, before_cursor: str) -> list[str]:
        if self._assist_language == "sql":
            candidates = self._sql_candidates(full_prefix, before_cursor)
        elif self._assist_language == "python":
            candidates = self._python_candidates(full_prefix)
        elif self._assist_language == "shell":
            candidates = {"cd", "pwd", "ls", "mkdir", "echo", "python", "pip"}
        else:
            candidates = set(self._assist_context.extra_words)
        segment_folded = segment.casefold()
        filtered = [
            candidate
            for candidate in candidates
            if candidate and (
                not segment_folded
                or candidate.casefold().startswith(segment_folded)
            )
            and candidate.casefold() != segment_folded
        ]
        return sorted(dict.fromkeys(filtered), key=lambda value: (value.casefold(), value))[:240]

    def _show_context_completion(self, force: bool = False) -> None:
        if self._assist_suppressed or self.isReadOnly():
            self._completer.popup().hide()
            return
        full, segment, start = self._completion_prefix()
        before = self.toPlainText()[: self.textCursor().position()]
        if not force:
            if not full:
                self._completer.popup().hide()
                return
            if "." not in full and len(segment) < 2:
                self._completer.popup().hide()
                return
        candidates = self._candidate_list(full, segment, before)
        if not candidates:
            self._completer.popup().hide()
            return
        self._completion_start = start
        self._completion_model.setStringList(candidates)
        self._completer.setCompletionPrefix(segment)
        popup = self._completer.popup()
        popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
        rect = self.cursorRect()
        width = min(520, max(260, popup.sizeHintForColumn(0) + 36))
        anchor = QRect(rect)
        anchor.translate(0, rect.height() + 6)
        anchor.setWidth(width)
        anchor.setHeight(1)
        self._completion_popup_width = width
        self._completer.complete(anchor)
        QTimer.singleShot(0, self._position_completion_popup)

    def _position_completion_popup(self) -> None:
        """Place autocomplete below or above the caret, never over its line."""
        popup = self._completer.popup()
        if not popup.isVisible():
            return

        cursor_rect = self.cursorRect()
        below = self.mapToGlobal(cursor_rect.bottomLeft()) + QPoint(0, 8)
        above_anchor = self.mapToGlobal(cursor_rect.topLeft())
        screen = QApplication.screenAt(below) or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else QRect()

        width = int(getattr(self, "_completion_popup_width", 320))
        row_count = min(10, max(1, self._completion_model.rowCount()))
        row_height = popup.sizeHintForRow(0)
        if row_height <= 0:
            row_height = max(24, self.fontMetrics().height() + 10)
        height = min(340, max(row_height + 8, (row_height * row_count) + 8))
        popup.resize(width, height)

        if available.isValid():
            x = max(available.left(), min(below.x(), available.right() - width + 1))
            y = below.y()
            if y + height > available.bottom() + 1:
                y = above_anchor.y() - height - 8
            y = max(available.top(), min(y, available.bottom() - height + 1))
            popup.move(x, y)
        else:
            popup.move(below)

    def _insert_completion(self, completion: str) -> None:
        cursor = self.textCursor()
        cursor.setPosition(self._completion_start)
        cursor.setPosition(self.textCursor().position(), QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(str(completion))
        self.setTextCursor(cursor)
        self._completer.popup().hide()

    def _accept_current_completion(self) -> bool:
        popup = self._completer.popup()
        if not popup.isVisible():
            return False
        index = popup.currentIndex()
        if not index.isValid():
            return False
        self._insert_completion(str(index.data() or ""))
        return True

    def handle_editor_assist_key(self, event: QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        control = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if self._completer.popup().isVisible():
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                if self._accept_current_completion():
                    event.accept()
                    return True
            if key == Qt.Key.Key_Escape:
                self._completer.popup().hide()
                event.accept()
                return True

        if control and key == Qt.Key.Key_Space:
            self.trigger_completion()
            event.accept()
            return True

        if control and key == Qt.Key.Key_Slash:
            self._clear_comment_chord()
            self._comment_chord_timer.stop()
            if self._apply_line_comment("toggle"):
                event.accept()
                return True

        if control and key == Qt.Key.Key_K:
            self._comment_chord_active = True
            self._comment_chord_timer.start()
            event.accept()
            return True

        if self._comment_chord_active:
            self._clear_comment_chord()
            self._comment_chord_timer.stop()
            if control and key == Qt.Key.Key_C and self._apply_line_comment("comment"):
                event.accept()
                return True
            if control and key == Qt.Key.Key_U and self._apply_line_comment("uncomment"):
                event.accept()
                return True

        if key == Qt.Key.Key_Tab and not control:
            if self._indent_selection(dedent=shift):
                event.accept()
                return True
        if key == Qt.Key.Key_Backtab:
            if self._indent_selection(dedent=True):
                event.accept()
                return True

        text = event.text()
        pairs = {"(": ")", "[": "]", "{": "}", "'": "'", '"': '"', "`": "`"}
        if text in pairs and not control:
            next_character = self._character_after_cursor()
            if text in {"'", '"', "`"} and next_character == text:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Right)
                self.setTextCursor(cursor)
            else:
                self._insert_pair(text, pairs[text])
            self._completion_timer.start()
            event.accept()
            return True
        if text in set(pairs.values()) and not control and self._character_after_cursor() == text:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            event.accept()
            return True

        if key == Qt.Key.Key_Backspace and not control:
            before = self._character_before_cursor()
            after = self._character_after_cursor()
            if pairs.get(before) == after:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Left)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2)
                cursor.removeSelectedText()
                self.setTextCursor(cursor)
                event.accept()
                return True

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not control:
            if not self._paired_enter():
                self._normal_enter()
            event.accept()
            return True

        if text and (text[-1].isalnum() or text[-1] in "_."):
            self._completion_timer.start()
        elif key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self._completion_timer.start()
        else:
            self._completer.popup().hide()
        return False


class AssistedPlainTextEdit(EditorAssistMixin, QPlainTextEdit):
    def __init__(
        self,
        parent=None,
        *,
        language: str = "plain",
        project_dir: Path | None = None,
    ):
        QPlainTextEdit.__init__(self, parent)
        self._init_editor_assist(language=language, project_dir=project_dir)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        if self.handle_editor_assist_key(event):
            return
        super().keyPressEvent(event)


class AssistedTextEdit(EditorAssistMixin, QTextEdit):
    def __init__(
        self,
        parent=None,
        *,
        language: str = "plain",
        project_dir: Path | None = None,
    ):
        QTextEdit.__init__(self, parent)
        self._init_editor_assist(language=language, project_dir=project_dir)
        self.setAcceptRichText(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        if self.handle_editor_assist_key(event):
            return
        super().keyPressEvent(event)
