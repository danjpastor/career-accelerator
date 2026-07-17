"""Shared native course-style widgets for Exercise Packs and Applied Labs.

The learning pages intentionally use normal Qt widgets rather than a monolithic
QTextEdit document. This keeps spacing, cards, tables, code controls, and
responsive behavior deterministic across Windows display scales.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Callable, Iterable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QSyntaxHighlighter, QTextCharFormat,
    QTextCursor, QTextFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.theme import COLORS


ACCENT = COLORS.get("purple", "#8b5cf6")
TEXT = COLORS.get("text", "#f4f4fb")
MUTED = COLORS.get("muted", "#b5b7ca")
BORDER = COLORS.get("border", "#343854")
SURFACE = COLORS.get("surface", "#111827")
SURFACE_ALT = COLORS.get("surface_alt", "#171a2a")


def clear_layout(layout: QVBoxLayout | QHBoxLayout) -> None:
    """Delete every widget/layout item owned by *layout*."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            # deleteLater() alone can leave the old course header painted until
            # the next deferred-delete pass when lessons are rebuilt quickly.
            # Detach and hide it immediately so responsive refreshes never show
            # duplicated/overlapping titles.
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        elif child_layout is not None:
            clear_layout(child_layout)  # type: ignore[arg-type]


def horizontal_rule() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet("background:#2b3347;border:none;")
    return line


def rich_text(value: str) -> str:
    """Render the small inline Markdown subset used by course content."""
    tokens: dict[str, str] = {}

    def code_token(match: re.Match[str]) -> str:
        key = f"@@CODE_{len(tokens)}@@"
        tokens[key] = (
            "<span style='font-family:Consolas,monospace; color:#efe8ff; "
            "background:#252b3d; border:1px solid #424a63; padding:1px 4px;'>"
            + html.escape(match.group(1), quote=False)
            + "</span>"
        )
        return key

    value = re.sub(r"`([^`\n]+)`", code_token, value)
    rendered = html.escape(value, quote=False)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", rendered)
    rendered = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r"<a style='color:#c5b3ff;text-decoration:none;' href='\2'>\1</a>",
        rendered,
    )
    for key, token in tokens.items():
        rendered = rendered.replace(key, token)
    return rendered.replace("\n", "<br>")


class SqlHighlighter(QSyntaxHighlighter):
    """Small dependency-free SQL highlighter for read-only course examples."""

    def __init__(self, document):
        super().__init__(document)
        self.rules: list[tuple[re.Pattern[str], QTextCharFormat]] = []

        keyword = QTextCharFormat()
        keyword.setForeground(QColor("#c6a3ff"))
        keyword.setFontWeight(QFont.Weight.Bold)
        keyword_pattern = re.compile(
            r"\b(?:SELECT|FROM|WHERE|AND|OR|NOT|IN|EXISTS|JOIN|LEFT|RIGHT|INNER|"
            r"OUTER|ON|AS|GROUP|BY|ORDER|HAVING|WITH|DISTINCT|CASE|WHEN|THEN|"
            r"ELSE|END|ASC|DESC|NULL|IS|LIKE|LIMIT|UNION|ALL)\b",
            re.IGNORECASE,
        )
        self.rules.append((keyword_pattern, keyword))

        function = QTextCharFormat()
        function.setForeground(QColor("#75d7f5"))
        function.setFontWeight(QFont.Weight.DemiBold)
        self.rules.append(
            (re.compile(r"\b(?:AVG|COUNT|SUM|MIN|MAX|ROUND)(?=\s*\()", re.I), function)
        )

        string = QTextCharFormat()
        string.setForeground(QColor("#b8df8a"))
        self.rules.append((re.compile(r"'(?:''|[^'])*'"), string))

        number = QTextCharFormat()
        number.setForeground(QColor("#ffc984"))
        self.rules.append((re.compile(r"\b\d+(?:\.\d+)?\b"), number))

        comment = QTextCharFormat()
        comment.setForeground(QColor("#7f8aa6"))
        comment.setFontItalic(True)
        self.rules.append((re.compile(r"--[^\n]*"), comment))

    def highlightBlock(self, text: str) -> None:  # noqa: N802 - Qt API
        for pattern, text_format in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), text_format)


