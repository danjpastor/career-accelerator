from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QAbstractSpinBox,
    QBoxLayout,
    QComboBox,
    QFrame,
    QHeaderView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QScrollArea,
    QSizePolicy,
    QTableView,
    QTableWidget,
    QTextEdit,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)


_STYLE_NUMBER = re.compile(r"(?P<number>\d+(?:\.\d+)?)(?P<unit>pt|px)")
_STYLE_BLOCK = re.compile(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}", re.S)
_STYLE_DECLARATION = re.compile(
    r"(?P<property>[A-Za-z-]+)(?P<separator>\s*:\s*)(?P<value>[^;{}]+)(?P<semicolon>;)",
    re.S,
)
_CONTROL_SIZE_PROPERTIES = {
    "padding",
    "padding-top",
    "padding-right",
    "padding-bottom",
    "padding-left",
    "min-height",
    "max-height",
}
_CONTROL_SELECTORS = (
    "QPushButton",
    "QComboBox",
    "QLineEdit",
    "QTextEdit",
    "QSpinBox",
    "QAbstractItemView",
    "QListWidget",
    "QTableWidget",
    "QTableView",
    "QTreeWidget",
    "QTreeView",
    "QHeaderView",
)


def _scaled_style_value(value: str, factor: float) -> str:
    def repl(match: re.Match[str]) -> str:
        number = float(match.group("number"))
        unit = match.group("unit")
        # Borders must remain visible and tiny radii should not collapse.
        minimum = 1.0 if unit == "px" else 6.5
        rendered_value = max(minimum, number * factor)
        if abs(rendered_value - round(rendered_value)) < 0.05:
            rendered = str(int(round(rendered_value)))
        else:
            rendered = f"{rendered_value:.1f}".rstrip("0").rstrip(".")
        return f"{rendered}{unit}"

    return _STYLE_NUMBER.sub(repl, value)


def _scaled_declarations(
    body: str,
    layout_scale: float,
    content_scale: float,
    *,
    control: bool,
) -> str:
    def replace_declaration(match: re.Match[str]) -> str:
        property_name = match.group("property").casefold()
        factor = layout_scale
        if property_name == "font-size":
            factor *= content_scale
        elif control and property_name in _CONTROL_SIZE_PROPERTIES:
            factor *= content_scale
        value = _scaled_style_value(match.group("value"), factor)
        return (
            f"{match.group('property')}{match.group('separator')}"
            f"{value}{match.group('semicolon')}"
        )

    return _STYLE_DECLARATION.sub(replace_declaration, body)


def scaled_stylesheet(
    source: str,
    scale: float,
    content_scale: float = 1.0,
    *,
    control: bool = False,
) -> str:
    """Scale layout geometry and readable content independently.

    ``scale`` continues to follow the responsive window size. ``content_scale``
    affects fonts and control padding/heights only, so cards and page geometry
    remain governed by the existing responsive layout calculations.
    """
    layout_scale = max(0.72, min(1.18, float(scale)))
    content_scale = max(0.80, min(1.20, float(content_scale)))
    source = source or ""

    if "{" not in source:
        return _scaled_declarations(
            source,
            layout_scale,
            content_scale,
            control=control,
        )

    def replace_block(match: re.Match[str]) -> str:
        selectors = match.group("selectors")
        is_control = any(token in selectors for token in _CONTROL_SELECTORS)
        body = _scaled_declarations(
            match.group("body"),
            layout_scale,
            content_scale,
            control=is_control,
        )
        return f"{selectors}{{{body}}}"

    return _STYLE_BLOCK.sub(replace_block, source)


def apply_inline_style_scale(
    root: QWidget,
    scale: float,
    content_scale: float = 1.0,
) -> None:
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
        is_control = isinstance(
            widget,
            (
                QAbstractButton,
                QAbstractItemView,
                QAbstractSpinBox,
                QComboBox,
                QLineEdit,
                QTextEdit,
            ),
        )
        updated = scaled_stylesheet(
            str(base),
            scale,
            content_scale,
            control=is_control,
        )
        if current != updated:
            widget.setStyleSheet(updated)
        widget.setProperty("responsive_rendered_stylesheet", updated)



def _metric_base(widget: QWidget, name: str, current: int) -> tuple[int, int | None]:
    """Return the unscaled baseline and the last height applied by this module."""
    base_name = f"_responsive_{name}_base"
    last_name = f"_responsive_{name}_last"
    base = getattr(widget, base_name, None)
    last = getattr(widget, last_name, None)
    if base is None or last is None or int(current) != int(last):
        base = int(current)
        setattr(widget, base_name, base)
    return int(base), None if last is None else int(last)


def _set_content_minimum_height(widget: QWidget, required: int) -> None:
    """Raise a widget's row height without permanently losing its base size."""
    required = max(0, int(required))
    current_minimum = int(widget.minimumHeight())
    base_minimum, _ = _metric_base(widget, "minimum_height", current_minimum)
    target_minimum = max(base_minimum, required)
    widget.setMinimumHeight(target_minimum)
    setattr(widget, "_responsive_minimum_height_last", target_minimum)

    current_maximum = int(widget.maximumHeight())
    if current_maximum < 16777215:
        base_maximum, _ = _metric_base(widget, "maximum_height", current_maximum)
        target_maximum = max(base_maximum, target_minimum)
        widget.setMaximumHeight(target_maximum)
        setattr(widget, "_responsive_maximum_height_last", target_maximum)


