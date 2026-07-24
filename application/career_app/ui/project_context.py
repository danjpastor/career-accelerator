"""Reusable previous-milestone artifact context for portfolio workspaces."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from career_app.services import project_artifacts


class ProjectContextWidget(QWidget):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        title = QLabel("Previous Milestone Context")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        help_text = QLabel(
            "Later milestones continue from the actual artifacts produced earlier in the project. Select an artifact to open it; missing artifacts remain visible instead of being silently ignored."
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.itemDoubleClicked.connect(lambda _item: self.open_selected())
        layout.addWidget(self.list, 1)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        refresh = QPushButton("Refresh Context")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        open_button = QPushButton("Open Selected Artifact")
        open_button.setObjectName("Primary")
        open_button.clicked.connect(self.open_selected)
        actions.addWidget(open_button)
        actions.addStretch()
        layout.addLayout(actions)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for milestone in project_artifacts.upstream_milestones(
            self.context.project_dir,
            self.context.milestone_key,
        ):
            header = QListWidgetItem(
                f"{'✓' if milestone['artifacts'] else '○'} {milestone['label']}"
            )
            header.setFlags(header.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            self.list.addItem(header)
            if milestone["artifacts"]:
                for relative in milestone["artifacts"]:
                    item = QListWidgetItem(f"    {relative}")
                    item.setData(Qt.ItemDataRole.UserRole, relative)
                    self.list.addItem(item)
            else:
                missing = QListWidgetItem("    No artifact detected")
                missing.setFlags(missing.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.list.addItem(missing)

    def open_selected(self) -> None:
        item = self.list.currentItem()
        relative = str(item.data(Qt.ItemDataRole.UserRole) or "") if item else ""
        if not relative:
            return
        path = self.context.project_dir / Path(relative)
        if not path.exists():
            QMessageBox.information(self, "Artifact Not Found", "The selected artifact no longer exists at its registered path.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
