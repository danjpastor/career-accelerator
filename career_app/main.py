from __future__ import annotations

import os
import random
import re
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QTimer, Signal
)
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFormLayout,
    QInputDialog,
    QBoxLayout, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton, QProgressBar,
    QScrollArea, QSizePolicy, QSlider, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)

from career_app import __version__
from career_app.database import (
    connect, ensure_default_state, factory_reset, save_setting, setting, state, update_state
)
from career_app.data.applied_exercises import (
    APPLIED_EXERCISES,
    CATEGORY_ORDER,
    exercise_number_for_label as applied_exercise_number_for_label,
    exercise_source as applied_exercise_source,
)
from career_app.data.duckdb_exercises import (
    DUCKDB_EXERCISES,
    exercise_number_for_label as duckdb_exercise_number_for_label,
    exercise_source,
)
from career_app.data.roadmap import (
    DATACAMP_TRACK, PROJECT_DIRS, PROJECT_NAMES, PROJECT_STAGES,
    SQL_COMPANION, WEEKLY_GUIDANCE
)
from career_app.services import (
    achievements,
    analytics,
    applied_workspace,
    coach,
    planner,
    duckdb_workspace,
    session_guard,
    sql_workspace,
    task_workspace,
    tracks,
)
from career_app.services import exercise_packs
from career_app.services.backup import create_backup, prune_backups_with_report
from career_app.services.migration import migrate
from career_app.services.publisher import publish
from career_app.theme import COLORS, stylesheet
from career_app.ui.duckdb_exercises import DuckDBExercisesWidget
from career_app.ui.course_ui import SqlCodeEditor
from career_app.ui.applied_labs import AppliedLabsWidget
from career_app.ui.exercise_packs import ExercisePacksWidget, ExerciseSuggestionPanel
from career_app.ui.task_workspace import TaskWorkspaceDialog
from career_app.ui.responsive import (
    ResponsiveScrollPage, apply_content_row_metrics,
    apply_inline_style_scale, clear_layout_positions, reflow_grid,
    set_box_direction,
)
from career_app.ui.widgets import (
    AreaChart, BadgeCard, BrandedBannerCard, Card, CircularTimer, Divider, FocusRow,
    FooterMetricBox, MetricRow, MiniSparkline, Ring, SectionHeader,
    SidebarMetricCard, SoftPanel, StatRow, TaskRow, make_card_scrollable
)

ROOT = Path(__file__).resolve().parents[1]

NAV = [
    ("🏠 Dashboard", 0),
    ("🚀 Adaptive Planner", 1),
    ("📚 Learning", 2),
    ("📁 Portfolio Workspace", 3),
    ("💻 SQL Companion", 4),
    ("⏱️ Study Session", 5),
    ("🎯 Job Readiness", 6),
    ("💼 Applications", 7),
    ("📝 Weekly Summary", 8),
    ("🚀 Publish & Git", 9),
    ("🗂️ Task Workspaces", 11),
    ("⚙️ Settings", 10),
]





