from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import (
    QEasingCurve, Property, QPropertyAnimation, QSequentialAnimationGroup,
    Qt, QRectF, QPointF, QSize, Signal
)
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QBrush,
    QLinearGradient
)
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QLabel, QHBoxLayout, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget
)

from career_app.theme import COLORS


class Card(QFrame):
    def __init__(self, title=None, subtitle=None):
        super().__init__()
        self.setObjectName("Card")
        self.setMinimumWidth(0)
        self.setMaximumHeight(16777215)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(8)

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            title_label.setWordWrap(True)
            title_label.setMinimumWidth(0)
            title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            self.layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("Muted")
            subtitle_label.setWordWrap(True)
            self.layout.addWidget(subtitle_label)


def make_card_scrollable(card: Card) -> QScrollArea:
    """Move a card's existing contents into its own vertical scroll area.

    The card keeps its normal border and rounded background while long forms or
    workspaces scroll inside the card instead of forcing the entire page to
    grow.  Calling this after the card has been populated preserves all child
    widgets and nested layouts.
    """
    if getattr(card, "_content_scroll", None) is not None:
        return card._content_scroll

    original = card.layout
    margins = original.contentsMargins()
    spacing = original.spacing()

    host = QWidget()
    host.setMinimumWidth(0)
    host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    host_layout = QVBoxLayout(host)
    host_layout.setContentsMargins(
        margins.left(), margins.top(), margins.right(), margins.bottom()
    )
    host_layout.setSpacing(spacing)

    while original.count():
        item = original.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        spacer = item.spacerItem()
        if widget is not None:
            host_layout.addWidget(widget, 0, item.alignment())
        elif child_layout is not None:
            host_layout.addLayout(child_layout)
        elif spacer is not None:
            host_layout.addItem(spacer)

    scroll = QScrollArea(card)
    scroll.setWidgetResizable(True)
    scroll.setMinimumSize(0, 0)
    scroll.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
    scroll.setWidget(host)

    original.setContentsMargins(0, 0, 0, 0)
    original.setSpacing(0)
    original.addWidget(scroll, 1)
    card.setMinimumHeight(0)
    card.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
    card._content_scroll = scroll
    card._content_host = host
    return scroll


class SoftPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("SoftPanel")


