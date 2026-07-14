from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import (
    QEasingCurve, Property, QPropertyAnimation, QSequentialAnimationGroup,
    Qt, QRectF, QPointF, Signal
)
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QBrush, QLinearGradient
)
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QLabel, QHBoxLayout, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget
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
        self.setMinimumWidth(172)
        self.setMinimumHeight(94)
        self.setMaximumHeight(98)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

    def set_value(self, value, subtitle="", extra=""):
        self.value = max(0, min(100, float(value)))
        self.subtitle = subtitle
        self.extra = extra
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        ring_rect = QRectF(8, 8, 76, 76)

        painter.setPen(
            QPen(
                QColor(COLORS["border"]),
                8.5,
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawArc(ring_rect, 90 * 16, -360 * 16)

        painter.setPen(
            QPen(
                self.color,
                8.5,
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
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(
            ring_rect,
            Qt.AlignCenter,
            f"{self.value:.0f}%",
        )

        text_left = 96
        text_width = max(
            88,
            self.width() - text_left - 6,
        )

        painter.setFont(
            QFont("Segoe UI", 9, QFont.Bold)
        )
        painter.drawText(
            QRectF(text_left, 10, text_width, 20),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.title,
        )

        painter.setPen(QColor(COLORS["muted"]))
        painter.setFont(QFont("Segoe UI", 8.5))
        painter.drawText(
            QRectF(text_left, 38, text_width, 19),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.subtitle,
        )
        painter.drawText(
            QRectF(text_left, 64, text_width, 19),
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
        self.caption = "Ready to focus • 0 / 60 min"
        self.progress = 0.0
        self._content_scale = 1.0
        self._pulse_group = None
        self.setFixedSize(138, 138)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

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

        rect = QRectF(8, 4, 122, 122)
        progress_color = QColor(
            COLORS["green"]
            if self.progress >= 1.0
            else COLORS["purple"]
        )

        painter.setPen(
            QPen(
                QColor("#493777"),
                10,
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )
        painter.drawArc(rect, 90 * 16, -360 * 16)

        if self.progress > 0:
            painter.setPen(
                QPen(
                    progress_color,
                    10,
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
        time_font.setPointSizeF(16 * self._content_scale)
        painter.setFont(time_font)
        painter.drawText(
            rect.adjusted(0, -7, 0, 0),
            Qt.AlignCenter,
            self.text,
        )

        painter.setPen(QColor(COLORS["muted"]))
        caption_font = QFont("Segoe UI", 8)
        caption_font.setPointSizeF(8 * self._content_scale)
        painter.setFont(caption_font)
        painter.drawText(
            rect.adjusted(-8, 33, 8, 0),
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
        self.setMinimumHeight(175)

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
        self.setObjectName("SoftPanel")
        self.setMinimumHeight(142)
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
            self.action_button = QPushButton(action_text)
            self.action_button.setObjectName("Link")
            self.action_button.setCursor(Qt.PointingHandCursor)
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
        category_text="",
        category_color=None,
        on_toggle=None,
    ):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(39)
        self.setMaximumHeight(41)

        layout = QHBoxLayout(self)
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
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)

        self.title_label = QLabel(title)
        title_label = self.title_label
        title_label.setWordWrap(False)
        title_label.setStyleSheet(
            "font-weight:600;background:transparent;border:none;"
        )
        title_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        title_label.setMinimumHeight(17)
        title_label.setMaximumHeight(18)
        title_label.setToolTip(title)
        text.addWidget(title_label)

        self.source_label = QLabel(source)
        source_label = self.source_label
        source_label.setObjectName("TaskSource")
        source_label.setStyleSheet("font-size:8.7pt;")
        source_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        source_label.setMinimumHeight(15)
        source_label.setMaximumHeight(16)
        source_label.setToolTip(source)
        text.addWidget(source_label)

        layout.addLayout(text, 1)

        metadata_text = status_text or category_text
        if metadata_text:
            self.metadata_label = QLabel(
                metadata_text
            )
            metadata = self.metadata_label
            metadata.setObjectName("TaskCategory")
            metadata.setFixedWidth(78)
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


class FocusRow(QWidget):
    def __init__(self, emoji, title, detail, duration, accent):
        super().__init__()
        self.setStyleSheet("background:transparent;border:none;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(38)
        self.setMaximumHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(9)

        icon = QLabel(emoji)
        icon.setStyleSheet("font-size:18pt;")
        icon.setFixedWidth(34)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon, 0, Qt.AlignVCenter)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-weight:700;color:{accent};"
        )
        title_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        title_label.setMinimumHeight(17)
        title_label.setMaximumHeight(18)
        title_label.setToolTip(title)
        text.addWidget(title_label)

        detail_label = QLabel(detail)
        detail_label.setObjectName("Muted")
        detail_label.setWordWrap(False)
        detail_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        detail_label.setMinimumHeight(16)
        detail_label.setMaximumHeight(17)
        detail_label.setToolTip(detail)
        text.addWidget(detail_label)

        layout.addLayout(text, 1)

        duration_label = QLabel(duration)
        duration_label.setObjectName("Muted")
        duration_label.setStyleSheet("font-weight:700;")
        duration_label.setFixedWidth(42)
        duration_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )
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
        self.setMinimumHeight(50)

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