class ButtonFeedbackFilter(QObject):
    """Adds tactile press/release animation to every QPushButton."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animations = {}

    def _effect(self, button):
        effect = button.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(button)
            effect.setOpacity(1.0)
            button.setGraphicsEffect(effect)
        return effect

    def _animate(self, button, target, duration):
        if not button.isEnabled():
            return

        effect = self._effect(button)
        key = id(button)

        previous = self._animations.pop(key, None)
        if previous is not None:
            previous.stop()
            previous.deleteLater()

        animation = QPropertyAnimation(
            effect,
            b"opacity",
            self,
        )
        animation.setDuration(duration)
        animation.setStartValue(effect.opacity())
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def cleanup():
            current = self._animations.get(key)
            if current is animation:
                self._animations.pop(key, None)

        animation.finished.connect(cleanup)
        self._animations[key] = animation
        animation.start()

    def eventFilter(self, watched, event):
        if isinstance(watched, QPushButton):
            if not watched.property("button_feedback_ready"):
                watched.setProperty(
                    "button_feedback_ready",
                    True,
                )
                watched.setCursor(Qt.PointingHandCursor)

            event_type = event.type()

            if event_type == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._animate(
                        watched,
                        0.72,
                        55,
                    )

            elif event_type == QEvent.MouseButtonRelease:
                target = (
                    0.94
                    if (
                        watched.property(
                            "workspace_open_button"
                        )
                        and watched.underMouse()
                    )
                    else 1.0
                )
                self._animate(
                    watched,
                    target,
                    115,
                )

            elif event_type == QEvent.Enter:
                if watched.property(
                    "workspace_open_button"
                ):
                    self._animate(
                        watched,
                        0.94,
                        95,
                    )

            elif event_type == QEvent.KeyPress:
                if event.key() in (
                    Qt.Key_Space,
                    Qt.Key_Return,
                    Qt.Key_Enter,
                ):
                    self._animate(
                        watched,
                        0.72,
                        55,
                    )

            elif event_type == QEvent.KeyRelease:
                if event.key() in (
                    Qt.Key_Space,
                    Qt.Key_Return,
                    Qt.Key_Enter,
                ):
                    self._animate(
                        watched,
                        1.0,
                        115,
                    )

            elif event_type in (
                QEvent.Leave,
                QEvent.FocusOut,
                QEvent.Hide,
            ):
                effect = watched.graphicsEffect()
                if (
                    isinstance(
                        effect,
                        QGraphicsOpacityEffect,
                    )
                    and effect.opacity() < 0.999
                ):
                    self._animate(
                        watched,
                        1.0,
                        90,
                    )

            elif event_type == QEvent.EnabledChange:
                effect = watched.graphicsEffect()
                if isinstance(
                    effect,
                    QGraphicsOpacityEffect,
                ):
                    effect.setOpacity(
                        1.0 if watched.isEnabled() else 0.62
                    )

        return super().eventFilter(watched, event)


class GradientButtonAnimator(QObject):
    """Gives primary action gradients a subtle, low-cost color drift.

    Only visible primary buttons are updated, and the animation pauses while
    the window is hidden or inactive.  Layout, fonts, padding, signals, and
    button behavior remain owned by the existing stylesheet and widgets.
    """

    PALETTE = (
        QColor("#FF4DB8"),
        QColor("#A85CFF"),
        QColor("#6D72FF"),
        QColor("#39B0FF"),
        QColor("#8A5CFF"),
        QColor("#FF6A9F"),
    )

    def __init__(self, root, parent=None):
        super().__init__(parent or root)
        self.root = root
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(90)
        self.timer.timeout.connect(self._advance)
        self.timer.start()

    @staticmethod
    def _mix(first, second, amount):
        amount = max(0.0, min(1.0, float(amount)))
        return QColor(
            round(first.red() + (second.red() - first.red()) * amount),
            round(first.green() + (second.green() - first.green()) * amount),
            round(first.blue() + (second.blue() - first.blue()) * amount),
        )

    def _sample(self, position):
        position = float(position) % 1.0
        scaled = position * len(self.PALETTE)
        index = int(scaled) % len(self.PALETTE)
        next_index = (index + 1) % len(self.PALETTE)
        return self._mix(
            self.PALETTE[index],
            self.PALETTE[next_index],
            scaled - int(scaled),
        )

    @staticmethod
    def _lighter(color, factor=118):
        return color.lighter(factor)

    @staticmethod
    def _darker(color, factor=132):
        return color.darker(factor)

    def _button_style(self):
        first = self._sample(self.phase)
        middle = self._sample(self.phase + 0.21)
        last = self._sample(self.phase + 0.47)
        hover_first = self._lighter(first, 116)
        hover_middle = self._lighter(middle, 112)
        hover_last = self._lighter(last, 114)
        pressed_first = self._darker(first, 138)
        pressed_middle = self._darker(middle, 142)
        pressed_last = self._darker(last, 136)

        return f"""
        QPushButton#Primary {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {first.name()},
                stop:0.52 {middle.name()},
                stop:1 {last.name()});
            border:1px solid {hover_middle.name()};
        }}
        QPushButton#Primary:hover {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {hover_first.name()},
                stop:0.52 {hover_middle.name()},
                stop:1 {hover_last.name()});
            border:1px solid #F0C8FF;
        }}
        QPushButton#Primary:pressed {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {pressed_first.name()},
                stop:0.52 {pressed_middle.name()},
                stop:1 {pressed_last.name()});
            border:1px solid #F3C5FF;
        }}
        QPushButton#Primary:disabled {{
            background:#0D1625;
            border:1px solid #1B293D;
        }}
        """

    def _advance(self):
        if not self.root.isVisible() or not self.root.isActiveWindow():
            return
        self.phase = (self.phase + 0.0085) % 1.0
        style = self._button_style()
        for button in self.root.findChildren(QPushButton):
            if button.objectName() != "Primary" or not button.isVisible():
                continue
            button.setStyleSheet(style)


class ResponsiveDashboardContent(QWidget):
    widthChanged = Signal(int)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.widthChanged.emit(event.size().width())


class CareerAccelerator(QMainWindow):
    DASHBOARD_WIDE_BREAKPOINT = 1120
    DASHBOARD_MEDIUM_BREAKPOINT = 840
    MINIMUM_WINDOW_WIDTH = 900
    MINIMUM_WINDOW_HEIGHT = 620

    def __init__(self):
        super().__init__()
        self.conn = connect()
        ensure_default_state(self.conn, date.today().isoformat())
        self.migration_result = migrate(self.conn, ROOT)
        planner.seed(self.conn)
        self.state = state(self.conn)
        planner.sync_google_course_progress(
            self.conn,
            self.state["google_course"],
        )
        tracks.sync_all(
            self.conn,
            self.state,
        )
        self.state = state(self.conn)

        self.elapsed_seconds = 0
        self.timer_state = "ready"
        self.growth_days = 14
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_timer)

        self.setWindowTitle(f"Data Career Accelerator v{__version__}")

        self.app_icon_path = (
            ROOT / "assets" / "career_accelerator.ico"
        )
        if self.app_icon_path.exists():
            app_icon = QIcon(str(self.app_icon_path))
            self.setWindowIcon(app_icon)
            QApplication.instance().setWindowIcon(app_icon)

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "DanielPastor.DataCareerAccelerator"
                )
            except Exception:
                pass

        self.resize(1536, 1020)
        self.setMinimumSize(
            self.MINIMUM_WINDOW_WIDTH,
            self.MINIMUM_WINDOW_HEIGHT,
        )
        self._ui_scale = 1.0
        try:
            interface_scale_percent = int(
                setting(self.conn, "interface_scale_percent", "100")
            )
        except (TypeError, ValueError):
            interface_scale_percent = 100
        interface_scale_percent = max(80, min(120, interface_scale_percent))
        self._content_scale = interface_scale_percent / 100.0
        self._style_signature = None
        self._responsive_update_pending = False
        self._apply_interface_styles()

        self.button_feedback = ButtonFeedbackFilter(self)
        QApplication.instance().installEventFilter(
            self.button_feedback
        )

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = self.build_sidebar()
        outer.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        builders = [
            self.dashboard_page,
            self.planner_page,
            self.learning_page,
            self.portfolio_page,
            self.sql_page,
            self.study_page,
            self.readiness_page,
            self.applications_page,
            self.review_page,
            self.publish_page,
            self.settings_page,
            self.task_workspaces_page,
        ]
        for builder in builders:
            self.stack.addWidget(builder())

        self.gradient_button_animator = GradientButtonAnimator(self, self)

        self.setup_shortcuts()
        self.update_timer_visuals()
        self.refresh_all()
        QTimer.singleShot(0, self._apply_responsive_shell)

        track_health = tracks.health_report(
            self.conn,
            self.state,
        )
        if (
            not track_health["healthy"]
            and hasattr(
                self,
                "settings_status",
            )
        ):
            self.settings_status.setText(
                "Track engine repaired with warnings: "
                + "; ".join(
                    track_health["issues"]
                )
            )
        self.update_time_based_header()

        self.greeting_timer = QTimer(self)
        self.greeting_timer.timeout.connect(self.update_time_based_header)
        self.greeting_timer.start(60_000)

        self.update_motivational_text()
        self.motivation_timer = QTimer(self)
        self.motivation_timer.timeout.connect(self.update_motivational_text)
        self.motivation_timer.start(15 * 60_000)

        autosave_ms = int(setting(self.conn, "autosave_minutes", "5")) * 60 * 1000
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(max(60000, autosave_ms))

    # ---------- Shell ----------
    def build_sidebar(self):
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setMinimumWidth(196)
        side.setMaximumWidth(266)
        side.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )

        shell = QVBoxLayout(side)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll.setStyleSheet(
            "QScrollArea {background:transparent;border:none;}"
        )
        self.sidebar_scroll = scroll

        content = QWidget()
        content.setMinimumWidth(0)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(4)
        self.sidebar_content_layout = layout

        # Use the approved horizontal Data Career Accelerator lockup as one
        # locked asset. This prevents the icon, wordmark, spacing, and gradient
        # from drifting at different window sizes while keeping the sidebar's
        # existing responsive layout rules intact.
        logo = QLabel()
        logo.setObjectName("BrandLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        logo.setMinimumWidth(0)
        logo_path = ROOT / "assets" / "data_career_accelerator_horizontal.png"
        self._sidebar_logo_source = QPixmap(str(logo_path))
        self._sidebar_brand_height = 66
        self.sidebar_logo = logo
        layout.addWidget(logo)
        self._update_sidebar_brand_logo()

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color:{COLORS['border']};")
        self.sidebar_divider = divider
        layout.addWidget(divider)

        group = QButtonGroup(self)
        group.setExclusive(True)
        self.nav_buttons = []

        # Navigation receives the flexible portion of the sidebar. The links
        # expand evenly between the logo and the fixed progress cards instead
        # of leaving a large unused vertical band above Current Streak.
        nav_host = QWidget()
        nav_host.setMinimumHeight(0)
        nav_host.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)
        self.sidebar_nav_host = nav_host
        self.sidebar_nav_layout = nav_layout

        for text, index in NAV:
            button = QPushButton(text)
            button.setObjectName("Nav")
            button.setMinimumHeight(34)
            button.setMaximumHeight(52)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, target=index: self.navigate(target)
            )
            group.addButton(button)
            nav_layout.addWidget(button, 1)
            self.nav_buttons.append(button)
            if index == 0:
                button.setChecked(True)

        layout.addWidget(nav_host, 1)

        streak_card = QFrame()
        streak_card.setObjectName("SidebarCard")
        streak_card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.sidebar_streak_card = streak_card
        streak_layout = QVBoxLayout(streak_card)
        streak_layout.setContentsMargins(16, 14, 16, 14)
        streak_layout.setSpacing(6)
        self.sidebar_streak_layout = streak_layout

        streak_title = QLabel("CURRENT STREAK")
        streak_title.setObjectName("Tiny")
        self.sidebar_streak_title = streak_title
        streak_layout.addWidget(streak_title)

        streak_value_row = QHBoxLayout()
        flame = QLabel("🔥")
        flame.setStyleSheet("font-size:24pt;")
        self.sidebar_flame = flame
        streak_value_row.addWidget(flame)

        self.side_streak_value = QLabel("0")
        self.side_streak_value.setStyleSheet("font-size:25pt;font-weight:700;")
        streak_value_row.addWidget(self.side_streak_value)

        days_label = QLabel("days")
        days_label.setObjectName("Muted")
        self.sidebar_days_label = days_label
        streak_value_row.addWidget(days_label)
        streak_value_row.addStretch()
        streak_layout.addLayout(streak_value_row)

        self.streak_week = QLabel("○  ○  ○  ○  ○  ○  ○")
        self.streak_week.setWordWrap(True)
        self.streak_week.setStyleSheet(
            f"color:{COLORS['purple']};font-size:13pt;"
        )
        streak_layout.addWidget(self.streak_week)

        self.best_streak_label = QLabel("Best Streak: 0 days")
        self.best_streak_label.setObjectName("Muted")
        self.best_streak_label.setWordWrap(True)
        streak_layout.addWidget(self.best_streak_label)
        layout.addWidget(streak_card)

        time_card = QFrame()
        time_card.setObjectName("SidebarCard")
        time_card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.sidebar_time_card = time_card
        time_layout = QVBoxLayout(time_card)
        time_layout.setContentsMargins(16, 14, 16, 14)
        time_layout.setSpacing(6)
        self.sidebar_time_layout = time_layout

        study_title = QLabel("⏱️  TOTAL STUDY TIME")
        study_title.setWordWrap(True)
        study_title.setStyleSheet(
            f"font-weight:700;color:{COLORS['cyan']};"
        )
        self.sidebar_study_title = study_title
        time_layout.addWidget(study_title)

        self.side_hours_value = QLabel("0h")
        self.side_hours_value.setStyleSheet("font-size:22pt;font-weight:700;")
        time_layout.addWidget(self.side_hours_value)

        this_week = QLabel("This Week")
        this_week.setObjectName("Muted")
        self.sidebar_this_week = this_week
        time_layout.addWidget(this_week)

        self.sidebar_goal = QProgressBar()
        self.sidebar_goal.setRange(0, 100)
        self.sidebar_goal.setTextVisible(False)
        time_layout.addWidget(self.sidebar_goal)

        goal_row = QHBoxLayout()
        self.sidebar_goal_label = QLabel("Goal: 0h")
        self.sidebar_goal_label.setObjectName("Muted")
        goal_row.addWidget(self.sidebar_goal_label)
        goal_row.addStretch()
        self.sidebar_goal_percent = QLabel("0%")
        self.sidebar_goal_percent.setObjectName("Muted")
        goal_row.addWidget(self.sidebar_goal_percent)
        time_layout.addLayout(goal_row)
        layout.addWidget(time_card)

        footer = QLabel("Keep building your future. 🚀")
        footer.setObjectName("Muted")
        footer.setWordWrap(True)
        self.sidebar_footer = footer
        layout.addWidget(footer)

        scroll.setWidget(content)
        shell.addWidget(scroll)
        return side

    def navigate(self, index):
        self.stack.setCurrentIndex(index)
        for button in self.nav_buttons:
            button.setChecked(False)
        label_map = {
            0: "Dashboard",
            1: "Adaptive Planner",
            2: "Learning",
            3: "Portfolio Workspace",
            4: "SQL Companion",
            5: "Study Session",
            6: "Job Readiness",
            7: "Applications",
            8: "Weekly Summary",
            9: "Publish & Git",
            10: "Settings",
            11: "Task Workspaces",
        }
        target = label_map.get(index)
        if target:
            for button in self.nav_buttons:
                if target in button.text():
                    button.setChecked(True)
                    break

    def page(self, title, subtitle=None):
        page = ResponsiveScrollPage(
            title,
            subtitle,
            f"📅 {datetime.now():%A, %B %d, %Y}",
        )
        return page, page.content_layout

    def _register_page_responsive(self, page, handler):
        if isinstance(page, ResponsiveScrollPage):
            page.add_responsive_handler(handler)
            QTimer.singleShot(
                0,
                lambda: handler(max(0, page.viewport().width())),
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._responsive_update_pending:
            self._responsive_update_pending = True
            QTimer.singleShot(25, self._apply_responsive_shell)

    def _apply_responsive_shell(self):
        self._responsive_update_pending = False
        width = max(self.width(), self.MINIMUM_WINDOW_WIDTH)
        height = max(self.height(), self.MINIMUM_WINDOW_HEIGHT)
        raw_scale = min(width / 1536.0, height / 1020.0)
        scale = max(0.78, min(1.08, raw_scale))
        scale = round(scale * 20) / 20

        if width < 1000:
            sidebar_width = 180
        elif width < 1120:
            sidebar_width = 196
        elif width < 1375:
            sidebar_width = 224
        else:
            sidebar_width = 266
        if hasattr(self, "sidebar"):
            self.sidebar.setMinimumWidth(sidebar_width)
            self.sidebar.setMaximumWidth(sidebar_width)
            self._update_sidebar_brand_logo()

        if abs(scale - self._ui_scale) >= 0.01:
            self._ui_scale = scale
        self._apply_interface_styles()
        if hasattr(self, "sidebar_content_layout"):
            self._apply_sidebar_density(height)

        responsive_painted_widgets = [
            *self.findChildren(Ring),
            *self.findChildren(CircularTimer),
        ]
        for widget in responsive_painted_widgets:
            widget.set_ui_scale(scale)

        # Custom text rows recalculate their own minimum heights from the live
        # font metrics.  Cards keep the same responsive geometry; only their
        # internal rows receive enough vertical room for the selected scale.
        for widget in self.findChildren(QWidget):
            setter = getattr(widget, "set_interface_scale", None)
            if callable(setter):
                setter(self._content_scale)

        if hasattr(self, "dashboard_scroll"):
            self.update_dashboard_layout(
                max(0, self.dashboard_scroll.viewport().width()),
                max(0, self.dashboard_scroll.viewport().height()),
            )

        # Density handlers update several inline styles after the first pass.
        # Scale those fresh styles once more without changing card geometry.
        apply_inline_style_scale(
            self,
            self._ui_scale,
            self._content_scale,
        )
        apply_content_row_metrics(
            self,
            self._ui_scale,
            self._content_scale,
        )
        self._update_growth_period_combo_width()

    def _apply_interface_styles(self):
        """Apply responsive geometry plus the user-selected content scale."""
        content_scale = max(0.80, min(1.20, float(self._content_scale)))
        signature = (round(self._ui_scale, 3), round(content_scale, 3))
        if signature != self._style_signature:
            self.setStyleSheet(stylesheet(self._ui_scale, content_scale))
            self._style_signature = signature
        apply_inline_style_scale(self, self._ui_scale, content_scale)
        self._update_growth_period_combo_width()

    def _update_growth_period_combo_width(self):
        """Keep the Dashboard period selector readable at every text scale."""
        combo = getattr(self, "growth_period_combo", None)
        if combo is None:
            return
        labels = [combo.itemText(index) for index in range(combo.count())]
        widest = max(
            (combo.fontMetrics().horizontalAdvance(label) for label in labels),
            default=0,
        )
        # Reserve room for both internal padding and the separate arrow button.
        chrome = round(66 * self._ui_scale * self._content_scale)
        target = max(108, min(172, widest + chrome))
        combo.setMinimumWidth(target)
        combo.setMaximumWidth(max(target, min(184, target + 12)))
        combo.updateGeometry()

    def change_interface_scale(self, value):
        """Preview and persist text/control scaling without resizing cards."""
        value = max(80, min(120, int(value)))
        self._content_scale = value / 100.0
        if hasattr(self, "interface_scale_value"):
            self.interface_scale_value.setText(f"{value}%")
        save_setting(self.conn, "interface_scale_percent", value)
        self._style_signature = None
        self._apply_interface_styles()
        # Re-run responsive sizing after the font metrics change. Card geometry
        # still comes from the window breakpoints; only their contents reflow.
        QTimer.singleShot(0, self._apply_responsive_shell)

    def _update_sidebar_brand_logo(self):
        """Scale the approved horizontal brand lockup inside the live sidebar."""
        label = getattr(self, "sidebar_logo", None)
        source = getattr(self, "_sidebar_logo_source", None)
        if label is None or source is None or source.isNull():
            return
        margins = self.sidebar_content_layout.contentsMargins()
        sidebar_width = self.sidebar.maximumWidth() if hasattr(self, "sidebar") else 224
        available_width = max(96, sidebar_width - margins.left() - margins.right())
        target_height = max(30, int(getattr(self, "_sidebar_brand_height", 58)))
        scaled = source.scaled(
            available_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setPixmap(scaled)
        label.setFixedHeight(target_height)
        label.setToolTip("Data Career Accelerator")
        label.updateGeometry()

    def _apply_sidebar_density(self, height):
        """Keep the complete navigation sidebar visible at supported heights."""
        height = max(0, int(height))
        if height >= 900:
            density = "comfortable"
        elif height >= 700:
            density = "compact"
        else:
            density = "ultra"
        if getattr(self, "sidebar_density", None) == density:
            return
        self.sidebar_density = density

        values = {
            "comfortable": {
                "margins": (16, 14, 16, 12),
                "spacing": 4,
                "nav_height": (34, 52),
                "nav_spacing": 4,
                "brand_height": 66,
                "card_height": 0,
                "card_margins": (16, 14, 16, 14),
                "card_spacing": 6,
                "flame": 24,
                "streak_value": 25,
                "hours": 22,
                "week": 13,
                "footer_visible": True,
            },
            "compact": {
                "margins": (12, 9, 12, 8),
                "spacing": 2,
                "nav_height": (27, 42),
                "nav_spacing": 2,
                "brand_height": 56,
                "card_height": 101,
                "card_margins": (11, 8, 11, 8),
                "card_spacing": 3,
                "flame": 19,
                "streak_value": 21,
                "hours": 18,
                "week": 10,
                "footer_visible": True,
            },
            "ultra": {
                "margins": (10, 6, 10, 5),
                "spacing": 1,
                "nav_height": (21, 30),
                "nav_spacing": 1,
                "brand_height": 44,
                "card_height": 80,
                "card_margins": (9, 5, 9, 5),
                "card_spacing": 1,
                "flame": 16,
                "streak_value": 18,
                "hours": 16,
                "week": 8,
                "footer_visible": True,
            },
        }[density]

        self.sidebar_content_layout.setContentsMargins(*values["margins"])
        self.sidebar_content_layout.setSpacing(values["spacing"])
        self.sidebar_nav_layout.setSpacing(values["nav_spacing"])
        for button in self.nav_buttons:
            button.setMinimumHeight(values["nav_height"][0])
            button.setMaximumHeight(values["nav_height"][1])
        self._sidebar_brand_height = values["brand_height"]
        self._update_sidebar_brand_logo()
        self.sidebar_streak_layout.setContentsMargins(*values["card_margins"])
        self.sidebar_streak_layout.setSpacing(values["card_spacing"])
        self.sidebar_time_layout.setContentsMargins(*values["card_margins"])
        self.sidebar_time_layout.setSpacing(values["card_spacing"])
        self.sidebar_flame.setStyleSheet(f"font-size:{values['flame']}pt;")
        self.side_streak_value.setStyleSheet(
            f"font-size:{values['streak_value']}pt;font-weight:700;"
        )
        self.side_hours_value.setStyleSheet(
            f"font-size:{values['hours']}pt;font-weight:700;"
        )
        self.streak_week.setStyleSheet(
            f"color:{COLORS['purple']};font-size:{values['week']}pt;"
        )
        self.sidebar_footer.setVisible(values["footer_visible"])

        card_height = values["card_height"]
        for card in (self.sidebar_streak_card, self.sidebar_time_card):
            if card_height:
                card.setMinimumHeight(card_height)
                card.setMaximumHeight(card_height)
            else:
                card.setMinimumHeight(0)
                card.setMaximumHeight(16777215)
        self.sidebar_scroll.widget().updateGeometry()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    # ---------- Dashboard ----------
    def dashboard_page(self):
        page = ResponsiveScrollPage()
        page.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )
        self.dashboard_scroll = page
        # The Dashboard is a true single-screen overview. Long-form pages may
        # scroll, but the front page must always resize to its viewport.
        page.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        page.content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        root = page.content_layout
        root.setContentsMargins(24, 16, 24, 14)
        root.setSpacing(10)
        root.setSizeConstraint(QLayout.SetDefaultConstraint)

        self.dashboard_content = page.content
        self.dashboard_root_layout = root
        self.dashboard_layout_mode = None
        self.dashboard_density = None

        # ---------- Header ----------
        self.dashboard_header_section = QWidget()
        self.dashboard_header_section.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        header = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.dashboard_header_section)
        self.dashboard_header_layout = header
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        left_header = QVBoxLayout()
        left_header.setSpacing(3)

        self.dashboard_hero = QLabel("")
        self.dashboard_hero.setObjectName("Hero")
        self.dashboard_hero.setWordWrap(False)
        self.dashboard_hero.setMinimumWidth(0)
        self.dashboard_hero.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.Fixed,
        )
        left_header.addWidget(self.dashboard_hero)

        self.dashboard_quote = QLabel("")
        self.dashboard_quote.setObjectName("Muted")
        self.dashboard_quote.setWordWrap(True)
        self.dashboard_quote.setMinimumWidth(0)
        self.dashboard_quote.setStyleSheet(
            "font-style:italic;color:#b6bfd0;"
        )
        left_header.addWidget(self.dashboard_quote)

        header.addLayout(left_header)
        header.addStretch()
        # BEGIN EXERCISE PACKS
        self.exercise_suggestion_panel = ExerciseSuggestionPanel(
            self.open_exercise_pack, self
        )
        header.addWidget(
            self.exercise_suggestion_panel, 0, Qt.AlignVCenter
        )
        # END EXERCISE PACKS

        right_header = QVBoxLayout()
        right_header.setSpacing(5)

        self.dashboard_program_meta = QLabel("")
        self.dashboard_program_meta.setAlignment(Qt.AlignRight)
        self.dashboard_program_meta.setStyleSheet(
            "font-weight:600;"
        )
        right_header.addWidget(self.dashboard_program_meta)

        self.dashboard_date = QLabel("")
        self.dashboard_date.setObjectName("Muted")
        self.dashboard_date.setAlignment(Qt.AlignRight)
        right_header.addWidget(self.dashboard_date)

        header.addLayout(right_header)

        # ---------- Progress metrics ----------
        self.dashboard_metrics_section = QWidget()
        self.dashboard_metrics_section.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.dashboard_metrics_grid = QGridLayout(
            self.dashboard_metrics_section
        )
        self.dashboard_metrics_grid.setContentsMargins(0, 0, 0, 0)
        self.dashboard_metrics_grid.setHorizontalSpacing(10)
        self.dashboard_metrics_grid.setVerticalSpacing(10)

        self.rings = [
            Ring("Sprint Progress", COLORS["purple"]),
            Ring("Google Certificate", COLORS["blue"]),
            Ring("SQL Progress", COLORS["green"]),
            Ring("Portfolio Progress", COLORS["orange"]),
            Ring("Weekly Goal", COLORS["gold"]),
        ]
        self.dashboard_metric_cards = []

        for ring in self.rings:
            card = Card()
            card.setMinimumHeight(96)
            card.setMaximumHeight(16777215)
            card.layout.setContentsMargins(8, 7, 8, 7)
            card.layout.setSpacing(0)
            card.layout.addWidget(
                ring,
                0,
                Qt.AlignVCenter,
            )
            self.dashboard_metric_cards.append(card)

        # ---------- Priority section ----------
        self.dashboard_primary_section = QWidget()
        self.dashboard_primary_section.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.dashboard_primary_grid = QGridLayout(
            self.dashboard_primary_section
        )
        self.dashboard_primary_grid.setContentsMargins(0, 0, 0, 0)
        self.dashboard_primary_grid.setHorizontalSpacing(10)
        self.dashboard_primary_grid.setVerticalSpacing(10)
        self.dashboard_primary_grid.setRowStretch(0, 0)

        self.dashboard_focus_card = Card()
        self.dashboard_focus_card.setMinimumHeight(248)
        self.dashboard_focus_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )
        self.dashboard_focus_card.layout.setSpacing(6)
        self.dashboard_focus_header = SectionHeader(
            "🎯",
            "Today's Focus",
            "Priority-driven plan grounded in this week's roadmap",
        )
        self.dashboard_focus_card.layout.addWidget(
            self.dashboard_focus_header
        )
        self.dashboard_extra_focus_candidate = None
        self.dashboard_tomorrow_preview = []

        self.focus_layout = QVBoxLayout()
        self.focus_layout.setSpacing(0)
        self.dashboard_focus_card.layout.addLayout(
            self.focus_layout
        )
        self.dashboard_focus_card.layout.addStretch(1)

        self.focus_footer_divider = Divider()
        self.dashboard_focus_card.layout.addWidget(
            self.focus_footer_divider
        )

        self.focus_footer_host = QWidget()
        self.focus_footer_host.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )
        focus_footer = QHBoxLayout(
            self.focus_footer_host
        )
        focus_footer.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        focus_footer.setSpacing(10)

        self.focus_total_time = FooterMetricBox(
            "⏱️",
            "Total Estimated Time",
            "0h 0m",
        )
        self.focus_task_count = FooterMetricBox(
            "✅",
            "Tasks",
            "0",
        )

        focus_footer.addWidget(
            self.focus_total_time,
            1,
        )
        focus_footer.addWidget(
            self.focus_task_count,
            1,
        )
        self.dashboard_focus_card.layout.addWidget(
            self.focus_footer_host
        )

        self.dashboard_tasks_card = Card()
        self.dashboard_tasks_card.setMinimumHeight(248)
        self.dashboard_tasks_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )
        self.dashboard_tasks_card.layout.setSpacing(6)

        task_header = SectionHeader(
            "📋",
            "Next Tasks",
            "Up next from your sprint",
            "View All",
        )
        task_header.action_button.clicked.connect(
            lambda: self.navigate(1)
        )
        self.dashboard_tasks_card.layout.addWidget(task_header)

        self.dashboard_tasks_layout = QVBoxLayout()
        self.dashboard_tasks_layout.setSpacing(0)
        self.dashboard_tasks_card.layout.addLayout(
            self.dashboard_tasks_layout
        )
        self.dashboard_tasks_card.layout.addStretch()

        self.dashboard_timer_card = Card()
        self.dashboard_timer_card.setMinimumHeight(248)
        self.dashboard_timer_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )
        self.dashboard_timer_card.layout.setSpacing(6)
        self.dashboard_timer_card.layout.addWidget(
            SectionHeader("⏱️", "Study Session")
        )

        self.dashboard_timer_stage = QWidget()
        timer_stage = self.dashboard_timer_stage
        timer_stage.setMinimumHeight(118)
        timer_stage.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )
        timer_stage_layout = QVBoxLayout(timer_stage)
        timer_stage_layout.setContentsMargins(0, 0, 0, 0)
        timer_stage_layout.setSpacing(0)
        timer_stage_layout.setAlignment(
            Qt.AlignTop | Qt.AlignHCenter
        )

        self.circular_timer = CircularTimer()
        timer_stage_layout.addWidget(
            self.circular_timer,
            0,
            Qt.AlignTop | Qt.AlignHCenter,
        )
        self.dashboard_timer_card.layout.addWidget(timer_stage)

        self.dashboard_start_button = QPushButton(
            "▶  Start Study Session"
        )
        self.dashboard_start_button.setObjectName("Primary")
        self.dashboard_start_button.clicked.connect(
            self.start_study_timer
        )
        self.dashboard_timer_card.layout.addWidget(
            self.dashboard_start_button
        )

        self.dashboard_timer_controls = QHBoxLayout()
        timer_controls = self.dashboard_timer_controls
        timer_controls.setSpacing(7)

        pause = QPushButton("⏸️ Pause")
        pause.setObjectName("Secondary")
        pause.clicked.connect(self.pause_study_timer)

        reset = QPushButton("🔄 Reset")
        reset.setObjectName("Secondary")
        reset.clicked.connect(self.confirm_reset_timer)

        log = QPushButton("📝 Log")
        log.setObjectName("Secondary")
        log.clicked.connect(self.transfer_timer)

        timer_controls.addWidget(pause, 1)
        timer_controls.addWidget(reset, 1)
        timer_controls.addWidget(log, 1)
        self.dashboard_timer_card.layout.addLayout(timer_controls)

        # ---------- Analytics section ----------
        self.dashboard_secondary_section = QWidget()
        self.dashboard_secondary_section.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.dashboard_secondary_grid = QGridLayout(
            self.dashboard_secondary_section
        )
        self.dashboard_secondary_grid.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.dashboard_secondary_grid.setHorizontalSpacing(10)
        self.dashboard_secondary_grid.setVerticalSpacing(10)

        self.dashboard_growth_card = Card()
        self.dashboard_growth_card.setMinimumHeight(190)
        self.dashboard_growth_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )

        growth_header = QHBoxLayout()
        growth_header.setSpacing(8)
        growth_header.addWidget(
            SectionHeader(
                "📈",
                "Growth Over Time",
                "Hours studied per day",
            ),
            1,
        )

        self.growth_period_combo = QComboBox()
        self.growth_period_combo.addItems(
            ["7 Days", "14 Days", "30 Days", "90 Days"]
        )
        self.growth_period_combo.setCurrentText("14 Days")
        self.growth_period_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.growth_period_combo.setMinimumWidth(108)
        self.growth_period_combo.setMaximumWidth(184)
        growth_header.addWidget(
            self.growth_period_combo,
            0,
            Qt.AlignRight | Qt.AlignTop,
        )
        self.dashboard_growth_card.layout.addLayout(growth_header)

        self.growth_chart = AreaChart()
        self.dashboard_growth_card.layout.addWidget(
            self.growth_chart
        )
        self.growth_period_combo.currentTextChanged.connect(
            self.change_growth_period
        )

        self.dashboard_achievement_card = Card()
        self.dashboard_achievement_card.setMinimumHeight(190)
        self.dashboard_achievement_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )
        self.dashboard_achievement_card.layout.setSpacing(10)

        achievement_header = SectionHeader(
            "🏅",
            "Achievements",
            "",
            "View All",
        )
        achievement_header.action_button.clicked.connect(
            self.show_all_achievements
        )
        self.dashboard_achievement_card.layout.addWidget(
            achievement_header
        )

        self.badge_layout = QHBoxLayout()
        self.badge_layout.setSpacing(8)
        self.badge_layout.setAlignment(Qt.AlignTop)
        self.dashboard_achievement_card.layout.addLayout(
            self.badge_layout,
            1,
        )

        self.dashboard_summary_card = Card()
        self.dashboard_summary_card.setMinimumHeight(190)
        self.dashboard_summary_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )

        summary_header = QHBoxLayout()
        summary_header.setSpacing(8)
        summary_header.addWidget(
            SectionHeader("📊", "Weekly Summary"),
            1,
        )

        self.summary_sparkline = MiniSparkline()
        summary_header.addWidget(
            self.summary_sparkline,
            0,
            Qt.AlignRight | Qt.AlignTop,
        )
        self.dashboard_summary_card.layout.addLayout(summary_header)

        self.summary_period = QLabel("")
        self.summary_period.setObjectName("Muted")
        self.dashboard_summary_card.layout.addWidget(
            self.summary_period
        )

        self.summary_rows = QVBoxLayout()
        self.summary_rows.setSpacing(0)
        self.dashboard_summary_card.layout.addLayout(
            self.summary_rows
        )

        self.dashboard_summary_button = QPushButton("View Full Summary")
        summary_button = self.dashboard_summary_button
        summary_button.setObjectName("Secondary")
        summary_button.clicked.connect(lambda: self.navigate(8))
        self.dashboard_summary_card.layout.addWidget(
            summary_button
        )

        # ---------- Encouragement and Mission Control ----------
        self.dashboard_footer_section = QWidget()
        self.dashboard_footer_section.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.dashboard_footer_grid = QGridLayout(
            self.dashboard_footer_section
        )
        self.dashboard_footer_grid.setContentsMargins(0, 0, 0, 0)
        self.dashboard_footer_grid.setHorizontalSpacing(10)
        self.dashboard_footer_grid.setVerticalSpacing(10)

        self.encouragement_card = BrandedBannerCard(
            ROOT / "assets" / "dashboard_encouragement_rocket.png",
            art_opacity=0.92,
        )
        self.encouragement_card.setMinimumHeight(125)
        self.encouragement_card.layout.setContentsMargins(
            16,
            12,
            16,
            12,
        )

        encouragement_row = QHBoxLayout()
        encouragement_row.setContentsMargins(0, 0, 0, 0)
        encouragement_row.setSpacing(12)
        encouragement_row.setAlignment(Qt.AlignVCenter)

        star = QLabel("⭐")
        star.setStyleSheet("font-size:22pt;")
        star.setFixedWidth(34)
        star.setAlignment(Qt.AlignCenter)
        encouragement_row.addWidget(
            star,
            0,
            Qt.AlignVCenter,
        )

        encouragement_text_host = QWidget()
        encouragement_text_host.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )
        encouragement_text_host.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        encouragement_text_layout = QVBoxLayout(
            encouragement_text_host
        )
        encouragement_text_layout.setContentsMargins(0, 0, 0, 0)
        encouragement_text_layout.setSpacing(2)
        encouragement_text_layout.setAlignment(Qt.AlignVCenter)

        self.footer_message = QLabel("")
        self.footer_message.setStyleSheet("font-weight:700;")
        self.footer_message.setWordWrap(True)
        self.footer_message.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.footer_message.setMinimumHeight(0)
        self.footer_message.setMaximumHeight(16777215)
        encouragement_text_layout.addWidget(
            self.footer_message
        )

        self.footer_subtitle = QLabel("")
        self.footer_subtitle.setObjectName("Muted")
        self.footer_subtitle.setWordWrap(True)
        self.footer_subtitle.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.footer_subtitle.setMinimumHeight(0)
        self.footer_subtitle.setMaximumHeight(16777215)
        encouragement_text_layout.addWidget(
            self.footer_subtitle
        )

        encouragement_row.addWidget(
            encouragement_text_host,
            1,
            Qt.AlignVCenter,
        )
        self.encouragement_card.layout.addLayout(encouragement_row)

        self.dashboard_mission_card = Card()
        self.dashboard_mission_card.setMinimumHeight(125)
        self.dashboard_mission_card.layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )
        self.dashboard_mission_card.layout.setSpacing(4)
        self.dashboard_mission_card.layout.addWidget(
            SectionHeader(
                "🚀",
                "Mission Control",
                "Your job-readiness journey at a glance",
            )
        )

        mission_score_row = QHBoxLayout()
        mission_score_row.setSpacing(8)

        mission_score_label = QLabel("Job Readiness")
        mission_score_label.setStyleSheet("font-weight:700;")
        mission_score_row.addWidget(mission_score_label)
        mission_score_row.addStretch()

        self.dashboard_mission_percent = QLabel("0%")
        self.dashboard_mission_percent.setStyleSheet(
            f"font-size:13pt;font-weight:700;"
            f"color:{COLORS['purple']};"
        )
        mission_score_row.addWidget(
            self.dashboard_mission_percent
        )
        self.dashboard_mission_card.layout.addLayout(
            mission_score_row
        )

        self.dashboard_mission_progress = QProgressBar()
        self.dashboard_mission_progress.setRange(0, 100)
        self.dashboard_mission_progress.setTextVisible(False)
        self.dashboard_mission_card.layout.addWidget(
            self.dashboard_mission_progress
        )

        self.dashboard_mission_detail = QLabel("")
        self.dashboard_mission_detail.setObjectName("Muted")
        self.dashboard_mission_detail.setWordWrap(True)
        self.dashboard_mission_detail.setMinimumHeight(0)
        self.dashboard_mission_detail.setMaximumHeight(16777215)
        self.dashboard_mission_card.layout.addWidget(
            self.dashboard_mission_detail
        )

        self.dashboard_mission_actions = QGridLayout()
        self.dashboard_mission_actions.setHorizontalSpacing(8)
        self.dashboard_mission_actions.setVerticalSpacing(6)

        self.dashboard_highest_impact_button = QPushButton(
            "▶ Continue Highest-Impact Task"
        )
        self.dashboard_highest_impact_button.setObjectName(
            "Primary"
        )
        self.dashboard_highest_impact_button.setMinimumHeight(32)
        self.dashboard_highest_impact_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.dashboard_highest_impact_button.clicked.connect(
            self.continue_highest_impact
        )

        self.dashboard_view_readiness_button = QPushButton(
            "View Job Readiness →"
        )
        self.dashboard_view_readiness_button.setObjectName(
            "Secondary"
        )
        self.dashboard_view_readiness_button.setMinimumHeight(32)
        self.dashboard_view_readiness_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.dashboard_view_readiness_button.clicked.connect(
            lambda: self.navigate(6)
        )

        self.dashboard_mission_card.layout.addLayout(
            self.dashboard_mission_actions
        )

        # Compact mode moves the two footer cards beside the priority cards.
        self.dashboard_compact_footer_stack = QWidget()
        self.dashboard_compact_footer_layout = QVBoxLayout(
            self.dashboard_compact_footer_stack
        )
        self.dashboard_compact_footer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.dashboard_compact_footer_layout.setSpacing(10)

        # Initial section order; update_dashboard_layout will reflow it.
        root.addWidget(self.dashboard_header_section)
        root.addWidget(self.dashboard_metrics_section)
        root.addWidget(self.dashboard_primary_section)
        root.addWidget(self.dashboard_secondary_section)
        root.addWidget(self.dashboard_footer_section)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Dashboard actions use compact vertical padding controlled by the
        # theme. This keeps labels vertically centered even when the no-scroll
        # density modes reduce card heights.
        for dashboard_button in (
            self.dashboard_start_button,
            pause,
            reset,
            log,
            self.dashboard_summary_button,
            self.dashboard_highest_impact_button,
            self.dashboard_view_readiness_button,
        ):
            dashboard_button.setProperty("dashboardAction", True)

        page.add_responsive_handler(self.update_dashboard_layout)
        page.heightChanged.connect(
            lambda height: self.update_dashboard_layout(
                max(0, page.viewport().width()),
                height,
            )
        )
        QTimer.singleShot(
            0,
            lambda: self.update_dashboard_layout(
                max(0, page.viewport().width())
            ),
        )
        return page

    def _take_layout_items(self, layout):
        # Grid stretch factors survive when widgets are removed. Reset them so
        # moving from a wide dashboard to a compact one cannot leave invisible
        # empty columns that squeeze the visible cards.
        if isinstance(layout, QGridLayout):
            for column in range(max(layout.columnCount(), 8)):
                layout.setColumnStretch(column, 0)
                layout.setColumnMinimumWidth(column, 0)
            for row in range(max(layout.rowCount(), 8)):
                layout.setRowStretch(row, 0)
                layout.setRowMinimumHeight(row, 0)
        while layout.count():
            layout.takeAt(0)

    def _set_dashboard_section_order(self, widgets):
        sections = [
            self.dashboard_header_section,
            self.dashboard_metrics_section,
            self.dashboard_primary_section,
            self.dashboard_secondary_section,
            self.dashboard_footer_section,
        ]
        for section in sections:
            self.dashboard_root_layout.removeWidget(section)

        for section in widgets:
            self.dashboard_root_layout.addWidget(section)

    def _layout_mission_actions(self, compact):
        self._take_layout_items(self.dashboard_mission_actions)

        if compact:
            self.dashboard_mission_actions.addWidget(
                self.dashboard_highest_impact_button,
                0,
                0,
                1,
                2,
            )
            self.dashboard_mission_actions.addWidget(
                self.dashboard_view_readiness_button,
                1,
                0,
                1,
                2,
            )
        else:
            self.dashboard_mission_actions.addWidget(
                self.dashboard_highest_impact_button,
                0,
                0,
            )
            self.dashboard_mission_actions.addWidget(
                self.dashboard_view_readiness_button,
                0,
                1,
            )
            self.dashboard_mission_actions.setColumnStretch(0, 3)
            self.dashboard_mission_actions.setColumnStretch(1, 2)

    @staticmethod
    def _set_dashboard_card_height(card, height):
        height = max(1, int(height))
        card.setMinimumHeight(height)
        card.setMaximumHeight(height)

    @staticmethod
    def _set_dashboard_section_height(section, height):
        """Keep a dashboard row wrapped tightly around its fixed-height cards.

        A QGridLayout expands its host widget when the surrounding page has
        spare height. Because the cards themselves have fixed heights, Qt then
        centers them inside those enlarged hosts, which appears as large blank
        bands between dashboard rows. Locking each row host to the calculated
        row height keeps the page grouped while still allowing the card heights
        themselves to scale fluidly with the viewport.
        """
        height = max(1, int(height))
        section.setMinimumHeight(height)
        section.setMaximumHeight(height)

    @staticmethod
    def _interpolate_dashboard_row_heights(base_heights, max_heights, target_total):
        """Interpolate row heights to fill the viewport without stretching gaps."""
        base = [max(1, int(value)) for value in base_heights]
        maximum = [max(base_value, int(value)) for base_value, value in zip(base, max_heights)]
        base_total = sum(base)
        max_total = sum(maximum)
        target = max(base_total, min(int(target_total), max_total))
        if target <= base_total or max_total <= base_total:
            return tuple(base)

        ratio = (target - base_total) / (max_total - base_total)
        values = [
            base_value + round((max_value - base_value) * ratio)
            for base_value, max_value in zip(base, maximum)
        ]

        # Rounding can leave the rows a few pixels short or tall. Reconcile the
        # remainder so the section stack uses the intended viewport height.
        remainder = target - sum(values)
        direction = 1 if remainder > 0 else -1
        while remainder:
            changed = False
            for index in (1, 2, 3, 0):
                candidate = values[index] + direction
                if base[index] <= candidate <= maximum[index]:
                    values[index] = candidate
                    remainder -= direction
                    changed = True
                    if remainder == 0:
                        break
            if not changed:
                break
        return tuple(values)

    def _apply_dashboard_density(self, width, height):
        width = max(0, int(width))
        height = max(0, int(height))
        # Height is the limiting dimension for the Dashboard. Use the roomier
        # visual density only when its complete card stack can fit; otherwise
        # retain the same three-column layout with tighter internal spacing.
        if height >= 980 and width >= 1050:
            density = "comfortable"
        elif height >= 700:
            density = "compact"
        else:
            density = "ultra"
        self.dashboard_density = density

        # These are content-safe minimums, not fixed target heights. The final
        # row heights are calculated from the live viewport so their sum plus
        # the header, margins, and inter-row spacing never exceeds the page.
        base_heights = {
            "comfortable": (88, 252, 244, 118),
            "compact": (72, 190, 158, 88),
            "ultra": (60, 156, 124, 68),
        }[density]
        maximum_heights = {
            "comfortable": (112, 326, 316, 176),
            "compact": (100, 292, 276, 154),
            "ultra": (84, 226, 204, 112),
        }[density]

        if density == "comfortable":
            self.dashboard_root_layout.setContentsMargins(24, 16, 24, 14)
            self.dashboard_root_layout.setSpacing(10)
            primary_margins = (14, 13, 14, 12)
            secondary_margins = (14, 13, 14, 12)
            footer_margins = (16, 12, 16, 12)
        elif density == "compact":
            self.dashboard_root_layout.setContentsMargins(12, 8, 12, 8)
            self.dashboard_root_layout.setSpacing(7)
            primary_margins = (9, 7, 9, 7)
            secondary_margins = (9, 7, 9, 7)
            footer_margins = (10, 7, 10, 7)
        else:
            self.dashboard_root_layout.setContentsMargins(8, 5, 8, 5)
            self.dashboard_root_layout.setSpacing(5)
            primary_margins = (7, 5, 7, 5)
            secondary_margins = (7, 5, 7, 5)
            footer_margins = (8, 5, 8, 5)

        # Use spare vertical space to grow the cards themselves rather than
        # allowing QGridLayout host widgets to grow around fixed-height cards.
        # This produces a compact, continuous dashboard at 125%/150% Windows
        # scaling while preserving the no-scroll front page.
        top_margin = self.dashboard_root_layout.contentsMargins().top()
        bottom_margin = self.dashboard_root_layout.contentsMargins().bottom()
        section_spacing = max(0, self.dashboard_root_layout.spacing())
        header_height = max(
            1,
            self.dashboard_header_section.sizeHint().height(),
            self.dashboard_header_section.minimumSizeHint().height(),
        )
        available_rows_height = max(
            1,
            height
            - top_margin
            - bottom_margin
            - header_height
            - (section_spacing * 4),
        )
        (
            metrics_height,
            primary_height,
            secondary_height,
            footer_height,
        ) = self._interpolate_dashboard_row_heights(
            base_heights,
            maximum_heights,
            available_rows_height,
        )

        self.dashboard_header_section.setMinimumHeight(header_height)
        self.dashboard_header_section.setMaximumHeight(header_height)
        self._set_dashboard_section_height(
            self.dashboard_metrics_section,
            metrics_height,
        )
        self._set_dashboard_section_height(
            self.dashboard_primary_section,
            primary_height,
        )
        self._set_dashboard_section_height(
            self.dashboard_secondary_section,
            secondary_height,
        )
        self._set_dashboard_section_height(
            self.dashboard_footer_section,
            footer_height,
        )

        for card, ring in zip(self.dashboard_metric_cards, self.rings):
            self._set_dashboard_card_height(card, metrics_height)
            card.layout.setContentsMargins(5, 3, 5, 3)
            ring.set_density(density)

        for card in (
            self.dashboard_focus_card,
            self.dashboard_tasks_card,
            self.dashboard_timer_card,
        ):
            self._set_dashboard_card_height(card, primary_height)
            card.layout.setContentsMargins(*primary_margins)
            card.layout.setSpacing(3 if density != "comfortable" else 6)

        for card in (
            self.dashboard_growth_card,
            self.dashboard_achievement_card,
            self.dashboard_summary_card,
        ):
            self._set_dashboard_card_height(card, secondary_height)
            card.layout.setContentsMargins(*secondary_margins)
            card.layout.setSpacing(3 if density == "ultra" else 6 if density == "compact" else 8)

        for card in (self.encouragement_card, self.dashboard_mission_card):
            self._set_dashboard_card_height(card, footer_height)
            card.layout.setContentsMargins(*footer_margins)
            card.layout.setSpacing(2 if density == "ultra" else 4)

        for header in self.dashboard_content.findChildren(SectionHeader):
            header.set_density(density)
        for row in getattr(self, "dashboard_focus_density_widgets", []):
            row.set_density(density)
        for row in getattr(self, "dashboard_task_density_widgets", []):
            row.set_density(density)
        for row in self.dashboard_summary_card.findChildren(StatRow):
            row.set_density(density)
        for badge in self.dashboard_achievement_card.findChildren(BadgeCard):
            badge.set_density(density)
        for metric in (self.focus_total_time, self.focus_task_count):
            metric.set_density(density)

        visible_limit = 99 if density == "comfortable" else 4 if density == "compact" else 3
        for index, row in enumerate(getattr(self, "dashboard_focus_density_widgets", [])):
            row.setVisible(index < visible_limit)
        for index, row in enumerate(getattr(self, "dashboard_task_density_widgets", [])):
            row.setVisible(index < visible_limit)

        for divider in self.dashboard_focus_card.findChildren(Divider):
            if divider is not self.focus_footer_divider:
                divider.setVisible(density == "comfortable")
        for divider in self.dashboard_tasks_card.findChildren(Divider):
            divider.setVisible(density == "comfortable")
        for divider in self.dashboard_summary_card.findChildren(Divider):
            divider.setVisible(density == "comfortable")

        self.growth_chart.set_density(density)
        self.circular_timer.set_dashboard_density(density)
        # Reserve a dedicated region based on the timer's actual scaled size.
        # A fixed stage smaller than the painted circle let the timer extend
        # behind the Start/Pause/Reset/Log buttons at compact DPI settings.
        timer_stage_height = self.circular_timer.height() + (6 if density == "comfortable" else 4)
        self.dashboard_timer_stage.setMinimumHeight(timer_stage_height)
        self.dashboard_timer_stage.setMaximumHeight(timer_stage_height)

        def fit_dashboard_button(button, target_height):
            # Never force a responsive button below the height requested by
            # its current scaled font and stylesheet padding. Doing so clips
            # glyph ascenders/descenders even when the surrounding card fits.
            fitted_height = max(
                int(target_height),
                int(button.sizeHint().height()),
            )
            button.setMinimumHeight(fitted_height)
            button.setMaximumHeight(fitted_height)
            return fitted_height

        start_height = 36 if density == "comfortable" else 31 if density == "compact" else 27
        fit_dashboard_button(self.dashboard_start_button, start_height)
        for index in range(self.dashboard_timer_controls.count()):
            button = self.dashboard_timer_controls.itemAt(index).widget()
            if button is not None:
                control_height = 32 if density == "comfortable" else 29 if density == "compact" else 26
                fit_dashboard_button(button, control_height)

        self.dashboard_quote.setVisible(density != "ultra")
        self.dashboard_date.setVisible(density != "ultra")
        self.dashboard_mission_detail.setVisible(density == "comfortable")
        self.footer_subtitle.setVisible(density == "comfortable")
        self.footer_message.setWordWrap(density == "comfortable")
        self.summary_period.setVisible(density != "ultra")
        self.summary_sparkline.setVisible(density == "comfortable")
        self.growth_period_combo.setVisible(density != "ultra")
        self.dashboard_summary_button.setText(
            "Summary →" if density == "ultra" else "View Full Summary"
        )
        summary_button_height = 32 if density == "comfortable" else 29 if density == "compact" else 26
        fit_dashboard_button(
            self.dashboard_summary_button,
            summary_button_height,
        )

        mission_button_height = 34 if density == "comfortable" else 30 if density == "compact" else 27
        for button in (
            self.dashboard_highest_impact_button,
            self.dashboard_view_readiness_button,
        ):
            fit_dashboard_button(button, mission_button_height)

        self.dashboard_content.updateGeometry()

    def update_dashboard_layout(self, width, height=None):
        width = max(0, int(width))
        if height is None:
            height = max(0, self.dashboard_scroll.viewport().height())
        height = max(0, int(height))

        if width >= self.DASHBOARD_WIDE_BREAKPOINT:
            mode = "wide"
        elif width >= 650:
            mode = "fit"
        else:
            mode = "compact"

        self._apply_dashboard_density(width, height)
        density = self.dashboard_density or "comfortable"

        compact_header = mode == "compact"
        set_box_direction(
            self.dashboard_header_layout,
            compact_header,
            spacing=5 if density == "ultra" else 8 if compact_header else 10,
        )
        self.dashboard_program_meta.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            if compact_header
            else Qt.AlignmentFlag.AlignRight
        )
        self.dashboard_date.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            if compact_header
            else Qt.AlignmentFlag.AlignRight
        )
        if hasattr(self, "exercise_suggestion_panel"):
            self.exercise_suggestion_panel.set_compact(
                mode != "wide" or density != "comfortable"
            )

        if mode == self.dashboard_layout_mode:
            self.dashboard_content.updateGeometry()
            return
        self.dashboard_layout_mode = mode

        self._take_layout_items(self.dashboard_metrics_grid)
        self._take_layout_items(self.dashboard_primary_grid)
        self._take_layout_items(self.dashboard_secondary_grid)
        self._take_layout_items(self.dashboard_footer_grid)
        self._take_layout_items(self.dashboard_compact_footer_layout)

        if mode in {"wide", "fit"}:
            self.dashboard_footer_section.show()
            self.dashboard_compact_footer_stack.hide()
            self._layout_mission_actions(compact=False)

            for column, card in enumerate(self.dashboard_metric_cards):
                self.dashboard_metrics_grid.addWidget(card, 0, column)
                self.dashboard_metrics_grid.setColumnStretch(column, 1)

            self.dashboard_primary_grid.addWidget(self.dashboard_focus_card, 0, 0)
            self.dashboard_primary_grid.addWidget(self.dashboard_tasks_card, 0, 1)
            self.dashboard_primary_grid.addWidget(self.dashboard_timer_card, 0, 2)
            self.dashboard_primary_grid.setColumnStretch(0, 34)
            self.dashboard_primary_grid.setColumnStretch(1, 33)
            self.dashboard_primary_grid.setColumnStretch(2, 33)

            self.dashboard_secondary_grid.addWidget(self.dashboard_growth_card, 0, 0)
            self.dashboard_secondary_grid.addWidget(self.dashboard_achievement_card, 0, 1)
            self.dashboard_secondary_grid.addWidget(self.dashboard_summary_card, 0, 2)
            self.dashboard_secondary_grid.setColumnStretch(0, 38)
            self.dashboard_secondary_grid.setColumnStretch(1, 29)
            self.dashboard_secondary_grid.setColumnStretch(2, 33)

            self.dashboard_footer_grid.addWidget(self.encouragement_card, 0, 0)
            self.dashboard_footer_grid.addWidget(self.dashboard_mission_card, 0, 1)
            self.dashboard_footer_grid.setColumnStretch(0, 1)
            self.dashboard_footer_grid.setColumnStretch(1, 1)

            self._set_dashboard_section_order(
                [
                    self.dashboard_header_section,
                    self.dashboard_metrics_section,
                    self.dashboard_primary_section,
                    self.dashboard_secondary_section,
                    self.dashboard_footer_section,
                ]
            )
        else:
            # Widths below the supported desktop minimum retain a scroll-safe
            # one-column fallback rather than clipping or creating horizontal
            # overflow.
            self.dashboard_footer_section.hide()
            self.dashboard_compact_footer_stack.show()
            self._layout_mission_actions(compact=True)

            for row, card in enumerate(self.dashboard_metric_cards):
                self.dashboard_metrics_grid.addWidget(card, row, 0)
            self.dashboard_metrics_grid.setColumnStretch(0, 1)

            self.dashboard_compact_footer_layout.addWidget(self.encouragement_card)
            self.dashboard_compact_footer_layout.addWidget(self.dashboard_mission_card)
            for row, card in enumerate(
                (
                    self.dashboard_focus_card,
                    self.dashboard_tasks_card,
                    self.dashboard_timer_card,
                    self.dashboard_compact_footer_stack,
                )
            ):
                self.dashboard_primary_grid.addWidget(card, row, 0)
            self.dashboard_primary_grid.setColumnStretch(0, 1)

            for row, card in enumerate(
                (
                    self.dashboard_growth_card,
                    self.dashboard_achievement_card,
                    self.dashboard_summary_card,
                )
            ):
                self.dashboard_secondary_grid.addWidget(card, row, 0)
            self.dashboard_secondary_grid.setColumnStretch(0, 1)

            self._set_dashboard_section_order(
                [
                    self.dashboard_header_section,
                    self.dashboard_primary_section,
                    self.dashboard_metrics_section,
                    self.dashboard_secondary_section,
                ]
            )

        self.dashboard_content.updateGeometry()

    # ---------- Planner ----------
    def planner_page(self):
        page, root = self.page(
            "🚀 Adaptive Planner",
            "Build a plan around the time and energy you actually have today.",
        )

        controls = Card("Plan This Session")
        form = QFormLayout()
        self.plan_minutes = QSpinBox()
        self.plan_minutes.setRange(15, 480)
        self.plan_minutes.setValue(90)
        self.plan_energy = QComboBox()
        self.plan_energy.addItems(["Low", "Normal", "High"])
        self.plan_energy.setCurrentText("Normal")
        form.addRow("Minutes available", self.plan_minutes)
        form.addRow("Energy level", self.plan_energy)
        controls.layout.addLayout(form)
        build = QPushButton("Build My Plan")
        build.setObjectName("Primary")
        build.clicked.connect(self.build_plan)
        controls.layout.addWidget(build)
        root.addWidget(controls)

        body = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.planner_body_layout = body
        queue = Card("Recommended Priority Queue")
        self.plan_list = QListWidget()
        self.plan_list.setWordWrap(True)
        self.plan_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.plan_list.itemDoubleClicked.connect(
            lambda _item: self.open_plan_workspace()
        )
        queue.layout.addWidget(self.plan_list)
        queue_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.planner_queue_buttons = queue_buttons
        continue_button = QPushButton("Continue")
        continue_button.setObjectName("Primary")
        continue_button.clicked.connect(self.continue_plan)
        defer_button = QPushButton("Move to Tomorrow")
        defer_button.clicked.connect(self.defer_plan)
        block_button = QPushButton("Mark Blocked")
        block_button.clicked.connect(self.block_plan)
        workspace_button = QPushButton("Open Workspace")
        workspace_button.clicked.connect(self.open_plan_workspace)
        queue_buttons.addWidget(continue_button)
        queue_buttons.addWidget(defer_button)
        queue_buttons.addWidget(block_button)
        queue_buttons.addWidget(workspace_button)
        queue.layout.addLayout(queue_buttons)
        body.addWidget(queue, 1)

        backlog = Card(
            "Sprint Backlog",
            (
                "Click a row to select it. "
                "The selected task stays highlighted in purple."
            ),
        )
        self.backlog_list = QListWidget()
        self.backlog_list.setWordWrap(True)
        self.backlog_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.backlog_list.setObjectName(
            "SprintBacklogList"
        )
        self.backlog_list.itemDoubleClicked.connect(
            lambda _item: self.open_backlog_workspace()
        )
        backlog.layout.addWidget(self.backlog_list)
        backlog_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.planner_backlog_actions = backlog_actions
        edit = QPushButton("Edit Selected Task")
        edit.clicked.connect(self.edit_task)
        workspace = QPushButton("Open Workspace")
        workspace.setObjectName("Primary")
        workspace.clicked.connect(self.open_backlog_workspace)
        backlog_actions.addWidget(edit)
        backlog_actions.addWidget(workspace)
        backlog.layout.addLayout(backlog_actions)

        history = QPushButton(
            "Completion History / Undo"
        )
        history.clicked.connect(
            self.open_completion_history
        )
        backlog.layout.addWidget(history)

        body.addWidget(backlog, 1)
        root.addLayout(body, 1)

        def update_planner_layout(width):
            stacked = width < 900
            set_box_direction(self.planner_body_layout, stacked, 10)
            compact_actions = width < 720
            set_box_direction(self.planner_queue_buttons, compact_actions, 7)
            set_box_direction(self.planner_backlog_actions, compact_actions, 7)
            self.plan_list.setMinimumHeight(210 if stacked else 260)
            self.backlog_list.setMinimumHeight(210 if stacked else 260)

        self._register_page_responsive(page, update_planner_layout)
        return page

    # ---------- Learning ----------
    def learning_page(self):
        page, root = self.page(
            "📚 Learning Dashboard",
            "Track structured learning and complete guided labs that produce employer-ready evidence.",
        )
        page.set_outer_scroll_enabled(False)
        self.learning_tabs = QTabWidget()
        self.learning_tabs.setObjectName("LearningTabs")
        # The Learning sections use dedicated navigation buttons instead of a
        # native tab strip.  Keeping the QTabWidget as the page stack preserves
        # existing routing while eliminating the tab-bar baseline/divider.
        self.learning_tabs.tabBar().hide()
        self.learning_tabs.setDocumentMode(False)
        self.learning_tabs.setStyleSheet(
            "QTabWidget#LearningTabs::pane {"
            "border:none;background:transparent;margin:0;padding:0;"
            "}"
        )
        self.learning_tabs.setMinimumWidth(0)
        self.learning_tabs.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )

        self.learning_section_nav = QWidget()
        self.learning_section_nav.setObjectName("LearningSectionNav")
        learning_section_layout = QHBoxLayout(self.learning_section_nav)
        learning_section_layout.setContentsMargins(0, 0, 0, 0)
        learning_section_layout.setSpacing(8)
        self.learning_tab_button_group = QButtonGroup(self.learning_section_nav)
        self.learning_tab_button_group.setExclusive(True)
        self.learning_tab_buttons = []
        for index, label in enumerate((
            "Learning Overview",
            "Applied Labs",
            "Exercises",
        )):
            button = QPushButton(label)
            button.setObjectName("LearningSectionButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, target=index: (
                    self.learning_tabs.setCurrentIndex(target)
                    if checked else None
                )
            )
            self.learning_tab_button_group.addButton(button, index)
            self.learning_tab_buttons.append(button)
            learning_section_layout.addWidget(button)
        learning_section_layout.addStretch(1)
        self.learning_tab_buttons[0].setChecked(True)
        self.learning_section_nav.setStyleSheet(
            f"""
            QWidget#LearningSectionNav {{
                background: transparent;
                border: none;
            }}
            QPushButton#LearningSectionButton {{
                background: {COLORS['panel']};
                color: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 8px 15px;
                min-height: 20px;
                font-weight: 600;
            }}
            QPushButton#LearningSectionButton:hover {{
                background: {COLORS['panel_hover']};
                color: white;
                border-color: {COLORS['purple_soft']};
            }}
            QPushButton#LearningSectionButton:checked {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 {COLORS['magenta']}, stop:1 {COLORS['purple']});
                color: white;
                border-color: #C07BFF;
                font-weight: 700;
            }}
            QPushButton#LearningSectionButton:checked:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #FF6BC6, stop:1 #A477FF);
                border-color: #E0B5FF;
            }}
            QPushButton#LearningSectionButton:pressed {{
                padding: 8px 15px;
            }}
            """
        )
        root.addWidget(self.learning_section_nav, 0)

        overview = QWidget()
        overview_root = QVBoxLayout(overview)
        overview_root.setContentsMargins(0, 8, 0, 0)
        overview_root.setSpacing(12)
        self.learning_cards = {}
        grid = QGridLayout()
        self.learning_overview_grid = grid
        self.learning_overview_cards = []
        learning_tracks = [
            ("🎓 Google Certificate", "Google"),
            ("📘 DataCamp", "DataCamp"),
            ("💻 SQL Practice", "SQL"),
            ("📊 Power BI", "Power BI"),
            ("🐍 Python", "Python"),
            ("📁 Portfolio", "Portfolio"),
            ("📐 Statistics", "Statistics"),
            ("🧪 Applied Labs", "Applied Labs"),
        ]
        for index, (title, key) in enumerate(learning_tracks):
            card = Card(title)
            value = QLabel("—")
            value.setStyleSheet("font-size:20pt;font-weight:700;")
            detail = QLabel("")
            detail.setObjectName("Muted")
            detail.setWordWrap(True)
            button = QPushButton("Continue →")
            card.layout.addWidget(value)
            card.layout.addWidget(detail)
            card.layout.addStretch()
            card.layout.addWidget(button)
            self.learning_overview_cards.append(card)
            self.learning_cards[key] = (value, detail)
        overview_root.addLayout(grid)

        progress = Card("Update Learning Progress")
        form = QFormLayout()
        self.week_input = QSpinBox(); self.week_input.setRange(1, 12)
        self.course_input = QSpinBox(); self.course_input.setRange(1, 9)
        self.module_input = QSpinBox(); self.module_input.setRange(1, 4)
        self.course_input.valueChanged.connect(
            self.update_google_module_range
        )
        self.hours_input = QSpinBox(); self.hours_input.setRange(1, 40)
        form.addRow("Current week", self.week_input)
        form.addRow("Google course", self.course_input)
        form.addRow("Google module", self.module_input)
        form.addRow("Weekly target hours", self.hours_input)
        progress.layout.addLayout(form)
        save = QPushButton("Save Learning Progress")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_learning)
        progress.layout.addWidget(save)
        overview_root.addWidget(progress)
        overview_root.addStretch(1)

        labs = QWidget()
        labs_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, labs)
        self.legacy_labs_layout = labs_layout
        labs_layout.setContentsMargins(0, 8, 0, 0)
        labs_layout.setSpacing(10)

        library = Card(
            "Applied Lab Library",
            "Power BI, Excel, pandas, communication, validation, diagnostic, and timed exercises.",
        )
        self.applied_track_summary = QLabel(
            ""
        )
        self.applied_track_summary.setObjectName(
            "Muted"
        )
        self.applied_track_summary.setWordWrap(
            True
        )
        library.layout.addWidget(
            self.applied_track_summary
        )

        pin_row = QHBoxLayout()
        pin_row.addWidget(
            QLabel("Adaptive branch")
        )
        self.applied_branch_pin = QComboBox()
        self.applied_branch_pin.addItems(
            [
                "Auto",
                *tracks.APPLIED_BRANCH_ORDER,
            ]
        )
        self.applied_branch_pin.currentTextChanged.connect(
            self.save_applied_branch_pin
        )
        pin_row.addWidget(
            self.applied_branch_pin,
            1,
        )
        library.layout.addLayout(
            pin_row
        )

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Category"))
        self.applied_category_filter = QComboBox()
        self.applied_category_filter.addItems(["All", *CATEGORY_ORDER])
        self.applied_category_filter.currentTextChanged.connect(self.refresh_applied_exercises)
        filter_row.addWidget(self.applied_category_filter, 1)
        library.layout.addLayout(filter_row)
        self.applied_exercise_list = QListWidget()
        self.applied_exercise_list.setWordWrap(True)
        self.applied_exercise_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.applied_exercise_list.currentItemChanged.connect(self.prefill_applied_exercise)
        library.layout.addWidget(self.applied_exercise_list, 1)
        labs_layout.addWidget(library, 1)

        detail = Card("Applied Lab Workspace")
        self.applied_workspace_status = QLabel("Select a lab on the left.")
        self.applied_workspace_status.setObjectName("Muted")
        self.applied_workspace_status.setWordWrap(True)
        detail.layout.addWidget(self.applied_workspace_status)
        detail_form = QFormLayout()
        self.applied_title = QLineEdit(); self.applied_title.setReadOnly(True)
        self.applied_category = QLineEdit(); self.applied_category.setReadOnly(True)
        self.applied_week = QLineEdit(); self.applied_week.setReadOnly(True)
        self.applied_concepts = QLineEdit(); self.applied_concepts.setReadOnly(True)
        self.applied_estimate = QLineEdit(); self.applied_estimate.setReadOnly(True)
        self.applied_submission_path = QLineEdit(); self.applied_submission_path.setReadOnly(True)
        self.applied_status = QComboBox(); self.applied_status.addItems(list(applied_workspace.VALID_STATUSES))
        self.applied_notes = QTextEdit()
        self.applied_notes.setPlaceholderText("Record assumptions, validation results, artifact paths, and interview notes.")
        detail_form.addRow("Lab", self.applied_title)
        detail_form.addRow("Category", self.applied_category)
        detail_form.addRow("Roadmap week", self.applied_week)
        detail_form.addRow("Concepts", self.applied_concepts)
        detail_form.addRow("Estimate", self.applied_estimate)
        detail_form.addRow("Status", self.applied_status)
        detail_form.addRow("Submission", self.applied_submission_path)
        detail_form.addRow("Notes", self.applied_notes)
        detail.layout.addLayout(detail_form)

        refs = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.legacy_labs_refs = refs
        self.applied_instructions_button = QPushButton("Open Instructions")
        self.applied_instructions_button.clicked.connect(lambda: self.open_applied_reference("instructions"))
        self.applied_starter_button = QPushButton("Open Starter")
        self.applied_starter_button.clicked.connect(lambda: self.open_applied_reference("starter"))
        self.applied_validation_button = QPushButton("Open Validation")
        self.applied_validation_button.clicked.connect(lambda: self.open_applied_reference("validation"))
        self.applied_datasets_button = QPushButton("Open Dataset Folder")
        self.applied_datasets_button.clicked.connect(self.open_applied_datasets)
        for button in (self.applied_instructions_button,self.applied_starter_button,self.applied_validation_button,self.applied_datasets_button):
            refs.addWidget(button)
        detail.layout.addLayout(refs)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.legacy_labs_actions = actions
        self.applied_submission_button = QPushButton("Create / Open Submission")
        self.applied_submission_button.setObjectName("Primary")
        self.applied_submission_button.clicked.connect(self.open_applied_submission)
        self.applied_save_button = QPushButton("Save Lab Progress")
        self.applied_save_button.clicked.connect(self.save_applied_progress)
        actions.addWidget(self.applied_submission_button)
        actions.addWidget(self.applied_save_button)
        detail.layout.addLayout(actions)
        self.applied_selected_number = None
        self.set_applied_workspace_enabled(False)
        labs_layout.addWidget(detail, 1)

        overview_scroll = QScrollArea()
        overview_scroll.setWidgetResizable(True)
        overview_scroll.setFrameShape(QFrame.Shape.NoFrame)
        overview_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        overview_scroll.setStyleSheet(
            "QScrollArea {background:transparent;border:none;}"
        )
        overview_scroll.setWidget(overview)
        self.learning_overview_scroll = overview_scroll
        self.learning_tabs.addTab(overview_scroll, "Learning Overview")
        # BEGIN EXERCISE PACKS
        self._legacy_applied_labs_page = labs
        self.applied_labs_widget = AppliedLabsWidget(
            self.conn, ROOT, self
        )
        self.applied_labs_widget.changed.connect(
            self._applied_labs_changed
        )
        self.learning_tabs.addTab(
            self.applied_labs_widget, "Applied Labs"
        )
        # END EXERCISE PACKS
        # BEGIN EXERCISE PACKS
        self.exercise_packs_widget = ExercisePacksWidget(
            self.conn, ROOT, self
        )
        self.exercise_packs_widget.packsChanged.connect(
            self._exercise_packs_changed
        )
        self.learning_tabs.addTab(
            self.exercise_packs_widget, "Exercises"
        )
        # END EXERCISE PACKS
        root.addWidget(self.learning_tabs, 1)

        def update_learning_layout(width):
            columns = 3 if width >= 1040 else 2 if width >= 680 else 1
            reflow_grid(
                self.learning_overview_grid,
                self.learning_overview_cards,
                columns,
            )
            stacked = width < 880
            set_box_direction(self.legacy_labs_layout, stacked, 10)
            set_box_direction(self.legacy_labs_refs, width < 720, 7)
            set_box_direction(self.legacy_labs_actions, width < 620, 7)
            self.learning_tabs.setMinimumHeight(0)
            self.learning_tabs.setMaximumHeight(16777215)

        self._learning_layout_handler = update_learning_layout
        def sync_learning_section_button(index):
            button = self.learning_tab_button_group.button(index)
            if button is not None:
                button.setChecked(True)

        self.learning_tabs.currentChanged.connect(sync_learning_section_button)
        self.learning_tabs.currentChanged.connect(
            lambda _index: update_learning_layout(max(0, page.viewport().width()))
        )
        self._register_page_responsive(page, update_learning_layout)
        return page
    # BEGIN EXERCISE PACKS
    def _applied_labs_changed(self):
        self.state = state(self.conn)
        tracks.sync_all(self.conn, self.state)
        self.state = state(self.conn)
        self.refresh_all(sync_tracks=False)
    # END EXERCISE PACKS

    # BEGIN EXERCISE PACKS
    def _exercise_packs_changed(self):
        if hasattr(self, "exercise_packs_widget"):
            self.exercise_packs_widget.refresh()
        self.refresh_dashboard(sync_tracks=False)

    def open_exercise_pack(self, pack_id):
        self.navigate(2)
        self.learning_tabs.setCurrentWidget(self.exercise_packs_widget)
        self.exercise_packs_widget.select_pack(pack_id)
    # END EXERCISE PACKS


    def set_applied_workspace_enabled(self, enabled):
        for widget in (
            self.applied_status,self.applied_notes,self.applied_instructions_button,
            self.applied_starter_button,self.applied_validation_button,
            self.applied_datasets_button,self.applied_submission_button,
            self.applied_save_button,
        ):
            widget.setEnabled(enabled)

    def save_applied_branch_pin(
        self,
        branch,
    ):
        if branch not in {
            "Auto",
            *tracks.APPLIED_BRANCH_ORDER,
        }:
            branch = "Auto"

        save_setting(
            self.conn,
            "applied_branch_pin",
            branch,
        )
        self.state = state(
            self.conn
        )
        tracks.sync_all(
            self.conn,
            self.state,
        )
        self.refresh_all(
            sync_tracks=False
        )
        self.statusBar().showMessage(
            (
                "Applied Labs branch set to "
                f"{branch}."
            ),
            4200,
        )

    def refresh_applied_exercises(
        self,
        _filter_text=None,
    ):
        previous = getattr(
            self,
            "applied_selected_number",
            None,
        )
        category = (
            self.applied_category_filter.currentText()
        )

        current_pin = (
            tracks.applied_branch_pin(
                self.conn
            )
        )
        self.applied_branch_pin.blockSignals(
            True
        )
        self.applied_branch_pin.setCurrentText(
            current_pin
        )
        self.applied_branch_pin.blockSignals(
            False
        )

        track = tracks.snapshot(
            self.conn,
            self.state,
        )["applied"]
        metadata = track["metadata"]
        next_title = metadata.get(
            "title",
            "No eligible lab yet",
        )
        branch = metadata.get(
            "branch",
            current_pin
            if current_pin != "Auto"
            else "Auto",
        )
        self.applied_track_summary.setText(
            (
                f"Adaptive track: "
                f"{track['status']} • "
                f"Branch: {branch} • "
                f"Next: {next_title} • "
                f"Week "
                f"{track['weekly_completed']} / "
                f"{track['weekly_target']}. "
                "Only the selected lab enters the active schedule."
            )
        )

        active_number = metadata.get(
            "lab_number"
        )
        self.applied_exercise_list.blockSignals(
            True
        )
        self.applied_exercise_list.clear()
        rows = {}

        for number, item in sorted(
            APPLIED_EXERCISES.items()
        ):
            if (
                category != "All"
                and item["category"]
                != category
            ):
                continue

            record = applied_workspace.progress(
                self.conn,
                ROOT,
                number,
            )
            readiness = (
                tracks.applied_lab_readiness(
                    self.conn,
                    self.state,
                    number,
                )
            )

            if record["status"] == "Completed":
                icon = "✅"
            elif (
                active_number is not None
                and int(active_number)
                == int(number)
                and track["status"]
                == "Active"
            ):
                icon = "▶"
            elif not readiness["ready"]:
                icon = "🔒"
            elif record["status"] == "In Progress":
                icon = "🟡"
            else:
                icon = "⬜"

            saved = (
                " • 💾 Submission"
                if record[
                    "submission_exists"
                ]
                else ""
            )
            optional_text = (
                " • Optional"
                if item.get(
                    "optional",
                    False,
                )
                else ""
            )
            self.applied_exercise_list.addItem(
                f"{icon} {number:02d}. "
                f"{item['category']} • "
                f"{item['title']} • "
                f"Week {item['week']} • "
                f"{item['minutes']} min"
                f"{optional_text}"
                f"{saved}"
            )
            index = (
                self.applied_exercise_list.count()
                - 1
            )
            list_item = (
                self.applied_exercise_list.item(
                    index
                )
            )
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                int(number),
            )

            eligibility = (
                "Ready"
                if readiness["ready"]
                else (
                    "Locked: "
                    + "; ".join(
                        readiness["missing"]
                    )
                )
            )
            list_item.setToolTip(
                (
                    f"Branch: "
                    f"{readiness['branch']}\n"
                    f"Concepts: "
                    f"{item['concepts']}\n"
                    f"Status: "
                    f"{record['status']}\n"
                    f"Adaptive eligibility: "
                    f"{eligibility}\n"
                    f"Submission: "
                    f"{record['submission_path'] or 'Not created'}"
                )
            )
            rows[number] = index

        self.applied_exercise_list.blockSignals(
            False
        )

        if not rows:
            self.applied_exercise_list.addItem(
                "No labs match this category."
            )
            self.applied_selected_number = None
            self.set_applied_workspace_enabled(
                False
            )
            return

        selected = (
            previous
            if previous in rows
            else (
                int(active_number)
                if (
                    active_number is not None
                    and int(active_number)
                    in rows
                )
                else next(iter(rows))
            )
        )
        self.applied_exercise_list.setCurrentRow(
            rows[selected]
        )

    def prefill_applied_exercise(self, item, _previous=None):
        if item is None:
            self.applied_selected_number = None
            self.set_applied_workspace_enabled(False)
            return
        number = item.data(Qt.ItemDataRole.UserRole)
        if number is None:
            return
        number = int(number)
        lab = APPLIED_EXERCISES[number]
        record = applied_workspace.progress(
            self.conn,
            ROOT,
            number,
        )
        readiness = (
            tracks.applied_lab_readiness(
                self.conn,
                self.state,
                number,
            )
        )
        self.applied_selected_number = number
        self.applied_title.setText(f"{number:02d}. {lab['title']}")
        self.applied_category.setText(lab["category"])
        self.applied_week.setText(f"Week {lab['week']}")
        self.applied_concepts.setText(lab["concepts"])
        self.applied_estimate.setText(f"{lab['minutes']} minutes")
        self.applied_status.setCurrentText(record["status"])
        self.applied_submission_path.setText(record["submission_path"] or "Not created")
        self.applied_notes.setPlainText(record["notes"])
        if record["status"] == "Completed":
            message = (
                "Completed. This lab contributes to "
                "Skills & Concepts and Demonstrated Evidence."
            )
        elif not readiness["ready"]:
            message = (
                "Locked for adaptive scheduling • "
                + "; ".join(
                    readiness["missing"]
                )
                + ". You may review the materials now, "
                  "but complete the prerequisites first."
            )
        elif record["submission_exists"]:
            message = (
                "Submission saved locally. Continue editing, "
                "validate the deliverables, and save progress."
            )
        else:
            message = (
                "Ready for adaptive scheduling. Read the instructions "
                "and validation guide, then create a saved submission."
            )
        if record["submission_exists"] and not record["submission_changed"]:
            message += " The submission still matches the starter."
        self.applied_workspace_status.setText(message)
        self.set_applied_workspace_enabled(True)

    def open_applied_reference(self, kind):
        number = self.applied_selected_number
        if number is None:
            self.statusBar().showMessage("Select an applied lab first.", 3200)
            return
        path = applied_workspace.paths(ROOT, number).get(kind)
        try:
            editor = sql_workspace.open_in_editor(path, root=ROOT)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Lab File", str(exc))
            return
        self.statusBar().showMessage(f"Opened {path.name} in {editor}.", 4200)

    def open_applied_datasets(self):
        number = self.applied_selected_number
        if number is None:
            self.statusBar().showMessage("Select an applied lab first.", 3200)
            return
        path = applied_workspace.paths(ROOT, number)["datasets"]
        try:
            app_name = applied_workspace.open_folder(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Dataset Folder", str(exc))
            return
        self.statusBar().showMessage(f"Opened the dataset folder in {app_name}.", 4200)

    def open_applied_submission(self):
        number = self.applied_selected_number
        if number is None:
            self.statusBar().showMessage("Select an applied lab first.", 3200)
            return
        try:
            path, created = applied_workspace.ensure_submission(ROOT, number)
            record = applied_workspace.progress(self.conn, ROOT, number)
            status = "In Progress" if record["status"] == "Not Started" else record["status"]
            applied_workspace.save_progress(
                self.conn, ROOT, number, status=status,
                notes=self.applied_notes.toPlainText(),
            )
            editor = sql_workspace.open_in_editor(path, root=ROOT)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Submission", str(exc))
            return
        self.applied_status.setCurrentText(status)
        self.applied_submission_path.setText(str(path.relative_to(ROOT)).replace("\\", "/"))
        self.refresh_applied_exercises()
        self.statusBar().showMessage(
            f"{'Created and opened' if created else 'Opened'} {path.name} in {editor}.", 5200
        )

    def save_applied_progress(self):
        number = self.applied_selected_number
        if number is None:
            self.statusBar().showMessage(
                "Select an applied lab first.",
                3200,
            )
            return

        status = (
            self.applied_status.currentText()
        )
        readiness = (
            tracks.applied_lab_readiness(
                self.conn,
                self.state,
                number,
            )
        )

        if (
            status == "Completed"
            and not readiness["ready"]
        ):
            QMessageBox.warning(
                self,
                "Prerequisites Not Complete",
                (
                    "Complete the following first:\n\n"
                    + "\n".join(
                        f"• {reason}"
                        for reason in readiness[
                            "missing"
                        ]
                    )
                ),
            )
            return

        submission = (
            applied_workspace.submission_path(
                ROOT,
                number,
            )
        )
        if (
            status == "Completed"
            and not submission.exists()
        ):
            QMessageBox.warning(
                self,
                "Submission Required",
                (
                    "Create a saved submission before "
                    "marking the lab complete."
                ),
            )
            return

        if (
            status == "Completed"
            and not applied_workspace.submission_has_changes(
                ROOT,
                number,
            )
        ):
            answer = QMessageBox.question(
                self,
                "Submission Matches Starter",
                (
                    "The saved submission still matches the starter. "
                    "Mark the lab complete anyway?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )
            if (
                answer
                != QMessageBox.StandardButton.Yes
            ):
                return

        session_snapshot = (
            session_guard.capture(self)
        )
        completion_message = None
        try:
            record = (
                applied_workspace.save_progress(
                    self.conn,
                    ROOT,
                    number,
                    status=status,
                    notes=(
                        self.applied_notes.toPlainText()
                    ),
                )
            )

            task_id = (
                record["task_ids"][0]
                if record["task_ids"]
                else None
            )
            active = (
                tracks.active_applied_task_for_number(
                    self.conn,
                    number,
                )
            )

            if (
                status == "Completed"
                and active is not None
            ):
                result = (
                    tracks.complete_track_task(
                        self.conn,
                        int(
                            active["task_id"]
                        ),
                        self.state,
                    )
                )
                completion_message = (
                    result.get(
                        "message"
                    )
                )
            else:
                tracks.record_applied_change(
                    self.conn,
                    number=number,
                    completed=(
                        status
                        == "Completed"
                    ),
                    task_id=task_id,
                )

            self.state = state(
                self.conn
            )
            tracks.sync_all(
                self.conn,
                self.state,
            )
            self.refresh_all(
                sync_tracks=False
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Save Applied Lab",
                str(exc),
            )
            return
        finally:
            session_guard.restore(
                self,
                session_snapshot,
            )

        message = (
            completion_message
            or (
                f"Applied Lab "
                f"{number:02d} saved as "
                f"{record['status']}."
            )
        )
        if status == "Completed":
            message += (
                " Added to Demonstrated Evidence."
            )
        self.statusBar().showMessage(
            message,
            6000,
        )


    # ---------- Portfolio ----------
    def portfolio_page(self):
        page, root = self.page(
            "📁 Portfolio Workspace",
            "A guided workspace for building evidence-quality analytics projects.",
        )

        top = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.portfolio_top_layout = top
        self.project_combo = QComboBox()
        for project_id, name in PROJECT_NAMES.items():
            self.project_combo.addItem(f"{project_id} — {name}", project_id)
        self.project_combo.currentIndexChanged.connect(self.load_project)
        top.addWidget(self.project_combo)
        set_active = QPushButton("Set Active")
        set_active.clicked.connect(self.set_active_project)
        top.addWidget(set_active)
        top.addStretch()
        root.addLayout(top)

        self.project_tabs = QTabWidget()
        self.project_tabs.setMinimumWidth(0)
        self.project_tabs.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        root.addWidget(self.project_tabs, 1)

        self.project_task_checks = []
        self.project_stage_widgets = {}
        for stage in PROJECT_STAGES:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            if stage in ("Overview", "Tasks"):
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                host = QWidget()
                host_layout = QVBoxLayout(host)
                scroll.setWidget(host)
                tab_layout.addWidget(scroll)
                self.project_stage_widgets[stage] = host_layout
            else:
                editor = QTextEdit()
                editor.setPlaceholderText(f"Document the {stage} work for this project.")
                tab_layout.addWidget(editor)
                save = QPushButton(f"Save {stage}")
                save.clicked.connect(
                    lambda checked=False, section=stage, widget=editor:
                    self.save_project_note(section, widget)
                )
                tab_layout.addWidget(save)
                self.project_stage_widgets[stage] = editor
            self.project_tabs.addTab(tab, stage)

        save_tasks = QPushButton("Save Project Milestones")
        save_tasks.setObjectName("Primary")
        save_tasks.clicked.connect(self.save_project_tasks)
        root.addWidget(save_tasks)

        def update_portfolio_layout(width):
            set_box_direction(self.portfolio_top_layout, width < 620, 8)
            self.project_tabs.setMinimumHeight(520 if width >= 700 else 620)

        self._register_page_responsive(page, update_portfolio_layout)
        return page

    # ---------- SQL ----------
    def sql_page(self):
        page, root = self.page(
            "💻 SQL Companion",
            (
                "Practice interview problems or complete guided DuckDB "
                "exercises with saved local submissions."
            ),
        )
        page.set_outer_scroll_enabled(False)

        self.sql_tabs = QTabWidget()
        self.sql_tabs.setMinimumWidth(0)
        self.sql_tabs.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )

        # DataLemur problem workspace.
        problem_tab = QWidget()
        problem_layout = QBoxLayout(
            QBoxLayout.Direction.LeftToRight,
            problem_tab,
        )
        self.sql_problem_layout = problem_layout
        problem_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )
        problem_layout.setSpacing(10)

        recommendations = Card(
            "Today's SQL"
        )
        self.sql_recommendations_card = recommendations
        self.sql_problem_list = QListWidget()
        self.sql_problem_list.setWordWrap(True)
        self.sql_problem_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.sql_problem_list.currentItemChanged.connect(
            self.prefill_sql
        )
        recommendations.layout.addWidget(
            self.sql_problem_list
        )
        problem_layout.addWidget(
            recommendations,
            1,
        )

        detail = Card("Problem Workspace")
        self.sql_detail_card = detail
        self.sql_workspace_status = QLabel(
            "Select a problem on the left."
        )
        self.sql_workspace_status.setObjectName(
            "Muted"
        )
        self.sql_workspace_status.setWordWrap(
            True
        )
        detail.layout.addWidget(
            self.sql_workspace_status
        )

        form = QFormLayout()
        self.sql_title = QLineEdit()
        self.sql_difficulty = QLineEdit(
            "Easy"
        )
        self.sql_topic = QLineEdit()
        self.sql_concepts = QLineEdit()
        for field in (
            self.sql_title,
            self.sql_difficulty,
            self.sql_topic,
            self.sql_concepts,
        ):
            field.setReadOnly(True)

        self.sql_mastery = QSpinBox()
        self.sql_mastery.setRange(1, 5)
        self.sql_mastery.setValue(1)
        self.sql_review = QLineEdit()
        self.sql_submission_path = QLineEdit()
        self.sql_submission_path.setReadOnly(True)
        self.sql_notes = QTextEdit()
        form.addRow(
            "Problem title",
            self.sql_title,
        )
        form.addRow(
            "Difficulty",
            self.sql_difficulty,
        )
        form.addRow(
            "Topic",
            self.sql_topic,
        )
        form.addRow(
            "Concepts",
            self.sql_concepts,
        )
        form.addRow(
            "Mastery (1–5)",
            self.sql_mastery,
        )
        form.addRow(
            "Review date",
            self.sql_review,
        )
        form.addRow(
            "Submission",
            self.sql_submission_path,
        )
        form.addRow(
            "Notes",
            self.sql_notes,
        )
        detail.layout.addLayout(form)

        sql_answer_label = QLabel("Your SQL submission")
        sql_answer_label.setObjectName("SectionTitle")
        detail.layout.addWidget(sql_answer_label)
        self.sql_answer_editor = SqlCodeEditor()
        self.sql_answer_editor.setMinimumHeight(190)
        self.sql_answer_editor.setPlaceholderText(
            "Write your interview-problem solution here. Save it before marking the problem complete."
        )
        detail.layout.addWidget(self.sql_answer_editor, 1)

        buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.sql_problem_buttons = buttons
        self.sql_save_button = QPushButton(
            "Save Submission"
        )
        self.sql_save_button.setObjectName(
            "Secondary"
        )
        self.sql_save_button.clicked.connect(
            self.save_sql_submission
        )
        self.sql_complete_button = QPushButton(
            "Mark Complete"
        )
        self.sql_complete_button.setObjectName(
            "Primary"
        )
        self.sql_complete_button.clicked.connect(
            self.save_sql
        )
        self.sql_hint_button = QPushButton(
            "Need a Hint"
        )
        self.sql_hint_button.clicked.connect(
            self.sql_hint
        )
        self.sql_solution_button = QPushButton(
            "Open Submission File"
        )
        self.sql_solution_button.clicked.connect(
            self.open_sql_solution
        )
        buttons.addWidget(
            self.sql_save_button
        )
        buttons.addWidget(
            self.sql_complete_button
        )
        buttons.addWidget(
            self.sql_hint_button
        )
        buttons.addWidget(
            self.sql_solution_button
        )
        detail.layout.addLayout(buttons)
        self.sql_detail_scroll = make_card_scrollable(detail)

        self.sql_selected_title = None
        self.set_sql_workspace_enabled(False)
        problem_layout.addWidget(detail, 1)

        # Guided DuckDB exercise workspace.
        exercise_tab = QWidget()
        exercise_layout = QBoxLayout(
            QBoxLayout.Direction.LeftToRight,
            exercise_tab,
        )
        self.legacy_duckdb_layout = exercise_layout
        exercise_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )
        exercise_layout.setSpacing(10)

        exercise_library = Card(
            "DuckDB Exercise Library",
            (
                "Select an exercise to open its instructions, datasets, "
                "starter SQL, validation guide, and saved submission."
            ),
        )
        self.duckdb_exercise_list = (
            QListWidget()
        )
        self.duckdb_exercise_list.currentItemChanged.connect(
            self.prefill_duckdb_exercise
        )
        exercise_library.layout.addWidget(
            self.duckdb_exercise_list
        )
        exercise_layout.addWidget(
            exercise_library,
            1,
        )

        exercise_detail = Card(
            "Exercise Workspace"
        )
        self.duckdb_workspace_status = QLabel(
            "Select an exercise on the left."
        )
        self.duckdb_workspace_status.setObjectName(
            "Muted"
        )
        self.duckdb_workspace_status.setWordWrap(
            True
        )
        exercise_detail.layout.addWidget(
            self.duckdb_workspace_status
        )

        exercise_form = QFormLayout()
        self.duckdb_title = QLineEdit()
        self.duckdb_week = QLineEdit()
        self.duckdb_concepts = QLineEdit()
        self.duckdb_estimate = QLineEdit()
        self.duckdb_submission_path = (
            QLineEdit()
        )
        for field in (
            self.duckdb_title,
            self.duckdb_week,
            self.duckdb_concepts,
            self.duckdb_estimate,
            self.duckdb_submission_path,
        ):
            field.setReadOnly(True)

        self.duckdb_status = QComboBox()
        self.duckdb_status.addItems(
            list(
                duckdb_workspace.VALID_STATUSES
            )
        )
        self.duckdb_notes = QTextEdit()
        self.duckdb_notes.setPlaceholderText(
            (
                "Record assumptions, checks, mistakes corrected, "
                "or what you learned."
            )
        )

        exercise_form.addRow(
            "Exercise",
            self.duckdb_title,
        )
        exercise_form.addRow(
            "Roadmap week",
            self.duckdb_week,
        )
        exercise_form.addRow(
            "Concepts",
            self.duckdb_concepts,
        )
        exercise_form.addRow(
            "Estimate",
            self.duckdb_estimate,
        )
        exercise_form.addRow(
            "Status",
            self.duckdb_status,
        )
        exercise_form.addRow(
            "Submission",
            self.duckdb_submission_path,
        )
        exercise_form.addRow(
            "Notes",
            self.duckdb_notes,
        )
        exercise_detail.layout.addLayout(
            exercise_form
        )

        reference_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.legacy_duckdb_reference_buttons = reference_buttons
        self.duckdb_instructions_button = (
            QPushButton("Open Instructions")
        )
        self.duckdb_instructions_button.clicked.connect(
            lambda: self.open_duckdb_reference(
                "instructions"
            )
        )
        self.duckdb_starter_button = QPushButton(
            "Open Starter SQL"
        )
        self.duckdb_starter_button.clicked.connect(
            lambda: self.open_duckdb_reference(
                "starter"
            )
        )
        self.duckdb_validation_button = (
            QPushButton("Open Validation")
        )
        self.duckdb_validation_button.clicked.connect(
            lambda: self.open_duckdb_reference(
                "validation"
            )
        )
        self.duckdb_datasets_button = QPushButton(
            "Open Dataset Folder"
        )
        self.duckdb_datasets_button.clicked.connect(
            self.open_duckdb_datasets
        )
        for button in (
            self.duckdb_instructions_button,
            self.duckdb_starter_button,
            self.duckdb_validation_button,
            self.duckdb_datasets_button,
        ):
            reference_buttons.addWidget(button)
        exercise_detail.layout.addLayout(
            reference_buttons
        )

        submission_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.legacy_duckdb_submission_buttons = submission_buttons
        self.duckdb_submission_button = (
            QPushButton(
                "Create / Open Submission"
            )
        )
        self.duckdb_submission_button.setObjectName(
            "Primary"
        )
        self.duckdb_submission_button.clicked.connect(
            self.open_duckdb_submission
        )
        self.duckdb_save_button = QPushButton(
            "Save Exercise Progress"
        )
        self.duckdb_save_button.clicked.connect(
            self.save_duckdb_progress
        )
        submission_buttons.addWidget(
            self.duckdb_submission_button
        )
        submission_buttons.addWidget(
            self.duckdb_save_button
        )
        exercise_detail.layout.addLayout(
            submission_buttons
        )

        self.duckdb_selected_number = None
        self.set_duckdb_workspace_enabled(
            False
        )
        exercise_layout.addWidget(
            exercise_detail,
            1,
        )

        self.sql_tabs.addTab(
            problem_tab,
            "Interview Problems",
        )
        # BEGIN EXERCISE PACKS
        self._legacy_duckdb_exercises_page = exercise_tab
        self.duckdb_exercises_widget = DuckDBExercisesWidget(
            self.conn, ROOT, self
        )
        self.duckdb_exercises_widget.changed.connect(
            self._duckdb_exercises_changed
        )
        self.sql_tabs.addTab(
            self.duckdb_exercises_widget, "DuckDB Exercises"
        )
        # END EXERCISE PACKS
        root.addWidget(
            self.sql_tabs,
            1,
        )

        def update_sql_layout(width):
            # At the supported desktop minimum the library and workspace stay
            # side by side; their own lists/editors/cards handle overflow.
            compact = width < 620
            set_box_direction(self.sql_problem_layout, compact, 10)
            set_box_direction(self.legacy_duckdb_layout, compact, 10)
            set_box_direction(self.sql_problem_buttons, width < 680, 7)
            set_box_direction(
                self.legacy_duckdb_reference_buttons, width < 720, 7
            )
            set_box_direction(
                self.legacy_duckdb_submission_buttons, width < 620, 7
            )
            self.sql_recommendations_card.setMinimumHeight(180 if compact else 0)
            self.sql_recommendations_card.setMaximumHeight(250 if compact else 16777215)
            self.sql_detail_card.setMinimumHeight(0)
            self.sql_problem_layout.setStretch(0, 0 if compact else 1)
            self.sql_problem_layout.setStretch(1, 1)
            self.sql_tabs.setMinimumHeight(0)
            self.sql_tabs.setMaximumHeight(16777215)

        self._sql_layout_handler = update_sql_layout
        self.sql_tabs.currentChanged.connect(
            lambda _index: update_sql_layout(max(0, page.viewport().width()))
        )
        self._register_page_responsive(page, update_sql_layout)
        return page
    # BEGIN EXERCISE PACKS
    @staticmethod
    def _normalized_learning_task_label(value):
        return re.sub(r'[^a-z0-9]+', ' ', str(value or '').casefold()).strip()

    def _route_sql_learning_task(self, task_id):
        try:
            task_row = task_workspace.task_record(self.conn, int(task_id))
        except Exception:
            return False
        if task_row is None:
            return False
        try:
            label = str(task_row['label'] or '')
            track_key = str(task_row['track_key'] or '')
            target_key = str(task_row['target_key'] or '')
        except (KeyError, IndexError, TypeError):
            label = str(getattr(task_row, 'label', '') or '')
            track_key = str(getattr(task_row, 'track_key', '') or '')
            target_key = str(getattr(task_row, 'target_key', '') or '')

        duckdb_number = duckdb_exercise_number_for_label(label)
        if duckdb_number is not None and hasattr(self, 'duckdb_exercises_widget'):
            self.navigate(4)
            self.sql_tabs.setCurrentWidget(self.duckdb_exercises_widget)
            self.duckdb_exercises_widget.select_exercise(int(duckdb_number))
            self.statusBar().showMessage(
                f'Opened DuckDB Exercise {int(duckdb_number):02d}.', 3200
            )
            return True

        normalized_label = self._normalized_learning_task_label(label)
        problem_title = None
        if track_key.casefold() == 'sql' and target_key.casefold().startswith('problem:'):
            direct_title = target_key.split(':', 1)[1].strip()
            problem_title = next(
                (entry[0] for entry in SQL_COMPANION if entry[0] == direct_title),
                None,
            )
        if problem_title is None:
            problem_title = next(
                (
                    entry[0]
                    for entry in SQL_COMPANION
                    if self._normalized_learning_task_label(entry[0])
                    in normalized_label
                ),
                None,
            )
        if not problem_title or not hasattr(self, 'sql_problem_list'):
            return False
        self.navigate(4)
        self.sql_tabs.setCurrentIndex(0)
        normalized_title = self._normalized_learning_task_label(problem_title)
        target_row = None
        for row_index in range(self.sql_problem_list.count()):
            item = self.sql_problem_list.item(row_index)
            item_title = item.data(Qt.ItemDataRole.UserRole) or item.text()
            if self._normalized_learning_task_label(item_title) == normalized_title:
                target_row = row_index
                break
        if target_row is None:
            catalog = next(entry for entry in SQL_COMPANION if entry[0] == problem_title)
            title, difficulty, topic, concepts, _week, estimate = catalog
            self.sql_problem_list.addItem(
                f'↪ {title} • {difficulty} • {topic} • {concepts} • {estimate} min'
            )
            target_row = self.sql_problem_list.count() - 1
            item = self.sql_problem_list.item(target_row)
            item.setData(Qt.ItemDataRole.UserRole, title)
        item = self.sql_problem_list.item(target_row)
        if self.sql_problem_list.currentRow() != target_row:
            self.sql_problem_list.setCurrentRow(target_row)
        else:
            self.prefill_sql(item)
        self.statusBar().showMessage(
            f'Opened interview problem: {problem_title}.', 3200
        )
        return True
    # END EXERCISE PACKS

    # BEGIN EXERCISE PACKS
    def _duckdb_exercises_changed(self):
        self.state = state(self.conn)
        tracks.sync_all(self.conn, self.state)
        self.state = state(self.conn)
        self.refresh_all(sync_tracks=False)
    # END EXERCISE PACKS


    def set_duckdb_workspace_enabled(
        self,
        enabled,
    ):
        for widget in (
            self.duckdb_status,
            self.duckdb_notes,
            self.duckdb_instructions_button,
            self.duckdb_starter_button,
            self.duckdb_validation_button,
            self.duckdb_datasets_button,
            self.duckdb_submission_button,
            self.duckdb_save_button,
        ):
            widget.setEnabled(enabled)

    def refresh_duckdb_exercises(self):
        previous_number = getattr(
            self,
            "duckdb_selected_number",
            None,
        )

        self.duckdb_exercise_list.blockSignals(
            True
        )
        self.duckdb_exercise_list.clear()

        number_to_row = {}
        for number, item in sorted(
            DUCKDB_EXERCISES.items()
        ):
            record = duckdb_workspace.progress(
                self.conn,
                ROOT,
                number,
            )
            status_icon = {
                "Completed": "✅",
                "In Progress": "🟡",
                "Not Started": "⬜",
            }.get(
                record["status"],
                "⬜",
            )
            submission_icon = (
                " • 💾 Submission"
                if record["submission_exists"]
                else ""
            )
            self.duckdb_exercise_list.addItem(
                f"{status_icon} "
                f"{number:02d}. {item['title']} • "
                f"{item['minutes']} min • "
                f"{item['concepts']}"
                f"{submission_icon}"
            )
            row_index = (
                self.duckdb_exercise_list.count()
                - 1
            )
            list_item = (
                self.duckdb_exercise_list.item(
                    row_index
                )
            )
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                int(number),
            )
            list_item.setToolTip(
                (
                    f"Roadmap week: {item['week']}\n"
                    f"Status: {record['status']}\n"
                    f"Concepts: {item['concepts']}\n"
                    f"Submission: "
                    f"{record['submission_path'] or 'Not created'}"
                )
            )
            number_to_row[
                number
            ] = row_index

        selected_number = (
            previous_number
            if previous_number
            in number_to_row
            else 1
        )

        self.duckdb_exercise_list.blockSignals(
            False
        )
        if selected_number in number_to_row:
            self.duckdb_exercise_list.setCurrentRow(
                number_to_row[
                    selected_number
                ]
            )

    def prefill_duckdb_exercise(
        self,
        item,
        _previous=None,
    ):
        if item is None:
            self.duckdb_selected_number = None
            self.set_duckdb_workspace_enabled(
                False
            )
            return

        number = item.data(
            Qt.ItemDataRole.UserRole
        )
        if number is None:
            return

        number = int(number)
        exercise = DUCKDB_EXERCISES[
            number
        ]
        record = duckdb_workspace.progress(
            self.conn,
            ROOT,
            number,
        )

        self.duckdb_selected_number = number
        self.duckdb_title.setText(
            f"{number:02d}. {exercise['title']}"
        )
        self.duckdb_week.setText(
            f"Week {exercise['week']}"
        )
        self.duckdb_concepts.setText(
            exercise["concepts"]
        )
        self.duckdb_estimate.setText(
            f"{exercise['minutes']} minutes"
        )
        self.duckdb_status.setCurrentText(
            record["status"]
        )
        self.duckdb_submission_path.setText(
            record["submission_path"]
            or "Not created"
        )
        self.duckdb_notes.setPlainText(
            record["notes"]
        )

        if record["status"] == "Completed":
            detail = (
                f"Completed "
                f"{record['completed_date'] or 'previously'}"
            )
        elif record["submission_exists"]:
            detail = (
                "Submission saved locally. "
                "Use Create / Open Submission to continue editing."
            )
        else:
            detail = (
                "Start with the instructions, then create a submission "
                "copy before writing your solution."
            )

        if (
            record["submission_exists"]
            and not record[
                "submission_changed"
            ]
        ):
            detail += (
                " The saved submission still matches the starter file."
            )

        self.duckdb_workspace_status.setText(
            detail
        )
        self.set_duckdb_workspace_enabled(
            True
        )

    def open_duckdb_reference(
        self,
        kind,
    ):
        number = self.duckdb_selected_number
        if number is None:
            self.statusBar().showMessage(
                "Select a DuckDB exercise first.",
                3200,
            )
            return

        path = duckdb_workspace.paths(
            ROOT,
            number,
        ).get(kind)
        if path is None:
            return

        try:
            editor_name = (
                sql_workspace.open_in_editor(
                    path,
                    root=ROOT,
                )
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Exercise File",
                str(exc),
            )
            return

        self.statusBar().showMessage(
            f"Opened {path.name} in {editor_name}.",
            4200,
        )

    def open_duckdb_datasets(self):
        number = self.duckdb_selected_number
        if number is None:
            self.statusBar().showMessage(
                "Select a DuckDB exercise first.",
                3200,
            )
            return

        path = duckdb_workspace.paths(
            ROOT,
            number,
        )["datasets"]
        try:
            app_name = (
                duckdb_workspace.open_folder(
                    path
                )
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Dataset Folder",
                str(exc),
            )
            return

        self.statusBar().showMessage(
            f"Opened the dataset folder in {app_name}.",
            4200,
        )

    def open_duckdb_submission(self):
        number = self.duckdb_selected_number
        if number is None:
            self.statusBar().showMessage(
                "Select a DuckDB exercise first.",
                3200,
            )
            return

        try:
            path, created = (
                duckdb_workspace.ensure_submission(
                    ROOT,
                    number,
                )
            )
            current = duckdb_workspace.progress(
                self.conn,
                ROOT,
                number,
            )
            status = current["status"]
            if status == "Not Started":
                status = "In Progress"

            duckdb_workspace.save_progress(
                self.conn,
                ROOT,
                number,
                status=status,
                notes=self.duckdb_notes.toPlainText(),
            )
            editor_name = (
                sql_workspace.open_in_editor(
                    path,
                    root=ROOT,
                )
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Submission",
                str(exc),
            )
            return

        self.duckdb_status.setCurrentText(
            status
        )
        self.duckdb_submission_path.setText(
            str(
                path.relative_to(ROOT)
            ).replace(
                "\\",
                "/",
            )
        )
        self.refresh_duckdb_exercises()

        action = (
            "Created and opened"
            if created
            else "Opened"
        )
        self.statusBar().showMessage(
            f"{action} {path.name} in {editor_name}.",
            5200,
        )

    def save_duckdb_progress(self):
        number = self.duckdb_selected_number
        if number is None:
            self.statusBar().showMessage(
                "Select a DuckDB exercise first.",
                3200,
            )
            return

        status = self.duckdb_status.currentText()
        submission = (
            duckdb_workspace.submission_path(
                ROOT,
                number,
            )
        )

        if (
            status == "Completed"
            and not submission.exists()
        ):
            QMessageBox.warning(
                self,
                "Submission Required",
                (
                    "Create a saved submission before marking the "
                    "exercise complete."
                ),
            )
            return

        if (
            status == "Completed"
            and not duckdb_workspace.submission_has_changes(
                ROOT,
                number,
            )
        ):
            confirmation = QMessageBox.question(
                self,
                "Submission Matches Starter",
                (
                    "The saved submission still matches the starter file. "
                    "Mark the exercise complete anyway?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )
            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

        session_snapshot = (
            session_guard.capture(self)
        )
        try:
            record = (
                duckdb_workspace.save_progress(
                    self.conn,
                    ROOT,
                    number,
                    status=status,
                    notes=self.duckdb_notes.toPlainText(),
                )
            )
            planner.mark_focus_task_completed(
                self.conn,
                task_id,
            )
            self.state = state(self.conn)
            tracks.sync_all(
                self.conn,
                self.state,
            )
            self.refresh_all(
                sync_tracks=False
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Save Exercise",
                str(exc),
            )
            return
        finally:
            session_guard.restore(
                self,
                session_snapshot,
            )

        message = (
            f"DuckDB Exercise {number:02d} saved as "
            f"{record['status']}."
        )
        if status == "Completed":
            message += (
                " Added to Demonstrated Evidence."
            )
        self.statusBar().showMessage(
            message,
            6000,
        )


    # ---------- Study ----------
    def study_page(self):
        page, root = self.page(
            "⏱️ Study Session",
            "Track focused time, capture what you completed, and turn each session into progress evidence.",
        )
        page.set_outer_scroll_enabled(False)

        body = QGridLayout()
        body.setHorizontalSpacing(12)
        body.setVerticalSpacing(12)
        body.setContentsMargins(0, 0, 0, 0)

        # Live timer mirrors the Dashboard timer, but uses the compact ring so
        # it can share a balanced left column with Recent Sessions.
        timer_card = Card(
            "⏱️ Live Timer",
            "The timer is shared with the Dashboard.",
        )
        timer_card.setMinimumWidth(0)
        timer_card.layout.setContentsMargins(14, 12, 14, 12)
        timer_card.layout.setSpacing(7)
        self.study_timer_subtitle = timer_card.layout.itemAt(1).widget()

        timer_stage = QWidget()
        timer_stage.setMinimumHeight(102)
        timer_stage.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )
        timer_stage_layout = QVBoxLayout(timer_stage)
        timer_stage_layout.setContentsMargins(0, 2, 0, 2)
        timer_stage_layout.setSpacing(0)
        timer_stage_layout.setAlignment(Qt.AlignCenter)

        self.study_circular_timer = CircularTimer()
        self.study_circular_timer.set_dashboard_density("compact")
        timer_stage_layout.addWidget(
            self.study_circular_timer,
            0,
            Qt.AlignCenter,
        )
        timer_card.layout.addWidget(timer_stage)

        goal_row = QHBoxLayout()
        goal_row.setSpacing(8)
        goal_label = QLabel("Focus goal")
        goal_label.setObjectName("Muted")
        goal_row.addWidget(goal_label)
        goal_row.addStretch()

        self.session_goal_minutes = QSpinBox()
        self.session_goal_minutes.setRange(5, 240)
        self.session_goal_minutes.setSingleStep(5)
        self.session_goal_minutes.setSuffix(" min")
        self.session_goal_minutes.setValue(
            int(
                setting(
                    self.conn,
                    "session_goal_minutes",
                    "60",
                )
            )
        )
        self.session_goal_minutes.setMinimumWidth(88)
        self.session_goal_minutes.setMaximumWidth(116)
        self.session_goal_minutes.valueChanged.connect(
            self.change_session_goal
        )
        goal_row.addWidget(self.session_goal_minutes)
        timer_card.layout.addLayout(goal_row)

        self.study_start_button = QPushButton("▶ Start Study Session")
        self.study_start_button.setObjectName("Primary")
        self.study_start_button.setMinimumHeight(36)
        self.study_start_button.clicked.connect(self.start_study_timer)
        timer_card.layout.addWidget(self.study_start_button)

        timer_controls = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.study_timer_controls = timer_controls
        timer_controls.setSpacing(7)

        self.study_pause_button = QPushButton("⏸️ Pause")
        self.study_pause_button.setObjectName("Secondary")
        self.study_pause_button.setMinimumHeight(32)
        self.study_pause_button.clicked.connect(self.pause_study_timer)

        self.study_reset_button = QPushButton("🔄 Reset")
        self.study_reset_button.setObjectName("Secondary")
        self.study_reset_button.setMinimumHeight(32)
        self.study_reset_button.clicked.connect(self.confirm_reset_timer)

        timer_controls.addWidget(self.study_pause_button, 1)
        timer_controls.addWidget(self.study_reset_button, 1)
        timer_card.layout.addLayout(timer_controls)

        self.study_use_time_button = QPushButton(
            "📝 Use Current Time in Session Log"
        )
        self.study_use_time_button.setObjectName("Secondary")
        self.study_use_time_button.setMinimumHeight(32)
        self.study_use_time_button.clicked.connect(
            self.apply_timer_to_session_log
        )
        timer_card.layout.addWidget(self.study_use_time_button)

        timer_tip = QLabel(
            "Pause preserves the current time. Reset asks before discarding unlogged time."
        )
        timer_tip.setObjectName("Muted")
        timer_tip.setWordWrap(True)
        timer_tip.setAlignment(Qt.AlignCenter)
        timer_card.layout.addWidget(timer_tip)
        self.study_timer_tip = timer_tip
        self.study_timer_stage = timer_stage
        self.study_timer_scroll = make_card_scrollable(timer_card)

        recent = Card(
            "📚 Recent Sessions",
            "Your latest logged study activity.",
        )
        recent.setMinimumWidth(0)
        recent.layout.setContentsMargins(14, 12, 14, 12)
        recent.layout.setSpacing(7)
        self.study_recent_card = recent
        self.session_list = QListWidget()
        self.session_list.setWordWrap(True)
        self.session_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.session_list.setMinimumHeight(54)
        self.session_list.itemDoubleClicked.connect(
            lambda _item: self.open_selected_session_workspace()
        )
        recent.layout.addWidget(self.session_list, 1)
        recent_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.study_recent_actions = recent_actions
        open_linked = QPushButton("Open Linked Task Workspace")
        open_linked.clicked.connect(self.open_selected_session_workspace)
        recent_actions.addWidget(open_linked)
        recent_actions.addStretch()
        recent.layout.addLayout(recent_actions)

        # The left side is intentionally a column of two cards: the compact
        # timer above the independently scrollable recent-session list.
        left_column = QWidget()
        left_column.setMinimumWidth(0)
        left_column.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(timer_card, 56)
        left_layout.addWidget(recent, 44)
        self.study_left_column = left_column
        self.study_left_layout = left_layout

        # Session log remains the large right-hand card and scrolls internally.
        log_card = Card(
            "📝 Log Session",
            "Document enough detail to support streaks, achievements, weekly summaries, and job-readiness evidence.",
        )
        log_card.layout.setContentsMargins(18, 16, 18, 16)
        log_card.layout.setSpacing(10)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(9)
        form_grid.setColumnStretch(1, 1)
        form_grid.setColumnStretch(3, 1)
        form_grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_date = QLineEdit(date.today().isoformat())
        self.session_hours = QLineEdit("1")
        self.session_productivity = QSpinBox()
        self.session_productivity.setRange(1, 10)
        self.session_productivity.setValue(7)
        self.session_sql = QSpinBox()
        self.session_sql.setRange(0, 20)
        self.session_task = QComboBox()
        self.session_task.addItem("No linked task", None)

        self.session_google = QLineEdit()
        self.session_google.setPlaceholderText(
            "Course, module, or lesson completed"
        )
        self.session_datacamp = QLineEdit()
        self.session_datacamp.setPlaceholderText(
            "Chapter or exercise completed"
        )
        self.session_portfolio = QLineEdit()
        self.session_portfolio.setPlaceholderText(
            "Milestone or project work completed"
        )
        self.session_notes = QTextEdit()
        self.session_notes.setPlaceholderText(
            "Key takeaways, blockers, questions, or next steps"
        )
        self.session_notes.setMinimumHeight(72)
        self.session_notes.setMaximumHeight(150)

        form_grid.addWidget(QLabel("Date"), 0, 0)
        form_grid.addWidget(self.session_date, 0, 1)
        form_grid.addWidget(QLabel("Hours"), 0, 2)
        form_grid.addWidget(self.session_hours, 0, 3)

        form_grid.addWidget(QLabel("Productivity"), 1, 0)
        form_grid.addWidget(self.session_productivity, 1, 1)
        form_grid.addWidget(QLabel("SQL problems"), 1, 2)
        form_grid.addWidget(self.session_sql, 1, 3)

        form_grid.addWidget(QLabel("Linked task"), 2, 0)
        form_grid.addWidget(self.session_task, 2, 1, 1, 3)

        form_grid.addWidget(QLabel("Google progress"), 3, 0)
        form_grid.addWidget(self.session_google, 3, 1, 1, 3)

        form_grid.addWidget(QLabel("DataCamp progress"), 4, 0)
        form_grid.addWidget(self.session_datacamp, 4, 1, 1, 3)

        form_grid.addWidget(QLabel("Portfolio progress"), 5, 0)
        form_grid.addWidget(self.session_portfolio, 5, 1, 1, 3)

        form_grid.addWidget(QLabel("Notes"), 6, 0)
        form_grid.addWidget(self.session_notes, 6, 1, 1, 3)

        form_host = QWidget()
        form_host.setMinimumWidth(0)
        form_host.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        form_host.setLayout(form_grid)
        log_card.layout.addWidget(form_host)
        self.study_log_form_host = form_host

        save = QPushButton("✅ Finish and Log Session")
        save.setObjectName("Primary")
        save.setMinimumHeight(38)
        save.clicked.connect(self.save_session)
        log_card.layout.addWidget(save)
        self.study_log_scroll = make_card_scrollable(log_card)
        log_card._content_host.layout().setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.study_body_grid = body
        self.study_timer_card = timer_card
        self.study_log_card = log_card
        body.addWidget(left_column, 0, 0)
        body.addWidget(log_card, 0, 1)
        body.setColumnStretch(0, 40)
        body.setColumnStretch(1, 60)
        body.setRowStretch(0, 1)
        root.addLayout(body, 1)

        def update_study_layout(width):
            clear_layout_positions(self.study_body_grid)
            horizontal = width >= 580
            if horizontal:
                self.study_body_grid.addWidget(self.study_left_column, 0, 0)
                self.study_body_grid.addWidget(self.study_log_card, 0, 1)
                self.study_body_grid.setColumnStretch(0, 40)
                self.study_body_grid.setColumnStretch(1, 60)
                self.study_body_grid.setRowStretch(0, 1)
            else:
                self.study_body_grid.addWidget(self.study_left_column, 0, 0)
                self.study_body_grid.addWidget(self.study_log_card, 1, 0)
                self.study_body_grid.setColumnStretch(0, 1)
                self.study_body_grid.setRowStretch(0, 1)
                self.study_body_grid.setRowStretch(1, 1)

            set_box_direction(self.study_timer_controls, width < 500, 6)
            set_box_direction(self.study_recent_actions, width < 520, 6)

            viewport_height = max(0, page.viewport().height())
            compact_height = viewport_height < 790
            self.study_timer_tip.setVisible(not compact_height)
            self.study_timer_subtitle.setVisible(not compact_height)
            self.study_timer_stage.setMinimumHeight(86 if compact_height else 104)
            self.study_circular_timer.set_dashboard_density(
                "ultra" if compact_height else "compact"
            )
            self.study_use_time_button.setText(
                "📝 Use Time in Session Log"
                if compact_height
                else "📝 Use Current Time in Session Log"
            )
            self.study_timer_card.layout.setContentsMargins(
                9 if compact_height else 14,
                8 if compact_height else 12,
                9 if compact_height else 14,
                8 if compact_height else 12,
            )
            self.study_timer_card.layout.setSpacing(4 if compact_height else 7)
            self.study_log_card._content_host.layout().setContentsMargins(
                12 if compact_height else 18,
                10 if compact_height else 16,
                12 if compact_height else 18,
                10 if compact_height else 16,
            )
            self.study_log_card._content_host.layout().setSpacing(
                7 if compact_height else 10
            )
            self.session_notes.setMinimumHeight(58 if compact_height else 72)
            self.session_notes.setMaximumHeight(110 if compact_height else 150)

            margins = root.contentsMargins()
            header_height = page.header.sizeHint().height() if page.header else 0
            body_height = max(260, viewport_height - margins.top() - margins.bottom() - header_height - root.spacing())
            if horizontal:
                left_gap = self.study_left_layout.spacing()
                timer_height = max(190, round((body_height - left_gap) * 0.56))
                recent_height = max(140, body_height - left_gap - timer_height)
                self.study_left_column.setFixedHeight(body_height)
                self.study_timer_card.setFixedHeight(timer_height)
                self.study_recent_card.setFixedHeight(recent_height)
                self.study_log_card.setFixedHeight(body_height)
            else:
                self.study_left_column.setMinimumHeight(0)
                self.study_left_column.setMaximumHeight(16777215)
                for card in (
                    self.study_timer_card,
                    self.study_recent_card,
                    self.study_log_card,
                ):
                    card.setMinimumHeight(0)
                    card.setMaximumHeight(16777215)

            for card in (
                self.study_timer_card,
                self.study_recent_card,
                self.study_log_card,
            ):
                card.setSizePolicy(
                    QSizePolicy.Policy.Ignored,
                    QSizePolicy.Policy.Expanding,
                )

        self._register_page_responsive(page, update_study_layout)
        page.heightChanged.connect(
            lambda _height: update_study_layout(max(0, page.viewport().width()))
        )
        return page

    # ---------- Readiness ----------
    def readiness_page(self):
        page, root = self.page(
            "🎯 Job Readiness",
            "Connect learning, portfolio work, and professional evidence directly to employability.",
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        content = QWidget()
        content.setObjectName(
            "ReadinessScrollContent"
        )
        content_layout = QVBoxLayout(
            content
        )
        content_layout.setContentsMargins(
            0,
            0,
            8,
            8,
        )
        content_layout.setSpacing(12)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.readiness_rings = {}
        rings = QGridLayout()
        self.readiness_rings_grid = rings
        self.readiness_ring_cards = []
        rings.setSpacing(10)

        for title, color in [
            ("Technical Skills", COLORS["blue"]),
            ("Portfolio", COLORS["purple"]),
            ("Interview Practice", COLORS["green"]),
            ("Networking", COLORS["orange"]),
            ("Applications", COLORS["gold"]),
            ("Overall", COLORS["cyan"]),
        ]:
            card = Card()
            card.setMinimumHeight(104)
            card.setMaximumHeight(16777215)
            card.layout.setContentsMargins(10, 8, 10, 8)

            ring = Ring(title, color)
            card.layout.addWidget(ring)
            self.readiness_ring_cards.append(card)
            self.readiness_rings[title] = ring

        content_layout.addLayout(rings)

        body = QGridLayout()
        self.readiness_body_grid = body
        body.setHorizontalSpacing(10)
        body.setVerticalSpacing(10)

        evidence_card = Card(
            "✅ Demonstrated Evidence",
            "Proof that supports your résumé, portfolio, and interview stories.",
        )
        evidence_card.setMinimumHeight(380)
        evidence_help = QLabel(
            (
                "Add proof you could show or explain to an employer: "
                "a completed query, dashboard, course deliverable, "
                "work example, certification, or portfolio artifact."
            )
        )
        evidence_help.setObjectName("Muted")
        evidence_help.setWordWrap(True)
        evidence_card.layout.addWidget(
            evidence_help
        )

        self.evidence_list = QListWidget()
        self.evidence_list.setWordWrap(True)
        self.evidence_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.evidence_list.setMinimumHeight(210)
        self.evidence_list.itemDoubleClicked.connect(
            self.view_selected_evidence
        )
        evidence_card.layout.addWidget(
            self.evidence_list,
            1,
        )

        evidence_buttons = QHBoxLayout()
        add_evidence = QPushButton(
            "➕ Add Evidence"
        )
        add_evidence.setObjectName("Primary")
        add_evidence.clicked.connect(
            self.add_evidence
        )
        view_evidence = QPushButton(
            "View Selected"
        )
        view_evidence.clicked.connect(
            self.view_selected_evidence
        )
        evidence_buttons.addWidget(
            add_evidence
        )
        evidence_buttons.addWidget(
            view_evidence
        )
        evidence_card.layout.addLayout(
            evidence_buttons
        )

        coach_card = Card(
            "🧭 Readiness Coach",
            "Prioritized recommendations based on your current progress.",
        )
        coach_card.setMinimumHeight(230)
        self.readiness_coach_layout = QVBoxLayout()
        self.readiness_coach_layout.setSpacing(8)
        coach_card.layout.addLayout(self.readiness_coach_layout)
        coach_card.layout.addStretch()

        leverage_card = Card(
            "🚀 Highest Leverage",
            "The next action most likely to improve employability.",
        )
        leverage_card.setMinimumHeight(230)

        leverage_score_row = QHBoxLayout()
        leverage_score_row.addWidget(QLabel("Overall readiness"))
        leverage_score_row.addStretch()

        self.readiness_overall_value = QLabel("0%")
        self.readiness_overall_value.setStyleSheet(
            f"font-size:16pt;font-weight:700;color:{COLORS['purple']};"
        )
        leverage_score_row.addWidget(self.readiness_overall_value)
        leverage_card.layout.addLayout(leverage_score_row)

        self.readiness_overall_progress = QProgressBar()
        self.readiness_overall_progress.setRange(0, 100)
        self.readiness_overall_progress.setTextVisible(False)
        leverage_card.layout.addWidget(self.readiness_overall_progress)

        self.readiness_leverage_title = QLabel("")
        self.readiness_leverage_title.setStyleSheet(
            "font-size:12pt;font-weight:700;"
        )
        self.readiness_leverage_title.setWordWrap(True)
        leverage_card.layout.addWidget(self.readiness_leverage_title)

        self.readiness_leverage_detail = QLabel("")
        self.readiness_leverage_detail.setObjectName("Muted")
        self.readiness_leverage_detail.setWordWrap(True)
        leverage_card.layout.addWidget(self.readiness_leverage_detail)

        leverage_card.layout.addStretch(1)

        continue_button = QPushButton("▶ Continue Highest-Impact Task")
        continue_button.setObjectName("Primary")
        continue_button.setMinimumHeight(38)
        continue_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        continue_button.clicked.connect(self.continue_highest_impact)
        leverage_card.layout.addWidget(continue_button)

        coverage_card = Card(
            "📊 Evidence Coverage",
            "Where your documented proof is strongest and where it is still missing.",
        )
        coverage_card.setMinimumHeight(210)
        self.readiness_coverage_layout = QVBoxLayout()
        self.readiness_coverage_layout.setSpacing(0)
        coverage_card.layout.addLayout(self.readiness_coverage_layout)
        coverage_card.layout.addStretch()

        body.addWidget(evidence_card, 0, 0, 2, 1)
        body.addWidget(coach_card, 0, 1)
        body.addWidget(leverage_card, 0, 2)
        body.addWidget(coverage_card, 1, 1, 1, 2)

        body.setColumnStretch(0, 34)
        body.setColumnStretch(1, 33)
        body.setColumnStretch(2, 33)
        body.setRowStretch(0, 0)
        body.setRowStretch(1, 0)

        content_layout.addLayout(body)

        skills_card = Card(
            "🧠 Skills & Concepts",
            (
                "A live inventory of what you have learned, what you are "
                "currently studying, and what remains to unlock."
            ),
        )
        self.skills_summary_label = QLabel("")
        self.skills_summary_label.setObjectName("Muted")
        self.skills_summary_label.setWordWrap(True)
        skills_card.layout.addWidget(self.skills_summary_label)

        self.skills_tabs = QTabWidget()
        self.skills_tabs.setMinimumWidth(0)
        self.skills_tabs.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        self.skills_learned_list = QListWidget()
        self.skills_learned_list.setWordWrap(True)
        self.skills_learned_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.skills_progress_list = QListWidget()
        self.skills_progress_list.setWordWrap(True)
        self.skills_progress_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.skills_locked_list = QListWidget()
        self.skills_locked_list.setWordWrap(True)
        self.skills_locked_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        for skill_list in (
            self.skills_learned_list,
            self.skills_progress_list,
            self.skills_locked_list,
        ):
            skill_list.setWordWrap(True)
            skill_list.setSpacing(4)
            skill_list.setMinimumHeight(170)

        self.skills_tabs.addTab(self.skills_learned_list, "Learned")
        self.skills_tabs.addTab(self.skills_progress_list, "In Progress")
        self.skills_tabs.addTab(self.skills_locked_list, "Locked")
        skills_card.layout.addWidget(self.skills_tabs)
        skills_card.setMinimumHeight(270)
        content_layout.addWidget(skills_card)
        content_layout.addStretch(1)

        def update_readiness_layout(width):
            ring_columns = 6 if width >= 1180 else 3 if width >= 760 else 2 if width >= 520 else 1
            reflow_grid(
                self.readiness_rings_grid,
                self.readiness_ring_cards,
                ring_columns,
            )
            clear_layout_positions(self.readiness_body_grid)
            if width >= 1120:
                self.readiness_body_grid.addWidget(evidence_card, 0, 0, 2, 1)
                self.readiness_body_grid.addWidget(coach_card, 0, 1)
                self.readiness_body_grid.addWidget(leverage_card, 0, 2)
                self.readiness_body_grid.addWidget(coverage_card, 1, 1, 1, 2)
                self.readiness_body_grid.setColumnStretch(0, 34)
                self.readiness_body_grid.setColumnStretch(1, 33)
                self.readiness_body_grid.setColumnStretch(2, 33)
            elif width >= 720:
                self.readiness_body_grid.addWidget(evidence_card, 0, 0, 1, 2)
                self.readiness_body_grid.addWidget(coach_card, 1, 0)
                self.readiness_body_grid.addWidget(leverage_card, 1, 1)
                self.readiness_body_grid.addWidget(coverage_card, 2, 0, 1, 2)
                self.readiness_body_grid.setColumnStretch(0, 1)
                self.readiness_body_grid.setColumnStretch(1, 1)
            else:
                for row, card in enumerate(
                    (evidence_card, coach_card, leverage_card, coverage_card)
                ):
                    self.readiness_body_grid.addWidget(card, row, 0)
                self.readiness_body_grid.setColumnStretch(0, 1)

        self._register_page_responsive(page, update_readiness_layout)
        return page

    # ---------- Applications ----------
    def applications_page(self):
        page, root = self.page(
            "💼 Applications CRM",
            "Move opportunities from wishlist to offer using a visual pipeline.",
        )
        page.set_outer_scroll_enabled(False)

        applications_body = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        applications_body.setSpacing(10)
        self.applications_body_layout = applications_body

        form_card = Card("Add Opportunity")
        self.applications_form_card = form_card
        form = QFormLayout()
        self.app_date = QLineEdit(date.today().isoformat())
        self.app_company = QLineEdit()
        self.app_role = QLineEdit()
        self.app_location = QLineEdit()
        self.app_source = QLineEdit()
        self.app_status = QComboBox()
        self.app_status.addItems(
            ["Wishlist", "Applying", "Applied", "Interview", "Final", "Offer", "Rejected"]
        )
        self.app_follow_up = QLineEdit()
        self.app_resume = QLineEdit()
        self.app_contact = QLineEdit()
        self.app_notes = QTextEdit()
        self.app_notes.setMinimumHeight(85)
        self.app_notes.setMaximumHeight(150)
        for label, widget in [
            ("Date", self.app_date),
            ("Company", self.app_company),
            ("Role", self.app_role),
            ("Location", self.app_location),
            ("Source", self.app_source),
            ("Status", self.app_status),
            ("Follow-up", self.app_follow_up),
            ("Resume version", self.app_resume),
            ("Contact", self.app_contact),
            ("Notes", self.app_notes),
        ]:
            form.addRow(label, widget)
        form_card.layout.addLayout(form)
        add = QPushButton("Add Opportunity")
        add.setObjectName("Primary")
        add.clicked.connect(self.add_application)
        form_card.layout.addWidget(add)
        self.applications_form_scroll = make_card_scrollable(form_card)
        applications_body.addWidget(form_card, 0)

        kanban_scroll = QScrollArea()
        kanban_scroll.setWidgetResizable(True)
        kanban_host = QWidget()
        self.kanban_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, kanban_host)
        self.kanban_host = kanban_host
        self.kanban_layout.setSpacing(8)
        kanban_scroll.setWidget(kanban_host)
        kanban_scroll.setMinimumSize(0, 0)
        kanban_scroll.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )
        self.applications_kanban_scroll = kanban_scroll
        applications_body.addWidget(kanban_scroll, 1)
        root.addLayout(applications_body, 1)

        def update_applications_layout(width):
            stacked = width < 620
            set_box_direction(self.applications_body_layout, stacked, 10)
            # Keep pipeline columns horizontal at supported desktop widths so
            # the kanban card scrolls internally rather than growing the page.
            vertical = width < 540
            set_box_direction(self.kanban_layout, vertical, 8)
            if stacked:
                self.applications_form_card.setMinimumWidth(0)
                self.applications_form_card.setMaximumWidth(16777215)
                self.applications_kanban_scroll.setMinimumWidth(0)
                self.applications_kanban_scroll.setMaximumWidth(16777215)
            else:
                form_width = 250 if width < 800 else 300 if width < 1100 else 340
                page_margins = page.content_layout.contentsMargins()
                available_body_width = max(
                    0,
                    width - page_margins.left() - page_margins.right(),
                )
                pipeline_width = max(
                    240,
                    available_body_width
                    - form_width
                    - self.applications_body_layout.spacing(),
                )
                self.applications_form_card.setMinimumWidth(form_width)
                self.applications_form_card.setMaximumWidth(form_width)
                # The kanban host is intentionally wider than its viewport and
                # scrolls internally.  Cap the viewport itself so its child
                # size hint cannot force the outer page wider or overlap the
                # fixed-width form card.
                self.applications_kanban_scroll.setMinimumWidth(pipeline_width)
                self.applications_kanban_scroll.setMaximumWidth(pipeline_width)
            for card in self.kanban_host.findChildren(Card):
                card.setMinimumWidth(0 if vertical else 220)
                card.setMaximumWidth(16777215)

        self._register_page_responsive(page, update_applications_layout)
        return page

    # ---------- Review ----------
    def review_page(self):
        page, root = self.page(
            "📝 Weekly Review",
            "Turn your activity into an automatic coaching summary.",
        )
        page.set_outer_scroll_enabled(False)
        body = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.review_body_layout = body
        form_card = Card("Generate Summary")
        form = QFormLayout()
        self.review_win = QTextEdit()
        self.review_blocker = QTextEdit()
        self.review_sql = QTextEdit()
        self.review_adjustment = QTextEdit()
        self.review_confidence = QSpinBox()
        self.review_confidence.setRange(1, 10)
        self.review_confidence.setValue(7)
        form.addRow("Biggest win", self.review_win)
        form.addRow("Primary blocker", self.review_blocker)
        form.addRow("SQL topic to review", self.review_sql)
        form.addRow("Next sprint adjustment", self.review_adjustment)
        form.addRow("Confidence (1–10)", self.review_confidence)
        form_card.layout.addLayout(form)
        generate = QPushButton("Generate Weekly Summary")
        generate.setObjectName("Primary")
        generate.clicked.connect(self.generate_summary)
        form_card.layout.addWidget(generate)
        workspace_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.review_workspace_buttons = workspace_buttons
        retrospective = QPushButton("Open Retrospective Workspace")
        retrospective.clicked.connect(
            lambda: self.open_weekly_workspace("retrospective")
        )
        study_plan = QPushButton("Open Study Plan Workspace")
        study_plan.clicked.connect(
            lambda: self.open_weekly_workspace("study_plan")
        )
        workspace_buttons.addWidget(retrospective)
        workspace_buttons.addWidget(study_plan)
        form_card.layout.addLayout(workspace_buttons)
        self.review_form_scroll = make_card_scrollable(form_card)
        body.addWidget(form_card, 1)

        summaries = Card("Saved Summaries")
        self.summary_list = QListWidget()
        self.summary_list.setWordWrap(True)
        self.summary_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        summaries.layout.addWidget(self.summary_list)
        body.addWidget(summaries, 1)
        root.addLayout(body, 1)

        def update_review_layout(width):
            set_box_direction(self.review_body_layout, width < 620, 10)
            set_box_direction(self.review_workspace_buttons, width < 620, 7)
            self.summary_list.setMinimumHeight(0)

        self._register_page_responsive(page, update_review_layout)
        return page

    # ---------- Publish ----------
    def publish_page(self):
        page, root = self.page(
            "🚀 Publish & Git",
            "Publish readable progress, review changes, commit, and push.",
        )
        card = Card("Repository Status")
        publish_button = QPushButton("Publish Progress Snapshot")
        publish_button.setObjectName("Primary")
        publish_button.clicked.connect(self.publish_progress)
        card.layout.addWidget(publish_button)

        self.git_status = QTextEdit()
        self.git_status.setReadOnly(True)
        self.git_status.setMinimumHeight(280)
        card.layout.addWidget(self.git_status)

        self.commit_message = QLineEdit("progress: update career accelerator")
        card.layout.addWidget(self.commit_message)

        buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.publish_buttons = buttons
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_git)
        commit = QPushButton("Commit")
        commit.clicked.connect(self.commit_git)
        push = QPushButton("Push")
        push.clicked.connect(self.push_git)
        buttons.addWidget(refresh)
        buttons.addWidget(commit)
        buttons.addWidget(push)
        card.layout.addLayout(buttons)
        root.addWidget(card)

        def update_publish_layout(width):
            set_box_direction(self.publish_buttons, width < 560, 7)

        self._register_page_responsive(page, update_publish_layout)
        return page

    # ---------- Settings ----------
    def settings_page(self):
        page, root = self.page(
            "⚙️ Settings",
            "Manage application behavior, backups, repository access, and optional future integrations.",
        )

        settings_grid = QGridLayout()
        self.settings_grid = settings_grid
        settings_grid.setHorizontalSpacing(12)
        settings_grid.setVerticalSpacing(12)

        # General behavior.
        general_card = Card(
            "⚙️ Application",
            "Local behavior and automatic backup timing.",
        )
        general_card.layout.setContentsMargins(18, 16, 18, 16)
        general_card.layout.setSpacing(10)

        autosave_row = QHBoxLayout()
        autosave_row.setSpacing(12)
        autosave_label = QLabel("Autosave interval")
        autosave_row.addWidget(autosave_label)
        autosave_row.addStretch()

        self.autosave_minutes = QSpinBox()
        self.autosave_minutes.setRange(1, 60)
        self.autosave_minutes.setSuffix(" min")
        self.autosave_minutes.setValue(
            int(
                setting(
                    self.conn,
                    "autosave_minutes",
                    "5",
                )
            )
        )
        self.autosave_minutes.setMinimumWidth(92)
        self.autosave_minutes.setMaximumWidth(120)
        autosave_row.addWidget(self.autosave_minutes)
        general_card.layout.addLayout(autosave_row)

        scale_header = QHBoxLayout()
        scale_header.setSpacing(10)
        scale_label = QLabel("Text and button size")
        scale_header.addWidget(scale_label)
        scale_header.addStretch()
        self.interface_scale_value = QLabel(
            f"{round(self._content_scale * 100):d}%"
        )
        self.interface_scale_value.setObjectName("Muted")
        self.interface_scale_value.setMinimumWidth(44)
        self.interface_scale_value.setAlignment(Qt.AlignRight)
        scale_header.addWidget(self.interface_scale_value)
        general_card.layout.addLayout(scale_header)

        scale_row = QHBoxLayout()
        scale_row.setSpacing(9)
        smaller = QLabel("A")
        smaller.setObjectName("Muted")
        scale_row.addWidget(smaller)
        self.interface_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.interface_scale_slider.setRange(80, 120)
        self.interface_scale_slider.setSingleStep(5)
        self.interface_scale_slider.setPageStep(5)
        self.interface_scale_slider.setTickInterval(5)
        self.interface_scale_slider.setValue(
            round(self._content_scale * 100)
        )
        self.interface_scale_slider.setToolTip(
            "Scale text, buttons, editors, lists, and form controls while "
            "keeping card dimensions tied to the responsive window layout."
        )
        self.interface_scale_slider.valueChanged.connect(
            self.change_interface_scale
        )
        scale_row.addWidget(self.interface_scale_slider, 1)
        larger = QLabel("A")
        larger.setStyleSheet("font-size:14pt;font-weight:700;")
        scale_row.addWidget(larger)
        general_card.layout.addLayout(scale_row)

        scale_note = QLabel(
            "Changes apply immediately. Cards continue to resize only with "
            "the application window."
        )
        scale_note.setObjectName("Muted")
        scale_note.setWordWrap(True)
        general_card.layout.addWidget(scale_note)

        save_settings = QPushButton("💾 Save Application Settings")
        save_settings.setObjectName("Primary")
        save_settings.clicked.connect(self.save_settings)
        general_card.layout.addWidget(save_settings)

        # Data maintenance.
        data_card = Card(
            "🗄️ Data and Recovery",
            "Create a backup or rebuild task data from repository files.",
        )
        data_card.layout.setContentsMargins(18, 16, 18, 16)
        data_card.layout.setSpacing(9)

        backup = QPushButton("💾 Create Database Backup")
        backup.setObjectName("Secondary")
        backup.clicked.connect(self.backup_database)
        data_card.layout.addWidget(backup)

        self.storage_summary_label = QLabel(self.storage_summary_text())
        self.storage_summary_label.setObjectName("Muted")
        self.storage_summary_label.setWordWrap(True)
        data_card.layout.addWidget(self.storage_summary_label)

        storage_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.settings_storage_actions = storage_actions
        clean_backups = QPushButton("🧹 Clean Old Backups")
        clean_backups.setObjectName("Secondary")
        clean_backups.clicked.connect(self.clean_old_backups)
        open_data = QPushButton("📂 Open Data Folder")
        open_data.setObjectName("Secondary")
        open_data.clicked.connect(self.open_data_folder)
        storage_actions.addWidget(clean_backups)
        storage_actions.addWidget(open_data)
        data_card.layout.addLayout(storage_actions)

        restore = QPushButton(
            "🔄 Restore Tasks From Repository Files"
        )
        restore.setObjectName("Secondary")
        restore.clicked.connect(self.restore_tasks)
        data_card.layout.addWidget(restore)

        rebuild_snapshot = QPushButton(
            "🗓️ Rebuild Today's Snapshot"
        )
        rebuild_snapshot.setObjectName("Secondary")
        rebuild_snapshot.setToolTip(
            "Recalculate Today's Focus from current progress without erasing completions or study history."
        )
        rebuild_snapshot.clicked.connect(
            self.confirm_rebuild_today_snapshot
        )
        self.rebuild_today_snapshot_button = rebuild_snapshot
        data_card.layout.addWidget(rebuild_snapshot)

        data_note = QLabel(
            "Automatic backups are deduplicated and retained as the newest 10, daily copies for 7 days, and weekly copies for 4 weeks."
        )
        data_note.setObjectName("Muted")
        data_note.setWordWrap(True)
        data_card.layout.addWidget(data_note)

        # Repository paths.
        repository_card = Card(
            "📁 Repository and Storage",
            "Quick access to the local project and working data.",
        )
        repository_card.layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )
        repository_card.layout.setSpacing(9)

        open_repo = QPushButton("📂 Open Repository Folder")
        open_repo.setObjectName("Primary")
        open_repo.clicked.connect(lambda: os.startfile(ROOT))
        repository_card.layout.addWidget(open_repo)

        database_location = QLabel(
            f"Database\n{ROOT / 'data' / 'career_accelerator.db'}"
        )
        database_location.setObjectName("Muted")
        database_location.setWordWrap(True)
        database_location.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        repository_card.layout.addWidget(database_location)

        backup_location = QLabel(
            f"Backups\n{ROOT / 'backups'}"
        )
        backup_location.setObjectName("Muted")
        backup_location.setWordWrap(True)
        backup_location.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        repository_card.layout.addWidget(backup_location)

        reset_card = Card(
            "⚠️ Reset Progress",
            "Prepare a clean starter profile for yourself or another learner.",
        )
        reset_card.layout.setContentsMargins(18, 16, 18, 16)
        reset_card.layout.setSpacing(9)

        reset_summary = QLabel(
            "Reset returns the app to Week 1, Google Course 1, Module 1, "
            "Portfolio Project 1, and today as the new start date. It clears "
            "all tracked progress while preserving technical preferences and backups."
        )
        reset_summary.setObjectName("Muted")
        reset_summary.setWordWrap(True)
        reset_card.layout.addWidget(reset_summary)

        self.reset_progress_button = QPushButton(
            "🗑️ Reset All Progress"
        )
        self.reset_progress_button.setObjectName("Danger")
        self.reset_progress_button.setMinimumHeight(40)
        self.reset_progress_button.clicked.connect(
            self.confirm_factory_reset
        )
        reset_card.layout.addWidget(
            self.reset_progress_button
        )

        self.settings_cards = [
            general_card,
            data_card,
            repository_card,
            reset_card,
        ]
        settings_grid.addWidget(general_card, 0, 0)
        settings_grid.addWidget(data_card, 0, 1)
        settings_grid.addWidget(repository_card, 1, 0)
        settings_grid.addWidget(reset_card, 1, 1)
        settings_grid.setColumnStretch(0, 1)
        settings_grid.setColumnStretch(1, 1)

        root.addLayout(settings_grid)

        status_card = Card("ℹ️ Status")
        status_card.layout.setContentsMargins(18, 12, 18, 12)

        status_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.settings_status_row = status_row
        self.settings_status = QLabel(
            f"Data Career Accelerator v{__version__} • Local SQLite mode"
        )
        self.settings_status.setObjectName("Muted")
        self.settings_status.setWordWrap(True)
        status_row.addWidget(self.settings_status, 1)

        shortcuts = QLabel("Ctrl+K Commands  •  Ctrl+S Backup")
        shortcuts.setObjectName("Muted")
        shortcuts.setAlignment(Qt.AlignRight)
        status_row.addWidget(shortcuts)

        status_card.layout.addLayout(status_row)
        root.addWidget(status_card)
        root.addStretch()

        def update_settings_layout(width):
            columns = 2 if width >= 820 else 1
            reflow_grid(self.settings_grid, self.settings_cards, columns)
            set_box_direction(self.settings_storage_actions, width < 620, 7)
            set_box_direction(self.settings_status_row, width < 650, 7)
            shortcuts.setAlignment(
                Qt.AlignmentFlag.AlignLeft
                if width < 650
                else Qt.AlignmentFlag.AlignRight
            )

        self._register_page_responsive(page, update_settings_layout)
        return page

    # ---------- Task Workspaces ----------
    def task_workspaces_page(self):
        page, root = self.page(
            "🗂️ Task Workspaces",
            (
                "Open every task's notes, reflection, retrospective, schedule, "
                "artifacts, and linked study sessions from one place."
            ),
        )

        quick = Card(
            "Quick Weekly Workspaces",
            "Create or open the current week's planning and reflection documents.",
        )
        quick_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.workspace_quick_row = quick_row
        retrospective = QPushButton("Open Current Retrospective")
        retrospective.setObjectName("Primary")
        retrospective.clicked.connect(
            lambda: self.open_weekly_workspace("retrospective")
        )
        study_plan = QPushButton("Open Current Study Plan")
        study_plan.clicked.connect(
            lambda: self.open_weekly_workspace("study_plan")
        )
        quick_row.addWidget(retrospective)
        quick_row.addWidget(study_plan)
        quick_row.addStretch()
        quick.layout.addLayout(quick_row)
        root.addWidget(quick)

        controls = Card("Find a Task")
        filter_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.workspace_filter_row = filter_row
        filter_row.addWidget(QLabel("Week"))
        self.workspace_week_filter = QComboBox()
        self.workspace_week_filter.addItem("Current Week", "current")
        self.workspace_week_filter.addItem("All Weeks", "all")
        for week in range(1, 13):
            self.workspace_week_filter.addItem(f"Week {week}", week)
        self.workspace_week_filter.currentIndexChanged.connect(
            self.refresh_task_workspaces
        )
        filter_row.addWidget(self.workspace_week_filter)

        filter_row.addWidget(QLabel("Status"))
        self.workspace_status_filter = QComboBox()
        self.workspace_status_filter.addItems(
            [
                "All",
                "Not Started",
                "In Progress",
                "Blocked",
                "Deferred",
                "Completed",
            ]
        )
        self.workspace_status_filter.currentTextChanged.connect(
            self.refresh_task_workspaces
        )
        filter_row.addWidget(self.workspace_status_filter)

        self.workspace_search = QLineEdit()
        self.workspace_search.setPlaceholderText("Search task names")
        self.workspace_search.textChanged.connect(self.refresh_task_workspaces)
        filter_row.addWidget(self.workspace_search, 1)
        controls.layout.addLayout(filter_row)
        root.addWidget(controls)

        workspace_card = Card(
            "Task Library",
            "Double-click a task or select it and choose Open Workspace.",
        )
        self.workspace_task_summary = QLabel("")
        self.workspace_task_summary.setObjectName("Muted")
        workspace_card.layout.addWidget(self.workspace_task_summary)
        self.workspace_task_list = QListWidget()
        self.workspace_task_list.setWordWrap(True)
        self.workspace_task_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.workspace_task_list.setMinimumHeight(300)
        self.workspace_task_list.itemDoubleClicked.connect(
            lambda _item: self.open_selected_task_workspace()
        )
        workspace_card.layout.addWidget(self.workspace_task_list, 1)

        buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.workspace_buttons = buttons
        open_button = QPushButton("Open Workspace")
        open_button.setObjectName("Primary")
        open_button.clicked.connect(self.open_selected_task_workspace)
        session_button = QPushButton("Start Linked Study Session")
        session_button.clicked.connect(self.start_selected_workspace_session)
        edit_button = QPushButton("Edit Task")
        edit_button.clicked.connect(self.edit_selected_workspace_task)
        buttons.addWidget(open_button)
        buttons.addWidget(session_button)
        buttons.addWidget(edit_button)
        buttons.addStretch()
        workspace_card.layout.addLayout(buttons)
        root.addWidget(workspace_card, 1)

        def update_workspace_layout(width):
            set_box_direction(self.workspace_quick_row, width < 650, 7)
            set_box_direction(self.workspace_filter_row, width < 760, 7)
            set_box_direction(self.workspace_buttons, width < 700, 7)

        self._register_page_responsive(page, update_workspace_layout)
        return page

    def update_time_based_header(self):
        """Refresh the Dashboard greeting and date using the computer's local time."""
        now = datetime.now()
        hour = now.hour

        if 5 <= hour < 12:
            greeting = "Good morning, Dan! 👋"
        elif 12 <= hour < 17:
            greeting = "Good afternoon, Dan! 👋"
        elif 17 <= hour < 22:
            greeting = "Good evening, Dan! 👋"
        else:
            greeting = "Working late, Dan? 🌙"

        if hasattr(self, "dashboard_hero"):
            self.dashboard_hero.setText(greeting)
            self.dashboard_hero.setWordWrap(False)
            self.dashboard_hero.setMinimumHeight(
                self.dashboard_hero.fontMetrics().height() + 4
            )

        if hasattr(self, "dashboard_date"):
            self.dashboard_date.setText(
                f"📅  {now:%A, %B %d, %Y}"
            )

    def update_motivational_text(self):
        quotes = [
            "“Discipline today, opportunity tomorrow.”",
            "“Consistency turns effort into expertise.”",
            "“Progress grows from focused repetition.”",
            "“Clarity comes from doing the work.”",
            "“Build the evidence, then tell the story.”",
            "“Small improvements compound into a new career.”",
            "“Learn deliberately. Apply confidently.”",
            "“Momentum matters more than perfection.”",
        ]

        encouragements = [
            (
                "Small daily improvements lead to big results.",
                "You've got this, Dan!",
            ),
            (
                "Every focused session strengthens your analyst toolkit.",
                "Keep building momentum.",
            ),
            (
                "The portfolio grows one meaningful milestone at a time.",
                "Make today's work visible.",
            ),
            (
                "Consistency is creating the career change.",
                "One strong step is enough for today.",
            ),
            (
                "Your VFX experience is becoming analytical evidence.",
                "Keep connecting your past work to your future role.",
            ),
            (
                "Practice, document, publish, repeat.",
                "That cycle is building job-ready proof.",
            ),
            (
                "You do not need a perfect day to make real progress.",
                "Complete the next highest-impact task.",
            ),
            (
                "The work you log today becomes tomorrow's confidence.",
                "Stay with the plan.",
            ),
        ]

        if hasattr(self, "dashboard_quote"):
            current_quote = self.dashboard_quote.text()
            quote_choices = [
                value for value in quotes
                if value != current_quote
            ] or quotes
            self.dashboard_quote.setText(
                random.choice(quote_choices)
            )

        if (
            hasattr(self, "footer_message")
            and hasattr(self, "footer_subtitle")
        ):
            current_pair = (
                self.footer_message.text(),
                self.footer_subtitle.text(),
            )
            encouragement_choices = [
                value for value in encouragements
                if value != current_pair
            ] or encouragements
            message, subtitle = random.choice(
                encouragement_choices
            )
            self.footer_message.setText(message)
            self.footer_subtitle.setText(subtitle)

    def change_growth_period(self, text):
        try:
            self.growth_days = int(text.split()[0])
        except (ValueError, IndexError):
            self.growth_days = 14
        self.refresh_growth_chart()

    def refresh_growth_chart(self):
        if not hasattr(self, "growth_chart"):
            return

        recent_hours = analytics.daily_hours(
            self.conn,
            self.growth_days,
        )
        self.growth_chart.set_values(recent_hours)

        if hasattr(self, "summary_sparkline"):
            self.summary_sparkline.set_values(
                analytics.weekly_daily_hours(self.conn)
            )

    def _unlock_achievement(self, key, title, description):
        existing = self.conn.execute(
            """SELECT id,title,description
               FROM achievements
               WHERE achievement_key=?""",
            (key,),
        ).fetchone()

        if existing:
            if (
                existing["title"] != title
                or existing["description"] != description
            ):
                self.conn.execute(
                    """UPDATE achievements
                       SET title=?, description=?
                       WHERE achievement_key=?""",
                    (title, description, key),
                )
            return False

        self.conn.execute(
            """INSERT INTO achievements
               (achievement_key,title,description)
               VALUES(?,?,?)""",
            (key, title, description),
        )
        return True

    def roadmap_achievement_details(self, row):
        category = row["category"] or "General"
        label = row["label"].strip()
        week = int(row["week"])
        order = int(row["sort_order"])

        category_config = {
            "Learning": {
                "emoji": "🎓",
                "prefix": "Learning Milestone",
                "accent": COLORS["blue"],
            },
            "SQL": {
                "emoji": "💻",
                "prefix": "SQL Challenge",
                "accent": COLORS["purple"],
            },
            "Portfolio": {
                "emoji": "📁",
                "prefix": "Portfolio Milestone",
                "accent": COLORS["orange"],
            },
            "Review": {
                "emoji": "📝",
                "prefix": "Weekly Reflection",
                "accent": COLORS["green"],
            },
            "General": {
                "emoji": "✅",
                "prefix": "Roadmap Accomplishment",
                "accent": COLORS["gold"],
            },
        }

        config = category_config.get(
            category,
            category_config["General"],
        )

        short_label = label
        if len(short_label) > 42:
            short_label = short_label[:39].rstrip() + "…"

        return {
            "emoji": config["emoji"],
            "accent": config["accent"],
            "title": f"{config['prefix']}: {short_label}",
            "description": (
                f"Week {week} • Roadmap task {order}\n"
                f"{label}"
            ),
        }

    def achievement_visual(self, achievement_key, title):
        if achievement_key.startswith("task:"):
            try:
                task_id = int(
                    achievement_key.split(":", 1)[1]
                )
            except (TypeError, ValueError):
                task_id = None

            if task_id is not None:
                row = self.conn.execute(
                    """SELECT
                           s.week,
                           s.sort_order,
                           s.label,
                           m.category
                       FROM sprint_tasks s
                       LEFT JOIN task_metadata m
                         ON m.task_id=s.id
                       WHERE s.id=?""",
                    (task_id,),
                ).fetchone()
                if row:
                    details = self.roadmap_achievement_details(
                        row
                    )
                    return (
                        details["emoji"],
                        details["accent"],
                    )

        prefix_styles = [
            ("project-task:", "📁", COLORS["orange"]),
            ("sql-problem:", "💻", COLORS["purple"]),
            ("study-session:", "⏱️", COLORS["cyan"]),
            ("application:", "💼", COLORS["gold"]),
            ("milestone:", "🏆", COLORS["green"]),
        ]
        for prefix, emoji, accent in prefix_styles:
            if achievement_key.startswith(prefix):
                return emoji, accent

        title_styles = {
            "Portfolio Milestone Complete": (
                "📁",
                COLORS["orange"],
            ),
            "SQL Problem Solved": (
                "💻",
                COLORS["purple"],
            ),
            "Study Session Logged": (
                "⏱️",
                COLORS["cyan"],
            ),
            "Application Tracked": (
                "💼",
                COLORS["gold"],
            ),
        }
        return title_styles.get(
            title,
            ("🏆", COLORS["purple"]),
        )

    def sync_achievement_records(self):
        """Persist rewards for every completed activity and major milestone."""
        unlocked = []
        valid_keys = set()

        def unlock(key, title, description):
            valid_keys.add(key)
            if self._unlock_achievement(
                key,
                title,
                description,
            ):
                unlocked.append(title)

        canonical_activities = (
            achievements.canonical_completed_activities(
                self.conn
            )
        )
        completed_tasks = canonical_activities[
            "tasks"
        ]
        completed_project_tasks = (
            canonical_activities[
                "projects"
            ]
        )
        sql_rows = canonical_activities[
            "sql"
        ]

        # Specialized records are the canonical representation of SQL and
        # portfolio accomplishments. Generic roadmap-task badges are generated
        # only for work that has no specialized completion record.
        for row in sql_rows:
            unlock(
                f"sql-problem:{row['id']}",
                "SQL Problem Solved",
                row["title"],
            )

        for row in completed_project_tasks:
            unlock(
                f"project-task:{row['id']}",
                "Portfolio Milestone Complete",
                row["label"],
            )

        for row in completed_tasks:
            details = self.roadmap_achievement_details(
                row
            )
            unlock(
                f"task:{row['id']}",
                details["title"],
                details["description"],
            )

        session_rows = self.conn.execute(
            """SELECT id,session_date,hours
               FROM study_sessions
               ORDER BY id"""
        ).fetchall()
        for row in session_rows:
            unlock(
                f"study-session:{row['id']}",
                "Study Session Logged",
                f"{row['session_date']} • {float(row['hours']):g}h",
            )

        application_rows = self.conn.execute(
            """SELECT id,company,role
               FROM applications
               ORDER BY id"""
        ).fetchall()
        for row in application_rows:
            unlock(
                f"application:{row['id']}",
                "Application Tracked",
                f"{row['role']} at {row['company']}",
            )

        session_count = len(session_rows)
        task_count = int(
            canonical_activities[
                "task_logical_count"
            ]
        )
        project_count = len(completed_project_tasks)
        sql_count = len(sql_rows)
        application_count = len(application_rows)
        total_hours = sum(
            float(row["hours"])
            for row in session_rows
        )
        best_streak = analytics.best_streak(self.conn)
        readiness_data = analytics.readiness(
            self.conn,
            self.state,
        )

        milestones = [
            (
                "milestone:first-session",
                session_count >= 1,
                "Getting Started",
                "Log your first study session.",
            ),
            (
                "milestone:five-sessions",
                session_count >= 5,
                "Focus Habit",
                "Log five study sessions.",
            ),
            (
                "milestone:ten-sessions",
                session_count >= 10,
                "Consistent Learner",
                "Log ten study sessions.",
            ),
            (
                "milestone:one-hour",
                total_hours >= 1,
                "First Focus Hour",
                "Log one hour of focused study.",
            ),
            (
                "milestone:ten-hours",
                total_hours >= 10,
                "Ten-Hour Builder",
                "Log ten study hours.",
            ),
            (
                "milestone:twenty-five-hours",
                total_hours >= 25,
                "Deep Work",
                "Log twenty-five study hours.",
            ),
            (
                "milestone:streak-three",
                best_streak >= 3,
                "Momentum",
                "Build a three-day study streak.",
            ),
            (
                "milestone:streak-seven",
                best_streak >= 7,
                "Week Warrior",
                "Build a seven-day study streak.",
            ),
            (
                "milestone:first-task",
                task_count >= 1,
                "First Roadmap Win",
                "Complete your first roadmap task.",
            ),
            (
                "milestone:five-tasks",
                task_count >= 5,
                "Task Builder",
                "Complete five roadmap tasks.",
            ),
            (
                "milestone:ten-tasks",
                task_count >= 10,
                "On Track",
                "Complete ten roadmap tasks.",
            ),
            (
                "milestone:twenty-five-tasks",
                task_count >= 25,
                "Roadmap Momentum",
                "Complete twenty-five roadmap tasks.",
            ),
            (
                "milestone:first-sql",
                sql_count >= 1,
                "First Query",
                "Complete your first SQL problem.",
            ),
            (
                "milestone:five-sql",
                sql_count >= 5,
                "SQL Starter",
                "Complete five SQL problems.",
            ),
            (
                "milestone:ten-sql",
                sql_count >= 10,
                "SQL Builder",
                "Complete ten SQL problems.",
            ),
            (
                "milestone:twenty-five-sql",
                sql_count >= 25,
                "SQL Momentum",
                "Complete twenty-five SQL problems.",
            ),
            (
                "milestone:first-project-task",
                project_count >= 1,
                "Project Started",
                "Complete your first portfolio milestone.",
            ),
            (
                "milestone:five-project-tasks",
                project_count >= 5,
                "Project Builder",
                "Complete five portfolio milestones.",
            ),
            (
                "milestone:ten-project-tasks",
                project_count >= 10,
                "Portfolio Momentum",
                "Complete ten portfolio milestones.",
            ),
            (
                "milestone:first-application",
                application_count >= 1,
                "Search Launched",
                "Track your first job application.",
            ),
            (
                "milestone:five-applications",
                application_count >= 5,
                "Application Momentum",
                "Track five job applications.",
            ),
            (
                "milestone:readiness-25",
                readiness_data["Overall"] >= 25,
                "Quarter Ready",
                "Reach 25% overall job readiness.",
            ),
            (
                "milestone:readiness-50",
                readiness_data["Overall"] >= 50,
                "Halfway Ready",
                "Reach 50% overall job readiness.",
            ),
            (
                "milestone:readiness-75",
                readiness_data["Overall"] >= 75,
                "Interview Ready",
                "Reach 75% overall job readiness.",
            ),
        ]

        for key, condition, title, description in milestones:
            if condition:
                unlock(key, title, description)

        removed = achievements.reconcile(
            self.conn,
            valid_keys,
        )
        self.last_removed_achievements = removed

        duplicate_groups = (
            achievements.duplicate_activity_groups(
                self.conn
            )
        )
        if duplicate_groups:
            # Defensive cleanup for any legacy generic task record that still
            # overlaps a canonical SQL or portfolio record.
            for keys in duplicate_groups.values():
                has_specialized = any(
                    key.startswith(
                        (
                            "sql-problem:",
                            "project-task:",
                        )
                    )
                    for key in keys
                )
                if not has_specialized:
                    continue
                for key in keys:
                    if key.startswith(
                        "task:"
                    ):
                        self.conn.execute(
                            """DELETE FROM achievements
                               WHERE achievement_key=?""",
                            (key,),
                        )

        self.conn.commit()
        return unlocked

    def achievement_progress(self):
        session_count = self.conn.execute(
            "SELECT COUNT(*) FROM study_sessions"
        ).fetchone()[0]
        completed_tasks = self.conn.execute(
            "SELECT COUNT(*) FROM sprint_tasks WHERE completed=1"
        ).fetchone()[0]
        sql_count = (
            achievements.completed_sql_count(
                self.conn
            )
        )
        portfolio_count = self.conn.execute(
            "SELECT COUNT(*) FROM project_tasks WHERE completed=1"
        ).fetchone()[0]
        applications = self.conn.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]
        total_hours = self.conn.execute(
            "SELECT COALESCE(SUM(hours),0) FROM study_sessions"
        ).fetchone()[0]
        best_streak = analytics.best_streak(self.conn)
        readiness_data = analytics.readiness(
            self.conn,
            self.state,
        )

        milestones = [
            ("🚀", "Getting Started", "Log your first study session", session_count, 1, COLORS["purple"]),
            ("⏱️", "Focus Habit", "Log five study sessions", session_count, 5, COLORS["cyan"]),
            ("🔥", "Momentum", "Build a three-day study streak", best_streak, 3, COLORS["gold"]),
            ("📅", "Week Warrior", "Build a seven-day study streak", best_streak, 7, COLORS["blue"]),
            ("✅", "First Roadmap Win", "Complete your first roadmap task", completed_tasks, 1, COLORS["green"]),
            ("🎯", "On Track", "Complete ten roadmap tasks", completed_tasks, 10, COLORS["green"]),
            ("💻", "First Query", "Complete your first SQL problem", sql_count, 1, COLORS["purple"]),
            ("🧠", "SQL Builder", "Complete ten SQL problems", sql_count, 10, COLORS["purple"]),
            ("📁", "Project Started", "Complete your first portfolio milestone", portfolio_count, 1, COLORS["orange"]),
            ("🏗️", "Project Builder", "Complete ten portfolio milestones", portfolio_count, 10, COLORS["orange"]),
            ("💼", "Search Launched", "Track your first application", applications, 1, COLORS["gold"]),
            ("📨", "Application Momentum", "Track five applications", applications, 5, COLORS["gold"]),
            ("⌛", "Ten-Hour Builder", "Log ten study hours", total_hours, 10, COLORS["cyan"]),
            ("🌟", "Deep Work", "Log twenty-five study hours", total_hours, 25, COLORS["purple"]),
            ("📈", "Quarter Ready", "Reach 25% overall readiness", readiness_data["Overall"], 25, COLORS["blue"]),
            ("🏆", "Halfway Ready", "Reach 50% overall readiness", readiness_data["Overall"], 50, COLORS["green"]),
        ]

        return [
            {
                "emoji": emoji,
                "title": title,
                "description": description,
                "current": min(float(current), float(target)),
                "target": target,
                "accent": accent,
            }
            for (
                emoji,
                title,
                description,
                current,
                target,
                accent,
            ) in milestones
        ]

    def recent_achievement_records(self, limit=12):
        return self.conn.execute(
            """SELECT
                   achievement_key,
                   title,
                   description,
                   unlocked_at
               FROM achievements
               ORDER BY id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

    def dashboard_achievement_cards(self):
        recent = self.recent_achievement_records(limit=3)

        if recent:
            cards = []
            for row in recent:
                emoji, accent = self.achievement_visual(
                    row["achievement_key"],
                    row["title"],
                )
                cards.append(
                    (
                        emoji,
                        row["title"],
                        row["description"],
                        accent,
                    )
                )
            return cards

        cards = []
        for achievement in self.achievement_progress()[:3]:
            cards.append(
                (
                    achievement["emoji"],
                    achievement["title"],
                    (
                        f"{achievement['description']}\n"
                        f"{achievement['current']:g} / "
                        f"{achievement['target']}"
                    ),
                    achievement["accent"],
                )
            )
        return cards

    def show_all_achievements(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("All Achievements")
        dialog.setStyleSheet(stylesheet(self._ui_scale, self._content_scale))
        dialog.resize(650, 560)

        layout = QVBoxLayout(dialog)

        title = QLabel("🏅 Achievements")
        title.setObjectName("Hero")
        layout.addWidget(title)

        subtitle = QLabel(
            (
                "Achievements reflect currently verified progress. "
                "Undoing or deleting the qualifying activity removes its "
                "related achievement and recalculates milestone badges."
            )
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        unlocked_label = QLabel("Unlocked Rewards")
        unlocked_label.setObjectName("SectionTitle")
        layout.addWidget(unlocked_label)

        achievement_list = QListWidget()
        achievement_list.setWordWrap(True)
        achievement_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        records = self.recent_achievement_records(limit=200)

        if records:
            for row in records:
                emoji, _ = self.achievement_visual(
                    row["achievement_key"],
                    row["title"],
                )
                achievement_list.addItem(
                    f"{emoji} {row['title']}\n"
                    f"    {row['description']}"
                )
        else:
            achievement_list.addItem(
                "No achievements unlocked yet. Complete the first task or log a study session."
            )

        layout.addWidget(achievement_list, 1)

        progress_label = QLabel("Milestone Progress")
        progress_label.setObjectName("SectionTitle")
        layout.addWidget(progress_label)

        progress_list = QListWidget()
        progress_list.setWordWrap(True)
        progress_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        for achievement in self.achievement_progress():
            unlocked = (
                achievement["current"]
                >= achievement["target"]
            )
            prefix = "✅" if unlocked else "🔒"
            progress_list.addItem(
                f"{prefix} {achievement['emoji']} "
                f"{achievement['title']} — "
                f"{achievement['current']:g} / "
                f"{achievement['target']}\n"
                f"    {achievement['description']}"
            )

        layout.addWidget(progress_list, 1)

        close_button = QPushButton("Close")
        close_button.setObjectName("Primary")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    # ---------- Refresh ----------
    def refresh_all(
        self,
        *,
        sync_tracks=True,
    ):
        self.state = state(self.conn)
        if sync_tracks:
            tracks.sync_all(
                self.conn,
                self.state,
            )
            self.state = state(self.conn)

        newly_unlocked = self.sync_achievement_records()

        self.refresh_dashboard(
            sync_tracks=False
        )
        self.refresh_planner()
        self.refresh_learning()
        self.refresh_project()
        self.refresh_sql()
        self.refresh_sessions()
        self.refresh_readiness()
        self.refresh_applications()
        self.refresh_summaries()
        self.refresh_git()
        self.refresh_task_workspaces()

        if newly_unlocked and self.isVisible():
            extra = (
                f"  +{len(newly_unlocked) - 1} more"
                if len(newly_unlocked) > 1
                else ""
            )
            self.statusBar().showMessage(
                f"🏆 Achievement unlocked: "
                f"{newly_unlocked[0]}{extra}",
                7000,
            )

    def dashboard_task_source(self, row):
        modular_source = tracks.source_for_task(
            self.conn,
            row["id"],
        )
        if modular_source:
            return modular_source

        label = str(row["label"] or "").strip()
        applied_source = applied_exercise_source(label)
        if applied_source:
            return applied_source

        duckdb_source = exercise_source(label)
        if duckdb_source:
            return duckdb_source

        lower_label = label.lower()
        category = row["category"] or "General"
        week = int(
            row["week"]
            or self.state["current_week"]
        )

        if "datacamp" in lower_label:
            if "sql" in lower_label:
                return "DataCamp • Introduction to SQL"
            return "DataCamp"

        current_google_match = re.match(
            r"Continue Google Course (\d+), "
            r"Module (\d+)$",
            label,
            re.IGNORECASE,
        )
        if current_google_match:
            return (
                f"Google • Course "
                f"{current_google_match.group(1)}, "
                f"Module "
                f"{current_google_match.group(2)}"
            )

        google_match = re.search(
            r"\[Google Course (\d+)\]",
            label,
            re.IGNORECASE,
        )
        if google_match:
            return (
                f"Google • Course "
                f"{google_match.group(1)}"
            )

        if category == "Learning":
            return (
                f"Google • Course "
                f"{self.state['google_course']}, "
                f"Module {self.state['google_module']}"
            )
        if category == "SQL":
            return "SQL Practice"
        if category == "Portfolio":
            return (
                f"Portfolio • Project "
                f"{self.state['current_project']}"
            )
        if category == "Review":
            return f"Weekly Review • Week {week}"
        return f"Roadmap • Week {week}"

    def refresh_dashboard(
        self,
        *,
        sync_tracks=True,
    ):
        if sync_tracks:
            tracks.sync_all(
                self.conn,
                self.state,
            )
            self.state = state(
                self.conn
            )

        week = self.state["current_week"]
        guide = WEEKLY_GUIDANCE.get(
            week,
            (
                "Keep Moving",
                "Continue the current course",
                "Continue DataCamp",
                [],
                "Advance the project",
            ),
        )

        tasks = self.conn.execute(
            """SELECT s.id,s.label,s.completed,m.estimated_minutes,
                      m.category,m.status
               FROM sprint_tasks s
               LEFT JOIN task_metadata m ON m.task_id=s.id
               WHERE s.week=?
               ORDER BY s.sort_order""",
            (week,),
        ).fetchall()

        done = sum(int(row["completed"]) for row in tasks)
        total = len(tasks)

        sql_count = (
            achievements.completed_sql_count(
                self.conn
            )
        )

        project_rows = self.conn.execute(
            "SELECT completed FROM project_tasks WHERE project_id=?",
            (self.state["current_project"],),
        ).fetchall()
        project_done = sum(int(row["completed"]) for row in project_rows)
        project_total = len(project_rows)

        week_hours = analytics.weekly_hours(self.conn)
        target_hours = float(self.state["weekly_target_hours"])
        weekly_goal = (
            min(100, week_hours / target_hours * 100)
            if target_hours else 0
        )

        ring_values = [
            (
                done / total * 100 if total else 0,
                f"{done} / {total} tasks",
                "●  On Track" if done else "○  Ready to start",
            ),
            (
                (self.state["google_course"] - 1)
                / self.state["google_total_courses"]
                * 100,
                f"Course {self.state['google_course']} • Module {self.state['google_module']}",
                "●  In Progress",
            ),
            (
                min(100, sql_count / self.state["sql_target"] * 100),
                f"{sql_count} / {self.state['sql_target']} problems",
                "●  Keep Going",
            ),
            (
                project_done / project_total * 100 if project_total else 0,
                f"Project {self.state['current_project']}",
                "●  In Progress",
            ),
            (
                weekly_goal,
                f"{week_hours:g}h / {target_hours:g}h",
                f"●  {target_hours:g}h Goal",
            ),
        ]
        for ring, values in zip(self.rings, ring_values):
            ring.set_value(*values)

        self.dashboard_program_meta.setText(
            f"Week {week}  •  Course {self.state['google_course']}  •  "
            f"Project {self.state['current_project']}"
        )
        self.update_time_based_header()
        # BEGIN EXERCISE PACKS
        suggestion = exercise_packs.best_suggestion_for_database(
            ROOT, self.conn, self.state
        )
        self.exercise_suggestion_panel.set_suggestion(suggestion)
        # END EXERCISE PACKS

        readiness_data = analytics.readiness(
            self.conn,
            self.state,
        )
        readiness_messages = coach.recommendations(
            self.conn,
            self.state,
        )
        self.dashboard_mission_percent.setText(
            f"{readiness_data['Overall']}%"
        )
        self.dashboard_mission_progress.setValue(
            readiness_data["Overall"]
        )
        mission_detail = (
            readiness_messages[0]
            if readiness_messages
            else "Continue the current roadmap priorities."
        )
        self.dashboard_mission_detail.setText(
            mission_detail
        )
        self.dashboard_mission_detail.setToolTip(
            mission_detail
        )

        # Focus rows.
        self.clear_layout(
            self.focus_layout
        )
        self.dashboard_focus_density_widgets = []

        intelligent_focus = (
            planner.intelligent_focus_plan(
                self.conn,
                week,
                guide,
                self.state,
                max_items=4,
            )
        )
        focus_summary = (
            planner.focus_day_summary(
                intelligent_focus,
                conn=self.conn,
                week=week,
            )
        )

        focus_styles = {
            "Learning": (
                "🎓",
                "Learning",
                COLORS["blue"],
            ),
            "SQL": (
                "💻",
                "SQL Practice",
                COLORS["purple"],
            ),
            "Portfolio": (
                "📁",
                "Portfolio Project",
                COLORS["orange"],
            ),
            "Review": (
                "📝",
                "Weekly Review",
                COLORS["green"],
            ),
            "General": (
                "📌",
                "Roadmap Task",
                COLORS["gold"],
            ),
        }

        focus_title_icons = {
            "Google Certificate": "🎓",
            "DataCamp": "📘",
            "Learning": "🎓",
            "SQL Practice": "💻",
            "DuckDB Practice": "🦆",
            "SQL Fundamentals": "💻",
            "Portfolio Project": "📁",
            "Applied Labs": "🧪",
            "Weekly Review": "📝",
            "Roadmap Task": "📌",
        }

        def add_focus_item(
            item,
            *,
            optional=False,
        ):
            completed = bool(
                item.get(
                    "completed"
                )
            )
            if completed:
                style_category = (
                    item.get(
                        "category"
                    )
                    or "General"
                )
                title = (
                    item.get(
                        "display_title"
                    )
                    or {
                        "google": (
                            "Google Certificate"
                        ),
                        "datacamp": (
                            "DataCamp"
                        ),
                        "sql": (
                            "SQL Practice"
                        ),
                        "portfolio": (
                            "Portfolio Project"
                        ),
                        "applied": (
                            "Applied Labs"
                        ),
                    }.get(
                        item.get(
                            "track_key"
                        ),
                        item.get(
                            "label",
                            "Completed task",
                        ),
                    )
                )
                detail = (
                    f"{item.get('label', title)} "
                    "• Completed today"
                )
                emoji = "✅"
                duration = "Done"
                accent = COLORS[
                    "green"
                ]
            else:
                presentation = (
                    tracks.focus_presentation(
                        self.conn,
                        item,
                    )
                )
                style_category = (
                    presentation[
                        "style_category"
                    ]
                )
                (
                    default_emoji,
                    _,
                    accent,
                ) = focus_styles.get(
                    style_category,
                    focus_styles[
                        "General"
                    ],
                )
                title = presentation[
                    "title"
                ]
                detail = presentation[
                    "detail"
                ]
                emoji = (
                    "✨"
                    if optional
                    else focus_title_icons.get(
                        title,
                        default_emoji,
                    )
                )
                duration = (
                    f"{int(item['estimated_minutes'])}m"
                )
                if optional:
                    original_title = title
                    task_label = str(
                        item.get(
                            "label",
                            original_title,
                        )
                    )
                    reason = str(
                        item.get(
                            "extra_reason",
                            "Optional progress",
                        )
                    )
                    short_reason = {
                        "Unfinished weekly target": (
                            "Weekly target remaining"
                        ),
                        (
                            "Advance the current "
                            "portfolio milestone"
                        ): "Portfolio milestone",
                        (
                            "Practice current SQL skills"
                        ): "SQL practice",
                        (
                            "Complete the next "
                            "eligible Applied Lab"
                        ): "Eligible Applied Lab",
                        (
                            "Get ahead on tomorrow's "
                            "external learning"
                        ): "External learning",
                    }.get(
                        reason,
                        reason,
                    )

                    detail = (
                        f"{original_title} • "
                        f"{short_reason}"
                    )
                    if item is (
                        self.dashboard_extra_focus_candidate
                    ):
                        title = (
                            f"Get Ahead • "
                            f"{task_label}"
                        )
                    else:
                        title = (
                            f"Extra • "
                            f"{task_label}"
                        )

            task_id = item.get(
                "task_id"
            )
            workspace_available = (
                task_workspace.workspace_supported_task_id(
                    self.conn,
                    task_id,
                )
            )
            action_text = None
            action_callback = None

            if optional and item is (
                self.dashboard_extra_focus_candidate
            ):
                action_text = "Start"
                action_callback = (
                    lambda _checked=False:
                    self.start_dashboard_extra_focus()
                )
            elif (
                task_id is not None
                and workspace_available
            ):
                action_text = "Open"
                action_callback = (
                    lambda _checked=False,
                    task_id=task_id:
                    self.open_task_workspace(
                        task_id=task_id
                    )
                )

            focus_row = FocusRow(
                emoji,
                title,
                detail,
                duration,
                accent,
                action_text=(
                    action_text
                ),
                on_action=(
                    action_callback
                ),
                completed=completed,
            )
            self.focus_layout.addWidget(focus_row)
            self.dashboard_focus_density_widgets.append(focus_row)

        if focus_summary[
            "all_base_complete"
        ]:
            complete_panel = SoftPanel()
            complete_panel.setMinimumHeight(
                44
            )
            complete_panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred,
            )
            complete_layout = QHBoxLayout(
                complete_panel
            )
            complete_layout.setContentsMargins(
                10,
                3,
                10,
                3,
            )
            complete_layout.setSpacing(
                10
            )

            complete_icon = QLabel(
                "🎉"
            )
            complete_icon.setStyleSheet(
                "font-size:15pt;"
            )
            complete_layout.addWidget(
                complete_icon
            )

            complete_text = (
                QVBoxLayout()
            )
            complete_text.setSpacing(0)
            complete_title = QLabel(
                "Today's plan complete"
            )
            complete_title.setStyleSheet(
                "font-weight:700;"
                f"color:{COLORS['green']};"
            )
            if focus_summary[
                "inferred_empty_complete"
            ]:
                if focus_summary[
                    "completed_count"
                ]:
                    completion_detail_text = (
                        f"{focus_summary['completed_count']} "
                        "completion(s) recorded today"
                    )
                elif focus_summary[
                    "session_count"
                ]:
                    completion_detail_text = (
                        f"{focus_summary['session_count']} "
                        "study session(s) recorded today"
                    )
                else:
                    completion_detail_text = (
                        "All currently available focus work is complete"
                    )
            else:
                completion_detail_text = (
                    f"{focus_summary['completed_count']} "
                    f"tasks • "
                    f"{focus_summary['planned_minutes'] // 60}h "
                    f"{focus_summary['planned_minutes'] % 60:02d}m "
                    "of planned work"
                )

            complete_detail = QLabel(
                completion_detail_text
            )
            complete_detail.setObjectName(
                "Muted"
            )
            complete_detail.setWordWrap(True)
            complete_detail.setStyleSheet(
                "font-size:8.2pt;"
            )
            complete_detail.setToolTip(
                "\n".join(
                    focus_summary[
                        "completed_titles"
                    ]
                )
            )
            complete_text.addWidget(
                complete_title
            )
            complete_text.addWidget(
                complete_detail
            )
            complete_layout.addLayout(
                complete_text,
                1,
            )
            self.focus_layout.addWidget(
                complete_panel
            )

            active_extra = focus_summary[
                "active_extra"
            ]
            if active_extra is not None:
                add_focus_item(
                    active_extra,
                    optional=True,
                )
                self.dashboard_extra_focus_candidate = None
            else:
                self.dashboard_extra_focus_candidate = (
                    planner.optional_focus_candidate(
                        self.conn,
                        week,
                        self.state,
                    )
                )
                if (
                    self.dashboard_extra_focus_candidate
                    is not None
                ):
                    add_focus_item(
                        self.dashboard_extra_focus_candidate,
                        optional=True,
                    )
                else:
                    no_extra = QLabel(
                        "No additional eligible task is available right now."
                    )
                    no_extra.setObjectName(
                        "Muted"
                    )
                    no_extra.setMinimumHeight(
                        38
                    )
                    no_extra.setWordWrap(True)
                    no_extra.setAlignment(
                        Qt.AlignVCenter
                    )
                    self.focus_layout.addWidget(
                        no_extra
                    )

            self.dashboard_tomorrow_preview = (
                planner.tomorrow_preview(
                    self.conn,
                    week,
                    self.state,
                    limit=3,
                )
            )
            preview_row = QHBoxLayout()
            preview_row.setContentsMargins(
                0,
                0,
                0,
                0,
            )
            preview_row.setSpacing(6)

            preview_count = len(
                self.dashboard_tomorrow_preview
            )
            if preview_count:
                first_preview = (
                    self.dashboard_tomorrow_preview[
                        0
                    ]["title"]
                )
                remaining_preview = (
                    preview_count - 1
                )
                preview_summary = (
                    f"Tomorrow • {first_preview}"
                    + (
                        f" + {remaining_preview} more"
                        if remaining_preview
                        else ""
                    )
                )
            else:
                preview_summary = (
                    "Tomorrow • Adaptive plan refreshes automatically"
                )

            preview_text = QLabel(
                preview_summary
            )
            preview_text.setObjectName(
                "Muted"
            )
            preview_text.setStyleSheet(
                "font-size:8.2pt;"
            )
            preview_text.setWordWrap(True)
            preview_text.setMinimumHeight(24)
            preview_text.setToolTip(
                "\n".join(
                    (
                        f"{item['title']} — "
                        f"{item['detail']} "
                        f"({item['minutes']}m)"
                    )
                    for item in self.dashboard_tomorrow_preview
                )
            )
            preview_row.addWidget(
                preview_text,
                1,
            )

            preview_button = QPushButton(
                "Preview"
            )
            preview_button.setObjectName(
                "Link"
            )
            preview_button.setFixedHeight(
                24
            )
            preview_button.clicked.connect(
                self.show_dashboard_tomorrow_preview
            )
            preview_row.addWidget(
                preview_button
            )
            self.focus_layout.addLayout(
                preview_row
            )
        else:
            self.dashboard_extra_focus_candidate = None
            self.dashboard_tomorrow_preview = []

            for index, item in enumerate(
                intelligent_focus
            ):
                add_focus_item(
                    item
                )
                if (
                    index
                    < len(
                        intelligent_focus
                    )
                    - 1
                ):
                    self.focus_layout.addWidget(
                        Divider()
                    )

        compact_completed_state = bool(
            focus_summary[
                "all_base_complete"
            ]
        )
        self.focus_footer_divider.setVisible(
            not compact_completed_state
        )
        self.focus_footer_host.setVisible(
            not compact_completed_state
        )
        self.dashboard_focus_card.layout.setSpacing(
            3
            if compact_completed_state
            else 6
        )

        planned_minutes = focus_summary[
            "planned_minutes"
        ]
        self.focus_total_time.set_value(
            (
                (
                    f"{planned_minutes // 60}h "
                    f"{planned_minutes % 60:02d}m"
                )
                if planned_minutes
                else (
                    "—"
                    if focus_summary[
                        "inferred_empty_complete"
                    ]
                    else "0h 00m"
                )
            )
        )
        self.focus_task_count.set_value(
            (
                f"{focus_summary['completed_count']} / "
                f"{focus_summary['total_count']}"
                if focus_summary[
                    "total_count"
                ]
                else (
                    "Complete"
                    if focus_summary[
                        "all_base_complete"
                    ]
                    else "0"
                )
            )
        )

        # Next task rows.
        self.clear_layout(self.dashboard_tasks_layout)
        self.dashboard_task_density_widgets = []
        available = planner.available(self.conn, week)

        task_category_colors = {
            "Learning": COLORS["blue"],
            "SQL": COLORS["purple"],
            "Portfolio": COLORS["orange"],
            "Review": COLORS["green"],
            "General": COLORS["muted"],
        }

        if available:
            for index, row in enumerate(available[:5]):
                workspace_available = (
                    task_workspace.workspace_supported_task_id(
                        self.conn,
                        row["id"],
                    )
                )
                task_row = TaskRow(
                    title=row["label"],
                    source=self.dashboard_task_source(
                        row
                    ),
                    checked=bool(row["completed"]),
                    status_text=(
                        "Completed"
                        if row["completed"] else ""
                    ),
                    category_text=row["category"],
                    category_color=task_category_colors.get(
                        row["category"],
                        COLORS["muted"],
                    ),
                    action_text=(
                        "Open"
                        if workspace_available
                        else None
                    ),
                    on_action=(
                        (
                            lambda _checked=False, task_id=row["id"]:
                            self.open_task_workspace(task_id=task_id)
                        )
                        if workspace_available
                        else None
                    ),
                    completed=bool(row["completed"]),
                )
                task_row.checkbox.stateChanged.connect(
                    lambda state_value,
                    task_row=task_row,
                    task_id=row["id"]:
                    self.queue_dashboard_task_completion(
                        task_row,
                        task_id,
                        state_value,
                    )
                )
                self.dashboard_tasks_layout.addWidget(task_row)
                self.dashboard_task_density_widgets.append(task_row)
                if index < min(len(available), 5) - 1:
                    self.dashboard_tasks_layout.addWidget(Divider())
        else:
            empty = QLabel("No unfinished tasks. Great work!")
            empty.setObjectName("Muted")
            self.dashboard_tasks_layout.addWidget(empty)

        self.dashboard_tasks_layout.addStretch()

        # Timer.
        self.update_timer_visuals()

        # Growth.
        self.refresh_growth_chart()

        # Achievements.
        self.clear_layout(self.badge_layout)
        for (
            emoji,
            title,
            description,
            accent,
        ) in self.dashboard_achievement_cards():
            self.badge_layout.addWidget(
                BadgeCard(
                    emoji,
                    title,
                    description,
                    accent,
                )
            )

        # Weekly summary.
        week_start, week_end = analytics.week_bounds()
        self.summary_period.setText(
            f"Week of {week_start:%b %d} – {week_end:%b %d}"
        )
        self.clear_layout(self.summary_rows)

        session_count = analytics.weekly_session_count(
            self.conn
        )
        weekly_sql = analytics.weekly_sql_count(self.conn)
        focus_score = analytics.weekly_focus_score(self.conn)

        summary_items = [
            ("⏱️", "Study Time", f"{week_hours:g}h"),
            ("📅", "Sessions", str(session_count)),
            ("✅", "Tasks Completed", f"{done} / {total}"),
            ("💾", "SQL Problems", str(weekly_sql)),
            (
                "⭐",
                "Focus Score",
                (
                    f"{focus_score:g} / 10"
                    if focus_score is not None
                    else "—"
                ),
            ),
        ]
        for index, (emoji, label, value) in enumerate(summary_items):
            self.summary_rows.addWidget(
                StatRow(
                    emoji,
                    label,
                    value,
                    COLORS["purple"],
                )
            )
            if index < len(summary_items) - 1:
                self.summary_rows.addWidget(Divider())

        # Sidebar.
        current_streak = analytics.streak(self.conn)
        best_streak = analytics.best_streak(self.conn)
        activity = analytics.week_activity(self.conn)

        self.side_streak_value.setText(str(current_streak))
        self.best_streak_label.setText(
            f"Best Streak: {best_streak} days"
        )
        self.streak_week.setText(
            "  ".join(
                "●" if active else "○"
                for active in activity
            )
        )
        self.streak_week.setToolTip(
            "Monday through Sunday study activity"
        )

        self.side_hours_value.setText(f"{week_hours:g}h")
        self.sidebar_goal.setValue(int(weekly_goal))
        self.sidebar_goal_label.setText(
            f"Goal: {target_hours:g}h"
        )
        self.sidebar_goal_percent.setText(
            f"{weekly_goal:.0f}%"
        )
        self._apply_dashboard_density(
            max(0, self.dashboard_scroll.viewport().width()),
            max(0, self.dashboard_scroll.viewport().height()),
        )

    def open_completion_history(self):
        history_rows = tracks.completion_history(
            self.conn
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Completion History / Undo"
        )
        dialog.setMinimumSize(760, 460)
        dialog.setStyleSheet(stylesheet(self._ui_scale, self._content_scale))

        layout = QVBoxLayout(dialog)
        instructions = QLabel(
            "Select a completed item and choose Undo Completion. "
            "Adaptive learning tracks are reversed with their saved "
            "progress evidence; later sequential completions must be "
            "undone first."
        )
        instructions.setWordWrap(True)
        instructions.setObjectName("Muted")
        layout.addWidget(instructions)

        history_list = QListWidget()
        history_list.setWordWrap(True)
        history_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        layout.addWidget(history_list, 1)

        for record in history_rows:
            completed_date = (
                record.get("completed_date")
                or "Date unavailable"
            )
            week_text = (
                f"Week {record['week']} • "
                if record.get("week")
                is not None
                else ""
            )
            track_text = (
                f"{record['track_key']} • "
                if record.get("track_key")
                else ""
            )
            history_list.addItem(
                f"{completed_date} • "
                f"{week_text}"
                f"{record['category']} • "
                f"{track_text}"
                f"{record['label']}"
            )
            list_item = history_list.item(
                history_list.count() - 1
            )
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                record,
            )

        if not history_rows:
            history_list.addItem(
                "No completed tasks were found."
            )

        buttons = QHBoxLayout()
        undo_button = QPushButton(
            "Undo Completion"
        )
        undo_button.setObjectName("Primary")
        close_button = QPushButton("Close")
        close_button.clicked.connect(
            dialog.reject
        )
        buttons.addWidget(undo_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        def undo_selected():
            item = history_list.currentItem()
            if item is None:
                self.statusBar().showMessage(
                    "Select a completed item first.",
                    3200,
                )
                return

            record = item.data(
                Qt.ItemDataRole.UserRole
            )
            if not record:
                return

            confirmation = QMessageBox.question(
                dialog,
                "Undo Completion",
                (
                    "Restore this item to unfinished?\n\n"
                    f"{record['label']}\n\n"
                    "This also reverses its matching adaptive "
                    "completion event or SQL completion record."
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )
            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

            session_snapshot = session_guard.capture(
                self
            )
            try:
                result = tracks.undo_completion(
                    self.conn,
                    self.state,
                    task_id=record.get("task_id"),
                    sql_title=record.get(
                        "sql_title"
                    ),
                )
                self.state = state(self.conn)
                tracks.sync_all(
                    self.conn,
                    self.state,
                )
                self.refresh_all()
            except ValueError as exc:
                QMessageBox.warning(
                    dialog,
                    "Cannot Undo Completion",
                    str(exc),
                )
                return
            finally:
                session_guard.restore(
                    self,
                    session_snapshot,
                )

            dialog.accept()
            self.statusBar().showMessage(
                result["message"],
                5200,
            )

        undo_button.clicked.connect(
            undo_selected
        )
        dialog.exec()

    def refresh_planner(self):
        self.build_plan()
        self.refresh_backlog()

    def refresh_backlog(self):
        selected_task_id = (
            self.backlog_list.property(
                "pendingSelectedTaskId"
            )
            or self.selected_task_id(
                self.backlog_list
            )
        )
        self.backlog_list.setProperty(
            "pendingSelectedTaskId",
            None,
        )
        selected_row = None

        self.backlog_list.blockSignals(True)
        self.backlog_list.clear()

        rows = self.conn.execute(
            """SELECT
                      s.id,
                      s.label,
                      s.completed,
                      m.status,
                      m.priority,
                      m.estimated_minutes,
                      m.energy,
                      m.deferred_until,
                      m.category,
                      m.prerequisite_state,
                      m.prerequisite_reason
               FROM sprint_tasks s
               JOIN task_metadata m
                 ON m.task_id=s.id
               WHERE s.week=?
                 AND (
                     s.label NOT LIKE
                         'Complete Applied Lab %'
                     OR s.completed=1
                     OR s.id IN (
                         SELECT task_id
                         FROM track_tasks
                         WHERE track_key='applied'
                     )
                 )
               ORDER BY m.priority,s.sort_order""",
            (self.state["current_week"],),
        ).fetchall()

        for row in rows:
            deferred = (
                f" → {row['deferred_until']}"
                if row["deferred_until"]
                else ""
            )
            eligibility_text = ""
            if (
                row["prerequisite_state"]
                == "Blocked"
            ):
                eligibility_text = " • 🔒 Locked"

            self.backlog_list.addItem(
                f"#{row['id']} • {row['status']} • "
                f"P{row['priority']} • "
                f"{row['estimated_minutes']}m • "
                f"{row['energy']} • "
                f"{row['category']}"
                f"{eligibility_text} • "
                f"{row['label']}{deferred}"
            )
            row_index = (
                self.backlog_list.count() - 1
            )
            list_item = self.backlog_list.item(
                row_index
            )
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                int(row["id"]),
            )
            list_item.setToolTip(
                (
                    f"Selected task #{row['id']}\n"
                    f"Status: {row['status']}\n"
                    f"Priority: {row['priority']}\n"
                    f"Estimate: {row['estimated_minutes']} minutes\n"
                    f"Eligibility: {row['prerequisite_state']}\n"
                    f"{row['prerequisite_reason'] or ''}"
                )
            )

            if (
                selected_task_id is not None
                and int(row["id"])
                == int(selected_task_id)
            ):
                selected_row = row_index

        self.backlog_list.blockSignals(False)

        if selected_row is not None:
            self.backlog_list.setCurrentRow(
                selected_row
            )

    def refresh_learning(self):
        track_data = tracks.snapshot(
            self.conn,
            self.state,
        )

        google = track_data["google"]
        datacamp = track_data["datacamp"]
        sql = track_data["sql"]
        portfolio = track_data["portfolio"]
        applied = track_data["applied"]

        google_meta = google["metadata"]
        google_detail = (
            f"Module {self.state['google_module']} • "
            f"Today "
            f"{google_meta.get('today_completed', 0)} / "
            f"{google_meta.get('today_target', 0)} • "
            f"Week "
            f"{google['weekly_completed']} / "
            f"{google['weekly_target']} • "
            f"{google_meta.get('pace_status', 'On pace')}"
        )

        data_course = datacamp["metadata"].get(
            "course",
            "Learning path",
        )
        data_lesson = datacamp["metadata"].get(
            "lesson",
            "Track complete",
        )
        datacamp_detail = (
            f"{data_lesson} • "
            f"Today "
            f"{datacamp['metadata'].get('today_completed', 0)} / "
            f"{datacamp['metadata'].get('today_target', 0)} • "
            f"Week "
            f"{datacamp['weekly_completed']} / "
            f"{datacamp['weekly_target']}"
        )

        sql_count = self.conn.execute(
            """SELECT COUNT(*)
               FROM sql_practice
               WHERE status='Completed'"""
        ).fetchone()[0]
        sql_next = sql["metadata"].get(
            "title",
            "Track complete",
        )
        sql_detail = (
            f"Next: {sql_next} • "
            f"Today "
            f"{sql['metadata'].get('today_completed', 0)} / "
            f"{sql['metadata'].get('today_target', 0)} • "
            f"Week "
            f"{sql['weekly_completed']} / "
            f"{sql['weekly_target']}"
        )

        project_rows = self.conn.execute(
            """SELECT completed
               FROM project_tasks
               WHERE project_id=?""",
            (self.state["current_project"],),
        ).fetchall()
        project_done = sum(
            int(row["completed"])
            for row in project_rows
        )
        portfolio_next = portfolio["metadata"].get(
            "milestone",
            "Project complete",
        )
        if portfolio["status"] == "Locked":
            portfolio_detail = (
                portfolio["metadata"].get(
                    "blocked_reason",
                    "Waiting for prerequisite skills.",
                )
            )
        else:
            portfolio_detail = (
                f"Next: {portfolio_next} • "
                f"Today "
                f"{portfolio['metadata'].get('today_completed', 0)} / "
                f"{portfolio['metadata'].get('today_target', 0)} • "
                f"Week "
                f"{portfolio['weekly_completed']} / "
                f"{portfolio['weekly_target']}"
            )

        completed_applied = set(
            tracks.completed_applied_numbers(
                self.conn
            )
        )
        power_bi_done = len(
            completed_applied
            & {
                1, 2, 3, 4, 5, 6, 36
            }
        )
        python_done = len(
            completed_applied
            & set(range(8, 12))
        )
        statistics_done = len(
            completed_applied
            & set(range(22, 29))
        )

        applied_meta = applied[
            "metadata"
        ]
        applied_next = applied_meta.get(
            "title",
            "No eligible lab yet",
        )
        applied_branch = applied_meta.get(
            "branch",
            "Auto",
        )
        applied_detail = (
            f"Next: {applied_next} • "
            f"Branch {applied_branch} • "
            f"Today "
            f"{applied_meta.get('today_completed', 0)} / "
            f"{applied_meta.get('today_target', 0)} • "
            f"Week "
            f"{applied['weekly_completed']} / "
            f"{applied['weekly_target']}"
        )

        data = {
            "Google": (
                f"Course {self.state['google_course']}",
                google_detail,
            ),
            "DataCamp": (
                data_course,
                datacamp_detail,
            ),
            "SQL": (
                f"{sql_count}/{self.state['sql_target']}",
                sql_detail,
            ),
            "Power BI": (
                f"{power_bi_done}/7 labs",
                (
                    "Complete the branched Power BI lab sequence "
                    "as prerequisites unlock."
                ),
            ),
            "Python": (
                f"{python_done}/4 labs",
                (
                    "Complete the compact pandas bridge after "
                    "Python instruction begins."
                ),
            ),
            "Portfolio": (
                f"{project_done}/{len(project_rows)}",
                portfolio_detail,
            ),
            "Statistics": (
                f"{statistics_done}/7 labs",
                (
                    "Progress from descriptive statistics through "
                    "experiments, causal reasoning, and regression."
                ),
            ),
            "Applied Labs": (
                (
                    f"{applied_meta.get('completed_items', 0)}"
                    f"/{len(APPLIED_EXERCISES)}"
                ),
                applied_detail,
            ),
        }

        for key, (value, detail) in data.items():
            self.learning_cards[key][0].setText(
                value
            )
            self.learning_cards[key][1].setText(
                detail
            )

        self.week_input.setValue(
            self.state["current_week"]
        )
        self.course_input.setValue(
            self.state["google_course"]
        )
        self.update_google_module_range(
            self.state["google_course"]
        )
        self.module_input.setValue(
            self.state["google_module"]
        )
        self.hours_input.setValue(
            int(self.state["weekly_target_hours"])
        )
        # BEGIN EXERCISE PACKS
        if hasattr(self, "applied_labs_widget"):
            self.applied_labs_widget.refresh()
        else:
            self.refresh_applied_exercises()
        # END EXERCISE PACKS
        # BEGIN EXERCISE PACKS
        if hasattr(self, "exercise_packs_widget"):
            self.exercise_packs_widget.refresh()
        # END EXERCISE PACKS



    def refresh_project(self):
        self.project_combo.blockSignals(True)
        self.project_combo.setCurrentIndex(self.state["current_project"] - 1)
        self.project_combo.blockSignals(False)
        self.load_project()

    def refresh_sql(self):
        previous_title = getattr(
            self,
            "sql_selected_title",
            None,
        )

        rows = self.conn.execute(
            "SELECT * FROM sql_practice"
        ).fetchall()
        records = {
            row["title"]: row
            for row in rows
        }
        completed = {
            title: row
            for title, row in records.items()
            if row["status"] == "Completed"
        }
        recommended = tracks.next_sql_titles(
            self.conn,
            self.state,
            limit=5,
        )
        recommended_set = set(recommended)

        active_title = None
        sql_track = tracks.snapshot(
            self.conn,
            self.state,
        ).get("sql", {})
        active_title = (
            sql_track.get("metadata", {})
            .get("title")
        )

        self.sql_problem_list.blockSignals(
            True
        )
        self.sql_problem_list.clear()

        title_to_row = {}
        for (
            title,
            difficulty,
            topic,
            concepts,
            _assigned_week,
            estimate,
        ) in SQL_COMPANION:
            if (
                title not in completed
                and title not in recommended_set
                and title != active_title
            ):
                continue

            readiness = tracks.sql_problem_readiness(
                self.conn,
                self.state,
                title,
            )
            status = (
                "✅"
                if title in completed
                else ("⬜" if readiness["ready"] else "🔒")
            )
            mastery = (
                f" • Mastery "
                f"{completed[title]['mastery']}/5"
                if title in completed
                else ""
            )
            self.sql_problem_list.addItem(
                f"{status} {title} • "
                f"{difficulty} • {topic} • "
                f"{concepts} • {estimate} min"
                f"{mastery}"
            )
            list_item = self.sql_problem_list.item(
                self.sql_problem_list.count() - 1
            )
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                title,
            )
            if readiness["ready"]:
                evidence_lines = []
                for skill_key in readiness["required_keys"]:
                    skill_name = tracks.SKILL_DEFINITIONS[skill_key][0]
                    sources = readiness["evidence"].get(skill_key, [])
                    evidence_lines.append(
                        f"{skill_name}: "
                        + ("; ".join(sources) if sources else "evidence recorded")
                    )
                tooltip = "Ready — approved evidence:\n" + "\n".join(evidence_lines)
            else:
                missing_lines = []
                for skill_key in readiness["missing_keys"]:
                    skill_name = tracks.SKILL_DEFINITIONS[skill_key][0]
                    accepted = readiness["accepted_evidence"].get(
                        skill_key,
                        "Complete approved learning or practice.",
                    )
                    missing_lines.append(f"{skill_name}: {accepted}")
                tooltip = (
                    "Locked — approved evidence needed:\n"
                    + "\n".join(missing_lines)
                )
            list_item.setToolTip(tooltip)
            title_to_row[title] = (
                self.sql_problem_list.count() - 1
            )

        selection_title = None
        for candidate in (
            previous_title,
            active_title,
            *recommended,
        ):
            if candidate in title_to_row:
                selection_title = candidate
                break

        if (
            selection_title is None
            and self.sql_problem_list.count()
        ):
            selection_title = (
                self.sql_problem_list.item(0)
                .data(
                    Qt.ItemDataRole.UserRole
                )
            )

        self.sql_problem_list.blockSignals(
            False
        )

        if selection_title is not None:
            self.sql_problem_list.setCurrentRow(
                title_to_row[selection_title]
            )
        else:
            self.clear_sql_workspace(
                (
                    "No SQL problem is eligible yet. "
                    "Complete an approved learning chapter, "
                    "DuckDB exercise, or concept-matched SQL problem."
                )
            )
        if hasattr(self, "duckdb_exercises_widget"):
            self.duckdb_exercises_widget.refresh()
        else:
            self.refresh_duckdb_exercises()


    def refresh_session_task_choices(self):
        if not hasattr(self, "session_task"):
            return
        requested = self.session_task.property("pendingTaskId")
        current = (
            requested
            if requested is not None
            else self.session_task.currentData()
        )
        self.session_task.setProperty("pendingTaskId", None)

        self.session_task.blockSignals(True)
        self.session_task.clear()
        self.session_task.addItem("No linked task", None)
        rows = self.conn.execute(
            """SELECT s.id,s.label,m.status,m.category
               FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               WHERE (
                   s.week=? AND m.status<>'Completed'
               ) OR s.id=?
               ORDER BY
                   CASE WHEN s.id=? THEN 0 ELSE 1 END,
                   m.priority,
                   s.sort_order""",
            (
                self.state["current_week"],
                int(current) if current is not None else -1,
                int(current) if current is not None else -1,
            ),
        ).fetchall()
        for row in rows:
            self.session_task.addItem(
                f"{row['category']} • {row['label']}",
                int(row["id"]),
            )
        index = self.session_task.findData(current)
        self.session_task.setCurrentIndex(index if index >= 0 else 0)
        self.session_task.blockSignals(False)

    def refresh_sessions(self):
        self.refresh_session_task_choices()
        self.session_list.clear()
        rows = self.conn.execute(
            """SELECT * FROM study_sessions
               ORDER BY id DESC LIMIT 30"""
        ).fetchall()
        for row in rows:
            linked = (
                f" • Task: {row['task_label_snapshot']}"
                if row["task_label_snapshot"]
                else ""
            )
            self.session_list.addItem(
                f"{row['session_date']} • {row['hours']:g}h • "
                f"Productivity {row['productivity_score'] or '-'}{linked}\n"
                f"Google: {row['google_progress'] or '-'} • "
                f"SQL: {row['sql_problems']}"
            )
            item = self.session_list.item(self.session_list.count() - 1)
            item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "session_id": int(row["id"]),
                    "task_id": row["task_id"],
                    "workspace_key": row["workspace_key"],
                },
            )

    def open_selected_session_workspace(self):
        item = self.session_list.currentItem()
        if item is None:
            self.statusBar().showMessage("Select a study session first.", 3200)
            return
        data = item.data(Qt.ItemDataRole.UserRole) or {}
        if data.get("workspace_key"):
            self.open_task_workspace(workspace_key=data["workspace_key"])
        elif data.get("task_id"):
            self.open_task_workspace(task_id=int(data["task_id"]))
        else:
            self.statusBar().showMessage(
                "That session is not linked to a task workspace.",
                4200,
            )


    def refresh_readiness(self):
        data = analytics.readiness(
            self.conn,
            self.state,
        )

        for key, value in data.items():
            self.readiness_rings[key].set_value(
                value,
                f"{value}%",
                "",
            )

        evidence = self.conn.execute(
            """SELECT *
               FROM evidence
               ORDER BY skill,source_type"""
        ).fetchall()

        self.evidence_list.clear()
        if evidence:
            for row in evidence:
                self.evidence_list.addItem(
                    f"✅ {row['skill']}\n"
                    f"    {row['source_type']} • "
                    f"{row['source_name']}"
                )
                evidence_item = (
                    self.evidence_list.item(
                        self.evidence_list.count()
                        - 1
                    )
                )
                evidence_item.setData(
                    Qt.ItemDataRole.UserRole,
                    int(row["id"]),
                )
                evidence_item.setToolTip(
                    row["description"]
                    or "No description recorded."
                )
        else:
            self.evidence_list.addItem(
                "No evidence logged yet.\n"
                "Add portfolio, coursework, SQL practice, "
                "certifications, or work examples."
            )

        recommendations = coach.recommendations(
            self.conn,
            self.state,
        )
        if not recommendations:
            recommendations = [
                (
                    "Continue the highest-priority task in Today’s Focus, "
                    "then document one piece of evidence from the work."
                ),
                (
                    "Keep building SQL and portfolio evidence so each learned "
                    "concept has a concrete example."
                ),
            ]

        self.clear_layout(self.readiness_coach_layout)
        recommendation_icons = [
            "🎯",
            "💻",
            "⏱️",
            "📊",
        ]

        for index, recommendation in enumerate(
            recommendations[:4]
        ):
            panel = SoftPanel()
            panel.setMinimumHeight(62)
            panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
            panel_layout = QHBoxLayout(panel)
            panel_layout.setContentsMargins(12, 10, 12, 10)
            panel_layout.setSpacing(9)

            icon = QLabel(
                recommendation_icons[
                    index % len(recommendation_icons)
                ]
            )
            icon.setStyleSheet("font-size:17pt;")
            panel_layout.addWidget(icon)

            text = QLabel(recommendation)
            text.setWordWrap(True)
            text.setObjectName("Muted")
            panel_layout.addWidget(text, 1)

            self.readiness_coach_layout.addWidget(panel)

        overall = data["Overall"]
        weakest = min(
            (
                key
                for key in data
                if key != "Overall"
            ),
            key=lambda key: data[key],
        )

        self.readiness_overall_value.setText(
            f"{overall}%"
        )
        self.readiness_overall_progress.setValue(overall)
        self.readiness_leverage_title.setText(
            f"Focus next: {weakest}"
        )
        self.readiness_leverage_detail.setText(
            recommendations[0]
            if recommendations
            else "Continue the current highest-priority roadmap task."
        )

        self.clear_layout(self.readiness_coverage_layout)

        source_counts = {
            row["source_type"]: row["count"]
            for row in self.conn.execute(
                """SELECT source_type,COUNT(*) AS count
                   FROM evidence
                   GROUP BY source_type"""
            ).fetchall()
        }

        coverage_rows = [
            ("📁", "Portfolio", source_counts.get("Portfolio", 0)),
            ("🎓", "Coursework", source_counts.get("Coursework", 0)),
            ("🎬", "Work Experience", source_counts.get("Work Experience", 0)),
            ("💻", "SQL Practice", source_counts.get("SQL Practice", 0)),
            ("📜", "Certification", source_counts.get("Certification", 0)),
        ]

        for index, (emoji, label, count) in enumerate(
            coverage_rows
        ):
            coverage_row = StatRow(
                emoji,
                label,
                f"{count} evidence item"
                f"{'' if count == 1 else 's'}",
                (
                    COLORS["green"]
                    if count > 0
                    else COLORS["muted"]
                ),
            )
            coverage_row.setMinimumHeight(40)
            coverage_row.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self.readiness_coverage_layout.addWidget(
                coverage_row
            )

            if index < len(coverage_rows) - 1:
                divider = Divider()
                divider.setMinimumHeight(1)
                divider.setMaximumHeight(1)
                self.readiness_coverage_layout.addWidget(
                    divider
                )

        inventory = tracks.skill_inventory(
            self.conn,
            self.state,
        )
        learned = [item for item in inventory if item["status"] == "Learned"]
        progress = [item for item in inventory if item["status"] == "In Progress"]
        locked = [item for item in inventory if item["status"] == "Locked"]

        self.skills_summary_label.setText(
            f"{len(learned)} learned • "
            f"{len(progress)} in progress • "
            f"{len(locked)} locked • "
            "Updated automatically from Google, DataCamp, DuckDB, and SQL Companion."
        )
        self.skills_tabs.setTabText(0, f"Learned ({len(learned)})")
        self.skills_tabs.setTabText(1, f"In Progress ({len(progress)})")
        self.skills_tabs.setTabText(2, f"Locked ({len(locked)})")

        self.skills_learned_list.clear()
        self.skills_progress_list.clear()
        self.skills_locked_list.clear()

        for item in learned:
            self.skills_learned_list.addItem(
                f"✅ {item['display_name']}\n"
                f"    {item['category']} • Evidence: "
                f"{'; '.join(item['evidence'])}"
            )
        for item in progress:
            self.skills_progress_list.addItem(
                f"🟡 {item['display_name']}\n"
                f"    {item['category']} • Working through: "
                f"{'; '.join(item['in_progress'])}"
            )
        for item in locked:
            self.skills_locked_list.addItem(
                f"🔒 {item['display_name']}\n"
                f"    {item['category']} • Unlock with: "
                f"{item['accepted_evidence']}"
            )

        if not learned:
            self.skills_learned_list.addItem("No concepts are marked learned yet.")
        if not progress:
            self.skills_progress_list.addItem(
                "No concepts are currently marked in progress."
            )
        if not locked:
            self.skills_locked_list.addItem("All tracked concepts are unlocked.")


    def refresh_applications(self):
        self.clear_layout(self.kanban_layout)
        statuses = ["Wishlist", "Applying", "Applied", "Interview", "Final", "Offer"]
        for status in statuses:
            column = Card(status)
            vertical_kanban = (
                hasattr(self, "kanban_layout")
                and self.kanban_layout.direction()
                == QBoxLayout.Direction.TopToBottom
            )
            column.setMinimumWidth(0 if vertical_kanban else 220)
            rows = self.conn.execute(
                "SELECT * FROM applications WHERE status=? ORDER BY id DESC",
                (status,),
            ).fetchall()
            if rows:
                for row in rows:
                    panel = SoftPanel()
                    panel_layout = QVBoxLayout(panel)
                    title = QLabel(row["company"])
                    title.setStyleSheet("font-weight:700;")
                    role = QLabel(row["role"])
                    role.setObjectName("Muted")
                    panel_layout.addWidget(title)
                    panel_layout.addWidget(role)
                    if row["follow_up_date"]:
                        follow = QLabel(f"📅 {row['follow_up_date']}")
                        follow.setObjectName("Tiny")
                        panel_layout.addWidget(follow)
                    column.layout.addWidget(panel)
            else:
                empty = QLabel("No opportunities")
                empty.setObjectName("Muted")
                column.layout.addWidget(empty)
            column.layout.addStretch()
            self.kanban_layout.addWidget(column)

    def refresh_summaries(self):
        self.summary_list.clear()
        rows = self.conn.execute(
            "SELECT week,summary FROM weekly_summaries ORDER BY week DESC"
        ).fetchall()
        for row in rows:
            self.summary_list.addItem(f"Week {row['week']}: {row['summary']}")

    # ---------- Actions ----------
    def queue_dashboard_task_completion(
        self,
        task_row,
        task_id,
        state_value,
    ):
        """Complete a dashboard task after the checkbox event finishes."""
        if int(state_value) != Qt.Checked.value:
            return

        task_row.checkbox.setEnabled(False)
        task_row.hide()

        QTimer.singleShot(
            0,
            lambda: self.finish_dashboard_task_completion(
                task_row,
                task_id,
            ),
        )

    def finish_dashboard_task_completion(
        self,
        task_row,
        task_id,
    ):
        try:
            self.complete_task(task_id)
        except Exception as error:
            task_row.show()
            task_row.setEnabled(True)
            task_row.checkbox.setChecked(False)
            QMessageBox.critical(
                self,
                "Task Completion Failed",
                (
                    "The task could not be marked complete. "
                    "Your progress was not intentionally discarded.\n\n"
                    f"Error: {error}"
                ),
            )
            raise

    def complete_task(self, task_id):
        # Task completion refreshes several pages. Preserve the active timer and
        # unsaved Study Session form so an unrelated checkbox cannot interrupt
        # the user's current study session.
        study_session_snapshot = session_guard.capture(
            self
        )

        completion_message = (
            "Task completed."
        )
        try:
            result = tracks.complete_track_task(
                self.conn,
                task_id,
                self.state,
            )

            if not result["handled"]:
                self.conn.execute(
                    """UPDATE sprint_tasks
                       SET completed=1
                       WHERE id=?""",
                    (task_id,),
                )
                self.conn.execute(
                    """UPDATE task_metadata
                       SET status='Completed',
                           deferred_until=NULL
                       WHERE task_id=?""",
                    (task_id,),
                )
                self.conn.commit()

            self.state = state(self.conn)
            tracks.sync_all(
                self.conn,
                self.state,
            )
            completion_message = result.get(
                "message",
                "Task completed.",
            )
            if result["handled"]:
                track_state = tracks.snapshot(
                    self.conn,
                    self.state,
                )[result["track_key"]]
                if (
                    track_state["status"]
                    == "Weekly Complete"
                ):
                    completion_message += (
                        " Weekly target complete; "
                        "the next item returns next week."
                    )
                elif (
                    track_state["status"]
                    == "Daily Complete"
                ):
                    completion_message += (
                        " Daily target complete; "
                        "the next item returns tomorrow."
                    )
                else:
                    completion_message += (
                        " Another item is due today."
                    )

            self.refresh_all()
        finally:
            session_guard.restore(
                self,
                study_session_snapshot,
            )

        self.statusBar().showMessage(
            completion_message,
            5200,
        )

        if result["handled"]:
            self.statusBar().showMessage(
                completion_message,
                5200,
            )

    def start_dashboard_extra_focus(
        self,
    ):
        candidate = getattr(
            self,
            "dashboard_extra_focus_candidate",
            None,
        )
        if candidate is None:
            self.statusBar().showMessage(
                "No optional extra task is currently available.",
                3600,
            )
            return

        try:
            started = planner.start_extra_focus(
                self.conn,
                int(
                    self.state[
                        "current_week"
                    ]
                ),
                self.state,
                candidate,
            )
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Could Not Start Extra Task",
                str(exc),
            )
            return

        self.refresh_all(
            sync_tracks=False
        )
        self.statusBar().showMessage(
            (
                "Optional extra task started. "
                "It does not change today's completed target "
                "and will not be treated as missed work."
            ),
            6000,
        )

        task_id = started.get(
            "task_id"
        )
        if (
            task_id is not None
            and task_workspace.workspace_supported_task_id(
                self.conn,
                task_id,
            )
        ):
            self.open_task_workspace(
                task_id=task_id
            )

    def show_dashboard_tomorrow_preview(
        self,
    ):
        items = getattr(
            self,
            "dashboard_tomorrow_preview",
            [],
        )
        if not items:
            QMessageBox.information(
                self,
                "Tomorrow Preview",
                (
                    "Tomorrow's adaptive plan will be created "
                    "when the new day begins."
                ),
            )
            return

        lines = [
            (
                f"• {item['title']} — "
                f"{item['detail']} "
                f"({item['minutes']} minutes)"
            )
            for item in items
        ]
        QMessageBox.information(
            self,
            "Tomorrow's Likely Focus",
            (
                "This is a non-binding preview. The adaptive "
                "scheduler may change it when progress, "
                "prerequisites, or availability change.\n\n"
                + "\n".join(lines)
            ),
        )

    def build_plan(self):
        rows, remaining = planner.make_plan(
            self.conn,
            self.state["current_week"],
            self.plan_minutes.value(),
            self.plan_energy.currentText(),
        )
        self.plan_list.clear()
        for row in rows:
            self.plan_list.addItem(
                f"#{row['id']} • {row['estimated_minutes']}m • "
                f"{row['energy']} • {row['category']} • {row['label']}"
            )
            item = self.plan_list.item(self.plan_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
        if not rows:
            self.plan_list.addItem("No eligible tasks for this time and energy level.")
        elif remaining:
            self.plan_list.addItem(f"Unused time: {remaining} minutes")

    def selected_task_id(self, widget):
        item = widget.currentItem()
        if not item:
            return None

        stored_id = item.data(
            Qt.ItemDataRole.UserRole
        )
        if stored_id is not None:
            try:
                return int(stored_id)
            except (TypeError, ValueError):
                pass

        match = re.search(
            r"#(\d+)",
            item.text(),
        )
        return (
            int(match.group(1))
            if match
            else None
        )

    def continue_plan(self):
        task_id = self.selected_task_id(self.plan_list)
        if not task_id and self.plan_list.count():
            self.plan_list.setCurrentRow(0)
            task_id = self.selected_task_id(self.plan_list)
        if not task_id:
            return
        row = self.conn.execute(
            "SELECT destination FROM task_metadata WHERE task_id=?", (task_id,)
        ).fetchone()
        self.conn.execute(
            "UPDATE task_metadata SET status='In Progress',deferred_until=NULL WHERE task_id=?",
            (task_id,),
        )
        self.conn.commit()
        if row:
            self.navigate(int(row["destination"]))

    def continue_highest_impact(self):
        rows = planner.available(self.conn, self.state["current_week"])
        if not rows:
            QMessageBox.information(self, "All Clear", "No available sprint tasks remain.")
            return
        task_id = rows[0]["id"]
        self.plan_list.clear()
        self.plan_list.addItem(
            f"#{task_id} • {rows[0]['estimated_minutes']}m • "
            f"{rows[0]['energy']} • {rows[0]['category']} • {rows[0]['label']}"
        )
        self.continue_plan()

    def defer_plan(self):
        task_id = self.selected_task_id(self.plan_list)
        if task_id:
            planner.defer(self.conn, task_id)
            self.refresh_all()

    def block_plan(self):
        task_id = self.selected_task_id(self.plan_list)
        if task_id:
            self.conn.execute(
                "UPDATE task_metadata SET status='Blocked' WHERE task_id=?",
                (task_id,),
            )
            self.conn.commit()
            self.refresh_all()

    def edit_task(self, task_id=None):
        if isinstance(task_id, bool):
            task_id = None
        task_id = (
            int(task_id)
            if task_id is not None
            else self.selected_task_id(self.backlog_list)
        )
        if not task_id:
            self.statusBar().showMessage(
                "Select a backlog task first.",
                3200,
            )
            return

        identity = tracks.task_edit_identity(
            self.conn,
            task_id,
        )
        row = self.conn.execute(
            """SELECT
                   s.label,
                   s.completed,
                   m.*
               FROM sprint_tasks s
               JOIN task_metadata m
                 ON m.task_id=s.id
               WHERE s.id=?""",
            (task_id,),
        ).fetchone()
        if row is None or identity is None:
            QMessageBox.warning(
                self,
                "Task Not Found",
                "The selected task no longer exists.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        dialog.setStyleSheet(stylesheet(self._ui_scale, self._content_scale))
        form = QFormLayout(dialog)

        status = QComboBox()
        status.addItems(
            [
                "Not Started",
                "In Progress",
                "Blocked",
                "Deferred",
                "Completed",
            ]
        )
        status.setCurrentText(
            row["status"]
            or "Not Started"
        )

        priority = QSpinBox()
        priority.setRange(1, 3)
        priority.setValue(
            int(row["priority"] or 3)
        )

        minutes = QSpinBox()
        minutes.setRange(5, 480)
        minutes.setValue(
            int(
                row["estimated_minutes"]
                or 30
            )
        )

        energy = QComboBox()
        energy.addItems(
            ["Low", "Normal", "High"]
        )
        energy.setCurrentText(
            row["energy"]
            or "Normal"
        )

        deferred = QLineEdit(
            row["deferred_until"]
            or ""
        )
        deferred.setPlaceholderText(
            "YYYY-MM-DD"
        )

        task_label = QLabel(row["label"])
        task_label.setWordWrap(True)

        form.addRow("Task", task_label)
        form.addRow("Status", status)
        form.addRow("Priority", priority)
        form.addRow(
            "Estimated minutes",
            minutes,
        )
        form.addRow("Energy", energy)
        form.addRow(
            "Deferred until",
            deferred,
        )

        button_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(
            dialog.reject
        )
        save = QPushButton("Save Changes")
        save.setObjectName("Primary")
        save.clicked.connect(
            dialog.accept
        )
        button_row.addStretch()
        button_row.addWidget(cancel)
        button_row.addWidget(save)
        form.addRow(button_row)

        if dialog.exec() != QDialog.Accepted:
            return

        previous_status = (
            row["status"]
            or "Not Started"
        )
        was_completed = (
            tracks.task_has_completion_evidence(
                self.conn,
                task_id,
            )
        )
        selected_status = status.currentText()
        selected_priority = priority.value()
        selected_minutes = minutes.value()
        selected_energy = energy.currentText()
        selected_deferred = (
            deferred.text().strip()
            or None
        )

        if (
            selected_status == "Deferred"
            and selected_deferred is None
        ):
            selected_deferred = (
                date.today()
                + timedelta(days=1)
            ).isoformat()
        elif selected_status != "Deferred":
            selected_deferred = None

        session_snapshot = session_guard.capture(
            self
        )
        effective_task_id = task_id

        try:
            if (
                was_completed
                and selected_status
                != "Completed"
            ):
                tracks.undo_completion(
                    self.conn,
                    self.state,
                    task_id=task_id,
                )

            # Normalize adaptive links before the user values are made final.
            # Older task rows may still have a previous week or legacy label,
            # which legitimately causes sync_all() to apply target defaults.
            self.state = state(self.conn)
            tracks.sync_all(
                self.conn,
                self.state,
            )
            self.state = state(self.conn)

            resolved_task_id = (
                tracks.resolve_task_edit_target(
                    self.conn,
                    identity,
                )
            )
            if resolved_task_id is None:
                raise RuntimeError(
                    "The task could not be resolved after "
                    "the adaptive plan refreshed."
                )
            effective_task_id = int(
                resolved_task_id
            )

            # The editor is authoritative after synchronization.
            self.conn.execute(
                """UPDATE task_metadata
                   SET status=?,
                       priority=?,
                       estimated_minutes=?,
                       energy=?,
                       deferred_until=?,
                       prerequisite_state=CASE
                           WHEN ?='Blocked'
                           THEN 'Blocked'
                           ELSE 'Ready'
                       END,
                       prerequisite_reason=CASE
                           WHEN ?='Blocked'
                           THEN 'Manually blocked in Adaptive Planner.'
                           ELSE NULL
                       END
                   WHERE task_id=?""",
                (
                    selected_status,
                    selected_priority,
                    selected_minutes,
                    selected_energy,
                    selected_deferred,
                    selected_status,
                    selected_status,
                    effective_task_id,
                ),
            )
            self.conn.execute(
                """UPDATE sprint_tasks
                   SET completed=?
                   WHERE id=?""",
                (
                    1
                    if selected_status
                    == "Completed"
                    else 0,
                    effective_task_id,
                ),
            )
            self.conn.commit()

            if (
                not was_completed
                and selected_status
                == "Completed"
            ):
                self.complete_task(
                    effective_task_id
                )
                return

            saved = self.conn.execute(
                """SELECT
                       s.completed,
                       m.status,
                       m.priority,
                       m.estimated_minutes,
                       m.energy,
                       m.deferred_until
                   FROM sprint_tasks s
                   JOIN task_metadata m
                     ON m.task_id=s.id
                   WHERE s.id=?""",
                (effective_task_id,),
            ).fetchone()
            if saved is None:
                raise RuntimeError(
                    "The task could not be read back after saving."
                )

            expected = {
                "status": selected_status,
                "priority": selected_priority,
                "estimated_minutes": selected_minutes,
                "energy": selected_energy,
                "deferred_until": selected_deferred,
            }
            actual = {
                "status": saved["status"],
                "priority": int(
                    saved["priority"]
                ),
                "estimated_minutes": int(
                    saved["estimated_minutes"]
                ),
                "energy": saved["energy"],
                "deferred_until": (
                    saved["deferred_until"]
                ),
            }
            if actual != expected:
                differences = [
                    (
                        f"{field}: expected "
                        f"{expected[field]!r}, "
                        f"saved {actual[field]!r}"
                    )
                    for field in expected
                    if expected[field]
                    != actual[field]
                ]
                raise RuntimeError(
                    "The saved values did not match:\n\n"
                    + "\n".join(differences)
                )

            schedule_result = (
                planner.task_schedule_eligibility(
                    self.conn,
                    effective_task_id,
                    self.state[
                        "current_week"
                    ],
                )
            )

            # Keep the exact edited task selected after rebuilding the backlog.
            self.backlog_list.setProperty(
                "pendingSelectedTaskId",
                effective_task_id,
            )

            # Refresh widgets from the values just verified without a hidden
            # second adaptive synchronization.
            self.refresh_all(
                sync_tracks=False
            )
        except (ValueError, RuntimeError) as exc:
            QMessageBox.warning(
                self,
                "Task Could Not Be Updated",
                str(exc),
            )
            return
        finally:
            session_guard.restore(
                self,
                session_snapshot,
            )

        self.statusBar().showMessage(
            (
                f"Saved task #{effective_task_id}: "
                f"{selected_status} • "
                f"P{selected_priority} • "
                f"{selected_minutes}m • "
                f"{selected_energy} • "
                f"{schedule_result['reason']}"
            ),
            6500,
        )


    def complete_workspace_task(self, task_id):
        task_id = int(task_id)
        row = task_workspace.task_record(self.conn, task_id)
        if row is None:
            raise ValueError("The selected task no longer exists.")
        if row["prerequisite_state"] == "Blocked":
            raise ValueError(
                row["prerequisite_reason"]
                or "Complete the required prerequisites before finishing this task."
            )

        label = str(row["label"] or "")
        applied_number = applied_exercise_number_for_label(label)
        duckdb_number = duckdb_exercise_number_for_label(label)
        session_snapshot = session_guard.capture(self)

        try:
            if applied_number is not None:
                readiness = tracks.applied_lab_readiness(
                    self.conn,
                    self.state,
                    applied_number,
                )
                if not readiness["ready"]:
                    raise ValueError(
                        "Complete the following first:\n\n"
                        + "\n".join(
                            f"• {reason}"
                            for reason in readiness["missing"]
                        )
                    )
                submission = applied_workspace.submission_path(
                    ROOT,
                    applied_number,
                )
                if not submission.exists():
                    raise ValueError(
                        "Create the Applied Lab submission before marking it complete."
                    )
                if not applied_workspace.submission_has_changes(
                    ROOT,
                    applied_number,
                ):
                    raise ValueError(
                        "The Applied Lab submission still matches the starter. "
                        "Add your completed work and validation before marking it complete."
                    )
                progress = applied_workspace.progress(
                    self.conn,
                    ROOT,
                    applied_number,
                )
                applied_workspace.save_progress(
                    self.conn,
                    ROOT,
                    applied_number,
                    status="Completed",
                    notes=progress["notes"],
                )
                active = tracks.active_applied_task_for_number(
                    self.conn,
                    applied_number,
                )
                if active is not None:
                    tracks.complete_track_task(
                        self.conn,
                        int(active["task_id"]),
                        self.state,
                    )
                else:
                    tracks.record_applied_change(
                        self.conn,
                        number=applied_number,
                        completed=True,
                        task_id=task_id,
                    )
                message = f"Applied Lab {applied_number:02d} completed."

            elif duckdb_number is not None:
                submission = duckdb_workspace.submission_path(
                    ROOT,
                    duckdb_number,
                )
                if not submission.exists():
                    raise ValueError(
                        "Create the DuckDB submission before marking it complete."
                    )
                if not duckdb_workspace.submission_has_changes(
                    ROOT,
                    duckdb_number,
                ):
                    raise ValueError(
                        "The DuckDB submission still matches the starter SQL. "
                        "Complete and validate the exercise first."
                    )
                progress = duckdb_workspace.progress(
                    self.conn,
                    ROOT,
                    duckdb_number,
                )
                duckdb_workspace.save_progress(
                    self.conn,
                    ROOT,
                    duckdb_number,
                    status="Completed",
                    notes=progress["notes"],
                )
                message = f"DuckDB Exercise {duckdb_number:02d} completed."

            else:
                self.complete_task(task_id)
                return

            planner.mark_focus_task_completed(
                self.conn,
                task_id,
            )
            self.state = state(self.conn)
            tracks.sync_all(self.conn, self.state)
            self.state = state(self.conn)
            self.refresh_all(sync_tracks=False)
            self.statusBar().showMessage(
                message + " Evidence and scheduling were updated.",
                5600,
            )
        finally:
            session_guard.restore(self, session_snapshot)

    def open_task_workspace(self, *, task_id=None, workspace_key=None):
        # BEGIN SQL LEARNING TASK ROUTING
        if task_id is not None and self._route_sql_learning_task(task_id):
            return
        # END SQL LEARNING TASK ROUTING
        if task_id is None and workspace_key is None:
            self.statusBar().showMessage("Select a task first.", 3200)
            return
        try:
            dialog = TaskWorkspaceDialog(
                self,
                conn=self.conn,
                root=ROOT,
                state=self.state,
                task_id=(int(task_id) if task_id is not None else None),
                workspace_key=workspace_key,
                complete_callback=self.complete_workspace_task,
                refresh_callback=lambda: self.refresh_all(sync_tracks=False),
                start_session_callback=self.start_session_for_task,
                edit_task_callback=self.edit_task,
            )
            dialog.exec()
            self.refresh_all(sync_tracks=False)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Task Workspace",
                str(exc),
            )

    def open_plan_workspace(self):
        task_id = self.selected_task_id(self.plan_list)
        if task_id is None:
            self.statusBar().showMessage("Select a planned task first.", 3200)
            return
        self.open_task_workspace(task_id=task_id)

    def open_backlog_workspace(self):
        task_id = self.selected_task_id(self.backlog_list)
        if task_id is None:
            self.statusBar().showMessage("Select a backlog task first.", 3200)
            return
        self.open_task_workspace(task_id=task_id)

    def selected_workspace_task_id(self):
        if not hasattr(self, "workspace_task_list"):
            return None
        item = self.workspace_task_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def open_selected_task_workspace(self):
        task_id = self.selected_workspace_task_id()
        if task_id is None:
            self.statusBar().showMessage("Select a task first.", 3200)
            return
        self.open_task_workspace(task_id=task_id)

    def edit_selected_workspace_task(self):
        task_id = self.selected_workspace_task_id()
        if task_id is None:
            self.statusBar().showMessage("Select a task first.", 3200)
            return
        self.edit_task(task_id)

    def start_selected_workspace_session(self):
        task_id = self.selected_workspace_task_id()
        if task_id is None:
            self.statusBar().showMessage("Select a task first.", 3200)
            return
        self.start_session_for_task(task_id)

    def start_session_for_task(self, task_id):
        task_id = int(task_id)
        task_row = task_workspace.task_record(
            self.conn,
            task_id,
        )
        if task_workspace.workspace_supported(
            task_row
        ):
            task_workspace.ensure_workspace(
                self.conn,
                ROOT,
                task_id=task_id,
                current_project=int(
                    self.state["current_project"]
                ),
            )
        task_workspace.mark_in_progress(self.conn, task_id)
        self.session_task.setProperty("pendingTaskId", task_id)
        self.refresh_session_task_choices()
        self.navigate(5)
        self.start_study_timer()
        self.statusBar().showMessage(
            "Study timer started and will be linked to the selected task when logged.",
            5200,
        )

    def open_weekly_workspace(self, kind):
        task_id = task_workspace.ensure_weekly_workspace_task(
            self.conn,
            int(self.state["current_week"]),
            kind,
        )
        self.refresh_all(sync_tracks=False)
        self.open_task_workspace(task_id=task_id)

    def refresh_task_workspaces(self, *_args):
        if not hasattr(self, "workspace_task_list"):
            return
        previous = self.selected_workspace_task_id()
        week_value = self.workspace_week_filter.currentData()
        if week_value == "current":
            week = int(self.state["current_week"])
        elif week_value == "all":
            week = None
        else:
            week = int(week_value)
        rows = task_workspace.task_rows(
            self.conn,
            week=week,
            status=self.workspace_status_filter.currentText(),
            search=self.workspace_search.text(),
        )
        self.workspace_task_list.blockSignals(True)
        self.workspace_task_list.clear()
        selected_row = None
        for row in rows:
            document = "📄" if row["document_path"] else "▫"
            schedule = (
                f" • Scheduled {row['scheduled_for']}"
                if row["scheduled_for"]
                else ""
            )
            linked = (
                f" • {row['artifact_count']} artifact(s)"
                f" • {row['session_count']} session(s)"
            )
            self.workspace_task_list.addItem(
                f"{document} Week {row['week']} • {row['status']} • "
                f"{row['category']} • {row['label']}{schedule}{linked}"
            )
            item = self.workspace_task_list.item(
                self.workspace_task_list.count() - 1
            )
            item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
            item.setToolTip(
                f"Priority {row['priority']} • {row['estimated_minutes']} minutes • "
                f"{row['energy']} energy • {row['prerequisite_state']}"
            )
            if previous is not None and int(row["id"]) == int(previous):
                selected_row = self.workspace_task_list.count() - 1
        self.workspace_task_list.blockSignals(False)
        if selected_row is not None:
            self.workspace_task_list.setCurrentRow(selected_row)
        elif self.workspace_task_list.count():
            self.workspace_task_list.setCurrentRow(0)
        self.workspace_task_summary.setText(
            f"{len(rows)} task(s) • Documents are created only when opened • "
            "Google Certificate and DataCamp work stays in Learning and "
            "Study Sessions rather than Task Workspaces."
        )

    def update_google_module_range(self, course=None):
        course = int(
            self.course_input.value()
            if course is None
            else course
        )
        maximum = tracks.google_module_count(course)
        self.module_input.setMaximum(maximum)
        self.module_input.setToolTip(
            f"Google Course {course} contains {maximum} modules."
        )

    def save_learning(self):
        previous_state = self.state
        google_course, google_module = tracks.normalize_google_position(
            self.course_input.value(),
            self.module_input.value(),
        )
        tracks.record_google_manual_change(
            self.conn,
            previous_state,
            google_course,
            google_module,
        )

        update_state(
            self.conn,
            current_week=self.week_input.value(),
            google_course=google_course,
            google_module=google_module,
            weekly_target_hours=self.hours_input.value(),
        )
        planner.sync_google_course_progress(
            self.conn,
            self.course_input.value(),
        )
        self.state = state(self.conn)
        tracks.sync_all(
            self.conn,
            self.state,
        )
        self.refresh_all()

    def load_project(self):
        project_id = int(self.project_combo.currentData() or 1)
        self.project_task_checks = []

        for stage in ("Overview", "Tasks"):
            layout = self.project_stage_widgets[stage]
            self.clear_layout(layout)

        rows = self.conn.execute(
            """SELECT id,stage,label,completed FROM project_tasks
               WHERE project_id=? ORDER BY sort_order""",
            (project_id,),
        ).fetchall()

        project_stage_colors = {
            "Discovery": COLORS["blue"],
            "Dataset": COLORS["cyan"],
            "SQL": COLORS["purple"],
            "Python": COLORS["green"],
            "Power BI": COLORS["orange"],
            "GitHub": COLORS["gold"],
            "README": COLORS["blue"],
            "Overview": COLORS["muted"],
            "Tasks": COLORS["muted"],
        }

        for row in rows:
            target_stage = (
                row["stage"]
                if row["stage"]
                in self.project_stage_widgets
                else "Tasks"
            )
            if target_stage not in ("Overview", "Tasks"):
                target_stage = "Tasks"

            task_row = TaskRow(
                title=row["label"],
                source=(
                    f"Project milestone • "
                    f"{row['stage']}"
                ),
                checked=bool(row["completed"]),
                status_text=(
                    "Completed"
                    if row["completed"]
                    else ""
                ),
                category_text=row["stage"],
                category_color=project_stage_colors.get(
                    row["stage"],
                    COLORS["muted"],
                ),
                on_toggle=(
                    lambda state, task_id=row["id"]:
                    self.set_project_task_completed(
                        task_id,
                        state,
                    )
                ),
            )
            self.project_stage_widgets[
                target_stage
            ].addWidget(task_row)
            self.project_task_checks.append(
                (row["id"], task_row.checkbox)
            )

        for stage in ("Overview", "Tasks"):
            self.project_stage_widgets[stage].addStretch()

        directory = ROOT / "projects" / PROJECT_DIRS[project_id]
        readme = directory / "README.md"
        overview_layout = self.project_stage_widgets["Overview"]
        if readme.exists():
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText(readme.read_text(encoding="utf-8"))
            overview_layout.insertWidget(0, preview)

        notes = {
            row["section"]: row["content"]
            for row in self.conn.execute(
                "SELECT section,content FROM project_notes WHERE project_id=?",
                (project_id,),
            ).fetchall()
        }
        for stage in PROJECT_STAGES:
            widget = self.project_stage_widgets.get(stage)
            if isinstance(widget, QTextEdit):
                widget.setPlainText(notes.get(stage, ""))

    def set_active_project(self):
        update_state(
            self.conn,
            current_project=int(self.project_combo.currentData()),
        )
        self.refresh_all()

    def set_project_task_completed(
        self,
        task_id,
        state_value,
    ):
        completed = (
            int(state_value)
            == Qt.Checked.value
        )
        self.conn.execute(
            """UPDATE project_tasks
               SET completed=?
               WHERE id=?""",
            (1 if completed else 0, task_id),
        )
        task_row = self.conn.execute(
            """SELECT label
               FROM project_tasks
               WHERE id=?""",
            (task_id,),
        ).fetchone()

        tracks.record_portfolio_change(
            self.conn,
            project_id=self.state[
                "current_project"
            ],
            project_task_id=task_id,
            label=(
                task_row["label"]
                if task_row
                else "Portfolio milestone"
            ),
            completed=completed,
        )
        tracks.sync_all(
            self.conn,
            self.state,
        )
        self.conn.commit()

        self.statusBar().showMessage(
            (
                "Portfolio milestone completed."
                if completed
                else "Portfolio milestone reopened."
            ),
            2200,
        )

        QTimer.singleShot(
            0,
            self.refresh_after_project_task_change,
        )

    def refresh_after_project_task_change(self):
        newly_unlocked = self.sync_achievement_records()
        self.load_project()
        self.refresh_dashboard()
        self.refresh_learning()
        self.refresh_readiness()

        if newly_unlocked:
            self.statusBar().showMessage(
                f"🏆 Achievement unlocked: "
                f"{newly_unlocked[0]}",
                5000,
            )

    def save_project_tasks(self):
        for task_id, checkbox in self.project_task_checks:
            self.conn.execute(
                """UPDATE project_tasks
                   SET completed=?
                   WHERE id=?""",
                (
                    1 if checkbox.isChecked() else 0,
                    task_id,
                ),
            )
        self.conn.commit()
        self.refresh_after_project_task_change()
        self.statusBar().showMessage(
            "Portfolio milestone states saved.",
            2200,
        )

    def save_project_note(self, section, widget):
        project_id = int(self.project_combo.currentData())
        self.conn.execute(
            """INSERT INTO project_notes(project_id,section,content)
               VALUES(?,?,?)
               ON CONFLICT(project_id,section)
               DO UPDATE SET content=excluded.content""",
            (project_id, section, widget.toPlainText()),
        )
        self.conn.commit()

    def set_sql_workspace_enabled(
        self,
        enabled,
    ):
        for widget in (
            self.sql_mastery,
            self.sql_review,
            self.sql_notes,
            self.sql_answer_editor,
            self.sql_save_button,
            self.sql_complete_button,
            self.sql_hint_button,
            self.sql_solution_button,
        ):
            widget.setEnabled(bool(enabled))

    def clear_sql_workspace(
        self,
        message="Select a problem on the left.",
    ):
        self.sql_selected_title = None
        for field in (
            self.sql_title,
            self.sql_difficulty,
            self.sql_topic,
            self.sql_concepts,
            self.sql_review,
        ):
            field.clear()
        self.sql_mastery.setValue(1)
        self.sql_notes.clear()
        self.sql_submission_path.clear()
        self.sql_answer_editor.clear()
        self.sql_workspace_status.setText(
            message
        )
        self.sql_complete_button.setText(
            "Mark Complete"
        )
        self.set_sql_workspace_enabled(
            False
        )

    def prefill_sql(
        self,
        item,
        _previous=None,
    ):
        if item is None:
            self.clear_sql_workspace()
            return

        title = item.data(
            Qt.ItemDataRole.UserRole
        )
        if not title:
            return

        match = next(
            (
                row
                for row in SQL_COMPANION
                if row[0] == title
            ),
            None,
        )
        if not match:
            self.clear_sql_workspace(
                "The selected problem is not in the SQL catalog."
            )
            return

        record = self.conn.execute(
            """SELECT *
               FROM sql_practice
               WHERE platform='DataLemur'
                 AND title=?""",
            (title,),
        ).fetchone()
        readiness = tracks.sql_problem_readiness(
            self.conn,
            self.state,
            title,
        )

        self.sql_selected_title = title
        self.sql_title.setText(match[0])
        self.sql_difficulty.setText(match[1])
        self.sql_topic.setText(match[2])
        self.sql_concepts.setText(match[3])
        self.sql_mastery.setValue(
            int(record["mastery"])
            if record is not None
            else 1
        )
        self.sql_review.setText(
            (
                record["review_date"]
                if record is not None
                and record["review_date"]
                else (
                    date.today()
                    + timedelta(days=7)
                ).isoformat()
            )
        )
        self.sql_notes.setPlainText(
            (
                record["notes"]
                if record is not None
                and record["notes"]
                else ""
            )
        )
        submission_path = sql_workspace.solution_path(ROOT, title)
        relative_submission = str(submission_path.relative_to(ROOT)).replace("\\", "/")
        self.sql_submission_path.setText(relative_submission)
        if submission_path.exists():
            try:
                submission_sql = submission_path.read_text(encoding="utf-8")
            except OSError:
                submission_sql = ""
        else:
            submission_sql = sql_workspace.starter_template(
                title=match[0], difficulty=match[1], topic=match[2], concepts=match[3]
            )
        self.sql_answer_editor.blockSignals(True)
        self.sql_answer_editor.setPlainText(submission_sql)
        self.sql_answer_editor.blockSignals(False)

        completed = (
            record is not None
            and record["status"] == "Completed"
        )
        if completed:
            completed_date = (
                record["completed_date"]
                or "previously"
            )
            self.sql_workspace_status.setText(
                f"Completed {completed_date} • "
                f"Required knowledge: "
                + ", ".join(
                    readiness["required_names"]
                )
            )
            self.sql_complete_button.setText(
                "Update Completion"
            )
        elif readiness["ready"]:
            evidence_summary = []
            for skill_key in readiness["required_keys"]:
                sources = readiness["evidence"].get(skill_key, [])
                if sources:
                    evidence_summary.append(sources[0])
            self.sql_workspace_status.setText(
                "Ready to solve • Evidence: "
                + (
                    "; ".join(evidence_summary)
                    if evidence_summary
                    else "approved concept evidence"
                )
            )
            self.sql_complete_button.setText("Mark Complete")
        else:
            missing_options = [
                readiness["accepted_evidence"].get(
                    skill_key,
                    "approved learning or practice",
                )
                for skill_key in readiness["missing_keys"]
            ]
            self.sql_workspace_status.setText(
                "Locked • Learn first: "
                + ", ".join(readiness["missing_names"])
                + " • Accepted evidence: "
                + " | ".join(missing_options)
            )
            self.sql_complete_button.setText("Locked")

        self.set_sql_workspace_enabled(
            completed or readiness["ready"]
        )

    def ensure_current_sql_solution(self):
        title = (
            self.sql_selected_title
            or self.sql_title.text().strip()
        )
        if not title:
            raise ValueError(
                "Select a SQL problem first."
            )

        return sql_workspace.ensure_solution_file(
            ROOT,
            title=title,
            difficulty=self.sql_difficulty.text(),
            topic=self.sql_topic.text(),
            concepts=self.sql_concepts.text(),
        )

    def link_current_sql_solution_artifact(
        self,
        title,
        path,
    ):
        active = tracks.active_sql_task_for_title(
            self.conn,
            title,
        )
        task_id = (
            int(active["task_id"])
            if active is not None
            else None
        )
        return task_workspace.link_sql_solution_artifact(
            self.conn,
            ROOT,
            title=title,
            solution_path=path,
            task_id=task_id,
            current_project=int(
                self.state["current_project"]
            ),
        )

    @staticmethod
    def _sql_submission_has_original_query(sql_text):
        sql_text = str(sql_text or "")
        without_comments = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql_text, flags=re.S)
        normalized = " ".join(without_comments.split())
        if not re.match(r"^(?:SELECT|WITH)\b", normalized, re.IGNORECASE):
            return False
        placeholders = (
            "requested columns",
            "source table",
            "write your answer",
            "write and test your own solution",
        )
        lower = sql_text.casefold()
        return len(normalized) >= 18 and not any(phrase in lower for phrase in placeholders)

    def _persist_sql_submission(self, *, completed=False):
        title = self.sql_selected_title or self.sql_title.text().strip()
        if not title:
            raise ValueError("Select a SQL problem first.")
        sql_text = self.sql_answer_editor.toPlainText().rstrip() + "\n"
        if completed and not self._sql_submission_has_original_query(sql_text):
            raise ValueError(
                "Write your own SQL query before marking the interview problem complete. "
                "The untouched starting template is not a completed submission."
            )
        path = sql_workspace.solution_path(ROOT, title)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sql_text, encoding="utf-8")
        relative_path = str(path.relative_to(ROOT)).replace("\\", "/")
        existing = self.conn.execute(
            "SELECT status,completed_date FROM sql_practice WHERE platform='DataLemur' AND title=?",
            (title,),
        ).fetchone()
        status = "Completed" if completed or (existing and existing["status"] == "Completed") else "In Progress"
        completed_date = (
            date.today().isoformat() if completed
            else (existing["completed_date"] if existing and existing["status"] == "Completed" else None)
        )
        self.conn.execute(
            """INSERT INTO sql_practice
               (platform,title,difficulty,topic,concepts,status,mastery,review_date,
                completed_date,solution_path,notes)
               VALUES('DataLemur',?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(platform,title) DO UPDATE SET
                   difficulty=excluded.difficulty,topic=excluded.topic,
                   concepts=excluded.concepts,status=excluded.status,
                   mastery=excluded.mastery,review_date=excluded.review_date,
                   completed_date=excluded.completed_date,
                   solution_path=excluded.solution_path,notes=excluded.notes""",
            (
                title,
                self.sql_difficulty.text(),
                self.sql_topic.text(),
                self.sql_concepts.text(),
                status,
                self.sql_mastery.value(),
                self.sql_review.text().strip() or None,
                completed_date,
                relative_path,
                self.sql_notes.toPlainText(),
            ),
        )
        if completed:
            source_name = f"Interview Problem: {title}"
            description = (
                f"Completed a {self.sql_difficulty.text()} SQL interview problem. "
                f"Concepts: {self.sql_concepts.text()}. "
                f"Mastery: {self.sql_mastery.value()}/5. "
                f"Completed: {completed_date}. Submission: {relative_path}."
            )
            notes = self.sql_notes.toPlainText().strip()
            if notes:
                description += f" Notes: {notes}"
            self.conn.execute(
                """INSERT INTO evidence(skill,source_type,source_name,description)
                   VALUES(?,?,?,?)
                   ON CONFLICT(skill,source_type,source_name)
                   DO UPDATE SET description=excluded.description""",
                (
                    f"SQL — {self.sql_concepts.text()}",
                    "Interview Problem",
                    source_name,
                    description,
                ),
            )
        self.conn.commit()
        self.link_current_sql_solution_artifact(title, path)
        self.sql_submission_path.setText(relative_path)
        return path, status

    def save_sql_submission(self):
        title = self.sql_selected_title or self.sql_title.text().strip()
        if not title:
            self.statusBar().showMessage("Select a SQL problem first.", 3200)
            return
        readiness = tracks.sql_problem_readiness(self.conn, self.state, title)
        if not readiness["ready"] and not self.conn.execute(
            "SELECT 1 FROM sql_practice WHERE platform='DataLemur' AND title=? AND status='Completed'",
            (title,),
        ).fetchone():
            QMessageBox.warning(
                self, "Problem Locked",
                "Complete the required concepts before saving a submission for this problem.",
            )
            return
        try:
            path, status = self._persist_sql_submission(completed=False)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Submission", str(exc))
            return
        self.statusBar().showMessage(
            f"Saved {path.name} as {status}. Your submission remains editable.", 4200
        )

    def save_sql(self):
        title = self.sql_selected_title or self.sql_title.text().strip()
        if not title:
            self.statusBar().showMessage("Select a SQL problem first.", 3200)
            return

        readiness = tracks.sql_problem_readiness(self.conn, self.state, title)
        if not readiness["ready"]:
            QMessageBox.warning(
                self,
                "Problem Locked",
                "Complete these concepts before attempting this problem:\n\n"
                + "\n".join(readiness["missing_names"]),
            )
            return

        study_session_snapshot = session_guard.capture(self)
        completion_message = f"SQL completed: {title}"
        try:
            path, _status = self._persist_sql_submission(completed=True)
            active_sql_task = tracks.active_sql_task_for_title(self.conn, title)
            if active_sql_task is not None:
                result = tracks.complete_track_task(
                    self.conn, int(active_sql_task["task_id"]), self.state
                )
                completion_message = result.get("message", completion_message)
            else:
                tracks.record_sql_completion(self.conn, title)

            self.state = state(self.conn)
            tracks.sync_all(self.conn, self.state)
            self.sql_selected_title = None
            self.refresh_all()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Complete Interview Problem", str(exc))
            return
        finally:
            session_guard.restore(self, study_session_snapshot)

        self.statusBar().showMessage(
            completion_message
            + " Added to Demonstrated Evidence and selected the next eligible problem.",
            6000,
        )

    def sql_hint(self):
        title = (
            self.sql_selected_title
            or self.sql_title.text().strip()
        )
        if not title:
            self.statusBar().showMessage(
                "Select a SQL problem first.",
                3200,
            )
            return

        topic = (
            self.sql_topic.text()
            or "the main SQL concept"
        )
        readiness = tracks.sql_problem_readiness(
            self.conn,
            self.state,
            title,
        )
        required = ", ".join(
            readiness["required_names"]
        )
        QMessageBox.information(
            self,
            "Hint",
            (
                "Identify the output grain first. "
                f"Then separate the {topic} logic "
                "into testable steps and validate "
                "each intermediate result.\n\n"
                f"Required knowledge: {required}"
            ),
        )

    def open_sql_solution(self):
        title = self.sql_selected_title or self.sql_title.text().strip()
        if not title:
            self.statusBar().showMessage("Select a SQL problem first.", 3200)
            return
        try:
            path, _status = self._persist_sql_submission(completed=False)
            editor_name = sql_workspace.open_in_editor(path, root=ROOT)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Submission", str(exc))
            return
        self.statusBar().showMessage(
            f"Saved and opened {path.name} in {editor_name}.", 4200
        )

    def session_goal_seconds(self):
        if hasattr(self, "session_goal_minutes"):
            minutes = self.session_goal_minutes.value()
        else:
            minutes = int(
                setting(
                    self.conn,
                    "session_goal_minutes",
                    "60",
                )
            )
        return max(60, int(minutes) * 60)

    def change_session_goal(self, value):
        save_setting(
            self.conn,
            "session_goal_minutes",
            str(int(value)),
        )
        self.update_timer_visuals(pulse=True)

    def timer_caption(self):
        goal_minutes = max(
            1,
            self.session_goal_seconds() // 60,
        )
        studied_minutes = self.elapsed_seconds // 60

        if self.elapsed_seconds >= self.session_goal_seconds():
            state_text = "Goal reached"
        elif self.timer_state == "running":
            state_text = "Focusing"
        elif self.timer_state == "paused":
            state_text = "Paused"
        else:
            state_text = "Ready to focus"

        return (
            f"{state_text} • "
            f"{studied_minutes} / {goal_minutes} min"
        )

    def update_timer_visuals(self, pulse=False):
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        progress = min(
            1.0,
            self.elapsed_seconds
            / self.session_goal_seconds(),
        )
        caption = self.timer_caption()

        for attribute in (
            "circular_timer",
            "study_circular_timer",
        ):
            timer_widget = getattr(self, attribute, None)
            if timer_widget is None:
                continue
            timer_widget.set_display(
                text,
                caption,
                progress,
            )
            if pulse:
                timer_widget.pulse()

    def start_study_timer(self):
        self.timer_state = "running"
        self.timer.start(1000)
        self.update_timer_visuals(pulse=True)
        self.statusBar().showMessage(
            "Study session started.",
            1800,
        )

    def pause_study_timer(self):
        self.timer.stop()
        if self.elapsed_seconds > 0:
            self.timer_state = "paused"
        else:
            self.timer_state = "ready"
        self.update_timer_visuals(pulse=True)
        self.statusBar().showMessage(
            "Study session paused.",
            1800,
        )

    def tick_timer(self):
        self.elapsed_seconds += 1
        self.update_timer_visuals()

    def confirm_reset_timer(self):
        if self.elapsed_seconds <= 0:
            self.reset_timer()
            return

        response = QMessageBox.question(
            self,
            "Reset Study Session",
            "Reset the current study timer? The unlogged time will be discarded.",
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if response == QMessageBox.StandardButton.Yes:
            self.reset_timer()

    def reset_timer(self):
        self.timer.stop()
        self.elapsed_seconds = 0
        self.timer_state = "ready"
        self.update_timer_visuals(pulse=True)
        self.statusBar().showMessage(
            "Study session reset.",
            1800,
        )

    def apply_timer_to_session_log(self):
        self.pause_study_timer()
        hours = self.elapsed_seconds / 3600
        self.session_hours.setText(
            f"{hours:.2f}"
        )
        self.statusBar().showMessage(
            "Current timer value copied into the session log.",
            3500,
        )

    def transfer_timer(self):
        self.pause_study_timer()
        self.session_hours.setText(
            f"{self.elapsed_seconds / 3600:.2f}"
        )
        self.navigate(5)

    def save_session(self):
        try:
            hours = float(self.session_hours.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Hours", "Hours must be numeric.")
            return
        linked_task_id = self.session_task.currentData()
        (
            linked_task_id,
            linked_workspace_key,
            linked_task_label,
        ) = task_workspace.session_link_values(
            self.conn,
            linked_task_id,
        )
        self.conn.execute(
            """INSERT INTO study_sessions
               (
                   session_date,hours,google_progress,datacamp_progress,
                   sql_problems,portfolio_progress,notes,productivity_score,
                   task_id,workspace_key,task_label_snapshot
               )
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                self.session_date.text(),
                hours,
                self.session_google.text(),
                self.session_datacamp.text(),
                self.session_sql.value(),
                self.session_portfolio.text(),
                self.session_notes.toPlainText(),
                self.session_productivity.value(),
                linked_task_id,
                linked_workspace_key,
                linked_task_label,
            ),
        )
        self.conn.commit()
        self.reset_timer()
        self.refresh_all()

    def add_evidence(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Add Demonstrated Evidence"
        )
        dialog.setMinimumSize(
            620,
            440,
        )
        dialog.setStyleSheet(
            stylesheet(self._ui_scale, self._content_scale)
        )
        form = QFormLayout(dialog)

        guidance = QLabel(
            (
                "Record something you can point to as proof. "
                "Name the skill, identify the artifact or experience, "
                "and describe what you personally did."
            )
        )
        guidance.setWordWrap(True)
        guidance.setObjectName("Muted")
        form.addRow(guidance)

        skill = QLineEdit()
        skill.setPlaceholderText(
            "Example: SQL aggregation and HAVING"
        )

        source_type = QComboBox()
        source_type.addItems(
            [
                "Portfolio",
                "Coursework",
                "Work Experience",
                "SQL Practice",
                "Certification",
            ]
        )

        source_name = QLineEdit()
        source_name.setPlaceholderText(
            (
                "Example: DuckDB Exercise 02 — "
                "Summarize retail orders"
            )
        )

        description = QTextEdit()
        description.setPlaceholderText(
            (
                "Example: Wrote grouped revenue and order-count queries, "
                "used HAVING to filter groups, and validated totals against "
                "the source CSV."
            )
        )

        form.addRow("Skill", skill)
        form.addRow(
            "Source type",
            source_type,
        )
        form.addRow(
            "Source name",
            source_name,
        )
        form.addRow(
            "What this proves",
            description,
        )

        buttons = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(
            dialog.reject
        )
        save = QPushButton("Save Evidence")
        save.setObjectName("Primary")
        save.clicked.connect(
            dialog.accept
        )
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        form.addRow(buttons)

        if (
            dialog.exec()
            != QDialog.Accepted
        ):
            return

        skill_text = skill.text().strip()
        source_text = (
            source_name.text().strip()
        )
        description_text = (
            description.toPlainText().strip()
        )

        if not skill_text or not source_text:
            QMessageBox.warning(
                self,
                "Evidence Needs More Detail",
                (
                    "Enter both the skill demonstrated and the "
                    "specific source or artifact."
                ),
            )
            return

        self.conn.execute(
            """INSERT INTO evidence
               (
                   skill,
                   source_type,
                   source_name,
                   description
               )
               VALUES(?,?,?,?)
               ON CONFLICT(
                   skill,
                   source_type,
                   source_name
               )
               DO UPDATE SET
                   description=excluded.description""",
            (
                skill_text,
                source_type.currentText(),
                source_text,
                description_text,
            ),
        )
        self.conn.commit()
        self.refresh_readiness()
        self.statusBar().showMessage(
            f"Evidence saved: {skill_text}",
            4200,
        )

    def view_selected_evidence(
        self,
        _item=None,
    ):
        item = self.evidence_list.currentItem()
        if item is None:
            self.statusBar().showMessage(
                "Select an evidence item first.",
                3200,
            )
            return

        evidence_id = item.data(
            Qt.ItemDataRole.UserRole
        )
        if evidence_id is None:
            return

        row = self.conn.execute(
            """SELECT *
               FROM evidence
               WHERE id=?""",
            (int(evidence_id),),
        ).fetchone()
        if row is None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Demonstrated Evidence"
        )
        dialog.setMinimumSize(
            620,
            380,
        )
        dialog.setStyleSheet(
            stylesheet(self._ui_scale, self._content_scale)
        )
        form = QFormLayout(dialog)

        skill_value = QLabel(row["skill"])
        skill_value.setWordWrap(True)
        source_value = QLabel(
            (
                f"{row['source_type']} • "
                f"{row['source_name']}"
            )
        )
        source_value.setWordWrap(True)
        description_value = QTextEdit()
        description_value.setReadOnly(True)
        description_value.setPlainText(
            row["description"]
            or "No description recorded."
        )

        form.addRow(
            "Skill",
            skill_value,
        )
        form.addRow(
            "Source",
            source_value,
        )
        form.addRow(
            "Evidence details",
            description_value,
        )

        close = QPushButton("Close")
        close.clicked.connect(
            dialog.accept
        )
        form.addRow(close)
        dialog.exec()


    def add_application(self):
        if not self.app_company.text().strip() or not self.app_role.text().strip():
            return
        self.conn.execute(
            """INSERT INTO applications
               (applied_date,company,role,location,source,status,
                follow_up_date,resume_version,contact,notes)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                self.app_date.text(),
                self.app_company.text(),
                self.app_role.text(),
                self.app_location.text(),
                self.app_source.text(),
                self.app_status.currentText(),
                self.app_follow_up.text(),
                self.app_resume.text(),
                self.app_contact.text(),
                self.app_notes.toPlainText(),
            ),
        )
        self.conn.commit()
        self.refresh_all()

    def generate_summary(self):
        week = self.state["current_week"]
        tasks = self.conn.execute(
            "SELECT completed FROM sprint_tasks WHERE week=?", (week,)
        ).fetchall()
        done = sum(int(row["completed"]) for row in tasks)
        total = len(tasks)
        hours = self.conn.execute(
            "SELECT COALESCE(SUM(hours),0) FROM study_sessions"
        ).fetchone()[0]
        sql_count = (
            achievements.completed_sql_count(
                self.conn
            )
        )

        summary = (
            f"Week {week}: {done}/{total} sprint tasks completed, "
            f"{hours:g} study hours, and {sql_count} SQL problems completed. "
            f"Win: {self.review_win.toPlainText() or 'Not recorded.'} "
            f"Blocker: {self.review_blocker.toPlainText() or 'None recorded.'} "
            f"SQL review: {self.review_sql.toPlainText() or 'Continue current progression.'} "
            f"Next adjustment: {self.review_adjustment.toPlainText() or 'Continue roadmap.'} "
            f"Confidence: {self.review_confidence.value()}/10."
        )
        self.conn.execute(
            """INSERT INTO weekly_summaries
               (week,hours,tasks_completed,tasks_total,sql_completed,summary)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(week) DO UPDATE SET
               generated_at=CURRENT_TIMESTAMP,hours=excluded.hours,
               tasks_completed=excluded.tasks_completed,
               tasks_total=excluded.tasks_total,
               sql_completed=excluded.sql_completed,summary=excluded.summary""",
            (week, hours, done, total, sql_count, summary),
        )
        self.conn.commit()
        retrospective_task_id = task_workspace.ensure_weekly_workspace_task(
            self.conn,
            week,
            "retrospective",
        )
        task_workspace.upsert_generated_section(
            self.conn,
            ROOT,
            retrospective_task_id,
            heading="Generated Weekly Summary",
            body=summary,
            current_project=int(self.state["current_project"]),
        )
        self.refresh_all()

    def publish_progress(self):
        readiness = analytics.readiness(self.conn, self.state)
        publish(self.conn, ROOT, self.state, PROJECT_NAMES, readiness)
        self.refresh_git()

    def refresh_git(self):
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.git_status.setPlainText(
            result.stdout or result.stderr or "Working tree clean."
        )

    def commit_git(self):
        subprocess.run(["git", "add", "."], cwd=ROOT)
        result = subprocess.run(
            ["git", "commit", "-m", self.commit_message.text()],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        QMessageBox.information(self, "Git", result.stdout or result.stderr)
        self.refresh_git()

    def push_git(self):
        result = subprocess.run(
            ["git", "push"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            QMessageBox.critical(self, "Push Failed", result.stderr or result.stdout)
        else:
            QMessageBox.information(self, "Pushed", result.stdout or "Push complete.")
        self.refresh_git()

    def save_settings(self):
        save_setting(self.conn, "autosave_minutes", self.autosave_minutes.value())
        if hasattr(self, "interface_scale_slider"):
            save_setting(
                self.conn,
                "interface_scale_percent",
                self.interface_scale_slider.value(),
            )
        interval = self.autosave_minutes.value() * 60 * 1000
        self.autosave_timer.start(max(60000, interval))
        self.settings_status.setText("Settings saved.")

    def confirm_rebuild_today_snapshot(self):
        result = QMessageBox.question(
            self,
            "Rebuild Today's Snapshot",
            (
                "Recalculate Today's Focus from your current progress and "
                "adaptive roadmap?\n\n"
                "This replaces only today's frozen recommendation. Completed "
                "tasks, study sessions, notes, achievements, and previous days "
                "will not be erased."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        self.rebuild_today_snapshot()

    def rebuild_today_snapshot(self):
        self.state = state(self.conn)
        tracks.sync_all(self.conn, self.state)
        self.state = state(self.conn)
        week = int(self.state["current_week"])
        guide = WEEKLY_GUIDANCE.get(
            week,
            (
                "Keep Moving",
                "Continue the current course",
                "Continue DataCamp",
                [],
                "Advance the project",
            ),
        )
        try:
            report = planner.rebuild_today_snapshot(
                self.conn,
                week,
                guide,
                self.state,
                max_items=4,
            )
            self.refresh_dashboard(sync_tracks=False)
            self.refresh_planner()
            message = (
                f"Today's snapshot rebuilt: {report['created']} focus "
                f"item(s) generated for {report['focus_date']}."
            )
            self.settings_status.setText(message)
            self.statusBar().showMessage(message, 7000)
            QMessageBox.information(
                self,
                "Snapshot Rebuilt",
                message
                + "\n\nYour task completions and study history were preserved.",
            )
        except Exception as error:
            self.settings_status.setText(
                f"Today's snapshot could not be rebuilt: {error}"
            )
            QMessageBox.critical(
                self,
                "Snapshot Rebuild Failed",
                (
                    "Data Career Accelerator could not rebuild today's snapshot.\n\n"
                    f"{error}"
                ),
            )

    def reset_progress_details(self):
        return (
            "This will permanently reset the active Data Career Accelerator profile.\\n\\n"
            "The following progress will be cleared:\\n"
            "• All roadmap and daily-focus completion\\n"
            "• All portfolio milestones and saved project notes\\n"
            "• All study sessions, hours, streaks, and productivity scores\\n"
            "• All completed SQL problems and review dates\\n"
            "• All achievements and weekly summaries\\n"
            "• All applications, follow-up dates, and evidence records\\n"
            "• All retrospective notes and progress dates\\n\\n"
            "The application will restart at:\\n"
            "• Week 1 of 12\\n"
            "• Google Course 1, Module 1\\n"
            "• Portfolio Project 1\\n"
            "• 0 study hours and 0 completed tasks\\n"
            f"• Start date: {date.today().isoformat()}\\n\\n"
            "A safety database backup will be created first. "
            "Autosave preferences, focus-goal preferences, and existing backup "
            "files will be preserved."
        )

    def confirm_factory_reset(self):
        first = QMessageBox.warning(
            self,
            "Reset All Progress — Confirmation 1 of 3",
            self.reset_progress_details(),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )
        if first != QMessageBox.StandardButton.Yes:
            return

        confirmation_text, accepted = QInputDialog.getText(
            self,
            "Reset All Progress — Confirmation 2 of 3",
            "Type RESET ALL PROGRESS exactly to continue:",
        )
        if (
            not accepted
            or confirmation_text.strip()
            != "RESET ALL PROGRESS"
        ):
            QMessageBox.information(
                self,
                "Reset Cancelled",
                "The confirmation phrase did not match. No data was changed.",
            )
            return

        final = QMessageBox.critical(
            self,
            "Reset All Progress — Final Confirmation",
            (
                "This is the final confirmation.\\n\\n"
                "Data Career Accelerator will create a safety backup and then erase "
                "all tracked progress listed in the previous warning. The active "
                "profile will be rebuilt from the Course 1 starter roadmap.\\n\\n"
                "Proceed with the irreversible reset?"
            ),
            (
                QMessageBox.StandardButton.Reset
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )
        if final != QMessageBox.StandardButton.Reset:
            return

        self.perform_factory_reset()

    def perform_factory_reset(self):
        self.timer.stop()
        self.conn.commit()
        backup_path = create_backup(ROOT)

        try:
            factory_reset(
                self.conn,
                date.today().isoformat(),
            )
            migrate_result = migrate(
                self.conn,
                ROOT,
            )
            planner.seed(self.conn)
            planner.sync_google_course_progress(
                self.conn,
                1,
            )
            self.state = state(self.conn)
            tracks.sync_all(
                self.conn,
                self.state,
            )
            self.elapsed_seconds = 0
            self.timer_state = "ready"
            self.update_timer_visuals()
            self.refresh_all()
            self.navigate(0)

            QMessageBox.information(
                self,
                "Progress Reset Complete",
                (
                    "Data Career Accelerator has been reset to a clean starter profile.\\n\\n"
                    f"Imported {migrate_result['sprint_tasks']} roadmap tasks and "
                    f"{migrate_result['project_tasks']} portfolio milestones.\\n\\n"
                    f"Safety backup:\\n{backup_path}"
                ),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Reset Failed",
                (
                    "The reset could not be completed. Your safety backup is available at:\\n"
                    f"{backup_path}\\n\\nError: {error}"
                ),
            )
            raise

    @staticmethod
    def _format_bytes(value):
        value = int(value or 0)
        units = ("B", "KB", "MB", "GB", "TB")
        amount = float(value)
        for unit in units:
            if amount < 1024 or unit == units[-1]:
                return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
            amount /= 1024
        return f"{value} B"

    @staticmethod
    def _directory_size(path):
        path = Path(path)
        if not path.exists():
            return 0
        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except OSError:
                    continue
        return total

    def storage_summary_text(self):
        database_path = ROOT / "data" / "career_accelerator.db"
        database_size = database_path.stat().st_size if database_path.exists() else 0
        backup_size = self._directory_size(ROOT / "backups")
        sql_size = sum(
            self._directory_size(path)
            for path in (
                ROOT / "practice" / "duckdb",
                ROOT / "practice" / "submissions",
                ROOT / "resources" / "sql",
            )
        )
        total = database_size + backup_size + sql_size
        return (
            f"Database: {self._format_bytes(database_size)}  •  "
            f"Backups: {self._format_bytes(backup_size)}\n"
            f"DuckDB and local SQL: {self._format_bytes(sql_size)}  •  "
            f"Combined local data: {self._format_bytes(total)}"
        )

    def refresh_storage_summary(self):
        if hasattr(self, "storage_summary_label"):
            self.storage_summary_label.setText(self.storage_summary_text())

    def clean_old_backups(self):
        report = prune_backups_with_report(ROOT / "backups")
        self.refresh_storage_summary()
        self.settings_status.setText(
            f"Removed {report['removed']} old backup(s) and recovered "
            f"{self._format_bytes(report['recovered_bytes'])}. "
            f"{report['kept']} retained backup(s) remain."
        )

    def open_data_folder(self):
        path = ROOT / "data"
        path.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Data Folder", str(exc))

    def backup_database(self):
        path = create_backup(ROOT)
        self.refresh_storage_summary()
        self.settings_status.setText(f"Backup ready: {path}")

    def restore_tasks(self):
        result = migrate(self.conn, ROOT)
        planner.seed(self.conn)
        self.settings_status.setText(
            f"Imported {result['sprint_tasks']} sprint tasks and "
            f"{result['project_tasks']} portfolio milestones."
        )
        self.refresh_all()

    def autosave(self):
        create_backup(ROOT)
        self.statusBar().showMessage("Autosave backup created.", 3000)

    # ---------- Shortcuts / Command Palette ----------
    def setup_shortcuts(self):
        palette_action = QAction(self)
        palette_action.setShortcut(QKeySequence("Ctrl+K"))
        palette_action.triggered.connect(self.command_palette)
        self.addAction(palette_action)

        save_action = QAction(self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.autosave)
        self.addAction(save_action)

    def command_palette(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Command Palette")
        dialog.setStyleSheet(stylesheet(self._ui_scale, self._content_scale))
        layout = QVBoxLayout(dialog)
        search = QLineEdit()
        search.setPlaceholderText("Type a command…")
        commands = QListWidget()
        command_items = [
            ("🏠 Open Dashboard", lambda: self.navigate(0)),
            ("🚀 Build Adaptive Plan", lambda: self.navigate(1)),
            ("📁 Open Portfolio Workspace", lambda: self.navigate(3)),
            ("💻 Open SQL Companion", lambda: self.navigate(4)),
            ("⏱️ Start Study Timer", self.start_study_timer),
            ("📝 Open Weekly Review", lambda: self.navigate(8)),
            ("🚀 Publish Progress", self.publish_progress),
            ("💾 Create Backup", self.backup_database),
        ]
        for label, _ in command_items:
            commands.addItem(label)
        layout.addWidget(search)
        layout.addWidget(commands)

        def filter_commands(text):
            for index in range(commands.count()):
                item = commands.item(index)
                item.setHidden(text.lower() not in item.text().lower())

        def run_selected():
            row = commands.currentRow()
            if row >= 0:
                command_items[row][1]()
                dialog.accept()

        search.textChanged.connect(filter_commands)
        commands.itemDoubleClicked.connect(lambda _: run_selected())
        search.returnPressed.connect(run_selected)
        dialog.resize(520, 420)
        dialog.exec()

def run():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CareerAccelerator()
    window.show()
    sys.exit(app.exec())