def _scale_list_widget_rows(view: QListWidget, required: int) -> None:
    """Keep QListWidget rows tall enough for the active font scale."""
    state = getattr(view, "_responsive_list_row_state", {})
    next_state: dict[int, tuple[int, int]] = {}
    for row in range(view.count()):
        item = view.item(row)
        key = id(item)
        current = item.sizeHint().height()
        base, last = state.get(key, (current, None))
        if last is None or current != last:
            base = current
        target = max(int(base), int(required))
        size = item.sizeHint()
        item.setSizeHint(QSize(size.width(), target))
        next_state[key] = (int(base), target)
    view._responsive_list_row_state = next_state


def _scale_tree_widget_rows(view: QTreeWidget, required: int) -> None:
    """Keep every visible learning/task tree row readable at larger scales."""
    state = getattr(view, "_responsive_tree_row_state", {})
    next_state: dict[int, tuple[int, int]] = {}
    iterator = QTreeWidgetItemIterator(view)
    while iterator.value() is not None:
        item = iterator.value()
        key = id(item)
        current = item.sizeHint(0).height()
        base, last = state.get(key, (current, None))
        if last is None or current != last:
            base = current
        target = max(int(base), int(required))
        for column in range(max(1, view.columnCount())):
            size = item.sizeHint(column)
            item.setSizeHint(column, QSize(size.width(), target))
        next_state[key] = (int(base), target)
        iterator += 1
    view._responsive_tree_row_state = next_state


def apply_content_row_metrics(
    root: QWidget,
    layout_scale: float,
    content_scale: float = 1.0,
) -> None:
    """Scale text-bearing rows and controls without resizing their cards.

    Qt stylesheets scale fonts and padding, but explicit row heights and item
    view section sizes can remain at their original values.  This pass derives
    safe heights from the live font metrics after styling, then adjusts only
    controls and rows.  Card/page geometry remains owned by the responsive
    layout code.
    """
    layout_scale = max(0.72, min(1.18, float(layout_scale)))
    content_scale = max(0.80, min(1.20, float(content_scale)))
    widgets: list[QWidget] = [root, *root.findChildren(QWidget)]

    for widget in widgets:
        font_height = max(1, widget.fontMetrics().height())
        if isinstance(widget, QComboBox):
            _set_content_minimum_height(
                widget,
                font_height + round(16 * layout_scale * content_scale),
            )
        elif isinstance(widget, (QLineEdit, QAbstractSpinBox)):
            _set_content_minimum_height(
                widget,
                font_height + round(14 * layout_scale * content_scale),
            )
        elif isinstance(widget, QAbstractButton):
            compact_dashboard = bool(widget.property("dashboardAction"))
            vertical_room = 8 if compact_dashboard else 12
            _set_content_minimum_height(
                widget,
                font_height
                + round(vertical_room * layout_scale * content_scale),
            )

    row_room = round(11 * layout_scale * content_scale)
    for view in root.findChildren(QListWidget):
        required = max(20, view.fontMetrics().height() + row_room)
        _scale_list_widget_rows(view, required)

    for view in root.findChildren(QTreeWidget):
        required = max(20, view.fontMetrics().height() + row_room)
        _scale_tree_widget_rows(view, required)

    for view in root.findChildren(QTableView):
        header = view.verticalHeader()
        if not isinstance(header, QHeaderView):
            continue
        required = max(22, view.fontMetrics().height() + row_room)
        current_default = int(header.defaultSectionSize())
        base_default = getattr(header, "_responsive_default_section_base", None)
        last_default = getattr(header, "_responsive_default_section_last", None)
        if (
            base_default is None
            or last_default is None
            or current_default != int(last_default)
        ):
            base_default = current_default
            header._responsive_default_section_base = base_default
        target_default = max(int(base_default), required)
        header.setMinimumSectionSize(min(target_default, required))
        header.setDefaultSectionSize(target_default)
        header._responsive_default_section_last = target_default

        model = view.model()
        row_count = model.rowCount() if model is not None else 0
        if isinstance(view, QTableWidget) and view.wordWrap():
            view.resizeRowsToContents()
        for row in range(row_count):
            if not header.isSectionHidden(row) and header.sectionSize(row) < required:
                header.resizeSection(row, required)


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
        self._outer_scroll_enabled = True

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

    def set_outer_scroll_enabled(self, enabled: bool) -> None:
        """Choose whether the page shell itself may scroll vertically.

        Dense workspaces use a fixed outer shell and delegate overflow to the
        lists, editors, tables, and cards inside the page.  This keeps the page
        header and tab bar anchored while still allowing long card content to
        remain accessible.
        """
        enabled = bool(enabled)
        self._outer_scroll_enabled = enabled
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
            if enabled
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        if enabled:
            self.content.setMinimumHeight(0)
            self.content.setMaximumHeight(16777215)
        else:
            self._sync_fixed_content_height()
        self.content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
            if enabled
            else QSizePolicy.Policy.Ignored,
        )
        self.content.updateGeometry()

    def _sync_fixed_content_height(self) -> None:
        """Lock non-scrolling page content to the live viewport height."""
        if self._outer_scroll_enabled:
            return
        height = max(0, self.viewport().height())
        if height:
            self.content.setFixedHeight(height)

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
        self._sync_fixed_content_height()
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
