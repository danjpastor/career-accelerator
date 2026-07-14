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
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFormLayout,
    QInputDialog,
    QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton, QProgressBar,
    QScrollArea, QSizePolicy, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)

from career_app import __version__
from career_app.database import (
    connect, ensure_default_state, factory_reset, save_setting, setting, state, update_state
)
from career_app.data.roadmap import (
    DATACAMP_TRACK, PROJECT_DIRS, PROJECT_NAMES, PROJECT_STAGES,
    SQL_COMPANION, WEEKLY_GUIDANCE
)
from career_app.services import analytics, coach, planner, tracks
from career_app.services.backup import create_backup
from career_app.services.migration import migrate
from career_app.services.publisher import publish
from career_app.theme import COLORS, stylesheet
from career_app.ui.widgets import (
    AreaChart, BadgeCard, Card, CircularTimer, Divider, FocusRow,
    FooterMetricBox, MetricRow, MiniSparkline, Ring, SectionHeader,
    SidebarMetricCard, SoftPanel, StatRow, TaskRow
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
    ("📝 Weekly Review", 8),
    ("🚀 Publish & Git", 9),
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
                self._animate(
                    watched,
                    1.0,
                    115,
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


class ResponsiveDashboardContent(QWidget):
    widthChanged = Signal(int)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.widthChanged.emit(event.size().width())


class CareerAccelerator(QMainWindow):
    DASHBOARD_WIDE_BREAKPOINT = 1150
    DASHBOARD_MEDIUM_BREAKPOINT = 700
    MINIMUM_WINDOW_WIDTH = 1500
    MINIMUM_WINDOW_HEIGHT = 1020

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

        self.setWindowTitle(f"Career Accelerator v{__version__}")

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
                    "DanielPastor.CareerAccelerator"
                )
            except Exception:
                pass

        self.resize(1536, 1020)
        self.setMinimumSize(
            self.MINIMUM_WINDOW_WIDTH,
            self.MINIMUM_WINDOW_HEIGHT,
        )
        self.setStyleSheet(stylesheet())

        self.button_feedback = ButtonFeedbackFilter(self)
        QApplication.instance().installEventFilter(
            self.button_feedback
        )

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self.build_sidebar())

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
        ]
        for builder in builders:
            self.stack.addWidget(builder())

        self.setup_shortcuts()
        self.update_timer_visuals()
        self.refresh_all()

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
        side.setFixedWidth(266)

        layout = QVBoxLayout(side)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(6)

        logo_row = QHBoxLayout()
        logo = QLabel("🚀")
        logo.setStyleSheet("font-size:28pt;")
        logo_row.addWidget(logo)

        title_layout = QVBoxLayout()
        career = QLabel("CAREER")
        career.setStyleSheet("font-size:17pt;font-weight:800;")
        accelerator = QLabel("ACCELERATOR")
        accelerator.setStyleSheet(
            f"font-size:15pt;font-weight:800;color:{COLORS['purple']};"
        )
        title_layout.addWidget(career)
        title_layout.addWidget(accelerator)
        logo_row.addLayout(title_layout, 1)
        layout.addLayout(logo_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color:{COLORS['border']};")
        layout.addWidget(divider)

        group = QButtonGroup(self)
        group.setExclusive(True)
        self.nav_buttons = []

        nav_items = [
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
            ("⚙️ Settings", 10),
        ]

        for text, index in nav_items:
            button = QPushButton(text)
            button.setObjectName("Nav")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, target=index: self.navigate(target)
            )
            group.addButton(button)
            layout.addWidget(button)
            self.nav_buttons.append(button)
            if index == 0:
                button.setChecked(True)

        layout.addStretch()

        streak_card = QFrame()
        streak_card.setObjectName("SidebarCard")
        streak_layout = QVBoxLayout(streak_card)
        streak_layout.setContentsMargins(16, 14, 16, 14)
        streak_layout.setSpacing(6)

        streak_title = QLabel("CURRENT STREAK")
        streak_title.setObjectName("Tiny")
        streak_layout.addWidget(streak_title)

        streak_value_row = QHBoxLayout()
        flame = QLabel("🔥")
        flame.setStyleSheet("font-size:24pt;")
        streak_value_row.addWidget(flame)

        self.side_streak_value = QLabel("0")
        self.side_streak_value.setStyleSheet("font-size:25pt;font-weight:700;")
        streak_value_row.addWidget(self.side_streak_value)

        days_label = QLabel("days")
        days_label.setObjectName("Muted")
        streak_value_row.addWidget(days_label)
        streak_value_row.addStretch()
        streak_layout.addLayout(streak_value_row)

        self.streak_week = QLabel("○  ○  ○  ○  ○  ○  ○")
        self.streak_week.setStyleSheet(
            f"color:{COLORS['purple']};font-size:13pt;"
        )
        streak_layout.addWidget(self.streak_week)

        self.best_streak_label = QLabel("Best Streak: 0 days")
        self.best_streak_label.setObjectName("Muted")
        streak_layout.addWidget(self.best_streak_label)

        layout.addWidget(streak_card)

        time_card = QFrame()
        time_card.setObjectName("SidebarCard")
        time_layout = QVBoxLayout(time_card)
        time_layout.setContentsMargins(16, 14, 16, 14)
        time_layout.setSpacing(6)

        study_title = QLabel("⏱️  TOTAL STUDY TIME")
        study_title.setStyleSheet(
            f"font-weight:700;color:{COLORS['cyan']};"
        )
        time_layout.addWidget(study_title)

        self.side_hours_value = QLabel("0h")
        self.side_hours_value.setStyleSheet("font-size:22pt;font-weight:700;")
        time_layout.addWidget(self.side_hours_value)

        this_week = QLabel("This Week")
        this_week.setObjectName("Muted")
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
        layout.addWidget(footer)
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
        }
        target = label_map.get(index)
        if target:
            for button in self.nav_buttons:
                if target in button.text():
                    button.setChecked(True)
                    break

    def page(self, title, subtitle=None):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        heading = QHBoxLayout()
        text = QVBoxLayout()
        hero = QLabel(title)
        hero.setObjectName("Hero")
        hero.setStyleSheet("background:transparent;border:none;")
        text.addWidget(hero)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("Muted")
            sub.setWordWrap(True)
            text.addWidget(sub)
        heading.addLayout(text)
        heading.addStretch()

        today = QLabel(f"📅 {datetime.now():%A, %B %d, %Y}")
        today.setObjectName("Muted")
        heading.addWidget(today)
        layout.addLayout(heading)
        return page, layout

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
        page = QWidget()
        page.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        root = QVBoxLayout(page)
        root.setContentsMargins(24, 16, 24, 14)
        root.setSpacing(10)
        root.setSizeConstraint(QLayout.SetDefaultConstraint)

        self.dashboard_content = page
        self.dashboard_root_layout = root
        self.dashboard_layout_mode = None

        # ---------- Header ----------
        self.dashboard_header_section = QWidget()
        header = QHBoxLayout(self.dashboard_header_section)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        left_header = QVBoxLayout()
        left_header.setSpacing(3)

        self.dashboard_hero = QLabel("")
        self.dashboard_hero.setObjectName("Hero")
        left_header.addWidget(self.dashboard_hero)

        self.dashboard_quote = QLabel("")
        self.dashboard_quote.setObjectName("Muted")
        self.dashboard_quote.setStyleSheet(
            "font-style:italic;color:#b6bfd0;"
        )
        left_header.addWidget(self.dashboard_quote)

        header.addLayout(left_header)
        header.addStretch()

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
            card.setMinimumHeight(116)
            card.setMaximumHeight(120)
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
        self.dashboard_primary_grid = QGridLayout(
            self.dashboard_primary_section
        )
        self.dashboard_primary_grid.setContentsMargins(0, 0, 0, 0)
        self.dashboard_primary_grid.setHorizontalSpacing(10)
        self.dashboard_primary_grid.setVerticalSpacing(10)

        self.dashboard_focus_card = Card()
        self.dashboard_focus_card.setMinimumHeight(286)
        self.dashboard_focus_card.layout.setContentsMargins(
            14,
            13,
            14,
            12,
        )
        self.dashboard_focus_card.layout.setSpacing(6)
        self.dashboard_focus_card.layout.addWidget(
            SectionHeader(
                "🎯",
                "Today's Focus",
                "Priority-driven plan grounded in this week's roadmap",
            )
        )

        self.focus_layout = QVBoxLayout()
        self.focus_layout.setSpacing(0)
        self.dashboard_focus_card.layout.addLayout(
            self.focus_layout
        )
        self.dashboard_focus_card.layout.addWidget(Divider())

        focus_footer = QHBoxLayout()
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

        focus_footer.addWidget(self.focus_total_time, 1)
        focus_footer.addWidget(self.focus_task_count, 1)
        self.dashboard_focus_card.layout.addLayout(focus_footer)

        self.dashboard_tasks_card = Card()
        self.dashboard_tasks_card.setMinimumHeight(286)
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
        self.dashboard_timer_card.setMinimumHeight(286)
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

        timer_stage = QWidget()
        timer_stage.setFixedHeight(144)
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

        timer_controls = QHBoxLayout()
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
        self.dashboard_growth_card.setMinimumHeight(232)
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
        self.growth_period_combo.setFixedWidth(104)
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
        self.dashboard_achievement_card.setMinimumHeight(232)
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
        self.dashboard_summary_card.setMinimumHeight(232)
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

        summary_button = QPushButton("View Full Summary")
        summary_button.setObjectName("Secondary")
        summary_button.clicked.connect(lambda: self.navigate(8))
        self.dashboard_summary_card.layout.addWidget(
            summary_button
        )

        # ---------- Encouragement and Mission Control ----------
        self.dashboard_footer_section = QWidget()
        self.dashboard_footer_grid = QGridLayout(
            self.dashboard_footer_section
        )
        self.dashboard_footer_grid.setContentsMargins(0, 0, 0, 0)
        self.dashboard_footer_grid.setHorizontalSpacing(10)
        self.dashboard_footer_grid.setVerticalSpacing(10)

        self.encouragement_card = Card()
        self.encouragement_card.setMinimumHeight(150)
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
        self.footer_message.setWordWrap(False)
        self.footer_message.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.footer_message.setMinimumHeight(19)
        self.footer_message.setMaximumHeight(20)
        encouragement_text_layout.addWidget(
            self.footer_message
        )

        self.footer_subtitle = QLabel("")
        self.footer_subtitle.setObjectName("Muted")
        self.footer_subtitle.setWordWrap(False)
        self.footer_subtitle.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.footer_subtitle.setMinimumHeight(18)
        self.footer_subtitle.setMaximumHeight(19)
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
        self.dashboard_mission_card.setMinimumHeight(150)
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
        self.dashboard_mission_detail.setMinimumHeight(18)
        self.dashboard_mission_detail.setMaximumHeight(36)
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

        QTimer.singleShot(
            0,
            lambda: self.update_dashboard_layout(
                self.DASHBOARD_WIDE_BREAKPOINT
            ),
        )
        return page

    def _take_layout_items(self, layout):
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
            self.dashboard_mission_card.setMinimumHeight(205)
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
            self.dashboard_mission_card.setMinimumHeight(150)

    def update_dashboard_layout(self, width):
        mode = "wide"

        if mode == self.dashboard_layout_mode:
            return
        self.dashboard_layout_mode = mode

        self._take_layout_items(self.dashboard_metrics_grid)
        self._take_layout_items(self.dashboard_primary_grid)
        self._take_layout_items(self.dashboard_secondary_grid)
        self._take_layout_items(self.dashboard_footer_grid)
        self._take_layout_items(
            self.dashboard_compact_footer_layout
        )

        if mode == "wide":
            self.dashboard_footer_section.show()
            self.dashboard_compact_footer_stack.hide()
            self._layout_mission_actions(compact=False)

            for column, card in enumerate(
                self.dashboard_metric_cards
            ):
                self.dashboard_metrics_grid.addWidget(
                    card,
                    0,
                    column,
                )
                self.dashboard_metrics_grid.setColumnStretch(
                    column,
                    1,
                )

            self.dashboard_primary_grid.addWidget(
                self.dashboard_focus_card,
                0,
                0,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_tasks_card,
                0,
                1,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_timer_card,
                0,
                2,
            )
            self.dashboard_primary_grid.setColumnStretch(0, 34)
            self.dashboard_primary_grid.setColumnStretch(1, 33)
            self.dashboard_primary_grid.setColumnStretch(2, 33)

            self.dashboard_secondary_grid.addWidget(
                self.dashboard_growth_card,
                0,
                0,
            )
            self.dashboard_secondary_grid.addWidget(
                self.dashboard_achievement_card,
                0,
                1,
            )
            self.dashboard_secondary_grid.addWidget(
                self.dashboard_summary_card,
                0,
                2,
            )
            self.dashboard_secondary_grid.setColumnStretch(0, 38)
            self.dashboard_secondary_grid.setColumnStretch(1, 29)
            self.dashboard_secondary_grid.setColumnStretch(2, 33)

            self.dashboard_footer_grid.addWidget(
                self.encouragement_card,
                0,
                0,
            )
            self.dashboard_footer_grid.addWidget(
                self.dashboard_mission_card,
                0,
                1,
            )
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

        elif mode == "medium":
            self.dashboard_footer_section.hide()
            self.dashboard_compact_footer_stack.show()
            self._layout_mission_actions(compact=True)

            metric_positions = [
                (0, 0, 1, 2),
                (0, 2, 1, 2),
                (0, 4, 1, 2),
                (1, 0, 1, 3),
                (1, 3, 1, 3),
            ]
            for card, position in zip(
                self.dashboard_metric_cards,
                metric_positions,
            ):
                self.dashboard_metrics_grid.addWidget(
                    card,
                    *position,
                )
            for column in range(6):
                self.dashboard_metrics_grid.setColumnStretch(
                    column,
                    1,
                )

            self.dashboard_compact_footer_layout.addWidget(
                self.encouragement_card
            )
            self.dashboard_compact_footer_layout.addWidget(
                self.dashboard_mission_card
            )

            self.dashboard_primary_grid.addWidget(
                self.dashboard_focus_card,
                0,
                0,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_timer_card,
                0,
                1,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_tasks_card,
                1,
                0,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_compact_footer_stack,
                1,
                1,
            )
            self.dashboard_primary_grid.setColumnStretch(0, 1)
            self.dashboard_primary_grid.setColumnStretch(1, 1)

            self.dashboard_secondary_grid.addWidget(
                self.dashboard_growth_card,
                0,
                0,
                1,
                2,
            )
            self.dashboard_secondary_grid.addWidget(
                self.dashboard_achievement_card,
                1,
                0,
            )
            self.dashboard_secondary_grid.addWidget(
                self.dashboard_summary_card,
                1,
                1,
            )
            self.dashboard_secondary_grid.setColumnStretch(0, 1)
            self.dashboard_secondary_grid.setColumnStretch(1, 1)

            self._set_dashboard_section_order(
                [
                    self.dashboard_header_section,
                    self.dashboard_primary_section,
                    self.dashboard_metrics_section,
                    self.dashboard_secondary_section,
                ]
            )

        else:
            self.dashboard_footer_section.hide()
            self.dashboard_compact_footer_stack.show()
            self._layout_mission_actions(compact=True)

            metric_positions = [
                (0, 0, 1, 1),
                (0, 1, 1, 1),
                (1, 0, 1, 1),
                (1, 1, 1, 1),
                (2, 0, 1, 2),
            ]
            for card, position in zip(
                self.dashboard_metric_cards,
                metric_positions,
            ):
                self.dashboard_metrics_grid.addWidget(
                    card,
                    *position,
                )
            self.dashboard_metrics_grid.setColumnStretch(0, 1)
            self.dashboard_metrics_grid.setColumnStretch(1, 1)

            self.dashboard_compact_footer_layout.addWidget(
                self.encouragement_card
            )
            self.dashboard_compact_footer_layout.addWidget(
                self.dashboard_mission_card
            )

            self.dashboard_primary_grid.addWidget(
                self.dashboard_focus_card,
                0,
                0,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_tasks_card,
                1,
                0,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_timer_card,
                2,
                0,
            )
            self.dashboard_primary_grid.addWidget(
                self.dashboard_compact_footer_stack,
                3,
                0,
            )
            self.dashboard_primary_grid.setColumnStretch(0, 1)

            self.dashboard_secondary_grid.addWidget(
                self.dashboard_growth_card,
                0,
                0,
            )
            self.dashboard_secondary_grid.addWidget(
                self.dashboard_achievement_card,
                1,
                0,
            )
            self.dashboard_secondary_grid.addWidget(
                self.dashboard_summary_card,
                2,
                0,
            )
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

        body = QHBoxLayout()
        queue = Card("Recommended Priority Queue")
        self.plan_list = QListWidget()
        queue.layout.addWidget(self.plan_list)
        queue_buttons = QHBoxLayout()
        continue_button = QPushButton("Continue")
        continue_button.setObjectName("Primary")
        continue_button.clicked.connect(self.continue_plan)
        defer_button = QPushButton("Move to Tomorrow")
        defer_button.clicked.connect(self.defer_plan)
        block_button = QPushButton("Mark Blocked")
        block_button.clicked.connect(self.block_plan)
        queue_buttons.addWidget(continue_button)
        queue_buttons.addWidget(defer_button)
        queue_buttons.addWidget(block_button)
        queue.layout.addLayout(queue_buttons)
        body.addWidget(queue, 1)

        backlog = Card("Sprint Backlog")
        self.backlog_list = QListWidget()
        backlog.layout.addWidget(self.backlog_list)
        edit = QPushButton("Edit Selected Task")
        edit.clicked.connect(self.edit_task)
        backlog.layout.addWidget(edit)
        body.addWidget(backlog, 1)
        root.addLayout(body, 1)
        return page

    # ---------- Learning ----------
    def learning_page(self):
        page, root = self.page(
            "📚 Learning Dashboard",
            "Duolingo-style progress across every skill track in the roadmap.",
        )
        self.learning_cards = {}
        grid = QGridLayout()
        tracks = [
            ("🎓 Google Certificate", "Google"),
            ("📘 DataCamp", "DataCamp"),
            ("💻 SQL Practice", "SQL"),
            ("📊 Power BI", "Power BI"),
            ("🐍 Python", "Python"),
            ("📁 Portfolio", "Portfolio"),
        ]
        for index, (title, key) in enumerate(tracks):
            card = Card(title)
            value = QLabel("—")
            value.setStyleSheet("font-size:20pt;font-weight:700;")
            detail = QLabel("")
            detail.setObjectName("Muted")
            detail.setWordWrap(True)
            continue_button = QPushButton("Continue →")
            card.layout.addWidget(value)
            card.layout.addWidget(detail)
            card.layout.addStretch()
            card.layout.addWidget(continue_button)
            grid.addWidget(card, index // 3, index % 3)
            self.learning_cards[key] = (value, detail)
        root.addLayout(grid)

        progress = Card("Update Learning Progress")
        form = QFormLayout()
        self.week_input = QSpinBox()
        self.week_input.setRange(1, 12)
        self.course_input = QSpinBox()
        self.course_input.setRange(1, 9)
        self.module_input = QSpinBox()
        self.module_input.setRange(1, 20)
        self.hours_input = QSpinBox()
        self.hours_input.setRange(1, 40)
        form.addRow("Current week", self.week_input)
        form.addRow("Google course", self.course_input)
        form.addRow("Google module", self.module_input)
        form.addRow("Weekly target hours", self.hours_input)
        progress.layout.addLayout(form)
        save = QPushButton("Save Learning Progress")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_learning)
        progress.layout.addWidget(save)
        root.addWidget(progress)
        return page

    # ---------- Portfolio ----------
    def portfolio_page(self):
        page, root = self.page(
            "📁 Portfolio Workspace",
            "A guided workspace for building evidence-quality analytics projects.",
        )

        top = QHBoxLayout()
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
        return page

    # ---------- SQL ----------
    def sql_page(self):
        page, root = self.page(
            "💻 SQL Companion",
            "Recommended problems, mastery tracking, notes, review scheduling, and solution files.",
        )

        body = QHBoxLayout()
        recommendations = Card("Today's SQL")
        self.sql_problem_list = QListWidget()
        self.sql_problem_list.itemDoubleClicked.connect(self.prefill_sql)
        recommendations.layout.addWidget(self.sql_problem_list)
        body.addWidget(recommendations, 1)

        detail = Card("Problem Workspace")
        form = QFormLayout()
        self.sql_title = QLineEdit()
        self.sql_difficulty = QLineEdit("Easy")
        self.sql_topic = QLineEdit()
        self.sql_concepts = QLineEdit()
        self.sql_mastery = QSpinBox()
        self.sql_mastery.setRange(1, 5)
        self.sql_mastery.setValue(1)
        self.sql_review = QLineEdit()
        self.sql_notes = QTextEdit()
        form.addRow("Problem title", self.sql_title)
        form.addRow("Difficulty", self.sql_difficulty)
        form.addRow("Topic", self.sql_topic)
        form.addRow("Concepts", self.sql_concepts)
        form.addRow("Mastery (1–5)", self.sql_mastery)
        form.addRow("Review date", self.sql_review)
        form.addRow("Notes", self.sql_notes)
        detail.layout.addLayout(form)

        buttons = QHBoxLayout()
        complete = QPushButton("Mark Complete")
        complete.setObjectName("Primary")
        complete.clicked.connect(self.save_sql)
        hint = QPushButton("Need a Hint")
        hint.clicked.connect(self.sql_hint)
        solution = QPushButton("Open My Solution")
        solution.clicked.connect(self.open_sql_solution)
        buttons.addWidget(complete)
        buttons.addWidget(hint)
        buttons.addWidget(solution)
        detail.layout.addLayout(buttons)
        body.addWidget(detail, 1)
        root.addLayout(body, 1)
        return page

    # ---------- Study ----------
    def study_page(self):
        page, root = self.page(
            "⏱️ Study Session",
            "Track focused time, capture what you completed, and turn each session into progress evidence.",
        )

        body = QGridLayout()
        body.setHorizontalSpacing(12)
        body.setVerticalSpacing(12)

        # Live timer mirrors the Dashboard timer component.
        timer_card = Card(
            "⏱️ Live Timer",
            "The timer is shared with the Dashboard.",
        )
        timer_card.setMinimumWidth(350)
        timer_card.layout.setContentsMargins(18, 16, 18, 16)
        timer_card.layout.setSpacing(10)

        timer_stage = QWidget()
        timer_stage.setFixedHeight(174)
        timer_stage.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )
        timer_stage_layout = QVBoxLayout(timer_stage)
        timer_stage_layout.setContentsMargins(0, 8, 0, 4)
        timer_stage_layout.setSpacing(0)
        timer_stage_layout.setAlignment(
            Qt.AlignCenter,
        )

        self.study_circular_timer = CircularTimer()
        timer_stage_layout.addWidget(
            self.study_circular_timer,
            0,
            Qt.AlignCenter,
        )
        timer_card.layout.addWidget(timer_stage)

        goal_row = QHBoxLayout()
        goal_row.setSpacing(10)
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
        self.session_goal_minutes.setFixedWidth(110)
        self.session_goal_minutes.valueChanged.connect(
            self.change_session_goal
        )
        goal_row.addWidget(self.session_goal_minutes)
        timer_card.layout.addLayout(goal_row)

        self.study_start_button = QPushButton(
            "▶ Start Study Session"
        )
        self.study_start_button.setObjectName("Primary")
        self.study_start_button.setMinimumHeight(38)
        self.study_start_button.clicked.connect(
            self.start_study_timer
        )
        timer_card.layout.addWidget(self.study_start_button)

        timer_controls = QHBoxLayout()
        timer_controls.setSpacing(8)

        self.study_pause_button = QPushButton("⏸️ Pause")
        self.study_pause_button.setObjectName("Secondary")
        self.study_pause_button.setMinimumHeight(34)
        self.study_pause_button.clicked.connect(self.pause_study_timer)

        self.study_reset_button = QPushButton("🔄 Reset")
        self.study_reset_button.setObjectName("Secondary")
        self.study_reset_button.setMinimumHeight(34)
        self.study_reset_button.clicked.connect(
            self.confirm_reset_timer
        )

        timer_controls.addWidget(self.study_pause_button, 1)
        timer_controls.addWidget(self.study_reset_button, 1)
        timer_card.layout.addLayout(timer_controls)

        self.study_use_time_button = QPushButton(
            "📝 Use Current Time in Session Log"
        )
        self.study_use_time_button.setObjectName("Secondary")
        self.study_use_time_button.setMinimumHeight(34)
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

        # Compact session form.
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

        self.session_date = QLineEdit(date.today().isoformat())
        self.session_hours = QLineEdit("1")
        self.session_productivity = QSpinBox()
        self.session_productivity.setRange(1, 10)
        self.session_productivity.setValue(7)
        self.session_sql = QSpinBox()
        self.session_sql.setRange(0, 20)

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
        self.session_notes.setMinimumHeight(115)
        self.session_notes.setMaximumHeight(145)

        form_grid.addWidget(QLabel("Date"), 0, 0)
        form_grid.addWidget(self.session_date, 0, 1)
        form_grid.addWidget(QLabel("Hours"), 0, 2)
        form_grid.addWidget(self.session_hours, 0, 3)

        form_grid.addWidget(QLabel("Productivity"), 1, 0)
        form_grid.addWidget(self.session_productivity, 1, 1)
        form_grid.addWidget(QLabel("SQL problems"), 1, 2)
        form_grid.addWidget(self.session_sql, 1, 3)

        form_grid.addWidget(QLabel("Google progress"), 2, 0)
        form_grid.addWidget(
            self.session_google,
            2,
            1,
            1,
            3,
        )

        form_grid.addWidget(QLabel("DataCamp progress"), 3, 0)
        form_grid.addWidget(
            self.session_datacamp,
            3,
            1,
            1,
            3,
        )

        form_grid.addWidget(QLabel("Portfolio progress"), 4, 0)
        form_grid.addWidget(
            self.session_portfolio,
            4,
            1,
            1,
            3,
        )

        form_grid.addWidget(QLabel("Notes"), 5, 0)
        form_grid.addWidget(
            self.session_notes,
            5,
            1,
            1,
            3,
        )

        log_card.layout.addLayout(form_grid)

        save = QPushButton("✅ Finish and Log Session")
        save.setObjectName("Primary")
        save.setMinimumHeight(38)
        save.clicked.connect(self.save_session)
        log_card.layout.addWidget(save)

        body.addWidget(timer_card, 0, 0)
        body.addWidget(log_card, 0, 1)
        body.setColumnStretch(0, 34)
        body.setColumnStretch(1, 66)
        root.addLayout(body)

        recent = Card(
            "📚 Recent Sessions",
            "Your latest logged study activity.",
        )
        self.session_list = QListWidget()
        self.session_list.setMinimumHeight(190)
        recent.layout.addWidget(self.session_list)
        root.addWidget(recent, 1)

        return page

    # ---------- Readiness ----------
    def readiness_page(self):
        page, root = self.page(
            "🎯 Job Readiness",
            "Connect learning, portfolio work, and professional evidence directly to employability.",
        )

        self.readiness_rings = {}
        rings = QHBoxLayout()
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
            card.setMinimumHeight(138)
            card.setMaximumHeight(148)
            card.layout.setContentsMargins(10, 8, 10, 8)

            ring = Ring(title, color)
            card.layout.addWidget(ring)
            rings.addWidget(card)
            self.readiness_rings[title] = ring

        root.addLayout(rings)

        body = QGridLayout()
        body.setHorizontalSpacing(10)
        body.setVerticalSpacing(10)

        evidence_card = Card(
            "✅ Demonstrated Evidence",
            "Proof that supports your résumé, portfolio, and interview stories.",
        )
        self.evidence_list = QListWidget()
        self.evidence_list.setMinimumHeight(250)
        evidence_card.layout.addWidget(self.evidence_list, 1)

        add_evidence = QPushButton("➕ Add Evidence")
        add_evidence.setObjectName("Primary")
        add_evidence.clicked.connect(self.add_evidence)
        evidence_card.layout.addWidget(add_evidence)

        coach_card = Card(
            "🧭 Readiness Coach",
            "Prioritized recommendations based on your current progress.",
        )
        self.readiness_coach_layout = QVBoxLayout()
        self.readiness_coach_layout.setSpacing(8)
        coach_card.layout.addLayout(self.readiness_coach_layout)
        coach_card.layout.addStretch()

        leverage_card = Card(
            "🚀 Highest Leverage",
            "The next action most likely to improve employability.",
        )

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

        continue_button = QPushButton("▶ Continue Highest-Impact Task")
        continue_button.setObjectName("Primary")
        continue_button.clicked.connect(self.continue_highest_impact)
        leverage_card.layout.addWidget(continue_button)

        coverage_card = Card(
            "📊 Evidence Coverage",
            "Where your documented proof is strongest and where it is still missing.",
        )
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
        body.setRowStretch(0, 1)
        body.setRowStretch(1, 1)

        root.addLayout(body, 1)
        return page

    # ---------- Applications ----------
    def applications_page(self):
        page, root = self.page(
            "💼 Applications CRM",
            "Move opportunities from wishlist to offer using a visual pipeline.",
        )

        form_card = Card("Add Opportunity")
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
        root.addWidget(form_card)

        kanban_scroll = QScrollArea()
        kanban_scroll.setWidgetResizable(True)
        kanban_host = QWidget()
        self.kanban_layout = QHBoxLayout(kanban_host)
        self.kanban_layout.setSpacing(8)
        kanban_scroll.setWidget(kanban_host)
        root.addWidget(kanban_scroll, 1)
        return page

    # ---------- Review ----------
    def review_page(self):
        page, root = self.page(
            "📝 Weekly Review",
            "Turn your activity into an automatic coaching summary.",
        )
        body = QHBoxLayout()
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
        body.addWidget(form_card, 1)

        summaries = Card("Saved Summaries")
        self.summary_list = QListWidget()
        summaries.layout.addWidget(self.summary_list)
        body.addWidget(summaries, 1)
        root.addLayout(body, 1)
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
        card.layout.addWidget(self.git_status)

        self.commit_message = QLineEdit("progress: update career accelerator")
        card.layout.addWidget(self.commit_message)

        buttons = QHBoxLayout()
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
        return page

    # ---------- Settings ----------
    def settings_page(self):
        page, root = self.page(
            "⚙️ Settings",
            "Manage application behavior, backups, repository access, and optional future integrations.",
        )

        settings_grid = QGridLayout()
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
        self.autosave_minutes.setFixedWidth(110)
        autosave_row.addWidget(self.autosave_minutes)
        general_card.layout.addLayout(autosave_row)

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

        restore = QPushButton(
            "🔄 Restore Tasks From Repository Files"
        )
        restore.setObjectName("Secondary")
        restore.clicked.connect(self.restore_tasks)
        data_card.layout.addWidget(restore)

        data_note = QLabel(
            "Backups exclude the repository and are stored locally in the backups folder."
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

        settings_grid.addWidget(general_card, 0, 0)
        settings_grid.addWidget(data_card, 0, 1)
        settings_grid.addWidget(repository_card, 1, 0)
        settings_grid.addWidget(reset_card, 1, 1)
        settings_grid.setColumnStretch(0, 1)
        settings_grid.setColumnStretch(1, 1)

        root.addLayout(settings_grid)

        status_card = Card("ℹ️ Status")
        status_card.layout.setContentsMargins(18, 12, 18, 12)

        status_row = QHBoxLayout()
        self.settings_status = QLabel(
            f"Career Accelerator v{__version__} • Local SQLite mode"
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

        def unlock(key, title, description):
            if self._unlock_achievement(
                key,
                title,
                description,
            ):
                unlocked.append(title)

        completed_tasks = self.conn.execute(
            """SELECT
                   s.id,
                   s.week,
                   s.sort_order,
                   s.label,
                   m.category
               FROM sprint_tasks s
               LEFT JOIN task_metadata m
                 ON m.task_id=s.id
               WHERE s.completed=1
               ORDER BY s.week,s.sort_order,s.id"""
        ).fetchall()
        for row in completed_tasks:
            details = self.roadmap_achievement_details(
                row
            )
            unlock(
                f"task:{row['id']}",
                details["title"],
                details["description"],
            )

        completed_project_tasks = self.conn.execute(
            """SELECT id,label
               FROM project_tasks
               WHERE completed=1
               ORDER BY id"""
        ).fetchall()
        for row in completed_project_tasks:
            unlock(
                f"project-task:{row['id']}",
                "Portfolio Milestone Complete",
                row["label"],
            )

        sql_rows = self.conn.execute(
            """SELECT id,title
               FROM sql_practice
               ORDER BY id"""
        ).fetchall()
        for row in sql_rows:
            unlock(
                f"sql-problem:{row['id']}",
                "SQL Problem Solved",
                row["title"],
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
        task_count = len(completed_tasks)
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

        self.conn.commit()
        return unlocked

    def achievement_progress(self):
        session_count = self.conn.execute(
            "SELECT COUNT(*) FROM study_sessions"
        ).fetchone()[0]
        completed_tasks = self.conn.execute(
            "SELECT COUNT(*) FROM sprint_tasks WHERE completed=1"
        ).fetchone()[0]
        sql_count = self.conn.execute(
            "SELECT COUNT(*) FROM sql_practice"
        ).fetchone()[0]
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
        dialog.setStyleSheet(stylesheet())
        dialog.resize(650, 560)

        layout = QVBoxLayout(dialog)

        title = QLabel("🏅 Achievements")
        title.setObjectName("Hero")
        layout.addWidget(title)

        subtitle = QLabel(
            "Every completed roadmap task, portfolio milestone, SQL problem, "
            "study session, and application earns a persistent achievement."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        unlocked_label = QLabel("Unlocked Rewards")
        unlocked_label.setObjectName("SectionTitle")
        layout.addWidget(unlocked_label)

        achievement_list = QListWidget()
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
    def refresh_all(self):
        self.state = state(self.conn)
        tracks.sync_all(
            self.conn,
            self.state,
        )
        self.state = state(self.conn)
        newly_unlocked = self.sync_achievement_records()

        self.refresh_dashboard()
        self.refresh_planner()
        self.refresh_learning()
        self.refresh_project()
        self.refresh_sql()
        self.refresh_sessions()
        self.refresh_readiness()
        self.refresh_applications()
        self.refresh_summaries()
        self.refresh_git()

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

    def refresh_dashboard(self):
        tracks.sync_all(
            self.conn,
            self.state,
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

        sql_count = self.conn.execute(
            "SELECT COUNT(*) FROM sql_practice"
        ).fetchone()[0]

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
        self.clear_layout(self.focus_layout)

        intelligent_focus = planner.intelligent_focus_plan(
            self.conn,
            week,
            guide,
            self.state,
            max_items=4,
        )

        focus_styles = {
            "Learning": ("🎓", "Learning", COLORS["blue"]),
            "SQL": ("💻", "SQL Practice", COLORS["purple"]),
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

        estimated_minutes = 0

        for index, item in enumerate(intelligent_focus):
            emoji, default_title, accent = focus_styles.get(
                item["category"],
                focus_styles["General"],
            )

            if item.get("roadmap_fallback"):
                title = item.get(
                    "display_title",
                    default_title,
                )
                detail = item.get(
                    "detail",
                    item["label"],
                )
            else:
                lower_label = item["label"].lower()
                if item["category"] == "Learning":
                    if any(
                        token in lower_label
                        for token in ("google", "course", "module")
                    ):
                        title = "Google Certificate"
                        emoji = "🎓"
                    elif "datacamp" in lower_label:
                        title = "DataCamp"
                        emoji = "📘"
                    else:
                        title = "Learning"
                else:
                    title = default_title

                adaptive_detail = (
                    tracks.task_detail(
                        self.conn,
                        item["task_id"],
                    )
                )
                if adaptive_detail:
                    detail = adaptive_detail
                else:
                    if item["carryover"]:
                        prefix = "Missed yesterday"
                    elif item["status"] == "In Progress":
                        prefix = "In progress"
                    else:
                        prefix = (
                            f"Priority "
                            f"{item['priority']}"
                        )

                    detail = (
                        f"{prefix} • "
                        f"{item['label']}"
                    )

            minutes = int(item["estimated_minutes"])
            estimated_minutes += minutes

            self.focus_layout.addWidget(
                FocusRow(
                    emoji,
                    title,
                    detail,
                    f"{minutes}m",
                    accent,
                )
            )

            if index < len(intelligent_focus) - 1:
                self.focus_layout.addWidget(Divider())

        self.focus_total_time.set_value(
            f"{estimated_minutes // 60}h "
            f"{estimated_minutes % 60:02d}m"
        )
        self.focus_task_count.set_value(
            str(len(intelligent_focus))
        )

        # Next task rows.
        self.clear_layout(self.dashboard_tasks_layout)
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

    def refresh_planner(self):
        self.build_plan()
        self.refresh_backlog()

    def refresh_backlog(self):
        self.backlog_list.clear()
        rows = self.conn.execute(
            """SELECT s.id,s.label,m.status,m.priority,m.estimated_minutes,
                      m.energy,m.deferred_until,m.category
               FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               WHERE s.week=? ORDER BY m.priority,s.sort_order""",
            (self.state["current_week"],),
        ).fetchall()
        for row in rows:
            deferred = f" → {row['deferred_until']}" if row["deferred_until"] else ""
            self.backlog_list.addItem(
                f"#{row['id']} • {row['status']} • P{row['priority']} • "
                f"{row['estimated_minutes']}m • {row['energy']} • "
                f"{row['category']} • {row['label']}{deferred}"
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

        google_meta = google["metadata"]
        google_detail = (
            f"Module {self.state['google_module']} • "
            f"Today "
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
            f"{datacamp['metadata'].get('role', 'Supplemental')} • "
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
            f"{sql['metadata'].get('role', 'Supplemental')} • "
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
                f"Week "
                f"{portfolio['weekly_completed']} / "
                f"{portfolio['weekly_target']}"
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
                "Planned",
                "Unlock through the DataCamp and portfolio tracks.",
            ),
            "Python": (
                "Planned",
                "Unlock through the DataCamp and portfolio tracks.",
            ),
            "Portfolio": (
                f"{project_done}/{len(project_rows)}",
                portfolio_detail,
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
        self.module_input.setValue(
            self.state["google_module"]
        )
        self.hours_input.setValue(
            int(self.state["weekly_target_hours"])
        )

    def refresh_project(self):
        self.project_combo.blockSignals(True)
        self.project_combo.setCurrentIndex(self.state["current_project"] - 1)
        self.project_combo.blockSignals(False)
        self.load_project()

    def refresh_sql(self):
        self.sql_problem_list.clear()
        completed = {
            row["title"]: row
            for row in self.conn.execute(
                "SELECT * FROM sql_practice"
            ).fetchall()
        }
        recommended = set(
            tracks.next_sql_titles(
                self.conn,
                self.state,
                limit=5,
            )
        )

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
                and title not in recommended
            ):
                continue

            status = (
                "✅"
                if title in completed
                else "⬜"
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

    def refresh_sessions(self):
        self.session_list.clear()
        rows = self.conn.execute(
            "SELECT * FROM study_sessions ORDER BY id DESC LIMIT 30"
        ).fetchall()
        for row in rows:
            self.session_list.addItem(
                f"{row['session_date']} • {row['hours']:g}h • "
                f"Productivity {row['productivity_score'] or '-'} • "
                f"Google: {row['google_progress'] or '-'} • "
                f"SQL: {row['sql_problems']}"
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
            self.readiness_coverage_layout.addWidget(
                StatRow(
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
            )

            if index < len(coverage_rows) - 1:
                self.readiness_coverage_layout.addWidget(
                    Divider()
                )

    def refresh_applications(self):
        self.clear_layout(self.kanban_layout)
        statuses = ["Wishlist", "Applying", "Applied", "Interview", "Final", "Offer"]
        for status in statuses:
            column = Card(status)
            column.setMinimumWidth(220)
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
        self.refresh_all()

        if result["handled"]:
            self.statusBar().showMessage(
                result["message"],
                4200,
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
        if not rows:
            self.plan_list.addItem("No eligible tasks for this time and energy level.")
        elif remaining:
            self.plan_list.addItem(f"Unused time: {remaining} minutes")

    def selected_task_id(self, widget):
        item = widget.currentItem()
        if not item:
            return None
        match = re.search(r"#(\d+)", item.text())
        return int(match.group(1)) if match else None

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

    def edit_task(self):
        task_id = self.selected_task_id(self.backlog_list)
        if not task_id:
            return
        row = self.conn.execute(
            """SELECT s.label,m.* FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id WHERE s.id=?""",
            (task_id,),
        ).fetchone()

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        dialog.setStyleSheet(stylesheet())
        form = QFormLayout(dialog)

        status = QComboBox()
        status.addItems(["Not Started", "In Progress", "Blocked", "Deferred", "Completed"])
        status.setCurrentText(row["status"])

        priority = QSpinBox()
        priority.setRange(1, 3)
        priority.setValue(row["priority"])

        minutes = QSpinBox()
        minutes.setRange(5, 480)
        minutes.setValue(row["estimated_minutes"])

        energy = QComboBox()
        energy.addItems(["Low", "Normal", "High"])
        energy.setCurrentText(row["energy"])

        deferred = QLineEdit(row["deferred_until"] or "")

        form.addRow("Task", QLabel(row["label"]))
        form.addRow("Status", status)
        form.addRow("Priority", priority)
        form.addRow("Estimated minutes", minutes)
        form.addRow("Energy", energy)
        form.addRow("Deferred until", deferred)

        save = QPushButton("Save")
        save.setObjectName("Primary")
        save.clicked.connect(dialog.accept)
        form.addRow(save)

        if dialog.exec() == QDialog.Accepted:
            self.conn.execute(
                """UPDATE task_metadata SET status=?,priority=?,estimated_minutes=?,
                   energy=?,deferred_until=? WHERE task_id=?""",
                (
                    status.currentText(),
                    priority.value(),
                    minutes.value(),
                    energy.currentText(),
                    deferred.text().strip() or None,
                    task_id,
                ),
            )
            self.conn.execute(
                "UPDATE sprint_tasks SET completed=? WHERE id=?",
                (1 if status.currentText() == "Completed" else 0, task_id),
            )
            self.conn.commit()
            self.refresh_all()

    def save_learning(self):
        previous_state = self.state
        tracks.record_google_manual_change(
            self.conn,
            previous_state,
            self.course_input.value(),
            self.module_input.value(),
        )

        update_state(
            self.conn,
            current_week=self.week_input.value(),
            google_course=self.course_input.value(),
            google_module=self.module_input.value(),
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

    def prefill_sql(self, item):
        text = item.text()
        title = text.split(" • ")[0].replace("✅ ", "").replace("⬜ ", "")
        match = next((row for row in SQL_COMPANION if row[0] == title), None)
        if not match:
            return
        self.sql_title.setText(match[0])
        self.sql_difficulty.setText(match[1])
        self.sql_topic.setText(match[2])
        self.sql_concepts.setText(match[3])
        self.sql_review.setText((date.today() + timedelta(days=7)).isoformat())

    def save_sql(self):
        title = self.sql_title.text().strip()
        if not title:
            return
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        path = ROOT / "resources" / "sql" / "datalemur" / f"{slug}.sql"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                f"-- Problem: {title}\n"
                f"-- Difficulty: {self.sql_difficulty.text()}\n"
                f"-- Topic: {self.sql_topic.text()}\n"
                f"-- Concepts: {self.sql_concepts.text()}\n\n"
                "-- My solution:\n",
                encoding="utf-8",
            )
        self.conn.execute(
            """INSERT INTO sql_practice
               (platform,title,difficulty,topic,concepts,status,mastery,
                review_date,completed_date,solution_path,notes)
               VALUES('DataLemur',?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(platform,title) DO UPDATE SET
               difficulty=excluded.difficulty,topic=excluded.topic,
               concepts=excluded.concepts,status=excluded.status,
               mastery=excluded.mastery,review_date=excluded.review_date,
               notes=excluded.notes""",
            (
                title,
                self.sql_difficulty.text(),
                self.sql_topic.text(),
                self.sql_concepts.text(),
                "Completed",
                self.sql_mastery.value(),
                self.sql_review.text().strip() or None,
                date.today().isoformat(),
                str(path.relative_to(ROOT)).replace("\\", "/"),
                self.sql_notes.toPlainText(),
            ),
        )
        self.conn.commit()
        tracks.record_sql_completion(
            self.conn,
            title,
        )
        self.state = state(self.conn)
        tracks.sync_all(
            self.conn,
            self.state,
        )
        self.refresh_all()

    def sql_hint(self):
        topic = self.sql_topic.text() or "the main SQL concept"
        QMessageBox.information(
            self,
            "Hint",
            f"Break the problem into steps. First identify the required grain, "
            f"then build the {topic} logic, and finally validate edge cases.",
        )

    def open_sql_solution(self):
        title = self.sql_title.text().strip()
        if not title:
            return
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        path = ROOT / "resources" / "sql" / "datalemur" / f"{slug}.sql"
        if path.exists():
            os.startfile(path)

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
        self.conn.execute(
            """INSERT INTO study_sessions
               (session_date,hours,google_progress,datacamp_progress,
                sql_problems,portfolio_progress,notes,productivity_score)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                self.session_date.text(),
                hours,
                self.session_google.text(),
                self.session_datacamp.text(),
                self.session_sql.value(),
                self.session_portfolio.text(),
                self.session_notes.toPlainText(),
                self.session_productivity.value(),
            ),
        )
        self.conn.commit()
        self.reset_timer()
        self.refresh_all()

    def add_evidence(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Evidence")
        dialog.setStyleSheet(stylesheet())
        form = QFormLayout(dialog)
        skill = QLineEdit()
        source_type = QComboBox()
        source_type.addItems(["Portfolio", "Coursework", "Work Experience", "SQL Practice", "Certification"])
        source_name = QLineEdit()
        description = QTextEdit()
        form.addRow("Skill", skill)
        form.addRow("Source type", source_type)
        form.addRow("Source name", source_name)
        form.addRow("Description", description)
        save = QPushButton("Save")
        save.setObjectName("Primary")
        save.clicked.connect(dialog.accept)
        form.addRow(save)
        if dialog.exec() == QDialog.Accepted:
            self.conn.execute(
                """INSERT OR IGNORE INTO evidence
                   (skill,source_type,source_name,description)
                   VALUES(?,?,?,?)""",
                (
                    skill.text(),
                    source_type.currentText(),
                    source_name.text(),
                    description.toPlainText(),
                ),
            )
            self.conn.commit()
            self.refresh_readiness()

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
        sql_count = self.conn.execute(
            "SELECT COUNT(*) FROM sql_practice"
        ).fetchone()[0]

        summary = (
            f"Week {week}: {done}/{total} sprint tasks completed, "
            f"{hours:g} study hours, and {sql_count} SQL problems logged. "
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
        interval = self.autosave_minutes.value() * 60 * 1000
        self.autosave_timer.start(max(60000, interval))
        self.settings_status.setText("Settings saved.")


    def reset_progress_details(self):
        return (
            "This will permanently reset the active Career Accelerator profile.\\n\\n"
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
                "Career Accelerator will create a safety backup and then erase "
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
                    "Career Accelerator has been reset to a clean starter profile.\\n\\n"
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

    def backup_database(self):
        path = create_backup(ROOT)
        self.settings_status.setText(f"Backup created: {path}")

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
        dialog.setStyleSheet(stylesheet())
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