class CodeCard(QFrame):
    """Reference-style read-only code box with language label and Copy action."""

    copied = Signal()

    def __init__(self, code: str, language: str = "sql", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("CourseCodeCard")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            "QFrame#CourseCodeCard {background:#101522;border:1px solid #303a52;"
            "border-radius:10px;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("CourseCodeHeader")
        header.setStyleSheet(
            "QWidget#CourseCodeHeader {background:#151d2d;border-top-left-radius:10px;"
            "border-top-right-radius:10px;border-bottom:1px solid #29334a;}"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 7, 8, 7)
        label_map = {
            "sql": "SQL",
            "duckdb": "SQL",
            "sqlite": "SQL",
            "text": "OUTPUT",
            "csv": "DATA",
            "json": "JSON",
            "python": "PYTHON",
            "powershell": "POWERSHELL",
            "bash": "TERMINAL",
        }
        language_key = (language or "code").lower()
        language_label = QLabel(label_map.get(language_key, language_key.upper()))
        language_label.setStyleSheet(
            "color:#b9c4da;font-size:9pt;font-weight:600;"
        )
        header_layout.addWidget(language_label)
        header_layout.addStretch()
        copy_button = QPushButton("▣  Copy")
        copy_button.setObjectName("Secondary")
        copy_button.setFixedHeight(30)
        copy_button.clicked.connect(self.copy_code)
        header_layout.addWidget(copy_button)
        layout.addWidget(header)

        code_row = QWidget()
        code_row_layout = QHBoxLayout(code_row)
        code_row_layout.setContentsMargins(0, 0, 0, 0)
        code_row_layout.setSpacing(0)

        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setPointSize(10)
        line_count = max(code.rstrip().count("\n") + 1, 1)

        self.line_numbers = QPlainTextEdit()
        self.line_numbers.setReadOnly(True)
        self.line_numbers.setPlainText("\n".join(str(index) for index in range(1, line_count + 1)))
        self.line_numbers.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.line_numbers.setFrameShape(QFrame.Shape.NoFrame)
        self.line_numbers.setFont(fixed_font)
        self.line_numbers.setFixedWidth(max(40, 18 + len(str(line_count)) * 9))
        self.line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setStyleSheet(
            "QPlainTextEdit {background:#111827;color:#6f7d95;border:none;"
            "border-right:1px solid #263148;padding:10px 7px;}"
        )
        code_row_layout.addWidget(self.line_numbers)

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setMinimumWidth(0)
        self.editor.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.editor.setPlainText(code.rstrip())
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.setFont(fixed_font)
        self.editor.setStyleSheet(
            "QPlainTextEdit {background:#0f1420;color:#f3f5fb;border:none;"
            "padding:10px 12px;selection-background-color:#6043b6;}"
        )
        if language_key in {"sql", "duckdb", "sqlite"}:
            self._highlighter = SqlHighlighter(self.editor.document())
        else:
            self._highlighter = None
        line_height = self.editor.fontMetrics().lineSpacing()
        code_height = min(max(line_count * line_height + 30, 88), 360)
        self.editor.setMinimumHeight(code_height)
        self.editor.setMaximumHeight(code_height)
        self.line_numbers.setMinimumHeight(code_height)
        self.line_numbers.setMaximumHeight(code_height)
        self.editor.verticalScrollBar().valueChanged.connect(
            self.line_numbers.verticalScrollBar().setValue
        )
        code_row_layout.addWidget(self.editor, 1)
        layout.addWidget(code_row)

    def copy_code(self) -> None:
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.copied.emit()




class SqlCodeEditor(QWidget):
    """Reusable SQL editor with line numbers and navigable error highlighting."""

    textChanged = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._error_line: int | None = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setPointSize(10)

        self.line_numbers = QPlainTextEdit()
        self.line_numbers.setReadOnly(True)
        self.line_numbers.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.line_numbers.setFrameShape(QFrame.Shape.NoFrame)
        self.line_numbers.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setFont(fixed_font)
        self.line_numbers.setStyleSheet(
            "QPlainTextEdit {background:#0c111c;color:#72809a;border:none;"
            "border-right:1px solid #29334a;padding:10px 7px;}"
        )

        self.editor = QPlainTextEdit()
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.editor.setFont(fixed_font)
        self.editor.setTabStopDistance(28)
        self.editor.setPlaceholderText("Write one read-only SELECT or WITH query here.")
        self.editor.setStyleSheet(
            "QPlainTextEdit {background:#111321;color:#f3f4ff;border:none;padding:10px;"
            "selection-background-color:#6747c7;}"
        )
        self._highlighter = SqlHighlighter(self.editor.document())

        self._layout.addWidget(self.line_numbers)
        self._layout.addWidget(self.editor, 1)

        self.editor.textChanged.connect(self._refresh_line_numbers)
        self.editor.textChanged.connect(self.clear_error_line)
        self.editor.textChanged.connect(self.textChanged.emit)
        self.editor.cursorPositionChanged.connect(self._refresh_extra_selections)
        self.editor.verticalScrollBar().valueChanged.connect(
            self.line_numbers.verticalScrollBar().setValue
        )
        self._refresh_line_numbers()
        self._refresh_extra_selections()

    def _refresh_line_numbers(self) -> None:
        count = max(1, self.editor.blockCount())
        self.line_numbers.setPlainText("\n".join(str(i) for i in range(1, count + 1)))
        self.line_numbers.setFixedWidth(max(42, 24 + len(str(count)) * 9))
        self.line_numbers.verticalScrollBar().setValue(
            self.editor.verticalScrollBar().value()
        )

    def _selection_for_line(self, line_number: int, background: str) -> QTextEdit.ExtraSelection | None:
        block = self.editor.document().findBlockByNumber(max(0, line_number - 1))
        if not block.isValid():
            return None
        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(block)
        selection.cursor.clearSelection()
        selection.format.setBackground(QColor(background))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        return selection

    def _refresh_extra_selections(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        current = self._selection_for_line(
            self.editor.textCursor().blockNumber() + 1, "#191c31"
        )
        if current is not None:
            selections.append(current)
        if self._error_line is not None:
            error = self._selection_for_line(self._error_line, "#452330")
            if error is not None:
                selections.append(error)
        self.editor.setExtraSelections(selections)

    def set_error_line(self, line_number: int | None, column: int = 1) -> None:
        self._error_line = int(line_number) if line_number else None
        self._refresh_extra_selections()
        if line_number:
            self.go_to_line(int(line_number), column)

    def clear_error_line(self) -> None:
        if self._error_line is not None:
            self._error_line = None
            self._refresh_extra_selections()

    def setPlainText(self, text: str) -> None:
        self.editor.setPlainText(str(text or ""))

    def toPlainText(self) -> str:
        return self.editor.toPlainText()

    def clear(self) -> None:
        self.editor.clear()

    def setPlaceholderText(self, text: str) -> None:
        self.editor.setPlaceholderText(text)

    def setReadOnly(self, read_only: bool) -> None:
        self.editor.setReadOnly(read_only)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.editor.setEnabled(enabled)
        self.line_numbers.setEnabled(enabled)

    def setFocus(self, reason=Qt.FocusReason.OtherFocusReason) -> None:
        self.editor.setFocus(reason)

    def blockSignals(self, block: bool) -> bool:
        previous = self.editor.blockSignals(block)
        super().blockSignals(block)
        return previous

    def navigate_to_error(self, message: str) -> bool:
        match = re.search(r"(?:line|LINE)\s+(\d+)(?::(\d+))?", str(message or ""))
        if not match:
            match = re.search(r"LINE\s+(\d+):", str(message or ""), re.IGNORECASE)
        if not match:
            return False
        line = int(match.group(1))
        column = int(match.group(2) or 1) if match.lastindex and match.lastindex >= 2 else 1
        self.set_error_line(line, column)
        return True

    def go_to_line(self, line_number: int, column: int = 1) -> None:
        block = self.editor.document().findBlockByNumber(max(0, line_number - 1))
        if not block.isValid():
            return
        cursor = self.editor.textCursor()
        cursor.setPosition(block.position() + max(0, column - 1))
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        self.editor.setFocus()
        self._refresh_extra_selections()


class CourseTable(QTableWidget):
    """Read-only polished data table with calm separators and zebra rows."""

    def __init__(
        self,
        headers: Iterable[str],
        rows: Iterable[Iterable[str]],
        alignments: Iterable[str] | None = None,
        parent: QWidget | None = None,
    ):
        headers = list(headers)
        rows = [list(row) for row in rows]
        super().__init__(len(rows), len(headers), parent)
        self.setHorizontalHeaderLabels(headers)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setMinimumSectionSize(60)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            "QTableWidget {background:#121927;alternate-background-color:#182235;"
            "color:#edf1f8;border:1px solid #303a51;border-radius:9px;}"
            "QTableWidget::item {padding:7px 10px;border-bottom:1px solid #253047;}"
            "QHeaderView::section {background:#1d293c;color:#dbe4f4;padding:8px 10px;"
            "border:none;border-bottom:2px solid #7f5ae8;font-weight:650;}"
        )
        alignments = list(alignments or ["left"] * len(headers))
        for row_index, row in enumerate(rows):
            for column_index in range(len(headers)):
                value = row[column_index] if column_index < len(row) else ""
                item = QTableWidgetItem(value)
                alignment = alignments[column_index] if column_index < len(alignments) else "left"
                if alignment == "right":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif alignment == "center":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.setItem(row_index, column_index, item)
        self.resizeRowsToContents()
        header_height = self.horizontalHeader().height() or 30
        rows_height = sum(self.rowHeight(row) for row in range(self.rowCount()))
        self.setMinimumHeight(min(header_height + rows_height + 6, 320))
        self.setMaximumHeight(min(header_height + rows_height + 8, 420))


class CourseCallout(QFrame):
    """Soft course callout used for goals, tasks, key ideas, and checkpoints."""

    STYLES = {
        "goal": ("◎", "#7656dd", "#181c31", "#3d3f6a"),
        "task": ("✓", "#7656dd", "#181c31", "#3d3f6a"),
        "idea": ("♧", "#9d76ff", "#191b31", "#5f4f8d"),
        "note": ("i", "#6d7d9b", "#171e2d", "#354158"),
        "warning": ("!", "#d7a55a", "#272116", "#6f5931"),
    }

    def __init__(
        self,
        title: str,
        body: str,
        *,
        kind: str = "note",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        icon, accent, background, border = self.STYLES.get(kind, self.STYLES["note"])
        self.setObjectName("CourseCallout")
        self.setStyleSheet(
            f"QFrame#CourseCallout {{background:{background};border:1px solid {border};"
            "border-radius:10px;}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        icon_label.setFixedWidth(24)
        icon_label.setStyleSheet(f"color:{accent};font-size:17pt;font-weight:700;")
        layout.addWidget(icon_label)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color:{accent};font-weight:700;font-size:10.5pt;")
        content_layout.addWidget(title_label)
        body_label = QLabel(rich_text(body))
        body_label.setTextFormat(Qt.TextFormat.RichText)
        body_label.setWordWrap(True)
        body_label.setOpenExternalLinks(True)
        body_label.setStyleSheet("color:#d9e0ec;font-size:10pt;")
        content_layout.addWidget(body_label)
        layout.addLayout(content_layout, 1)


@dataclass
class MarkdownBlock:
    kind: str
    value: object
    extra: object | None = None


class CourseMarkdownParser:
    """Parse the constrained Markdown used by generated course packs."""

    TABLE_DIVIDER = re.compile(r"^\s*:?-{3,}:?\s*$")
    ORDERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
    UNORDERED = re.compile(r"^\s*[-*+]\s+(.*)$")

    @staticmethod
    def split_table_row(line: str) -> list[str]:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [cell.strip() for cell in line.split("|")]

    def parse(self, markdown: str) -> list[MarkdownBlock]:
        lines = markdown.replace("\r\n", "\n").split("\n")
        blocks: list[MarkdownBlock] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if not stripped:
                index += 1
                continue
            if stripped == ":::columns":
                index += 1
                column_lines: list[list[str]] = []
                current_column: list[str] | None = None
                while index < len(lines) and lines[index].strip() != ":::":
                    if lines[index].strip() == ":::column":
                        if current_column is not None:
                            column_lines.append(current_column)
                        current_column = []
                    else:
                        if current_column is None:
                            current_column = []
                        current_column.append(lines[index])
                    index += 1
                if current_column is not None:
                    column_lines.append(current_column)
                if index < len(lines) and lines[index].strip() == ":::":
                    index += 1
                parsed_columns = [
                    self.parse("\n".join(column))
                    for column in column_lines
                    if any(line.strip() for line in column)
                ]
                if parsed_columns:
                    blocks.append(MarkdownBlock("columns", parsed_columns))
                continue
            if stripped.startswith("```"):
                language = stripped[3:].strip() or "text"
                code_lines: list[str] = []
                index += 1
                while index < len(lines) and not lines[index].strip().startswith("```"):
                    code_lines.append(lines[index])
                    index += 1
                index += 1
                blocks.append(MarkdownBlock("code", "\n".join(code_lines), language))
                continue
            if stripped == "---":
                blocks.append(MarkdownBlock("rule", ""))
                index += 1
                continue
            heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
            if heading:
                blocks.append(MarkdownBlock(f"h{len(heading.group(1))}", heading.group(2)))
                index += 1
                continue
            if stripped.startswith(">"):
                quote_lines: list[str] = []
                while index < len(lines) and lines[index].strip().startswith(">"):
                    quote_lines.append(lines[index].strip()[1:].strip())
                    index += 1
                blocks.append(MarkdownBlock("quote", "\n".join(quote_lines)))
                continue
            if (
                index + 1 < len(lines)
                and "|" in stripped
                and "|" in lines[index + 1]
            ):
                headers = self.split_table_row(stripped)
                dividers = self.split_table_row(lines[index + 1])
                if len(headers) == len(dividers) and all(
                    self.TABLE_DIVIDER.match(cell) for cell in dividers
                ):
                    alignments: list[str] = []
                    for cell in dividers:
                        cell = cell.strip()
                        if cell.startswith(":") and cell.endswith(":"):
                            alignments.append("center")
                        elif cell.endswith(":"):
                            alignments.append("right")
                        else:
                            alignments.append("left")
                    index += 2
                    rows: list[list[str]] = []
                    while index < len(lines) and "|" in lines[index] and lines[index].strip():
                        rows.append(self.split_table_row(lines[index]))
                        index += 1
                    blocks.append(MarkdownBlock("table", (headers, rows), alignments))
                    continue
            ordered = self.ORDERED.match(line)
            unordered = self.UNORDERED.match(line)
            if ordered or unordered:
                list_kind = "ordered" if ordered else "unordered"
                items: list[str] = []
                pattern = self.ORDERED if ordered else self.UNORDERED
                while index < len(lines):
                    match = pattern.match(lines[index])
                    if not match:
                        break
                    items.append(match.group(1).strip())
                    index += 1
                blocks.append(MarkdownBlock("list", items, list_kind))
                continue
            paragraph = [stripped]
            index += 1
            while index < len(lines):
                next_line = lines[index]
                next_stripped = next_line.strip()
                if not next_stripped:
                    break
                if (
                    next_stripped.startswith(("#", ">", "```", ":::"))
                    or next_stripped == "---"
                    or self.ORDERED.match(next_line)
                    or self.UNORDERED.match(next_line)
                ):
                    break
                if index + 1 < len(lines) and "|" in next_stripped and "|" in lines[index + 1]:
                    possible = self.split_table_row(lines[index + 1])
                    if possible and all(self.TABLE_DIVIDER.match(cell) for cell in possible):
                        break
                paragraph.append(next_stripped)
                index += 1
            blocks.append(MarkdownBlock("paragraph", " ".join(paragraph)))
        return blocks


class CoursePageWidget(QWidget):
    """Native, responsive lesson page matching the approved learning reference."""

    backRequested = Signal()
    continueRequested = Signal()
    bookmarkToggled = Signal(bool)
    overflowRequested = Signal()

    RESPONSIVE_COLUMNS_BREAKPOINT = 900
    COMPACT_PAGE_BREAKPOINT = 680

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._parser = CourseMarkdownParser()
        self._bookmarked = False
        self._responsive_columns: list[QBoxLayout] = []
        self._responsive_mode: str | None = None
        self._title_label: QLabel | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # Persistent extension points let feature pages place native controls
        # in the reference-style header, lesson body, and navigation footer.
        # They are detached before the Markdown body is rebuilt so Qt never
        # deletes caller-owned controls during a lesson refresh.
        self.header_actions_host = QWidget(self)
        self.header_actions_layout = QHBoxLayout(self.header_actions_host)
        self.header_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.header_actions_layout.setSpacing(7)
        self.header_actions_host.hide()

        self.embedded_host = QWidget(self)
        self.embedded_layout = QVBoxLayout(self.embedded_host)
        self.embedded_layout.setContentsMargins(0, 4, 0, 0)
        self.embedded_layout.setSpacing(10)
        self.embedded_host.hide()

        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(0)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        self.page = QWidget()
        self.page.setObjectName("NativeCoursePage")
        self.page.setMinimumWidth(0)
        self.page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.page.setStyleSheet("QWidget#NativeCoursePage {background:transparent;}")
        self.page_layout = QVBoxLayout(self.page)
        self.page_layout.setContentsMargins(22, 20, 22, 22)
        self.page_layout.setSpacing(12)
        self.scroll.setWidget(self.page)
        outer.addWidget(self.scroll, 1)

        self.navigation = QFrame()
        self.navigation.setObjectName("CourseNavigationFooter")
        self.navigation.setStyleSheet(
            "QFrame#CourseNavigationFooter {background:#121a2a;border:1px solid #2d3850;"
            "border-radius:10px;}"
        )
        navigation_layout = QHBoxLayout(self.navigation)
        navigation_layout.setContentsMargins(14, 10, 14, 10)
        self.back_button = QPushButton("←  Back to Pack")
        self.back_button.setObjectName("Secondary")
        self.back_button.clicked.connect(lambda: self.backRequested.emit())
        navigation_layout.addWidget(self.back_button)
        self.footer_actions_host = QWidget()
        self.footer_actions_layout = QHBoxLayout(self.footer_actions_host)
        self.footer_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.footer_actions_layout.setSpacing(7)
        self.footer_actions_host.hide()
        navigation_layout.addWidget(self.footer_actions_host)
        navigation_layout.addStretch()
        next_layout = QVBoxLayout()
        next_layout.setContentsMargins(0, 0, 6, 0)
        next_layout.setSpacing(1)
        next_caption = QLabel("Next")
        next_caption.setStyleSheet("color:#8f9ab0;font-size:8.5pt;")
        self.next_title = QLabel("Continue")
        self.next_title.setStyleSheet("color:#f3f5fb;font-size:10.5pt;font-weight:650;")
        next_layout.addWidget(next_caption, 0, Qt.AlignmentFlag.AlignRight)
        next_layout.addWidget(self.next_title, 0, Qt.AlignmentFlag.AlignRight)
        navigation_layout.addLayout(next_layout)
        self.continue_button = QPushButton("Continue  →")
        self.continue_button.setObjectName("Primary")
        self.continue_button.clicked.connect(lambda: self.continueRequested.emit())
        navigation_layout.addWidget(self.continue_button)
        outer.addWidget(self.navigation)
        self.navigation.hide()

    def set_navigation(
        self,
        *,
        next_title: str | None,
        show_back: bool = True,
        continue_text: str = "Continue  →",
    ) -> None:
        self.back_button.setVisible(show_back)
        self.next_title.setText(next_title or "Complete")
        self.continue_button.setText(continue_text)
        self.continue_button.setVisible(bool(next_title))
        self.navigation.setVisible(
            show_back or bool(next_title) or not self.footer_actions_host.isHidden()
        )

    def set_header_controls(self, *widgets: QWidget) -> None:
        """Place caller-owned controls before the bookmark button."""
        while self.header_actions_layout.count():
            item = self.header_actions_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        for widget in widgets:
            self.header_actions_layout.addWidget(widget)
        self.header_actions_host.setVisible(bool(widgets))

    def set_footer_controls(self, *widgets: QWidget) -> None:
        """Place workflow actions on the left side of the navigation card."""
        while self.footer_actions_layout.count():
            item = self.footer_actions_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        for widget in widgets:
            self.footer_actions_layout.addWidget(widget)
        self.footer_actions_host.setVisible(bool(widgets))

    def set_embedded_widget(self, widget: QWidget | None) -> None:
        """Embed a native interactive workspace below the course material."""
        while self.embedded_layout.count():
            item = self.embedded_layout.takeAt(0)
            previous = item.widget()
            if previous is not None:
                previous.setParent(None)
        if widget is None:
            self.embedded_host.hide()
            return
        self.embedded_layout.addWidget(widget)
        self.embedded_host.show()

    def set_bookmarked(self, bookmarked: bool) -> None:
        self._bookmarked = bool(bookmarked)
        if hasattr(self, "bookmark_button"):
            self.bookmark_button.setText("◆" if self._bookmarked else "◇")
            self.bookmark_button.setToolTip(
                "Remove bookmark" if self._bookmarked else "Bookmark this page"
            )

    def _toggle_bookmark(self) -> None:
        self.set_bookmarked(not self._bookmarked)
        self.bookmarkToggled.emit(self._bookmarked)

    def clear(self) -> None:
        self.header_actions_host.setParent(self)
        self.embedded_host.setParent(self)
        clear_layout(self.page_layout)
        self.navigation.hide()

    def _add_title(self, title: str, eyebrow: str, subtitle: str | None) -> None:
        top = QHBoxLayout()
        title_column = QVBoxLayout()
        title_column.setContentsMargins(0, 0, 0, 0)
        title_column.setSpacing(9)
        pill = QLabel(eyebrow.upper())
        pill.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        pill.setStyleSheet(
            "background:#7652d6;color:white;border-radius:10px;padding:4px 10px;"
            "font-size:8.5pt;font-weight:700;"
        )
        title_column.addWidget(pill, 0, Qt.AlignmentFlag.AlignLeft)
        title_label = QLabel(title)
        self._title_label = title_label
        title_label.setWordWrap(True)
        title_label.setMinimumWidth(0)
        title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        title_label.setStyleSheet("color:#f7f8fc;font-size:24pt;font-weight:700;")
        title_column.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setWordWrap(True)
            subtitle_label.setMinimumWidth(0)
            subtitle_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            subtitle_label.setStyleSheet(
                "color:#bec7d7;background:#141c2b;border:1px solid #344159;"
                "border-radius:12px;padding:4px 10px;font-size:9.5pt;"
            )
            title_column.addWidget(subtitle_label, 0, Qt.AlignmentFlag.AlignLeft)
        top.addLayout(title_column, 1)
        action_row = QHBoxLayout()
        action_row.setSpacing(7)
        # isVisible() is false while the parent tab is hidden, even when the
        # host was intentionally enabled. isHidden() reflects the explicit
        # state and prevents header controls from becoming unlaid-out floaters.
        if not self.header_actions_host.isHidden():
            action_row.addWidget(self.header_actions_host)
        self.bookmark_button = QPushButton("◆" if self._bookmarked else "◇")
        self.bookmark_button.setObjectName("Secondary")
        self.bookmark_button.setFixedSize(38, 38)
        self.bookmark_button.setToolTip("Bookmark this page")
        self.bookmark_button.clicked.connect(self._toggle_bookmark)
        action_row.addWidget(self.bookmark_button)
        overflow = QPushButton("⋮")
        overflow.setObjectName("Secondary")
        overflow.setFixedSize(38, 38)
        overflow.setToolTip("More page actions")
        overflow.clicked.connect(lambda: self.overflowRequested.emit())
        action_row.addWidget(overflow)
        top.addLayout(action_row)
        self.page_layout.addLayout(top)
        self.page_layout.addWidget(horizontal_rule())

    def _add_section_title(self, text: str, target: QVBoxLayout | None = None) -> None:
        target = target or self.page_layout
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 7, 0, 0)
        layout.setSpacing(6)
        label = QLabel(rich_text(text))
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setStyleSheet("color:#f4f6fb;font-size:12pt;font-weight:700;")
        layout.addWidget(label)
        layout.addWidget(horizontal_rule())
        target.addWidget(container)

    def _add_subheader(self, text: str, target: QVBoxLayout | None = None) -> None:
        target = target or self.page_layout
        label = QLabel(rich_text(text))
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        label.setStyleSheet(
            "color:#bda8ff;background:#151c2c;border:1px solid #4b3f76;"
            "border-radius:7px;padding:5px 9px;font-size:9.5pt;font-weight:650;"
        )
        target.addWidget(label, 0, Qt.AlignmentFlag.AlignLeft)

    def _add_paragraph(self, text: str, target: QVBoxLayout | None = None) -> None:
        target = target or self.page_layout
        label = QLabel(rich_text(text))
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        label.setMinimumWidth(0)
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setStyleSheet("color:#d5dceb;font-size:10pt;")
        target.addWidget(label)

    def _add_list(
        self,
        items: list[str],
        ordered: bool,
        target: QVBoxLayout | None = None,
    ) -> None:
        target = target or self.page_layout
        frame = QFrame()
        frame.setStyleSheet("QFrame {background:transparent;border:none;}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 0, 0, 4)
        layout.setSpacing(7)
        for index, item in enumerate(items, start=1):
            row = QHBoxLayout()
            marker = QLabel(str(index) if ordered else "•")
            marker.setFixedWidth(24)
            marker.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            marker.setStyleSheet(
                "color:#a987ff;font-size:10pt;font-weight:700;"
                + (
                    "background:#2b2350;border-radius:9px;padding:1px;"
                    if ordered
                    else ""
                )
            )
            row.addWidget(marker)
            body = QLabel(rich_text(item))
            body.setTextFormat(Qt.TextFormat.RichText)
            body.setWordWrap(True)
            body.setStyleSheet("color:#d6ddea;font-size:10pt;")
            row.addWidget(body, 1)
            layout.addLayout(row)
        target.addWidget(frame)

    @staticmethod
    def _quote_parts(value: str) -> tuple[str, str, str]:
        match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", value)
        if not match:
            return "Key idea", value, "idea"
        raw_title = match.group(1).strip()
        body = match.group(2).strip()
        lowered = raw_title.lower()
        if "learning goal" in lowered or "objective" in lowered:
            kind = "goal"
        elif "task" in lowered or "checkpoint" in lowered:
            kind = "task"
        elif "warning" in lowered or "do not" in lowered:
            kind = "warning"
        elif "read first" in lowered or "note" in lowered:
            kind = "note"
        else:
            kind = "idea"
        return raw_title, body, kind

    def _render_blocks(
        self,
        blocks: list[MarkdownBlock],
        target: QVBoxLayout,
    ) -> None:
        for block in blocks:
            if block.kind in {"h1", "h2"}:
                self._add_section_title(str(block.value), target)
            elif block.kind == "h3":
                self._add_subheader(str(block.value), target)
            elif block.kind == "paragraph":
                self._add_paragraph(str(block.value), target)
            elif block.kind == "quote":
                title_text, body, kind = self._quote_parts(str(block.value))
                target.addWidget(CourseCallout(title_text, body, kind=kind))
            elif block.kind == "code":
                target.addWidget(CodeCard(str(block.value), str(block.extra or "text")))
            elif block.kind == "table":
                headers, rows = block.value  # type: ignore[misc]
                clean_headers = [re.sub(r"[`*]", "", item) for item in headers]
                clean_rows = [
                    [re.sub(r"[`*]", "", item) for item in row]
                    for row in rows
                ]
                target.addWidget(CourseTable(clean_headers, clean_rows, block.extra or []))
            elif block.kind == "list":
                self._add_list(list(block.value), block.extra == "ordered", target)
            elif block.kind == "rule":
                target.addWidget(horizontal_rule())
            elif block.kind == "columns":
                row_widget = QWidget()
                row_widget.setMinimumWidth(0)
                row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                row_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(14)
                self._responsive_columns.append(row_layout)
                for column_blocks in block.value:  # type: ignore[union-attr]
                    column = QFrame()
                    column.setMinimumWidth(0)
                    column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                    column.setStyleSheet("QFrame {background:transparent;border:none;}")
                    column_layout = QVBoxLayout(column)
                    column_layout.setContentsMargins(0, 0, 0, 0)
                    column_layout.setSpacing(10)
                    self._render_blocks(list(column_blocks), column_layout)
                    column_layout.addStretch(1)
                    row_layout.addWidget(column, 1)
                target.addWidget(row_widget)

    def _refresh_responsive_layout(self) -> None:
        if not hasattr(self, "scroll") or not hasattr(self, "page_layout"):
            return
        width = max(self.scroll.viewport().width(), 0)
        mode = (
            "compact"
            if width < self.COMPACT_PAGE_BREAKPOINT
            else (
                "stacked"
                if width < self.RESPONSIVE_COLUMNS_BREAKPOINT
                else "wide"
            )
        )
        if mode == self._responsive_mode and self._responsive_columns:
            return
        self._responsive_mode = mode
        stack_columns = mode != "wide"
        direction = (
            QBoxLayout.Direction.TopToBottom
            if stack_columns
            else QBoxLayout.Direction.LeftToRight
        )
        for layout in self._responsive_columns:
            layout.setDirection(direction)
            layout.setSpacing(10 if stack_columns else 14)

        if mode == "compact":
            self.page_layout.setContentsMargins(12, 14, 12, 16)
            self.page_layout.setSpacing(10)
            title_size = 17
        elif mode == "stacked":
            self.page_layout.setContentsMargins(16, 17, 16, 18)
            self.page_layout.setSpacing(11)
            title_size = 19
        else:
            self.page_layout.setContentsMargins(22, 20, 22, 22)
            self.page_layout.setSpacing(12)
            title_size = 24
        if self._title_label is not None:
            self._title_label.setStyleSheet(
                f"color:#f7f8fc;font-size:{title_size}pt;font-weight:700;"
            )
        self.page.updateGeometry()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._refresh_responsive_layout()

    def set_markdown(
        self,
        markdown: str,
        *,
        eyebrow: str,
        subtitle: str | None = None,
        bookmarked: bool = False,
    ) -> None:
        self._bookmarked = bool(bookmarked)
        self.header_actions_host.setParent(self)
        self.embedded_host.setParent(self)
        self._responsive_columns = []
        self._responsive_mode = None
        clear_layout(self.page_layout)
        blocks = self._parser.parse(markdown)
        title = "Course material"
        if blocks and blocks[0].kind == "h1":
            title = str(blocks.pop(0).value)
        self._add_title(title, eyebrow, subtitle)
        self._render_blocks(blocks, self.page_layout)
        if self.embedded_host.isVisible():
            self.page_layout.addWidget(self.embedded_host)
        self.page_layout.addStretch(1)
        self.scroll.verticalScrollBar().setValue(0)
        self.set_bookmarked(bookmarked)
        QTimer.singleShot(0, self._refresh_responsive_layout)
