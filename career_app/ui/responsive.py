from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


_STYLE_NUMBER = re.compile(r"(?P<number>\d+(?:\.\d+)?)(?P<unit>pt|px)")


def scaled_stylesheet(source: str, scale: float) -> str:
    """Scale point/pixel values in an inline Qt stylesheet without compounding."""
    scale = max(0.72, min(1.18, float(scale)))

    def repl(match: re.Match[str]) -> str:
        number = float(match.group("number"))
        unit = match.group("unit")
        # Borders must remain visible and tiny radii should not collapse.
        minimum = 1.0 if unit == "px" else 6.5
        value = max(minimum, number * scale)
        if abs(value - round(value)) < 0.05:
            rendered = str(int(round(value)))
        else:
            rendered = f"{value:.1f}".rstrip("0").rstrip(".")
        return f"{rendered}{unit}"

    return _STYLE_NUMBER.sub(repl, source or "")


def apply_inline_style_scale(root: QWidget, scale: float) -> None:
    """Scale child inline styles while preserving later dynamic style changes."""
    widgets: list[QWidget] = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        current = widget.styleSheet()
        if not current:
            continue
        rendered = widget.property("responsive_rendered_stylesheet")
        base = widget.property("responsive_base_stylesheet")
        if base is None or current != rendered:
            base = current
            widget.setProperty("responsive_base_stylesheet", base)
        updated = scaled_stylesheet(str(base), scale)
        if current != updated:
            widget.setStyleSheet(updated)
        widget.setProperty("responsive_rendered_stylesheet", updated)


def clear_layout_positions(layout: QLayout) -> None:
    """Remove layout items without deleting their widgets or stale grid sizing."""
    if isinstance(layout, QGridLayout):
        for column in range(max(layout.columnCount(), 8)):
            layout.setColumnStretch(column, 0)
            layout.setColumnMinimumWidth(column, 0)
        for row in range(max(layout.rowCount(), 8)):
            layout.setRowStretch(row, 0)
            layout.setRowMinimumHeight(row, 0)
    while layout.count():
        layout.takeAt(0)


def set_box_direction(layout: QBoxLayout, vertical: bool, spacing: int | None = None) -> None:
    layout.setDirection(
        QBoxLayout.Direction.TopToBottom
        if vertical
        else QBoxLayout.Direction.LeftToRight
    )
    if spacing is not None:
        layout.setSpacing(spacing)


def reflow_grid(
    layout: QGridLayout,
    widgets: Iterable[QWidget],
    columns: int,
    *,
    column_stretch: int = 1,
) -> None:
    """Place widgets into a simple responsive grid."""
    previous_columns = max(layout.columnCount(), 1)
    clear_layout_positions(layout)
    columns = max(1, int(columns))
    items = list(widgets)
    for index, widget in enumerate(items):
        row, column = divmod(index, columns)
        layout.addWidget(widget, row, column)
    # QGridLayout keeps stretch factors for columns that no longer contain
    # widgets. Clear those stale factors first or a one-column compact layout
    # can remain visually constrained to half of the available width.
    for column in range(max(previous_columns, columns, 8)):
        layout.setColumnStretch(column, 0)
    for column in range(columns):
        layout.setColumnStretch(column, column_stretch)


class ResponsiveScrollPage(QScrollArea):
    """Scroll-safe page shell with a header that reflows at narrow widths."""

    widthChanged = Signal(int)
    heightChanged = Signal(int)

    def __init__(
        self,
        title: str | None = None,
        subtitle: str | None = None,
        date_text: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.content = QWidget()
        self.content.setMinimumWidth(0)
        self.content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(22, 18, 22, 18)
        self.content_layout.setSpacing(12)
        self.setWidget(self.content)

        self.header: QWidget | None = None
        self.header_layout: QGridLayout | None = None
        self.header_text: QWidget | None = None
        self.title_label: QLabel | None = None
        self.subtitle_label: QLabel | None = None
        self.date_label: QLabel | None = None
        self._responsive_handlers: list[Callable[[int], None]] = []
        self._mode: str | None = None

        if title:
            self._build_header(title, subtitle, date_text)

    def _build_header(
        self,
        title: str,
        subtitle: str | None,
        date_text: str | None,
    ) -> None:
        self.header = QWidget()
        self.header.setMinimumWidth(0)
        self.header_layout = QGridLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setHorizontalSpacing(12)
        self.header_layout.setVerticalSpacing(5)

        self.header_text = QWidget()
        self.header_text.setMinimumWidth(0)
        text_layout = QVBoxLayout(self.header_text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("Hero")
        self.title_label.setWordWrap(True)
        self.title_label.setMinimumWidth(0)
        self.title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        text_layout.addWidget(self.title_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("Muted")
            self.subtitle_label.setWordWrap(True)
            self.subtitle_label.setMinimumWidth(0)
            self.subtitle_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred,
            )
            text_layout.addWidget(self.subtitle_label)

        self.header_layout.addWidget(self.header_text, 0, 0)
        if date_text:
            self.date_label = QLabel(date_text)
            self.date_label.setObjectName("Muted")
            self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            # Dates are compact metadata and should never split across lines.
            # At narrow widths the whole label moves below the title instead.
            self.date_label.setWordWrap(False)
            self.date_label.setSizePolicy(
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Fixed,
            )
            self.date_label.setMinimumWidth(self.date_label.sizeHint().width())
            self.header_layout.addWidget(self.date_label, 0, 1)
        self.header_layout.setColumnStretch(0, 1)
        self.content_layout.addWidget(self.header)

    def add_responsive_handler(self, handler: Callable[[int], None]) -> None:
        self._responsive_handlers.append(handler)
        width = max(0, self.viewport().width())
        if width:
            handler(width)

    def _apply_shell_mode(self, width: int) -> None:
        mode = "compact" if width < 700 else "medium" if width < 1040 else "wide"
        if mode == self._mode:
            return
        self._mode = mode

        if mode == "compact":
            margins = (12, 12, 12, 14)
            spacing = 9
        elif mode == "medium":
            margins = (17, 15, 17, 17)
            spacing = 11
        else:
            margins = (22, 18, 22, 18)
            spacing = 12
        self.content_layout.setContentsMargins(*margins)
        self.content_layout.setSpacing(spacing)

        if self.header_layout is not None and self.header_text is not None:
            clear_layout_positions(self.header_layout)
            if mode == "compact" and self.date_label is not None:
                self.header_layout.addWidget(self.header_text, 0, 0)
                self.header_layout.addWidget(self.date_label, 1, 0)
                self.date_label.setAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                )
                self.header_layout.setColumnStretch(0, 1)
            else:
                self.header_layout.addWidget(self.header_text, 0, 0)
                if self.date_label is not None:
                    self.header_layout.addWidget(self.date_label, 0, 1)
                    self.date_label.setAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
                    )
                self.header_layout.setColumnStretch(0, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        width = max(0, self.viewport().width())
        height = max(0, self.viewport().height())
        self._apply_shell_mode(width)
        for handler in tuple(self._responsive_handlers):
            handler(width)
        self.widthChanged.emit(width)
        self.heightChanged.emit(height)


class ResponsiveBox(QWidget):
    """Small host that can switch its child layout between rows and columns."""

    def __init__(self, vertical: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QBoxLayout(
            QBoxLayout.Direction.TopToBottom
            if vertical
            else QBoxLayout.Direction.LeftToRight,
            self,
        )
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

    def set_vertical(self, vertical: bool) -> None:
        set_box_direction(self.layout, vertical)
