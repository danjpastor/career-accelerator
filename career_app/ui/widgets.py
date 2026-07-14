from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QBrush, QLinearGradient
)
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QLabel, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
)

from career_app.theme import COLORS


class Card(QFrame):
    def __init__(self, title=None, subtitle=None):
        super().__init__()
        self.setObjectName("Card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(8)

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            self.layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("Muted")
            subtitle_label.setWordWrap(True)
            self.layout.addWidget(subtitle_label)


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
        self.setMinimumSize(190, 122)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_value(self, value, subtitle="", extra=""):
        self.value = max(0, min(100, float(value)))
        self.subtitle = subtitle
        self.extra = extra
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        ring_rect = QRectF(10, 13, 86, 86)

        painter.setPen(
            QPen(QColor(COLORS["border"]), 9.5, Qt.SolidLine, Qt.RoundCap)
        )
        painter.drawArc(ring_rect, 90 * 16, -360 * 16)

        painter.setPen(
            QPen(self.color, 9.5, Qt.SolidLine, Qt.RoundCap)
        )
        painter.drawArc(
            ring_rect,
            90 * 16,
            int(-360 * 16 * self.value / 100),
        )

        painter.setPen(QColor(COLORS["text"]))
        painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
        painter.drawText(
            ring_rect,
            Qt.AlignCenter,
            f"{self.value:.0f}%",
        )

        text_left = 110
        text_width = max(100, self.width() - text_left - 8)

        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(
            QRectF(text_left, 20, text_width, 22),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.title,
        )

        painter.setPen(QColor(COLORS["muted"]))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(text_left, 49, text_width, 22),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.subtitle,
        )
        painter.drawText(
            QRectF(text_left, 76, text_width, 22),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.extra,
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
        self.caption = "Ready to focus?"
        self.progress = 0.18
        self.setMinimumSize(210, 210)
        self.setMaximumHeight(222)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_text(self, text):
        self.text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height()) - 24
        x = (self.width() - size) / 2
        y = 4
        rect = QRectF(x, y, size, size)

        painter.setPen(
            QPen(QColor("#493777"), 13, Qt.SolidLine, Qt.RoundCap)
        )
        painter.drawArc(rect, 90 * 16, -360 * 16)

        painter.setPen(
            QPen(QColor(COLORS["purple"]), 13, Qt.SolidLine, Qt.RoundCap)
        )
        painter.drawArc(
            rect,
            90 * 16,
            int(-360 * 16 * self.progress),
        )

        painter.setPen(QColor(COLORS["text"]))
        painter.setFont(QFont("Segoe UI", 20, QFont.Medium))
        painter.drawText(
            rect.adjusted(0, -10, 0, 0),
            Qt.AlignCenter,
            self.text,
        )

        painter.setPen(QColor(COLORS["muted"]))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            rect.adjusted(0, 48, 0, 0),
            Qt.AlignCenter,
            self.caption,
        )


class AreaChart(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self._points = []
        self._hover_index = None
        self.setMouseTracking(True)
        self.setMinimumHeight(235)

    def set_values(self, values):
        self.values = values[-14:]
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
        self.setObjectName("SoftPanel")
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"font-size:34pt;color:{accent};"
        )

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight:700;")

        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setObjectName("Muted")
        description_label.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch(1)


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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMaximumHeight(48 if subtitle else 32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icon = QLabel(emoji)
        icon.setStyleSheet("font-size:15pt;")
        layout.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(1)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        text.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("Muted")
            subtitle_label.setStyleSheet("font-size:8.8pt;")
            text.addWidget(subtitle_label)

        layout.addLayout(text, 1)

        self.action_button = None
        if action_text:
            self.action_button = QLabel(action_text)
            self.action_button.setStyleSheet(
                f"color:{COLORS['blue']};font-weight:700;"
            )
            layout.addWidget(self.action_button)



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
            int(Qt.Checked if self._checked else Qt.Unchecked)
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
        on_toggle=None,
    ):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        self.checkbox = VisibleCheckBox(checked=checked)
        if on_toggle is not None:
            self.checkbox.stateChanged.connect(on_toggle)
        layout.addWidget(self.checkbox, 0, Qt.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(2)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(
            "font-weight:600;background:transparent;border:none;"
        )
        text.addWidget(title_label)

        source_label = QLabel(source)
        source_label.setObjectName("Muted")
        source_label.setStyleSheet("font-size:8.7pt;")
        text.addWidget(source_label)

        layout.addLayout(text, 1)

        if status_text:
            status = QLabel(status_text)
            status.setStyleSheet(
                f"color:{COLORS['green']};font-weight:700;"
            )
            layout.addWidget(status)


class FocusRow(QWidget):
    def __init__(self, emoji, title, detail, duration, accent):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        icon = QLabel(emoji)
        icon.setStyleSheet("font-size:19pt;")
        icon.setFixedWidth(36)
        layout.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-weight:700;color:{accent};"
        )
        text.addWidget(title_label)

        detail_label = QLabel(detail)
        detail_label.setObjectName("Muted")
        detail_label.setWordWrap(True)
        text.addWidget(detail_label)

        layout.addLayout(text, 1)

        duration_label = QLabel(duration)
        duration_label.setObjectName("Muted")
        duration_label.setStyleSheet("font-weight:700;")
        layout.addWidget(duration_label)


class StatRow(QWidget):
    def __init__(self, emoji, label, value, accent=None):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(8)

        icon = QLabel(emoji)
        icon.setFixedWidth(22)
        icon.setStyleSheet("font-size:11pt;")
        layout.addWidget(icon)

        label_widget = QLabel(label)
        layout.addWidget(label_widget)
        layout.addStretch()

        value_widget = QLabel(value)
        style = "font-weight:700;"
        if accent:
            style += f"color:{accent};"
        value_widget.setStyleSheet(style)
        layout.addWidget(value_widget)


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
        self.setObjectName("SoftPanel")
        self.setMinimumHeight(58)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        icon = QLabel(emoji)
        icon.setStyleSheet("font-size:17pt;")
        icon.setFixedWidth(28)
        layout.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(1)

        label_widget = QLabel(label)
        label_widget.setObjectName("Muted")
        label_widget.setStyleSheet("font-size:8.5pt;")
        text.addWidget(label_widget)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-weight:700;")
        text.addWidget(self.value_label)

        layout.addLayout(text, 1)

    def set_value(self, value):
        self.value_label.setText(value)


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

        if not self.values:
            values = [0.2, 0.35, 0.25, 0.5, 0.45, 0.7, 0.55]
        else:
            values = self.values

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