class Ring(QWidget):
    def __init__(self, title, color):
        super().__init__()
        self.title = title
        self.color = QColor(color)
        self.value = 0
        self.subtitle = ""
        self.extra = ""
        self._ui_scale = 1.0
        self._interface_scale = 1.0
        self._density = "comfortable"
        self.setMinimumWidth(0)
        self.setMinimumHeight(70)
        self.setMaximumHeight(16777215)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

    def sizeHint(self):  # noqa: N802 - Qt API
        height = {
            "comfortable": 86,
            "compact": 74,
            "ultra": 66,
        }.get(self._density, 80)
        return QSize(158, round(height * self._ui_scale))

    def set_density(self, density):
        self._density = str(density or "comfortable")
        base = {
            "comfortable": 82,
            "compact": 70,
            "ultra": 62,
        }.get(self._density, 76)
        self.setMinimumHeight(round(base * self._ui_scale))
        self.updateGeometry()
        self.update()

    def set_ui_scale(self, scale):
        self._ui_scale = max(0.76, min(1.14, float(scale)))
        self.set_density(self._density)

    def set_interface_scale(self, scale):
        self._interface_scale = max(0.80, min(1.20, float(scale)))
        self.update()

    def set_value(self, value, subtitle="", extra=""):
        self.value = max(0, min(100, float(value)))
        self.subtitle = subtitle
        self.extra = extra
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scale = self._ui_scale
        font_scale = self._ui_scale * self._interface_scale
        density_scale = {
            "comfortable": 1.0,
            "compact": 0.9,
            "ultra": 0.78,
        }.get(self._density, 1.0)
        diameter = min(
            72 * scale * density_scale,
            max(44.0, self.height() - 10.0),
            max(44.0, self.width() * 0.48),
        )
        ring_rect = QRectF(
            5,
            max(4.0, (self.height() - diameter) / 2),
            diameter,
            diameter,
        )

        painter.setPen(
            QPen(
                QColor(COLORS["border"]),
                max(5.5, 8.0 * scale * density_scale),
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawArc(ring_rect, 90 * 16, -360 * 16)

        painter.setPen(
            QPen(
                self.color,
                max(5.5, 8.0 * scale * density_scale),
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawArc(
            ring_rect,
            90 * 16,
            int(-360 * 16 * self.value / 100),
        )

        painter.setPen(QColor(COLORS["text"]))
        painter.setFont(
            QFont(
                "Segoe UI",
                max(7, round(11 * font_scale * density_scale)),
                QFont.Bold,
            )
        )
        painter.drawText(
            ring_rect,
            Qt.AlignCenter,
            f"{self.value:.0f}%",
        )

        text_left = int(ring_rect.right() + max(6, 9 * scale * density_scale))
        text_width = max(1, self.width() - text_left - 4)

        title_font = QFont(
            "Segoe UI",
            max(6, round(8.5 * font_scale * density_scale)),
            QFont.Bold,
        )
        detail_font = QFont(
            "Segoe UI",
            max(6, round(7.7 * font_scale * density_scale)),
        )
        title_metrics = painter.fontMetrics()
        painter.setFont(title_font)
        title_metrics = painter.fontMetrics()
        painter.setPen(QColor(COLORS["text"]))

        detail_line_height = QFontMetrics(detail_font).height()
        title_line_height = title_metrics.height()
        gap = 2 if self._density == "ultra" else 3
        total_text_height = title_line_height + (detail_line_height * 2) + (gap * 2)
        top = max(2, int((self.height() - total_text_height) / 2))

        painter.drawText(
            QRectF(text_left, top, text_width, title_line_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            title_metrics.elidedText(self.title, Qt.ElideRight, text_width),
        )

        painter.setPen(QColor(COLORS["muted"]))
        painter.setFont(detail_font)
        detail_metrics = painter.fontMetrics()
        subtitle_y = top + title_line_height + gap
        painter.drawText(
            QRectF(text_left, subtitle_y, text_width, detail_line_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            detail_metrics.elidedText(self.subtitle, Qt.ElideRight, text_width),
        )
        extra_y = subtitle_y + detail_line_height + gap
        painter.drawText(
            QRectF(text_left, extra_y, text_width, detail_line_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            detail_metrics.elidedText(self.extra, Qt.ElideRight, text_width),
        )


class MetricRow(QFrame):
    def __init__(self, icon, title, detail, value, accent):
        super().__init__()
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background:transparent;border:none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 7, 0, 7)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size:18pt;")
        icon_label.setFixedWidth(32)
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight:700;")

        detail_label = QLabel(detail)
        detail_label.setObjectName("Muted")
        detail_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(detail_label)
        layout.addLayout(text_layout, 1)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"font-weight:700;color:{accent};"
        )
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_label.setFixedWidth(58)
        layout.addWidget(value_label)


class CircularTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.text = "00:00:00"
        self.caption = "Ready to focus • 0 / 60 min"
        self.progress = 0.0
        self._content_scale = 1.0
        self._interface_scale = 1.0
        self._ui_scale = 1.0
        self._dashboard_base_size = 138
        self._pulse_group = None
        self.setFixedSize(138, 138)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_ui_scale(self, scale):
        self._ui_scale = max(0.78, min(1.12, float(scale)))
        size = round(self._dashboard_base_size * self._ui_scale)
        self.setFixedSize(size, size)
        self.updateGeometry()
        self.update()

    def set_interface_scale(self, scale):
        self._interface_scale = max(0.80, min(1.20, float(scale)))
        self.update()

    def set_dashboard_density(self, density):
        self._dashboard_base_size = {
            "comfortable": 138,
            "compact": 98,
            "ultra": 82,
        }.get(str(density or "comfortable"), 118)
        self.set_ui_scale(self._ui_scale)

    def set_display(self, text, caption, progress):
        self.text = text
        self.caption = caption
        self.progress = max(0.0, min(1.0, float(progress)))
        self.update()

    def set_text(self, text):
        self.text = text
        self.update()

    def set_caption(self, caption):
        self.caption = caption
        self.update()

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, float(progress)))
        self.update()

    def _get_content_scale(self):
        return self._content_scale

    def _set_content_scale(self, value):
        self._content_scale = float(value)
        self.update()

    contentScale = Property(
        float,
        _get_content_scale,
        _set_content_scale,
    )

    def pulse(self):
        if self._pulse_group is not None:
            self._pulse_group.stop()
            self._pulse_group.deleteLater()

        group = QSequentialAnimationGroup(self)

        grow = QPropertyAnimation(self, b"contentScale", group)
        grow.setDuration(95)
        grow.setStartValue(self._content_scale)
        grow.setEndValue(1.15)
        grow.setEasingCurve(QEasingCurve.OutCubic)

        shrink = QPropertyAnimation(self, b"contentScale", group)
        shrink.setDuration(90)
        shrink.setStartValue(1.15)
        shrink.setEndValue(0.94)
        shrink.setEasingCurve(QEasingCurve.InOutCubic)

        settle = QPropertyAnimation(self, b"contentScale", group)
        settle.setDuration(125)
        settle.setStartValue(0.94)
        settle.setEndValue(1.0)
        settle.setEasingCurve(QEasingCurve.OutBack)

        group.addAnimation(grow)
        group.addAnimation(shrink)
        group.addAnimation(settle)
        self._pulse_group = group
        group.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scale = self._ui_scale
        shortest = max(1.0, float(min(self.width(), self.height())))
        margin = max(4.0, shortest * 0.07)
        rect = QRectF(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin,
        )
        progress_color = QColor(
            COLORS["green"]
            if self.progress >= 1.0
            else COLORS["purple"]
        )

        painter.setPen(
            QPen(
                QColor("#493777"),
                max(4.0, min(10 * scale, shortest * 0.08)),
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawArc(rect, 90 * 16, -360 * 16)

        if self.progress > 0:
            painter.setPen(
                QPen(
                    progress_color,
                    max(4.0, min(10 * scale, shortest * 0.08)),
                    Qt.SolidLine,
                    Qt.RoundCap,
                )
            )
            painter.drawArc(
                rect,
                90 * 16,
                int(-360 * 16 * self.progress),
            )

        painter.setPen(QColor(COLORS["text"]))
        time_font = QFont("Segoe UI", 16, QFont.Medium)
        time_size = max(6.5, min(16.0 * scale, shortest / 8.0))
        time_font.setPointSizeF(time_size * self._content_scale * self._interface_scale)
        painter.setFont(time_font)
        time_metrics = painter.fontMetrics()
        time_text = time_metrics.elidedText(
            self.text,
            Qt.TextElideMode.ElideRight,
            max(1, int(rect.width() - 6)),
        )
        time_height = time_metrics.height()
        center_y = rect.center().y() - max(2.0, shortest * 0.04)
        painter.drawText(
            QRectF(
                rect.left() + 3,
                center_y - time_height,
                rect.width() - 6,
                time_height,
            ),
            Qt.AlignCenter,
            time_text,
        )

        painter.setPen(QColor(COLORS["muted"]))
        caption_font = QFont("Segoe UI", 8)
        caption_size = max(5.0, min(8.0 * scale, shortest / 14.0))
        caption_font.setPointSizeF(caption_size * self._content_scale * self._interface_scale)
        painter.setFont(caption_font)
        caption_metrics = painter.fontMetrics()
        caption_text = caption_metrics.elidedText(
            self.caption.replace("Ready to focus", "Ready"),
            Qt.TextElideMode.ElideRight,
            max(1, int(rect.width() - 2)),
        )
        caption_height = caption_metrics.height()
        painter.drawText(
            QRectF(
                rect.left() + 1,
                center_y + 1,
                rect.width() - 2,
                caption_height,
            ),
            Qt.AlignCenter,
            caption_text,
        )


class AreaChart(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self._points = []
        self._hover_index = None
        self._density = "comfortable"
        self.setMouseTracking(True)
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_density(self, density):
        self._density = str(density or "comfortable")
        minimum = {
            "comfortable": 130,
            "compact": 86,
            "ultra": 62,
        }.get(self._density, 100)
        self.setMinimumHeight(minimum)
        self.updateGeometry()
        self.update()

    def set_values(self, values):
        self.values = list(values)
        self._hover_index = None
        self.update()

    def mouseMoveEvent(self, event):
        if not self._points:
            self._hover_index = None
            self.update()
            return

        mouse_x = event.position().x()
        nearest = min(
            range(len(self._points)),
            key=lambda index: abs(self._points[index].x() - mouse_x),
        )
        self._hover_index = nearest
        self.update()

    def leaveEvent(self, event):
        self._hover_index = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        left = 44
        right = 18
        top = 18
        bottom = 34
        plot_height = max(1, height - top - bottom)
        plot_width = max(1, width - left - right)

        display_values = list(self.values)
        if display_values:
            max_data = max(value for _, value in display_values)
            axis_max = max(4.0, float(int(max_data + 0.999)))
        else:
            axis_max = 4.0

        painter.setFont(QFont("Segoe UI", 8))

        for index in range(5):
            fraction = index / 4
            y = top + plot_height * fraction
            label_value = axis_max * (1 - fraction)

            painter.setPen(QPen(QColor("#1e2b42"), 1, Qt.DotLine))
            painter.drawLine(left, int(y), width - right, int(y))

            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(
                QRectF(0, y - 9, left - 7, 18),
                Qt.AlignRight | Qt.AlignVCenter,
                f"{label_value:g}h",
            )

        if display_values:
            labels = [label for label, _ in display_values]
        else:
            today = date.today()
            labels = [
                (today - timedelta(days=offset)).isoformat()
                for offset in reversed(range(14))
            ]

        tick_indexes = list(range(0, len(labels), max(1, len(labels) // 6)))
        if labels and (len(labels) - 1) not in tick_indexes:
            tick_indexes.append(len(labels) - 1)

        painter.setPen(QColor(COLORS["muted"]))
        for index in tick_indexes:
            x = left + plot_width * (
                index / max(1, len(labels) - 1)
            )
            label = labels[index]
            short_label = label[5:] if len(label) >= 7 else label
            painter.drawText(
                QRectF(x - 24, height - bottom + 7, 48, 18),
                Qt.AlignCenter,
                short_label,
            )

        if not display_values:
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(
                QRectF(left, top, plot_width, plot_height),
                Qt.AlignCenter,
                "Log study sessions to see your growth chart.",
            )
            self._points = []
            return

        self._points = []
        for index, (_, value) in enumerate(display_values):
            x = left + plot_width * (
                index / max(1, len(display_values) - 1)
            )
            y = (
                height
                - bottom
                - plot_height * (float(value) / axis_max)
            )
            self._points.append(QPointF(x, y))

        area = QPainterPath()
        area.moveTo(self._points[0])
        for point in self._points[1:]:
            area.lineTo(point)
        area.lineTo(self._points[-1].x(), height - bottom)
        area.lineTo(self._points[0].x(), height - bottom)
        area.closeSubpath()

        gradient = QLinearGradient(0, top, 0, height - bottom)
        gradient.setColorAt(0, QColor(139, 92, 246, 115))
        gradient.setColorAt(1, QColor(139, 92, 246, 5))
        painter.fillPath(area, QBrush(gradient))

        line = QPainterPath()
        line.moveTo(self._points[0])
        for point in self._points[1:]:
            line.lineTo(point)

        painter.setPen(
            QPen(
                QColor(COLORS["purple"]),
                3,
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawPath(line)

        painter.setBrush(QColor(COLORS["purple"]))
        painter.setPen(Qt.NoPen)
        for point in self._points:
            painter.drawEllipse(point, 4, 4)

        if (
            self._hover_index is not None
            and 0 <= self._hover_index < len(self._points)
        ):
            point = self._points[self._hover_index]
            label, value = display_values[self._hover_index]

            painter.setBrush(QColor("#ffffff"))
            painter.setPen(
                QPen(QColor(COLORS["purple"]), 3)
            )
            painter.drawEllipse(point, 6, 6)

            tooltip_width = 94
            tooltip_height = 43
            tooltip_x = min(
                width - right - tooltip_width,
                max(left, point.x() - tooltip_width / 2),
            )
            tooltip_y = max(top, point.y() - 54)

            tooltip_rect = QRectF(
                tooltip_x,
                tooltip_y,
                tooltip_width,
                tooltip_height,
            )
            painter.setBrush(QColor("#152238"))
            painter.setPen(QPen(QColor(COLORS["border"]), 1))
            painter.drawRoundedRect(tooltip_rect, 7, 7)

            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(
                tooltip_rect.adjusted(8, 4, -8, -22),
                Qt.AlignLeft | Qt.AlignVCenter,
                label,
            )
            painter.setPen(QColor(COLORS["text"]))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(
                tooltip_rect.adjusted(8, 20, -8, -4),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{float(value):g}h",
            )


class BadgeCard(QFrame):
    def __init__(self, icon, title, description, accent):
        super().__init__()
        self._density = "comfortable"
        self._accent = accent
        self.setObjectName("SoftPanel")
        self.setMinimumHeight(118)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.setStyleSheet(
            f"QFrame#SoftPanel{{"
            f"background:{COLORS['panel_alt']};"
            f"border:1px solid {COLORS['border']};"
            "border-radius:11px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(7)

        self.icon_label = QLabel(icon)
        icon_label = self.icon_label
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"font-size:34pt;color:{accent};"
        )

        self.title_label = QLabel(title)
        title_label = self.title_label
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setMinimumWidth(0)
        title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        title_label.setStyleSheet("font-weight:700;")

        self.description_label = QLabel(description)
        description_label = self.description_label
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setObjectName("Muted")
        description_label.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch(1)

    def set_density(self, density):
        self._density = str(density or "comfortable")
        compact = self._density != "comfortable"
        ultra = self._density == "ultra"
        margins = 6 if ultra else 9 if compact else 14
        self.layout().setContentsMargins(margins, margins, margins, margins)
        self.layout().setSpacing(3 if compact else 7)
        self.setMinimumHeight(68 if ultra else 82 if compact else 118)
        self.icon_label.setStyleSheet(
            f"font-size:{20 if ultra else 25 if compact else 34}pt;"
            f"color:{self._accent};"
        )
        self.description_label.setVisible(not compact)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            f"font-size:{6.5 if ultra else 8 if compact else 9.5}pt;"
            "font-weight:700;"
        )
        self.updateGeometry()


class Divider(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(
            f"background:{COLORS['border']};border:none;"
        )


class SectionHeader(QWidget):
    def __init__(self, emoji, title, subtitle="", action_text=""):
        super().__init__()
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMaximumHeight(16777215)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel(emoji)
        icon = self.icon_label
        icon.setStyleSheet("font-size:15pt;")
        layout.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(1)

        self.title_label = QLabel(title)
        title_label = self.title_label
        title_label.setObjectName("CardTitle")
        title_label.setWordWrap(True)
        title_label.setMinimumWidth(0)
        text.addWidget(title_label)

        self.subtitle_label = None
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            subtitle_label = self.subtitle_label
            subtitle_label.setObjectName("Muted")
            subtitle_label.setWordWrap(True)
            subtitle_label.setMinimumWidth(0)
            subtitle_label.setStyleSheet("font-size:8.8pt;")
            text.addWidget(subtitle_label)

        layout.addLayout(text, 1)

        self.action_button = None
        if action_text:
            self.action_button = QPushButton(action_text)
            self.action_button.setObjectName("Link")
            self.action_button.setCursor(Qt.PointingHandCursor)
            layout.addWidget(self.action_button)

    def set_density(self, density):
        density = str(density or "comfortable")
        compact = density != "comfortable"
        ultra = density == "ultra"
        self.layout().setSpacing(4 if compact else 8)
        self.icon_label.setStyleSheet(
            f"font-size:{10 if ultra else 12 if compact else 15}pt;"
        )
        self.title_label.setWordWrap(not compact)
        if self.subtitle_label is not None:
            self.subtitle_label.setVisible(not compact)
        if self.action_button is not None:
            self.action_button.setMinimumHeight(24 if ultra else 28)
            self.action_button.setMaximumHeight(28 if ultra else 32)
        self.updateGeometry()



class VisibleCheckBox(QWidget):
    stateChanged = Signal(int)

    def __init__(self, checked=False):
        super().__init__()
        self._checked = bool(checked)
        self._hovered = False
        self.setFixedSize(22, 22)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Mark task complete")

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        checked = bool(checked)
        if self._checked == checked:
            return
        self._checked = checked
        self.update()

    def toggle(self):
        self._checked = not self._checked
        self.update()
        self.stateChanged.emit(
            (
                Qt.Checked.value
                if self._checked
                else Qt.Unchecked.value
            )
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
            event.accept()
            return
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        box = QRectF(2.5, 2.5, 17, 17)

        if self._checked:
            fill = QColor(COLORS["purple"])
            border = QColor("#a98bff")
        elif self._hovered:
            fill = QColor("#182844")
            border = QColor("#9aa9bf")
        else:
            fill = QColor("#0c1728")
            border = QColor("#72819a")

        painter.setBrush(fill)
        painter.setPen(QPen(border, 1.6))
        painter.drawRoundedRect(box, 4, 4)

        if self._checked:
            painter.setPen(
                QPen(
                    QColor("#ffffff"),
                    2.2,
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin,
                )
            )
            check = QPainterPath()
            check.moveTo(6.1, 10.8)
            check.lineTo(9.1, 13.8)
            check.lineTo(15.8, 7.2)
            painter.drawPath(check)


class TaskRow(QWidget):
    def __init__(
        self,
        title,
        source,
        checked=False,
        status_text="",
        category_text="",
        category_color=None,
        on_toggle=None,
        action_text=None,
        on_action=None,
        completed=False,
    ):
        super().__init__()
        self._forced_density = "comfortable"
        self._interface_scale = 1.0
        self.setStyleSheet("background:transparent;border:none;")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumHeight(39)
        self.setMaximumHeight(16777215)

        layout = QHBoxLayout(self)
        self.row_layout = layout
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(9)

        self.checkbox = VisibleCheckBox(checked=checked)
        if on_toggle is not None:
            self.checkbox.stateChanged.connect(on_toggle)
        layout.addWidget(
            self.checkbox,
            0,
            Qt.AlignVCenter,
        )

        text = QVBoxLayout()
        self.text_layout = text
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)

        self.title_label = QLabel(title)
        title_label = self.title_label
        title_label.setWordWrap(False)
        title_label.setMinimumWidth(0)
        title_label.setStyleSheet(
            "font-weight:600;background:transparent;border:none;"
        )
        title_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Preferred,
        )
        title_label.setToolTip(title)
        text.addWidget(title_label)

        self.source_label = QLabel(source)
        source_label = self.source_label
        source_label.setObjectName("TaskSource")
        source_label.setStyleSheet("font-size:8.7pt;")
        source_label.setMinimumWidth(0)
        source_label.setWordWrap(False)
        source_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Preferred,
        )
        source_label.setToolTip(source)
        text.addWidget(source_label)

        layout.addLayout(text, 1)

        metadata_text = status_text or category_text
        self.metadata_label = None
        if metadata_text:
            self.metadata_label = QLabel(
                metadata_text
            )
            metadata = self.metadata_label
            metadata.setObjectName("TaskCategory")
            metadata.setMinimumWidth(58)
            metadata.setMaximumWidth(78)
            metadata.setAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )
            metadata.setToolTip(metadata_text)

            if status_text:
                metadata.setStyleSheet(
                    f"color:{COLORS['green']};"
                    "font-size:8.7pt;font-weight:700;"
                    "background:transparent;border:none;"
                )
            else:
                accent = (
                    category_color
                    or COLORS["muted"]
                )
                metadata.setStyleSheet(
                    f"color:{accent};"
                    "font-size:8.7pt;font-weight:700;"
                    "background:transparent;border:none;"
                )

            layout.addWidget(
                metadata,
                0,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        self.action_button = None
        if action_text and on_action is not None:
            self.action_button = QPushButton(action_text)
            action = self.action_button
            action.setObjectName("WorkspaceOpen")
            action.setMinimumSize(52, 28)
            action.setMaximumHeight(32)
            action.setToolTip("Open Task Workspace")
            action.setProperty(
                "workspace_open_button",
                True,
            )
            action.clicked.connect(on_action)
            action.setEnabled(not completed)
            layout.addWidget(
                action,
                0,
                Qt.AlignVCenter,
            )

    def _refresh_content_height(self):
        compact = self._forced_density != "comfortable"
        ultra = self._forced_density == "ultra"
        base = 25 if ultra else 30 if compact else 39
        margins = self.row_layout.contentsMargins()
        text_height = self.title_label.fontMetrics().height()
        if self.source_label.isVisible():
            text_height += self.source_label.fontMetrics().height()
            text_height += self.text_layout.spacing()
        required = text_height + margins.top() + margins.bottom() + 2
        self.setMinimumHeight(max(base, required))

    def set_interface_scale(self, scale):
        self._interface_scale = max(0.80, min(1.20, float(scale)))
        self._refresh_content_height()
        self.updateGeometry()

    def set_density(self, density):
        self._forced_density = str(density or "comfortable")
        compact = self._forced_density != "comfortable"
        ultra = self._forced_density == "ultra"
        self.source_label.setVisible(not compact)
        self.title_label.setWordWrap(False)
        self.row_layout.setContentsMargins(0, 1 if compact else 3, 0, 1 if compact else 3)
        self.row_layout.setSpacing(4 if ultra else 6 if compact else 9)
        if self.metadata_label is not None:
            self.metadata_label.setVisible(not ultra)
        if self.action_button is not None:
            self.action_button.setMinimumSize(40 if ultra else 46, 24 if ultra else 27)
            self.action_button.setMaximumHeight(26 if ultra else 30)
        self._refresh_content_height()
        self.updateGeometry()

    def resizeEvent(self, event):
        if self._forced_density == "comfortable":
            compact = event.size().width() < 430
            self.title_label.setWordWrap(compact)
            self.source_label.setWordWrap(compact)
            self.row_layout.setSpacing(6 if compact else 9)
        self._refresh_content_height()
        self.updateGeometry()
        super().resizeEvent(event)


class FocusRow(QWidget):
    def __init__(
        self,
        emoji,
        title,
        detail,
        duration,
        accent,
        action_text=None,
        on_action=None,
        completed=False,
    ):
        super().__init__()
        self._forced_density = "comfortable"
        self._interface_scale = 1.0
        self.setStyleSheet("background:transparent;border:none;")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumHeight(38)
        self.setMaximumHeight(16777215)

        layout = QHBoxLayout(self)
        self.row_layout = layout
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(9)

        self.icon_label = QLabel(emoji)
        icon = self.icon_label
        icon.setStyleSheet("font-size:18pt;")
        icon.setFixedWidth(34)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon, 0, Qt.AlignVCenter)

        text = QVBoxLayout()
        self.text_layout = text
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)

        self.title_label = QLabel(title)
        title_label = self.title_label
        title_label.setMinimumWidth(0)
        title_label.setStyleSheet(
            f"font-weight:700;color:{COLORS['muted'] if completed else accent};"
            + ("text-decoration:line-through;" if completed else "")
        )
        title_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Preferred,
        )
        title_label.setToolTip(title)
        text.addWidget(title_label)

        self.detail_label = QLabel(detail)
        detail_label = self.detail_label
        detail_label.setObjectName("Muted")
        detail_label.setWordWrap(False)
        detail_label.setMinimumWidth(0)
        detail_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Preferred,
        )
        detail_label.setToolTip(detail)
        text.addWidget(detail_label)

        layout.addLayout(text, 1)

        self.duration_label = QLabel(duration)
        duration_label = self.duration_label
        duration_label.setObjectName("Muted")
        duration_label.setStyleSheet(
            "color:#7f8798;font-weight:700;"
            if completed
            else "font-weight:700;"
        )
        duration_label.setMinimumWidth(34)
        duration_label.setMaximumWidth(48)
        duration_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )
        layout.addWidget(duration_label)

        self.action_button = None
        if action_text and on_action is not None:
            self.action_button = QPushButton(action_text)
            action = self.action_button
            action.setObjectName("WorkspaceOpen")
            action.setMinimumSize(52, 28)
            action.setMaximumHeight(32)
            action.setToolTip("Open Task Workspace")
            action.setProperty(
                "workspace_open_button",
                True,
            )
            action.clicked.connect(on_action)
            action.setEnabled(not completed)
            layout.addWidget(
                action,
                0,
                Qt.AlignVCenter,
            )

    def _refresh_content_height(self):
        compact = self._forced_density != "comfortable"
        ultra = self._forced_density == "ultra"
        base = 25 if ultra else 30 if compact else 38
        margins = self.row_layout.contentsMargins()
        text_height = self.title_label.fontMetrics().height()
        if self.detail_label.isVisible():
            text_height += self.detail_label.fontMetrics().height()
            text_height += self.text_layout.spacing()
        required = text_height + margins.top() + margins.bottom() + 2
        self.setMinimumHeight(max(base, required))

    def set_interface_scale(self, scale):
        self._interface_scale = max(0.80, min(1.20, float(scale)))
        self._refresh_content_height()
        self.updateGeometry()

    def set_density(self, density):
        self._forced_density = str(density or "comfortable")
        compact = self._forced_density != "comfortable"
        ultra = self._forced_density == "ultra"
        self.detail_label.setVisible(not compact)
        self.title_label.setWordWrap(False)
        self.row_layout.setContentsMargins(0, 1 if compact else 3, 0, 1 if compact else 3)
        self.row_layout.setSpacing(4 if ultra else 6 if compact else 9)
        self.icon_label.setFixedWidth(24 if ultra else 28 if compact else 34)
        self.icon_label.setStyleSheet(
            f"font-size:{12 if ultra else 15 if compact else 18}pt;"
        )
        self.duration_label.setMinimumWidth(27 if ultra else 32)
        self.duration_label.setMaximumWidth(38 if ultra else 46)
        if self.action_button is not None:
            self.action_button.setMinimumSize(40 if ultra else 46, 24 if ultra else 27)
            self.action_button.setMaximumHeight(26 if ultra else 30)
        self._refresh_content_height()
        self.updateGeometry()

    def resizeEvent(self, event):
        if self._forced_density == "comfortable":
            compact = event.size().width() < 440
            self.title_label.setWordWrap(compact)
            self.detail_label.setWordWrap(compact)
            self.row_layout.setSpacing(6 if compact else 9)
        self._refresh_content_height()
        self.updateGeometry()
        super().resizeEvent(event)


class StatRow(QWidget):
    def __init__(self, emoji, label, value, accent=None):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")
        self._row_layout = None
        self._density = "comfortable"
        self._interface_scale = 1.0

        layout = QHBoxLayout(self)
        self._row_layout = layout
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(8)

        self.icon_label = QLabel(emoji)
        icon = self.icon_label
        icon.setFixedWidth(22)
        icon.setStyleSheet("font-size:11pt;")
        layout.addWidget(icon)

        self.label_widget = QLabel(label)
        label_widget = self.label_widget
        layout.addWidget(label_widget)
        layout.addStretch()

        self.value_widget = QLabel(value)
        value_widget = self.value_widget
        style = "font-weight:700;"
        if accent:
            style += f"color:{accent};"
        value_widget.setStyleSheet(style)
        layout.addWidget(value_widget)

    def _refresh_content_height(self):
        compact = self._density != "comfortable"
        ultra = self._density == "ultra"
        base_minimum = 14 if ultra else 17 if compact else 0
        margins = self._row_layout.contentsMargins()
        required = max(
            self.icon_label.fontMetrics().height(),
            self.label_widget.fontMetrics().height(),
            self.value_widget.fontMetrics().height(),
        ) + margins.top() + margins.bottom() + 2
        target = max(base_minimum, required)
        self.setMinimumHeight(target)
        base_maximum = 16 if ultra else 20 if compact else 16777215
        self.setMaximumHeight(max(base_maximum, target) if compact else 16777215)

    def set_interface_scale(self, scale):
        self._interface_scale = max(0.80, min(1.20, float(scale)))
        self._refresh_content_height()
        self.updateGeometry()

    def set_density(self, density):
        self._density = str(density or "comfortable")
        compact = self._density != "comfortable"
        ultra = self._density == "ultra"
        self._row_layout.setContentsMargins(
            0,
            0 if ultra else 1 if compact else 6,
            0,
            0 if ultra else 1 if compact else 6,
        )
        self._row_layout.setSpacing(3 if ultra else 5 if compact else 8)
        font_size = 6.5 if ultra else 7.5 if compact else 9.5
        self.icon_label.setFixedWidth(14 if ultra else 18 if compact else 22)
        self.icon_label.setStyleSheet(
            f"font-size:{7 if ultra else 9 if compact else 11}pt;"
        )
        self.label_widget.setStyleSheet(f"font-size:{font_size}pt;")
        self.value_widget.setStyleSheet(
            f"font-size:{font_size}pt;font-weight:700;"
            f"color:{COLORS['purple']};"
        )
        self._refresh_content_height()
        self.updateGeometry()


class SidebarMetricCard(QFrame):
    def __init__(self, title, emoji):
        super().__init__()
        self.setObjectName("SidebarCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(6)

        heading = QLabel(f"{emoji}  {title}")
        heading.setObjectName("Tiny")
        self.layout.addWidget(heading)


class FooterMetricBox(QFrame):
    def __init__(self, emoji, label, value=""):
        super().__init__()
        self._density = "comfortable"
        self._interface_scale = 1.0
        self.setObjectName("SoftPanel")
        self.setMinimumHeight(48)
        self.setMaximumHeight(16777215)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self._box_layout = QHBoxLayout(self)
        layout = self._box_layout
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        self.icon_label = QLabel(emoji)
        icon = self.icon_label
        icon.setStyleSheet("font-size:17pt;")
        icon.setFixedWidth(28)
        layout.addWidget(icon)

        text = QVBoxLayout()
        self._text_layout = text
        text.setSpacing(1)

        self.label_widget = QLabel(label)
        label_widget = self.label_widget
        label_widget.setObjectName("Muted")
        label_widget.setStyleSheet("font-size:8.5pt;")
        text.addWidget(label_widget)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-weight:700;")
        text.addWidget(self.value_label)

        layout.addLayout(text, 1)

    def set_value(self, value):
        self.value_label.setText(value)

    def _refresh_content_height(self):
        compact = self._density != "comfortable"
        ultra = self._density == "ultra"
        base = 32 if ultra else 39 if compact else 48
        margins = self._box_layout.contentsMargins()
        text_height = self.value_label.fontMetrics().height()
        if self.label_widget.isVisible():
            text_height += self.label_widget.fontMetrics().height()
            text_height += self._text_layout.spacing()
        required = text_height + margins.top() + margins.bottom() + 2
        self.setMinimumHeight(max(base, required))

    def set_interface_scale(self, scale):
        self._interface_scale = max(0.80, min(1.20, float(scale)))
        self._refresh_content_height()
        self.updateGeometry()

    def set_density(self, density):
        self._density = str(density or "comfortable")
        compact = self._density != "comfortable"
        ultra = self._density == "ultra"
        self._box_layout.setContentsMargins(
            6 if ultra else 8 if compact else 12,
            4 if ultra else 6 if compact else 9,
            6 if ultra else 8 if compact else 12,
            4 if ultra else 6 if compact else 9,
        )
        self._box_layout.setSpacing(5 if compact else 10)
        self.icon_label.setFixedWidth(20 if ultra else 24 if compact else 28)
        self.icon_label.setStyleSheet(
            f"font-size:{11 if ultra else 14 if compact else 17}pt;"
        )
        self.label_widget.setVisible(not ultra)
        self._refresh_content_height()
        self.updateGeometry()


class MiniSparkline(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self.setFixedSize(112, 36)

    def set_values(self, values):
        self.values = [
            float(value)
            for _, value in values[-7:]
        ]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        values = self.values

        if not values:
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "No data",
            )
            return

        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum or 1

        points = []
        for index, value in enumerate(values):
            x = 5 + (self.width() - 10) * (
                index / max(1, len(values) - 1)
            )
            y = 5 + (self.height() - 10) * (
                1 - ((value - minimum) / span)
            )
            points.append(QPointF(x, y))

        path = QPainterPath()
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)

        painter.setPen(
            QPen(
                QColor(COLORS["purple"]),
                2,
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawPath(path)

        painter.setBrush(QColor(COLORS["purple"]))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(points[-1], 3, 3)
