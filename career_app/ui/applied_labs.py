"""Polished in-app Applied Labs learning and practice workspace."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.data.applied_exercises import APPLIED_EXERCISES, CATEGORY_ORDER
from career_app.database import save_setting, state
from career_app.services import applied_lab_runner, applied_workspace, tracks
from career_app.theme import COLORS
from career_app.ui.course_ui import CoursePageWidget, SqlCodeEditor
from career_app.ui.exercise_packs import FeedbackLabel, RotatedLabel
from career_app.ui.widgets import Card


class AppliedLabsWidget(QWidget):
    """Course-style Applied Labs browser with an embedded SQL sandbox."""

    changed = Signal()

    def __init__(self, conn, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self.conn = conn
        self.root = Path(root)
        self.current_number: int | None = None
        self.current_item: dict[str, Any] | None = None
        self.current_sql_check_passed = False
        self._building = False
        self._settings = QSettings("DanjPastor", "Career Accelerator")
        self._library_collapsed = self._settings.value(
            "applied_labs/library_collapsed", False, type=bool
        )
        self._preferred_library_collapsed = self._library_collapsed
        self._responsive_mode: str | None = None
        saved_width = self._settings.value("applied_labs/library_width_v2", None)
        self._library_expanded_width = int(saved_width) if saved_width else None
        self._build_ui()
        self.refresh()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 8, 0, 0)
        outer.setSpacing(10)

        self.course_toolbar = Card()
        self.course_toolbar.layout.setContentsMargins(10, 7, 10, 7)
        toolbar_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.toolbar_row = toolbar_row
        toolbar_row.setSpacing(8)
        self.breadcrumb_root = QLabel("Applied Labs")
        self.breadcrumb_root.setStyleSheet("color:#B8C4D8;font-size:9.5pt;")
        toolbar_row.addWidget(self.breadcrumb_root)
        self.breadcrumb_category = QLabel("›  Select a lab")
        self.breadcrumb_category.setStyleSheet("color:#B8C4D8;font-size:9.5pt;")
        toolbar_row.addWidget(self.breadcrumb_category)
        self.breadcrumb_page = QLabel("")
        self.breadcrumb_page.setStyleSheet("color:#dce4f3;font-size:9.5pt;")
        toolbar_row.addWidget(self.breadcrumb_page)
        toolbar_row.addStretch()
        self.open_submissions_button = QPushButton("Open Submissions Folder")
        self.open_submissions_button.setObjectName("Secondary")
        self.open_submissions_button.clicked.connect(self.open_submissions_folder)
        toolbar_row.addWidget(self.open_submissions_button)
        self.course_toolbar.layout.addLayout(toolbar_row)
        outer.addWidget(self.course_toolbar)

        self.lab_splitter = QSplitter(Qt.Horizontal)
        self.lab_splitter.setMinimumWidth(0)
        self.lab_splitter.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self.lab_splitter.setChildrenCollapsible(False)
        self.lab_splitter.setHandleWidth(5)

        self.library_card = Card()
        self.library_card.setMinimumWidth(270)
        self.library_card.setMaximumWidth(16777215)
        library_margins = self.library_card.layout.contentsMargins()
        self._library_expanded_margins = (
            library_margins.left(),
            library_margins.top(),
            library_margins.right(),
            library_margins.bottom(),
        )
        self.library_header_widget = QWidget()
        self.library_header = QHBoxLayout(self.library_header_widget)
        self.library_header.setContentsMargins(0, 0, 0, 0)
        self.library_header.setSpacing(8)
        self.library_title = QLabel("Applied Labs")
        self.library_title.setObjectName("SectionTitle")
        self.library_header.addWidget(self.library_title, 1)
        self.library_progress_text = QLabel("")
        self.library_progress_text.setObjectName("Muted")
        self.library_header.addWidget(self.library_progress_text)
        self.library_toggle = QPushButton("◀")
        self.library_toggle.setObjectName("Secondary")
        self.library_toggle.setFixedSize(28, 28)
        self.library_toggle.setToolTip("Collapse Applied Labs")
        self.library_toggle.clicked.connect(self.toggle_library)
        self.library_header.addWidget(self.library_toggle)
        self.library_card.layout.addWidget(self.library_header_widget)

        self.library_collapsed_control = QWidget()
        collapsed_control_layout = QVBoxLayout(self.library_collapsed_control)
        collapsed_control_layout.setContentsMargins(0, 0, 0, 0)
        collapsed_control_layout.setSpacing(0)
        collapsed_control_layout.addStretch(1)
        self.library_collapsed_cluster = QWidget()
        self.library_collapsed_cluster_layout = QVBoxLayout(
            self.library_collapsed_cluster
        )
        self.library_collapsed_cluster_layout.setContentsMargins(0, 0, 0, 0)
        self.library_collapsed_cluster_layout.setSpacing(5)
        self.library_vertical_title = RotatedLabel("Applied Labs")
        self.library_vertical_title.setObjectName("SectionTitle")
        self.library_collapsed_cluster_layout.addWidget(
            self.library_vertical_title, 0, Qt.AlignHCenter
        )
        collapsed_control_layout.addWidget(
            self.library_collapsed_cluster, 0, Qt.AlignHCenter
        )
        collapsed_control_layout.addStretch(1)
        self.library_collapsed_control.hide()
        self.library_card.layout.addWidget(self.library_collapsed_control, 1)

        self.library_body = QWidget()
        library_body_layout = QVBoxLayout(self.library_body)
        library_body_layout.setContentsMargins(0, 4, 0, 0)
        library_body_layout.setSpacing(8)

        self.library_progress = QProgressBar()
        self.library_progress.setRange(0, 100)
        self.library_progress.setTextVisible(False)
        library_body_layout.addWidget(self.library_progress)

        branch_row = QHBoxLayout()
        branch_row.addWidget(QLabel("Adaptive branch"))
        self.branch_filter = QComboBox()
        self.branch_filter.addItems(["Auto", *tracks.APPLIED_BRANCH_ORDER])
        self.branch_filter.currentTextChanged.connect(self._branch_changed)
        branch_row.addWidget(self.branch_filter, 1)
        library_body_layout.addLayout(branch_row)

        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Category"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", *CATEGORY_ORDER])
        self.category_filter.currentTextChanged.connect(self.refresh)
        category_row.addWidget(self.category_filter, 1)
        library_body_layout.addLayout(category_row)

        self.track_summary = QLabel("")
        self.track_summary.setObjectName("Muted")
        self.track_summary.setWordWrap(True)
        self.track_summary.setStyleSheet("padding:4px 1px 6px 1px;")
        library_body_layout.addWidget(self.track_summary)

        self.lab_list = QListWidget()
        self.lab_list.setWordWrap(True)
        self.lab_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.lab_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lab_list.setSpacing(4)
        self.lab_list.currentItemChanged.connect(self._lab_selected)
        library_body_layout.addWidget(self.lab_list, 1)
        self.library_card.layout.addWidget(self.library_body, 1)
        self.lab_splitter.addWidget(self.library_card)

        self.workspace_card = Card()
        self.workspace_card.layout.setContentsMargins(8, 8, 8, 8)
        self.workspace_status = QLabel("")
        self.workspace_status.hide()

        self.learn_page = QWidget()
        learn_layout = QVBoxLayout(self.learn_page)
        learn_layout.setContentsMargins(0, 0, 0, 0)
        self.learn_view = CoursePageWidget()
        self.learn_view.continueRequested.connect(self._continue_to_next_lab)
        self.learn_view.bookmarkToggled.connect(self._bookmark_current_lab)
        self.learn_view.overflowRequested.connect(self._show_lab_page_menu)
        learn_layout.addWidget(self.learn_view)

        # The lab workspace is embedded directly in the Learn page so the
        # course material, SQL runner, evidence notes, and completion workflow
        # remain visible in one continuous course-style experience.
        self.practice_panel = QWidget()
        practice_layout = QVBoxLayout(self.practice_panel)
        practice_layout.setContentsMargins(0, 4, 0, 4)
        practice_layout.setSpacing(12)

        self.sql_section = QFrame()
        self.sql_section.setObjectName("AppliedLabSqlCard")
        self.sql_section.setStyleSheet(
            "QFrame#AppliedLabSqlCard {background:#121a2a;border:1px solid #263754;"
            "border-radius:10px;}"
        )
        sql_layout = QVBoxLayout(self.sql_section)
        sql_layout.setContentsMargins(12, 12, 12, 12)
        sql_layout.setSpacing(8)
        sql_heading = QHBoxLayout()
        sql_title = QLabel("SQL Workspace")
        sql_title.setObjectName("SectionTitle")
        sql_heading.addWidget(sql_title)
        sql_heading.addStretch()
        self.dataset_label = QLabel("")
        self.dataset_label.setObjectName("Muted")
        sql_heading.addWidget(self.dataset_label)
        sql_layout.addLayout(sql_heading)

        self.sql_editor = SqlCodeEditor()
        self.sql_editor.setPlaceholderText(
            "Write SQL here. Dataset files are loaded automatically as tables named after each file."
        )
        self.sql_editor.textChanged.connect(self._sql_edited)
        self.sql_editor.setMinimumHeight(180)
        sql_layout.addWidget(self.sql_editor)

        sql_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.sql_actions = sql_actions
        self.run_button = QPushButton("▶ Run SQL")
        self.run_button.setObjectName("Secondary")
        self.run_button.clicked.connect(self.run_sql)
        self.check_button = QPushButton("✓ Check Lab")
        self.check_button.setObjectName("Primary")
        self.check_button.clicked.connect(self.check_sql)
        sql_actions.addWidget(self.run_button)
        sql_actions.addWidget(self.check_button)
        sql_actions.addStretch()
        sql_layout.addLayout(sql_actions)

        self.sql_feedback = FeedbackLabel()
        sql_layout.addWidget(self.sql_feedback)
        self.result_table = QTableWidget()
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setShowGrid(False)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setMinimumHeight(140)
        self.result_table.setStyleSheet(
            f"QTableWidget {{background:{COLORS.get('surface_alt', '#111A2C')};"
            "alternate-background-color:#121F34;color:#FFFFFF;"
            f"border:1px solid {COLORS.get('border', '#2B3656')};border-radius:8px;}}"
            "QHeaderView::section {background:#1B2540;color:#FFFFFF;padding:7px;"
            "border:none;border-right:1px solid #3a3d5e;font-weight:600;}"
        )
        sql_layout.addWidget(self.result_table)
        practice_layout.addWidget(self.sql_section)

        progress_card = QFrame()
        progress_card.setObjectName("AppliedLabProgressCard")
        progress_card.setStyleSheet(
            "QFrame#AppliedLabProgressCard {background:#111D31;border:1px solid #263754;"
            "border-radius:9px;}"
        )
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(12, 10, 12, 10)
        progress_layout.setSpacing(8)
        progress_title = QLabel("Progress & Evidence")
        progress_title.setObjectName("SectionTitle")
        progress_layout.addWidget(progress_title)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Record assumptions, validation findings, decisions, artifact paths, and interview-ready takeaways."
        )
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(145)
        self.notes.setStyleSheet(
            f"QTextEdit {{background:{COLORS.get('surface_alt', '#111A2C')};"
            f"border:1px solid {COLORS.get('border', '#2B3656')};"
            "border-radius:8px;padding:7px;}"
            f"QTextEdit:focus {{border:1px solid {COLORS.get('purple', '#8A5CFF')};}}"
        )
        progress_layout.addWidget(self.notes)

        file_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.file_actions = file_actions
        self.instructions_button = QPushButton("Open Instructions")
        self.instructions_button.clicked.connect(lambda: self.open_reference("instructions"))
        self.starter_button = QPushButton("Open Starter")
        self.starter_button.clicked.connect(lambda: self.open_reference("starter"))
        self.validation_button = QPushButton("Open Validation")
        self.validation_button.clicked.connect(lambda: self.open_reference("validation"))
        self.datasets_button = QPushButton("Open Dataset Folder")
        self.datasets_button.clicked.connect(self.open_dataset_folder)
        for button in (
            self.instructions_button,
            self.starter_button,
            self.validation_button,
            self.datasets_button,
        ):
            button.setObjectName("Secondary")
            file_actions.addWidget(button)
        file_actions.addStretch()
        progress_layout.addLayout(file_actions)
        practice_layout.addWidget(progress_card)

        self.status_combo = QComboBox()
        self.status_combo.addItems(list(applied_workspace.VALID_STATUSES))
        self.status_combo.setMinimumWidth(132)
        self.status_combo.setToolTip("Task status")

        self.create_submission_button = QPushButton("Create / Open Submission")
        self.create_submission_button.setObjectName("Secondary")
        self.create_submission_button.clicked.connect(self.open_submission)
        self.save_progress_button = QPushButton("Save Progress")
        self.save_progress_button.setObjectName("Secondary")
        self.save_progress_button.clicked.connect(self.save_progress)
        self.complete_button = QPushButton("Mark Complete")
        self.complete_button.setObjectName("Primary")
        self.complete_button.clicked.connect(self.mark_complete)

        self.learn_view.set_header_controls(self.status_combo)
        self.learn_view.set_embedded_widget(self.practice_panel)
        self.learn_view.set_footer_controls(
            self.create_submission_button,
            self.save_progress_button,
            self.complete_button,
        )
        self.workspace_card.layout.addWidget(self.learn_page, 1)
        self.lab_splitter.addWidget(self.workspace_card)
        self.lab_splitter.setStretchFactor(0, 1)
        self.lab_splitter.setStretchFactor(1, 2)
        self.lab_splitter.splitterMoved.connect(self._remember_library_width)
        outer.addWidget(self.lab_splitter, 1)

        self._set_library_collapsed(self._library_collapsed, persist=False)
        QTimer.singleShot(0, self._apply_initial_split)
        self._set_enabled(False)

    def _apply_responsive_layout(self) -> None:
        width = max(0, self.width())
        mode = "compact" if width < 760 else "medium" if width < 1080 else "wide"
        if mode == self._responsive_mode:
            return
        self._responsive_mode = mode

        self.toolbar_row.setDirection(
            QBoxLayout.Direction.TopToBottom
            if mode == "compact"
            else QBoxLayout.Direction.LeftToRight
        )
        for layout in (self.sql_actions, self.file_actions):
            layout.setDirection(
                QBoxLayout.Direction.TopToBottom
                if width < 660
                else QBoxLayout.Direction.LeftToRight
            )

        if mode == "compact":
            self._set_library_collapsed(True, persist=False)
            self.lab_splitter.setSizes([42, max(560, width - 42)])
        else:
            self._set_library_collapsed(
                self._preferred_library_collapsed,
                persist=False,
            )
            if not self._library_collapsed:
                QTimer.singleShot(0, self._apply_initial_split)
        self.updateGeometry()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def toggle_library(self) -> None:
        self._preferred_library_collapsed = not self._library_collapsed
        self._set_library_collapsed(self._preferred_library_collapsed)

    def _apply_initial_split(self) -> None:
        """Default the expanded layout to one-third navigation, two-thirds Learn."""
        if self._library_collapsed:
            return
        total = sum(self.lab_splitter.sizes()) or self.lab_splitter.width() or self.width()
        if total <= 0:
            return
        preferred = self._library_expanded_width or round(total / 3)
        maximum = max(total - 560, 270)
        width = min(max(int(preferred), 270), maximum)
        self.lab_splitter.setSizes([width, max(total - width, 560)])

    def _set_library_collapsed(self, collapsed: bool, *, persist: bool = True) -> None:
        self._library_collapsed = bool(collapsed)
        if collapsed:
            sizes = self.lab_splitter.sizes()
            if sizes and sizes[0] >= 270:
                self._library_expanded_width = sizes[0]
            self.library_body.hide()
            self.library_header.removeWidget(self.library_toggle)
            self.library_collapsed_cluster_layout.addWidget(
                self.library_toggle, 0, Qt.AlignHCenter
            )
            self.library_header_widget.hide()
            self.library_collapsed_control.show()
            self.library_card.layout.setContentsMargins(5, 8, 5, 8)
            self.library_card.setMinimumWidth(42)
            self.library_card.setMaximumWidth(42)
            self.library_toggle.setText("▶")
            self.library_toggle.setToolTip("Expand Applied Labs")
            total = max(sum(sizes), self.width(), 720)
            self.lab_splitter.setSizes([42, max(total - 42, 560)])
        else:
            self.library_collapsed_cluster_layout.removeWidget(self.library_toggle)
            self.library_header.addWidget(self.library_toggle)
            self.library_collapsed_control.hide()
            self.library_header_widget.show()
            self.library_card.setMaximumWidth(16777215)
            self.library_card.setMinimumWidth(270)
            self.library_card.layout.setContentsMargins(*self._library_expanded_margins)
            self.library_body.show()
            self.library_toggle.setText("◀")
            self.library_toggle.setToolTip("Collapse Applied Labs")
            QTimer.singleShot(0, self._apply_initial_split)
        if persist:
            self._preferred_library_collapsed = self._library_collapsed
            self._settings.setValue("applied_labs/library_collapsed", self._library_collapsed)

    def _remember_library_width(self, _position: int, _index: int) -> None:
        if self._library_collapsed:
            return
        sizes = self.lab_splitter.sizes()
        if sizes and sizes[0] >= 270:
            self._library_expanded_width = sizes[0]
            self._settings.setValue("applied_labs/library_width_v2", sizes[0])

    def _bookmark_key(self) -> str | None:
        if self.current_number is None:
            return None
        return f"applied_labs/bookmarks/{self.current_number}"

    def _bookmark_current_lab(self, bookmarked: bool) -> None:
        key = self._bookmark_key()
        if key:
            self._settings.setValue(key, bool(bookmarked))

    def _show_lab_page_menu(self) -> None:
        if self.current_item is None:
            return
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        instructions_action = menu.addAction("Open Instructions")
        dataset_action = menu.addAction("Open Dataset Folder")
        submissions_action = menu.addAction("Open Submissions Folder")
        chosen = menu.exec(self.learn_view.mapToGlobal(self.learn_view.rect().topRight()))
        if chosen == instructions_action:
            self.open_reference("instructions")
        elif chosen == dataset_action:
            self.open_dataset_folder()
        elif chosen == submissions_action:
            self.open_submissions_folder()

    def _next_lab_title(self, number: int) -> str | None:
        numbers = list(APPLIED_EXERCISES)
        try:
            index = numbers.index(number)
        except ValueError:
            return None
        if index + 1 >= len(numbers):
            return None
        return APPLIED_EXERCISES[numbers[index + 1]]["title"]

    def _continue_to_next_lab(self) -> None:
        if self.current_number is None:
            return
        for row in range(self.lab_list.count()):
            item = self.lab_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == self.current_number:
                if row + 1 < self.lab_list.count():
                    self.lab_list.setCurrentRow(row + 1)
                return

    # ---------- Course rendering ----------
    def _render_markdown(self, markdown: str, *, subtitle: str) -> None:
        key = self._bookmark_key()
        bookmarked = bool(key and self._settings.value(key, False, type=bool))
        self.learn_view.set_markdown(
            markdown,
            eyebrow="APPLIED LAB",
            subtitle=subtitle,
            bookmarked=bookmarked,
        )

    def _lab_markdown(self, number: int, item: dict[str, Any]) -> str:
        steps = "\n".join(
            f"{index}. {step}" for index, step in enumerate(item.get("steps", []), start=1)
        )
        deliverables = "\n".join(f"- {value}" for value in item.get("deliverables", []))
        validation = "\n".join(f"- {value}" for value in item.get("validation", []))
        sql_note = ""
        if applied_lab_runner.is_sql_lab(item):
            inventory = applied_lab_runner.dataset_inventory(self.root, number, item)
            if inventory:
                rows = ["| Table | File | Rows |", "|---|---|---:|"]
                for dataset in inventory:
                    row_count = dataset["rows"] if dataset["rows"] is not None else "—"
                    rows.append(
                        f"| `{dataset['table']}` | `{dataset['relative_path']}` | {row_count} |"
                    )
                sql_note = (
                    "\n## In-app SQL workspace\n"
                    "> The dataset files below are loaded automatically into an isolated DuckDB "
                    "database. Run each step as you build it, then use **Check Lab** for execution "
                    "and rubric validation.\n\n"
                    + "\n".join(rows)
                    + "\n"
                )
        extra = ""
        instructions_path = applied_lab_runner.lab_paths(self.root, number, item)["instructions"]
        if instructions_path.exists():
            source = instructions_path.read_text(encoding="utf-8").strip()
            # Avoid showing a second top-level title while preserving any richer
            # course notes supplied by the lab package.
            source = source.replace("\r\n", "\n")
            source = source.split("\n", 1)[1].lstrip() if source.startswith("# ") and "\n" in source else source
            if source:
                extra = f"\n---\n\n## Detailed lab guide\n\n{source}\n"
        return (
            f"# {item['title']}\n\n"
            f"> **Learning objective:** {item['objective']}\n\n"
            "## What you will practice\n"
            f"{item['concepts']}\n\n"
            "## Lab workflow\n"
            f"{steps}\n\n"
            "## Deliverables\n"
            f"{deliverables}\n\n"
            "## Validation checklist\n"
            f"{validation}\n"
            f"{sql_note}{extra}"
        )

    # ---------- Refresh and selection ----------
    def _app_state(self) -> dict[str, Any]:
        window = self.window()
        current = getattr(window, "state", None)
        return current if isinstance(current, dict) else state(self.conn)

    def refresh(self, _unused: str | None = None) -> None:
        if self._building:
            return
        self._building = True
        try:
            previous = self.current_number
            category = self.category_filter.currentText() if hasattr(self, "category_filter") else "All"
            app_state = self._app_state()
            pin = tracks.applied_branch_pin(self.conn)
            self.branch_filter.blockSignals(True)
            self.branch_filter.setCurrentText(pin)
            self.branch_filter.blockSignals(False)
            snapshot = tracks.snapshot(self.conn, app_state).get("applied", {})
            metadata = snapshot.get("metadata", {})
            self.track_summary.setText(
                f"Adaptive track: {snapshot.get('status', 'Not Started')} • "
                f"Branch: {metadata.get('branch', pin)} • "
                f"Next: {metadata.get('title', 'No eligible lab yet')}"
            )

            completed = 0
            rows: dict[int, int] = {}
            self.lab_list.blockSignals(True)
            self.lab_list.clear()
            active_number = metadata.get("exercise_number") or metadata.get("number")
            for number, item in APPLIED_EXERCISES.items():
                if category != "All" and item["category"] != category:
                    continue
                record = applied_workspace.progress(self.conn, self.root, number)
                if record["status"] == "Completed":
                    completed += 1
                readiness = tracks.applied_lab_readiness(self.conn, app_state, number)
                icon = "✅" if record["status"] == "Completed" else ("◐" if record["status"] == "In Progress" else ("○" if readiness["ready"] else "🔒"))
                optional = " • Optional" if item.get("optional") else ""
                list_item = QListWidgetItem(
                    f"{icon}  LAB {number:02d} • {item['category']}\n     {item['title']}"
                )
                list_item.setSizeHint(QSize(0, 58))
                list_item.setData(Qt.ItemDataRole.UserRole, int(number))
                list_item.setToolTip(
                    f"Week {item['week']} • {item['minutes']} minutes{optional}\n"
                    f"Concepts: {item['concepts']}\n"
                    + ("Ready" if readiness["ready"] else "Locked: " + "; ".join(readiness["missing"]))
                )
                self.lab_list.addItem(list_item)
                rows[int(number)] = self.lab_list.count() - 1
            self.lab_list.blockSignals(False)

            total = len(APPLIED_EXERCISES)
            all_completed = sum(
                1
                for number in APPLIED_EXERCISES
                if applied_workspace.progress(self.conn, self.root, number)["status"] == "Completed"
            )
            percent = round((all_completed / total) * 100) if total else 0
            self.library_progress.setValue(percent)
            self.library_progress_text.setText(f"{all_completed}/{total}")

            if rows:
                selected = previous if previous in rows else (
                    int(active_number) if active_number is not None and int(active_number) in rows else next(iter(rows))
                )
                self.lab_list.setCurrentRow(rows[selected])
            else:
                self.current_number = None
                self.current_item = None
                self._set_enabled(False)
                self.workspace_status.setText("No labs match this category.")
        finally:
            self._building = False

    def _lab_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            self.current_number = None
            self.current_item = None
            self._set_enabled(False)
            return
        number = current.data(Qt.ItemDataRole.UserRole)
        if number is None:
            return
        self.load_lab(int(number))

    def load_lab(self, number: int) -> None:
        item = APPLIED_EXERCISES[int(number)]
        record = applied_workspace.progress(self.conn, self.root, number)
        readiness = tracks.applied_lab_readiness(self.conn, self._app_state(), number)
        self.current_number = int(number)
        self.current_item = item
        self.current_sql_check_passed = False
        self._set_enabled(True)

        subtitle = f"{item['category']} • Week {item['week']} • {item['minutes']} minutes"
        self.breadcrumb_category.setText(f"›  {item['category']}")
        self.breadcrumb_page.setText(f"›  {item['title']}")
        # Set the value before rebuilding the native page so the header control
        # paints with its real status on the first frame.
        self.status_combo.blockSignals(True)
        self.status_combo.setCurrentText(record["status"])
        self.status_combo.blockSignals(False)
        self._render_markdown(self._lab_markdown(number, item), subtitle=subtitle)
        self.learn_view.set_navigation(
            next_title=self._next_lab_title(number),
            show_back=False,
            continue_text="Next Lab  →",
        )
        lock_text = "Ready" if readiness["ready"] else "Locked: " + "; ".join(readiness["missing"])
        self.workspace_status.setText(
            f"{record['status']} • {lock_text} • {item['concepts']}"
        )
        self.notes.setPlainText(record.get("notes", ""))

        sql_lab = applied_lab_runner.is_sql_lab(item)
        self.sql_section.setVisible(sql_lab)
        self.check_button.setVisible(sql_lab)
        self.run_button.setVisible(sql_lab)
        self.create_submission_button.setVisible(True)
        self.sql_feedback.setText("")
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        if sql_lab:
            try:
                sql = applied_lab_runner.current_sql(self.root, number, item)
                inventory = applied_lab_runner.dataset_inventory(self.root, number, item)
                self.dataset_label.setText(
                    f"{len(inventory)} table{'s' if len(inventory) != 1 else ''} loaded automatically"
                )
            except applied_lab_runner.AppliedLabRunnerError as exc:
                sql = ""
                self.dataset_label.setText("Dataset unavailable")
                self.sql_feedback.setText(f"❌ {exc}")
            self.sql_editor.blockSignals(True)
            self.sql_editor.setPlainText(sql)
            self.sql_editor.blockSignals(False)

    def _set_enabled(self, enabled: bool) -> None:
        for widget in (
            self.learn_view,
            self.status_combo,
            self.notes,
            self.instructions_button,
            self.starter_button,
            self.validation_button,
            self.datasets_button,
            self.create_submission_button,
            self.save_progress_button,
            self.complete_button,
            self.run_button,
            self.check_button,
            self.sql_editor,
        ):
            widget.setEnabled(enabled)

    # ---------- SQL ----------
    def _sql_edited(self) -> None:
        self.current_sql_check_passed = False
        if self.sql_feedback.text().startswith("✅"):
            self.sql_feedback.setText("Your SQL changed. Run Check Lab again before completion.")

    def _populate_result(self, result: dict[str, Any] | None) -> None:
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        if not result:
            return
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels([str(column) for column in columns])
        self.result_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.result_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem("NULL" if value is None else str(value)),
                )
        self.result_table.resizeRowsToContents()

    def run_sql(self) -> None:
        if self.current_number is None or self.current_item is None:
            return
        try:
            result = applied_lab_runner.run_sql(
                self.root,
                self.current_number,
                self.current_item,
                self.sql_editor.toPlainText(),
            )
        except applied_lab_runner.AppliedLabRunnerError as exc:
            message = str(exc)
            self.sql_feedback.setText(f"❌ {message}")
            self.sql_editor.navigate_to_error(message)
            self._populate_result(None)
            return
        self._populate_result(result.get("last_result"))
        result_count = len(result.get("result_sets", []))
        self.sql_feedback.setText(
            f"✅ Executed {result['statement_count']} statement(s). "
            f"Displayed the last of {result_count} result set(s)."
        )

    def check_sql(self) -> bool:
        if self.current_number is None or self.current_item is None:
            return False
        result = applied_lab_runner.check_sql(
            self.root,
            self.current_number,
            self.current_item,
            self.sql_editor.toPlainText(),
        )
        self.current_sql_check_passed = bool(result["passed"])
        self._populate_result((result.get("run") or {}).get("last_result"))
        lines = []
        for check in result["checklist"]:
            lines.append(("✓" if check["passed"] else "•") + " " + check["label"])
        if result["passed"]:
            self.sql_feedback.setText(
                "✅ Automated execution and rubric checks passed. "
                "Review the lab's interpretation and validation checklist before marking complete.\n"
                + "\n".join(lines)
            )
        else:
            failed = [check for check in result["checklist"] if not check["passed"]]
            detail = failed[0]["detail"] if failed else "Review the checklist."
            self.sql_feedback.setText(
                "Not quite — complete the remaining automated checks. " + detail + "\n" + "\n".join(lines)
            )
            self.sql_editor.navigate_to_error(detail)
        return self.current_sql_check_passed

    def save_sql_submission(self) -> Path | None:
        if self.current_number is None or self.current_item is None:
            return None
        try:
            path = applied_lab_runner.save_submission(
                self.root,
                self.current_number,
                self.current_item,
                self.sql_editor.toPlainText(),
            )
        except applied_lab_runner.AppliedLabRunnerError as exc:
            QMessageBox.warning(self, "Could Not Save SQL", str(exc))
            return None
        current_status = self.status_combo.currentText()
        if current_status == "Not Started":
            current_status = "In Progress"
            self.status_combo.setCurrentText(current_status)
        applied_workspace.save_progress(
            self.conn,
            self.root,
            self.current_number,
            status=current_status,
            notes=self.notes.toPlainText(),
        )
        self.sql_feedback.setText(
            f"✅ Saved {path.name}. Run Check Lab when the analysis is ready."
        )
        return path

    # ---------- Files and progress ----------
    def _open_path(self, path: Path) -> str:
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        if os.name == "nt":
            os.startfile(str(path))
            return "the default application"
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return "the default application"
        command = shutil.which("xdg-open")
        if command:
            subprocess.Popen([command, str(path)])
            return "the default application"
        raise RuntimeError("No supported file-opening command was found.")

    def open_reference(self, kind: str) -> None:
        if self.current_number is None or self.current_item is None:
            return
        path = applied_lab_runner.lab_paths(
            self.root, self.current_number, self.current_item
        ).get(kind)
        if path is None:
            return
        try:
            app_name = self._open_path(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Lab File", str(exc))
            return
        self.window().statusBar().showMessage(f"Opened {path.name} in {app_name}.", 4200)

    def open_dataset_folder(self) -> None:
        if self.current_number is None or self.current_item is None:
            return
        path = applied_lab_runner.lab_paths(
            self.root, self.current_number, self.current_item
        )["datasets"]
        try:
            app_name = applied_workspace.open_folder(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Dataset Folder", str(exc))
            return
        self.window().statusBar().showMessage(f"Opened dataset folder in {app_name}.", 4200)

    def open_submissions_folder(self) -> None:
        path = self.root / "practice" / "applied" / "submissions"
        path.mkdir(parents=True, exist_ok=True)
        try:
            app_name = applied_workspace.open_folder(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Submissions", str(exc))
            return
        self.window().statusBar().showMessage(f"Opened submissions in {app_name}.", 4200)

    def open_submission(self) -> None:
        if self.current_number is None or self.current_item is None:
            return
        try:
            if applied_lab_runner.is_sql_lab(self.current_item):
                path = self.save_sql_submission()
                if path is None:
                    return
            else:
                path, _created = applied_workspace.ensure_submission(
                    self.root, self.current_number
                )
            app_name = self._open_path(path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Submission", str(exc))
            return
        if self.status_combo.currentText() == "Not Started":
            self.status_combo.setCurrentText("In Progress")
        self.window().statusBar().showMessage(f"Opened {path.name} in {app_name}.", 4200)

    def save_progress(self) -> None:
        if self.current_number is None or self.current_item is None:
            return
        if applied_lab_runner.is_sql_lab(self.current_item):
            if self.save_sql_submission() is None:
                return
        record = applied_workspace.save_progress(
            self.conn,
            self.root,
            self.current_number,
            status=self.status_combo.currentText(),
            notes=self.notes.toPlainText(),
        )
        self.workspace_status.setText(
            f"{record['status']} • Progress saved • {self.current_item['concepts']}"
        )
        self.changed.emit()

    def mark_complete(self) -> None:
        if self.current_number is None or self.current_item is None:
            return
        readiness = tracks.applied_lab_readiness(
            self.conn, self._app_state(), self.current_number
        )
        if not readiness["ready"]:
            QMessageBox.warning(
                self,
                "Prerequisites Not Complete",
                "Complete the following first:\n\n"
                + "\n".join(f"• {reason}" for reason in readiness["missing"]),
            )
            return
        if applied_lab_runner.is_sql_lab(self.current_item):
            self.save_sql_submission()
            if not self.current_sql_check_passed and not self.check_sql():
                QMessageBox.warning(
                    self,
                    "SQL Checks Not Complete",
                    "Run and pass the in-app SQL checks before marking this lab complete.",
                )
                return
        else:
            path = applied_workspace.submission_path(self.root, self.current_number)
            if not path.exists():
                QMessageBox.warning(
                    self,
                    "Submission Required",
                    "Create a saved submission before marking the lab complete.",
                )
                return
            if not applied_workspace.submission_has_changes(self.root, self.current_number):
                answer = QMessageBox.question(
                    self,
                    "Submission Matches Starter",
                    "The saved submission still matches the starter. Mark complete anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
        self.status_combo.setCurrentText("Completed")
        applied_workspace.save_progress(
            self.conn,
            self.root,
            self.current_number,
            status="Completed",
            notes=self.notes.toPlainText(),
        )
        self.changed.emit()
        self.refresh()

    def _branch_changed(self, branch: str) -> None:
        if self._building:
            return
        if branch not in {"Auto", *tracks.APPLIED_BRANCH_ORDER}:
            branch = "Auto"
        save_setting(self.conn, "applied_branch_pin", branch)
        app_state = self._app_state()
        tracks.sync_all(self.conn, app_state)
        self.changed.emit()
        self.refresh()
