from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMessageBox, QPushButton, QProgressBar, QScrollArea, QSpinBox,
    QStackedWidget, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget
)

from career_app import __version__
from career_app.database import (
    connect, ensure_default_state, save_setting, setting, state, update_state
)
from career_app.data.roadmap import (
    PROJECT_DIRS, PROJECT_NAMES, PROJECT_STAGES, SQL_COMPANION, WEEKLY_GUIDANCE
)
from career_app.services import analytics, coach, planner
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

class CareerAccelerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conn = connect()
        ensure_default_state(self.conn, "2026-07-13")
        self.migration_result = migrate(self.conn, ROOT)
        planner.seed(self.conn)
        self.state = state(self.conn)

        self.elapsed_seconds = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_timer)

        self.setWindowTitle(f"Career Accelerator v{__version__}")
        self.resize(1536, 960)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(stylesheet())

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
        self.refresh_all()
        self.update_time_based_header()

        self.greeting_timer = QTimer(self)
        self.greeting_timer.timeout.connect(self.update_time_based_header)
        self.greeting_timer.start(60_000)

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
            ("📚 Learning", 2),
            ("📁 Portfolio Workspace", 3),
            ("💻 SQL Companion", 4),
            ("⏱️ Study Session", 5),
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
            2: "Learning",
            3: "Portfolio Workspace",
            4: "SQL Companion",
            5: "Study Session",
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
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    # ---------- Dashboard ----------
    def dashboard_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(28, 20, 28, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)

        left_header = QVBoxLayout()
        left_header.setSpacing(3)

        self.dashboard_hero = QLabel("")
        self.dashboard_hero.setObjectName("Hero")
        left_header.addWidget(self.dashboard_hero)

        quote = QLabel("“Discipline today, opportunity tomorrow.”")
        quote.setObjectName("Muted")
        quote.setStyleSheet("font-style:italic;color:#b6bfd0;")
        left_header.addWidget(quote)

        header.addLayout(left_header)
        header.addStretch()

        right_header = QVBoxLayout()
        right_header.setSpacing(5)

        self.dashboard_program_meta = QLabel("")
        self.dashboard_program_meta.setAlignment(Qt.AlignRight)
        self.dashboard_program_meta.setStyleSheet("font-weight:600;")
        right_header.addWidget(self.dashboard_program_meta)

        self.dashboard_date = QLabel("")
        self.dashboard_date.setObjectName("Muted")
        self.dashboard_date.setAlignment(Qt.AlignRight)
        right_header.addWidget(self.dashboard_date)

        header.addLayout(right_header)
        root.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)

        self.rings = [
            Ring("Sprint Progress", COLORS["purple"]),
            Ring("Google Certificate", COLORS["blue"]),
            Ring("SQL Progress", COLORS["green"]),
            Ring("Portfolio Progress", COLORS["orange"]),
            Ring("Weekly Goal", COLORS["gold"]),
        ]

        for ring in self.rings:
            card = Card()
            card.setMinimumHeight(138)
            card.setMaximumHeight(148)
            card.layout.setContentsMargins(10, 8, 10, 8)
            card.layout.addWidget(ring)
            metrics.addWidget(card)

        root.addLayout(metrics)

        # Reference uses a 3-column grid:
        # Focus 32%, Tasks 32%, Study Session 36%.
        middle = QGridLayout()
        middle.setHorizontalSpacing(10)
        middle.setVerticalSpacing(10)

        focus_card = Card()
        focus_card.layout.setContentsMargins(14, 13, 14, 12)
        focus_card.layout.addWidget(
            SectionHeader(
                "🎯",
                "Today's Focus",
                "Recommended plan for today",
            )
        )

        self.focus_layout = QVBoxLayout()
        self.focus_layout.setSpacing(0)
        focus_card.layout.addLayout(self.focus_layout)

        focus_card.layout.addWidget(Divider())

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
        focus_card.layout.addLayout(focus_footer)

        tasks_card = Card()
        tasks_card.layout.setContentsMargins(14, 13, 14, 12)

        task_header = SectionHeader(
            "📋",
            "Next Tasks",
            "Up next from your sprint",
            "View All",
        )
        tasks_card.layout.addWidget(task_header)

        self.dashboard_tasks_layout = QVBoxLayout()
        self.dashboard_tasks_layout.setSpacing(0)
        tasks_card.layout.addLayout(self.dashboard_tasks_layout)
        tasks_card.layout.addStretch()

        timer_card = Card()
        timer_card.layout.setContentsMargins(14, 13, 14, 12)
        timer_card.layout.setSpacing(7)
        timer_card.layout.addWidget(
            SectionHeader("⏱️", "Study Session")
        )

        self.circular_timer = CircularTimer()
        timer_card.layout.addWidget(
            self.circular_timer,
            0,
            Qt.AlignTop | Qt.AlignHCenter,
        )

        start = QPushButton("▶  Start Study Session")
        start.setObjectName("Primary")
        start.clicked.connect(lambda: self.timer.start(1000))
        timer_card.layout.addWidget(start)

        timer_controls = QHBoxLayout()
        timer_controls.setSpacing(8)

        pause = QPushButton("⏸️  Pause")
        pause.setObjectName("Secondary")
        pause.clicked.connect(self.timer.stop)

        log = QPushButton("📝  Log Session")
        log.setObjectName("Secondary")
        log.clicked.connect(self.transfer_timer)

        timer_controls.addWidget(pause, 1)
        timer_controls.addWidget(log, 1)
        timer_card.layout.addLayout(timer_controls)

        middle.addWidget(focus_card, 0, 0)
        middle.addWidget(tasks_card, 0, 1)
        middle.addWidget(timer_card, 0, 2)

        middle.setColumnStretch(0, 34)
        middle.setColumnStretch(1, 33)
        middle.setColumnStretch(2, 33)
        root.addLayout(middle, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        growth_card = Card()
        growth_card.layout.setContentsMargins(14, 13, 14, 12)
        growth_card.layout.addWidget(
            SectionHeader(
                "📈",
                "Growth Over Time",
                "Hours studied per day (last 14 days)",
                "14 Days ▾",
            )
        )
        self.growth_chart = AreaChart()
        growth_card.layout.addWidget(self.growth_chart)

        achievement_card = Card()
        achievement_card.layout.setContentsMargins(14, 13, 14, 12)
        achievement_card.layout.setSpacing(10)
        achievement_card.layout.addWidget(
            SectionHeader("🏅", "Achievements", "", "View All")
        )

        self.badge_layout = QHBoxLayout()
        self.badge_layout.setSpacing(8)
        self.badge_layout.setAlignment(Qt.AlignTop)
        achievement_card.layout.addLayout(self.badge_layout, 1)

        summary_card = Card()
        summary_card.layout.setContentsMargins(14, 13, 14, 12)

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
        summary_card.layout.addLayout(summary_header)

        self.summary_period = QLabel("")
        self.summary_period.setObjectName("Muted")
        summary_card.layout.addWidget(self.summary_period)

        self.summary_rows = QVBoxLayout()
        self.summary_rows.setSpacing(0)
        summary_card.layout.addLayout(self.summary_rows)

        summary_button = QPushButton("View Full Summary")
        summary_button.setObjectName("Secondary")
        summary_button.clicked.connect(lambda: self.navigate(8))
        summary_card.layout.addWidget(summary_button)

        bottom.addWidget(growth_card, 38)
        bottom.addWidget(achievement_card, 29)
        bottom.addWidget(summary_card, 33)
        root.addLayout(bottom, 1)

        footer_card = Card()
        footer_card.layout.setContentsMargins(16, 10, 16, 10)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(12)

        star = QLabel("⭐")
        star.setStyleSheet("font-size:22pt;")
        footer_row.addWidget(star)

        footer_text = QVBoxLayout()
        footer_text.setSpacing(1)

        message = QLabel("Small daily improvements lead to big results.")
        message.setStyleSheet("font-weight:700;")
        footer_text.addWidget(message)

        subtitle = QLabel("You've got this, Dan!")
        subtitle.setObjectName("Muted")
        footer_text.addWidget(subtitle)

        footer_row.addLayout(footer_text)
        footer_row.addStretch()
        footer_card.layout.addLayout(footer_row)
        root.addWidget(footer_card)

        return page

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
            "Track focus time, notes, productivity, and the work completed.",
        )
        body = QHBoxLayout()
        timer_card = Card("Live Timer")
        self.study_timer = QLabel("00:00:00")
        self.study_timer.setAlignment(Qt.AlignCenter)
        self.study_timer.setStyleSheet(
            f"font-size:36pt;font-weight:700;color:{COLORS['blue']};"
        )
        timer_card.layout.addWidget(self.study_timer)
        timer_buttons = QHBoxLayout()
        start = QPushButton("Start")
        start.setObjectName("Primary")
        start.clicked.connect(lambda: self.timer.start(1000))
        pause = QPushButton("Pause")
        pause.clicked.connect(self.timer.stop)
        reset = QPushButton("Reset")
        reset.clicked.connect(self.reset_timer)
        timer_buttons.addWidget(start)
        timer_buttons.addWidget(pause)
        timer_buttons.addWidget(reset)
        timer_card.layout.addLayout(timer_buttons)
        body.addWidget(timer_card, 1)

        log_card = Card("Log Session")
        form = QFormLayout()
        self.session_date = QLineEdit(date.today().isoformat())
        self.session_hours = QLineEdit("1")
        self.session_google = QLineEdit()
        self.session_datacamp = QLineEdit()
        self.session_sql = QSpinBox()
        self.session_sql.setRange(0, 20)
        self.session_portfolio = QLineEdit()
        self.session_productivity = QSpinBox()
        self.session_productivity.setRange(1, 10)
        self.session_productivity.setValue(7)
        self.session_notes = QTextEdit()
        form.addRow("Date", self.session_date)
        form.addRow("Hours", self.session_hours)
        form.addRow("Google progress", self.session_google)
        form.addRow("DataCamp progress", self.session_datacamp)
        form.addRow("SQL problems", self.session_sql)
        form.addRow("Portfolio progress", self.session_portfolio)
        form.addRow("Productivity (1–10)", self.session_productivity)
        form.addRow("Notes", self.session_notes)
        log_card.layout.addLayout(form)
        save = QPushButton("Finish Session")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_session)
        log_card.layout.addWidget(save)
        body.addWidget(log_card, 2)
        root.addLayout(body)

        recent = Card("Recent Sessions")
        self.session_list = QListWidget()
        recent.layout.addWidget(self.session_list)
        root.addWidget(recent, 1)
        return page

    # ---------- Readiness ----------
    def readiness_page(self):
        page, root = self.page(
            "🎯 Job Readiness",
            "Connect learning and portfolio evidence directly to employability.",
        )

        self.readiness_rings = {}
        rings = QHBoxLayout()
        for title, color in [
            ("Technical Skills", COLORS["blue"]),
            ("Portfolio", COLORS["purple"]),
            ("Interview Practice", COLORS["green"]),
            ("Networking", COLORS["orange"]),
            ("Applications", COLORS["gold"]),
            ("Overall", COLORS["cyan"]),
        ]:
            card = Card()
            ring = Ring(title, color)
            card.layout.addWidget(ring)
            rings.addWidget(card)
            self.readiness_rings[title] = ring
        root.addLayout(rings)

        body = QHBoxLayout()
        evidence = Card("Demonstrated Evidence")
        self.evidence_list = QListWidget()
        evidence.layout.addWidget(self.evidence_list)
        add_evidence = QPushButton("Add Evidence")
        add_evidence.clicked.connect(self.add_evidence)
        evidence.layout.addWidget(add_evidence)
        body.addWidget(evidence, 1)

        gaps = Card("Readiness Coach")
        self.readiness_coach = QLabel("")
        self.readiness_coach.setWordWrap(True)
        self.readiness_coach.setObjectName("Muted")
        gaps.layout.addWidget(self.readiness_coach)
        body.addWidget(gaps, 1)
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
            "Control autosave, backups, migration, and local application behavior.",
        )
        card = Card("Application Settings")
        form = QFormLayout()
        self.autosave_minutes = QSpinBox()
        self.autosave_minutes.setRange(1, 60)
        self.autosave_minutes.setValue(int(setting(self.conn, "autosave_minutes", "5")))
        form.addRow("Autosave interval (minutes)", self.autosave_minutes)
        card.layout.addLayout(form)

        save_settings = QPushButton("Save Settings")
        save_settings.setObjectName("Primary")
        save_settings.clicked.connect(self.save_settings)
        card.layout.addWidget(save_settings)

        backup = QPushButton("Create Database Backup")
        backup.clicked.connect(self.backup_database)
        card.layout.addWidget(backup)

        restore = QPushButton("Restore Tasks From Repository Files")
        restore.clicked.connect(self.restore_tasks)
        card.layout.addWidget(restore)

        open_repo = QPushButton("Open Repository Folder")
        open_repo.clicked.connect(lambda: os.startfile(ROOT))
        card.layout.addWidget(open_repo)

        self.settings_status = QLabel("")
        self.settings_status.setObjectName("Muted")
        self.settings_status.setWordWrap(True)
        card.layout.addWidget(self.settings_status)
        root.addWidget(card)
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

    # ---------- Refresh ----------
    def refresh_all(self):
        self.state = state(self.conn)
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

    def refresh_dashboard(self):
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

        total_hours = self.conn.execute(
            "SELECT COALESCE(SUM(hours),0) FROM study_sessions"
        ).fetchone()[0]
        target_hours = float(self.state["weekly_target_hours"])
        weekly_goal = (
            min(100, total_hours / target_hours * 100)
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
                f"{total_hours:g}h / {target_hours:g}h",
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

        # Focus rows.
        self.clear_layout(self.focus_layout)
        focus_items = [
            (
                "🎓",
                "Google Certificate",
                f"Continue Course {self.state['google_course']} • "
                f"Complete Module {self.state['google_module']}",
                "60m",
                COLORS["blue"],
            ),
            (
                "📘",
                "DataCamp",
                guide[2],
                "45m",
                COLORS["green"],
            ),
            (
                "💻",
                "SQL Practice",
                "Solve 2 problems on DataLemur",
                "60m",
                COLORS["purple"],
            ),
            (
                "📁",
                "Portfolio Project",
                "Define KPIs for the VFX Dashboard",
                "45m",
                COLORS["orange"],
            ),
        ]
        for index, item in enumerate(focus_items):
            self.focus_layout.addWidget(FocusRow(*item))
            if index < len(focus_items) - 1:
                self.focus_layout.addWidget(Divider())

        estimated_minutes = sum((60, 45, 60, 45))
        self.focus_total_time.set_value(
            f"{estimated_minutes // 60}h "
            f"{estimated_minutes % 60:02d}m"
        )
        self.focus_task_count.set_value("4")

        # Next task rows.
        self.clear_layout(self.dashboard_tasks_layout)
        available = planner.available(self.conn, week)

        task_sources = {
            "Learning": "Google • Module 3",
            "SQL": "SQL Practice",
            "Portfolio": "Portfolio Project 1",
            "Review": "Weekly Review",
            "General": "Roadmap",
        }

        if available:
            for index, row in enumerate(available[:5]):
                task_row = TaskRow(
                    title=row["label"],
                    source=task_sources.get(row["category"], "Roadmap"),
                    checked=bool(row["completed"]),
                    status_text=(
                        "Completed"
                        if row["completed"] else ""
                    ),
                    on_toggle=(
                        lambda _, task_id=row["id"]:
                        self.complete_task(task_id)
                    ),
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
        text = self.study_timer.text() if hasattr(self, "study_timer") else "00:00:00"
        self.circular_timer.set_text(text)

        # Growth.
        recent_hours = analytics.daily_hours(self.conn, 14)
        self.growth_chart.set_values(recent_hours)
        self.summary_sparkline.set_values(recent_hours)

        # Achievements.
        self.clear_layout(self.badge_layout)
        badge_data = [
            ("🚀", "Getting Started", "Log your first study session", COLORS["purple"]),
            ("📅", "Week Warrior", "Study 7 days in a week", COLORS["blue"]),
            ("🎯", "On Track", "Complete 10 tasks", COLORS["green"]),
        ]
        for icon, title, description, accent in badge_data:
            self.badge_layout.addWidget(
                BadgeCard(icon, title, description, accent)
            )

        # Weekly summary.
        self.summary_period.setText(
            f"Week of {datetime.now():%b %d} – "
            f"{(datetime.now() + timedelta(days=6)):%b %d}"
        )
        self.clear_layout(self.summary_rows)

        session_count = self.conn.execute(
            "SELECT COUNT(*) FROM study_sessions"
        ).fetchone()[0]

        summary_items = [
            ("⏱️", "Study Time", f"{total_hours:g}h"),
            ("📅", "Sessions", str(session_count)),
            ("✅", "Tasks Completed", f"{done} / {total}"),
            ("💾", "SQL Problems", str(sql_count)),
            ("⭐", "Focus Score", "—"),
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
        streak = analytics.streak(self.conn)
        self.side_streak_value.setText(str(streak))
        self.best_streak_label.setText(f"Best Streak: {streak} days")
        self.streak_week.setText(
            "●  ●  ●  ●  ●  ●  ●" if streak >= 7
            else "○  ●  ●  ●  ●  ●  ○" if streak
            else "○  ○  ○  ○  ○  ○  ○"
        )

        self.side_hours_value.setText(f"{total_hours:g}h")
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
        week = self.state["current_week"]
        guide = WEEKLY_GUIDANCE.get(
            week, ("Keep Moving", "", "", [], "")
        )
        sql_count = self.conn.execute("SELECT COUNT(*) FROM sql_practice").fetchone()[0]
        project_rows = self.conn.execute(
            "SELECT completed FROM project_tasks WHERE project_id=?",
            (self.state["current_project"],),
        ).fetchall()
        project_done = sum(int(row["completed"]) for row in project_rows)

        data = {
            "Google": (f"Course {self.state['google_course']}", guide[1]),
            "DataCamp": ("Active", guide[2]),
            "SQL": (f"{sql_count}/{self.state['sql_target']}", ", ".join(guide[3][:2])),
            "Power BI": ("Planned", "Recommended Week 4"),
            "Python": ("Planned", "Recommended Week 7"),
            "Portfolio": (f"{project_done}/{len(project_rows)}", guide[4]),
        }
        for key, (value, detail) in data.items():
            self.learning_cards[key][0].setText(value)
            self.learning_cards[key][1].setText(detail)

        self.week_input.setValue(self.state["current_week"])
        self.course_input.setValue(self.state["google_course"])
        self.module_input.setValue(self.state["google_module"])
        self.hours_input.setValue(int(self.state["weekly_target_hours"]))

    def refresh_project(self):
        self.project_combo.blockSignals(True)
        self.project_combo.setCurrentIndex(self.state["current_project"] - 1)
        self.project_combo.blockSignals(False)
        self.load_project()

    def refresh_sql(self):
        self.sql_problem_list.clear()
        completed = {
            row["title"]: row
            for row in self.conn.execute("SELECT * FROM sql_practice").fetchall()
        }
        for title, difficulty, topic, concepts, assigned_week, estimate in SQL_COMPANION:
            if assigned_week == self.state["current_week"] or title in completed:
                status = "✅" if title in completed else "⬜"
                mastery = (
                    f" • Mastery {completed[title]['mastery']}/5"
                    if title in completed else ""
                )
                self.sql_problem_list.addItem(
                    f"{status} {title} • {difficulty} • {topic} • "
                    f"{concepts} • {estimate} min{mastery}"
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
        data = analytics.readiness(self.conn, self.state)
        for key, value in data.items():
            self.readiness_rings[key].set_value(value, f"{value}%", "")

        self.evidence_list.clear()
        evidence = self.conn.execute(
            "SELECT * FROM evidence ORDER BY skill,source_type"
        ).fetchall()
        if evidence:
            for row in evidence:
                self.evidence_list.addItem(
                    f"✅ {row['skill']} • {row['source_type']} • {row['source_name']}"
                )
        else:
            self.evidence_list.addItem(
                "No evidence logged yet. Add portfolio, coursework, or work examples."
            )

        self.readiness_coach.setText(
            "\n\n".join(coach.recommendations(self.conn, self.state))
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
    def complete_task(self, task_id):
        self.conn.execute(
            "UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,)
        )
        self.conn.execute(
            "UPDATE task_metadata SET status='Completed',deferred_until=NULL WHERE task_id=?",
            (task_id,),
        )
        self.conn.commit()
        self.refresh_all()

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
        update_state(
            self.conn,
            current_week=self.week_input.value(),
            google_course=self.course_input.value(),
            google_module=self.module_input.value(),
            weekly_target_hours=self.hours_input.value(),
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

        for row in rows:
            target_stage = row["stage"] if row["stage"] in self.project_stage_widgets else "Tasks"
            if target_stage not in ("Overview", "Tasks"):
                target_stage = "Tasks"
            checkbox = QCheckBox(row["label"])
            checkbox.setChecked(bool(row["completed"]))
            self.project_stage_widgets[target_stage].addWidget(checkbox)
            self.project_task_checks.append((row["id"], checkbox))

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

    def save_project_tasks(self):
        for task_id, checkbox in self.project_task_checks:
            self.conn.execute(
                "UPDATE project_tasks SET completed=? WHERE id=?",
                (1 if checkbox.isChecked() else 0, task_id),
            )
        self.conn.commit()
        self.refresh_all()

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

    def tick_timer(self):
        self.elapsed_seconds += 1
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if hasattr(self, "circular_timer"):
            self.circular_timer.set_text(text)
        self.study_timer.setText(text)

    def reset_timer(self):
        self.timer.stop()
        self.elapsed_seconds = 0
        if hasattr(self, "circular_timer"):
            self.circular_timer.set_text("00:00:00")
        self.study_timer.setText("00:00:00")

    def transfer_timer(self):
        self.timer.stop()
        self.session_hours.setText(f"{self.elapsed_seconds / 3600:.2f}")
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
            ("⏱️ Start Study Timer", lambda: self.timer.start(1000)),
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
