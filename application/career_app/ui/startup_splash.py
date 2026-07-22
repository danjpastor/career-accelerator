from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


PATHWAY_ASSETS = {
    "data_analytics": ("data_analytics_stacked.png", "data_analytics_app_icon.png"),
    "it_support": ("it_support_stacked.png", "it_support_app_icon.png"),
    "cybersecurity": ("cybersecurity_stacked.png", "cybersecurity_app_icon.png"),
    "software_engineering": (
        "software_engineering_stacked.png",
        "software_engineering_app_icon.png",
    ),
}
NEUTRAL_ASSETS = ("career_accelerator_stacked.png", "career_accelerator_app_icon.png")


def _selected_pathway(root: Path) -> str | None:
    candidates = (
        root / "data" / "onboarding_state.json",
        root / "application" / "data" / "onboarding_state.json",
    )
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        pathway = payload.get("selected_pathway_id") or payload.get("pathway_id")
        if pathway:
            return str(pathway)
    return None


class StartupSplash(QWidget):
    """Frameless, pathway-aware splash shown while the main window initializes."""

    def __init__(self, root: Path, asset_root: Path) -> None:
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.root = Path(root)
        self.asset_root = Path(asset_root) / "pathways"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setFixedSize(720, 540)

        pathway = _selected_pathway(self.root)
        logo_name, icon_name = PATHWAY_ASSETS.get(pathway, NEUTRAL_ASSETS)
        self.logo_path = self.asset_root / logo_name
        self.icon_path = self.asset_root / icon_name
        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))

        shell = QFrame(self)
        shell.setObjectName("SplashShell")
        shell.setGeometry(0, 0, 720, 540)
        shell.setStyleSheet(
            """
            QFrame#SplashShell {
                background: #07122C;
                border: 2px solid #4C7DFF;
                border-radius: 28px;
            }
            QLabel { color: #FFFFFF; background: transparent; }
            QLabel#Muted { color: #AAB8D1; font-size: 11pt; }
            QLabel#Status { color: #FFFFFF; font-size: 12pt; font-weight: 600; }
            QLabel#Step { color: #A85CFF; font-size: 10pt; font-weight: 700; }
            QProgressBar {
                background: #0B1732;
                border: 1px solid #344A72;
                border-radius: 10px;
                min-height: 20px;
                color: white;
                text-align: center;
                font-weight: 700;
            }
            QProgressBar::chunk {
                border-radius: 9px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4C7DFF,
                    stop:0.55 #9A5CFF,
                    stop:1 #F33AAE
                );
            }
            """
        )

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(54, 34, 54, 32)
        layout.setSpacing(16)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        source = QPixmap(str(self.logo_path))
        if not source.isNull():
            self.logo.setPixmap(
                source.scaled(
                    390,
                    245,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.logo.setFixedHeight(250)
        layout.addWidget(self.logo)

        title = QLabel("Starting Career Accelerator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 19pt; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Preparing your 90-day career plan.")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(5)
        layout.addWidget(self.progress)

        row = QHBoxLayout()
        self.status = QLabel("Starting application…")
        self.status.setObjectName("Status")
        self.step = QLabel("Step 1 of 6")
        self.step.setObjectName("Step")
        row.addWidget(self.status, 1)
        row.addWidget(self.step)
        layout.addLayout(row)

        footer = QLabel("No console window is required.")
        footer.setObjectName("Muted")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(footer)

    def update_stage(self, message: str, value: int, step: int) -> None:
        self.status.setText(str(message))
        self.progress.setValue(max(0, min(100, int(value))))
        self.step.setText(f"Step {max(1, step)} of 6")
        QApplication.processEvents()

    def show_centered(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(
                geometry.center().x() - self.width() // 2,
                geometry.center().y() - self.height() // 2,
            )
        self.show()
        self.raise_()
        QApplication.processEvents()
