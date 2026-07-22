from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QSizePolicy


class OverlayNotifier(QFrame):
    """Transient message overlay that never consumes QMainWindow layout space."""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setObjectName("OverlayNotifier")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "QFrame#OverlayNotifier {"
            " background: rgba(14, 24, 40, 242);"
            " border: 1px solid #40516a;"
            " border-radius: 9px;"
            "}"
            "QLabel { color: #e8eef8; padding: 1px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)
        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(520)
        layout.addWidget(self.label)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        parent.installEventFilter(self)
        self.hide()

    def show_message(self, message: str, timeout_ms: int = 3000) -> None:
        text = " ".join(str(message or "").split())
        if not text:
            self.hide()
            return
        self.label.setText(text)
        self.adjustSize()
        self._reposition()
        self.raise_()
        self.show()
        self._timer.start(max(800, int(timeout_ms or 3000)))

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        margin = 18
        width = min(max(220, self.sizeHint().width()), max(220, parent.width() - margin * 2))
        self.setFixedWidth(width)
        self.adjustSize()
        x = max(margin, parent.width() - self.width() - margin)
        y = max(margin, parent.height() - self.height() - margin)
        self.move(x, y)

    def eventFilter(self, watched, event):
        if watched is self.parentWidget() and event.type() in {
            QEvent.Type.Resize,
            QEvent.Type.Move,
            QEvent.Type.Show,
            QEvent.Type.WindowStateChange,
        }:
            self._reposition()
        return super().eventFilter(watched, event)
