"""Native course workspace for SQL Companion's guided DuckDB exercises."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.data.duckdb_exercises import DUCKDB_EXERCISES
from career_app.services import duckdb_workspace
from career_app.services import duckdb_exercise_runner as runner
from career_app.theme import COLORS
from career_app.ui.course_ui import CoursePageWidget, SqlCodeEditor
from career_app.ui.widgets import Card


class FeedbackBanner(QLabel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.hide()

    def show_message(self, text: str, kind: str = "neutral") -> None:
        palette = {
            "success": ("#17392f", "#63dfa9", "#9af0ca"),
            "error": ("#3a202d", "#ec7caa", "#ffc1d8"),
            "hint": ("#292342", "#9b77f4", "#d9cbff"),
            "neutral": ("#172333", "#4b6688", "#cbd8ea"),
        }
        background, border, foreground = palette.get(kind, palette["neutral"])
        self.setStyleSheet(
            f"background:{background};border:1px solid {border};color:{foreground};"
            "border-radius:8px;padding:8px 10px;"
        )
        self.setText(text)
        self.show()


class DuckDBExercisesWidget(QWidget):
    """Course navigation + Learn + Practice for all guided DuckDB exercises."""

    changed = Signal()

    def __init__(self, conn, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.conn = conn
        self.root = Path(root)
        self.current_number: int | None = None
        self._loading = False
        self._settings = QSettings("CareerAccelerator", "CareerAccelerator")
        self._question_definitions: list[runner.QuestionBlock] = []
        self._question_answers: dict[int, str] = {}
        self._question_notes: dict[int, str] = {}
        self._active_question_number: int | None = None
        self._question_results: dict[int, dict[str, Any]] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        toolbar = QFrame()
        toolbar.setObjectName("DuckDBExerciseToolbar")
        toolbar.setStyleSheet(
            "QFrame#DuckDBExerciseToolbar {background:#111a29;border:1px solid #2d3850;"
            "border-radius:10px;}"
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 7, 10, 7)
        toolbar_layout.setSpacing(8)
        self.back_button = QPushButton("‹")
        self.back_button.setObjectName("Secondary")
        self.back_button.setFixedSize(36, 34)
        self.back_button.clicked.connect(self.previous_exercise)
        toolbar_layout.addWidget(self.back_button)
        self.breadcrumb = QLabel("SQL Companion  ›  DuckDB Exercises")
        self.breadcrumb.setStyleSheet("color:#c4cde0;font-size:9.5pt;")
        toolbar_layout.addWidget(self.breadcrumb, 1)
        open_folder = QPushButton("Open Practice Folder")
        open_folder.setObjectName("Secondary")
        open_folder.clicked.connect(self.open_practice_folder)
        toolbar_layout.addWidget(open_folder)
        outer.addWidget(toolbar)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(4)

        self.navigation_card = Card()
        self.navigation_card.setMinimumWidth(310)
        self.navigation_card.layout.setContentsMargins(12, 12, 12, 12)
        self.navigation_card.layout.setSpacing(9)
        nav_title_row = QHBoxLayout()
        nav_title = QLabel("▤  DuckDB Exercises")
        nav_title.setStyleSheet("font-size:13pt;font-weight:700;color:#f4f6fb;")
        nav_title_row.addWidget(nav_title, 1)
        self.progress_count = QLabel("0/12")
        self.progress_count.setObjectName("Muted")
        nav_title_row.addWidget(self.progress_count)
        self.navigation_card.layout.addLayout(nav_title_row)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(7)
        self.navigation_card.layout.addWidget(self.progress_bar)
        self.track_caption = QLabel(
            "Complete each exercise inside Career Accelerator and save a reviewable SQL submission."
        )
        self.track_caption.setObjectName("Muted")
        self.track_caption.setWordWrap(True)
        self.navigation_card.layout.addWidget(self.track_caption)
        self.exercise_list = QListWidget()
        self.exercise_list.setObjectName("DuckDBCourseNavigation")
        self.exercise_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.exercise_list.setStyleSheet(
            "QListWidget#DuckDBCourseNavigation {background:transparent;border:none;outline:none;}"
            "QListWidget#DuckDBCourseNavigation::item {padding:9px 8px;border-radius:7px;"
            "border-left:3px solid transparent;}"
            "QListWidget#DuckDBCourseNavigation::item:selected {background:#202b40;"
            "border-left:3px solid #8b5cf6;color:#ffffff;}"
            "QListWidget#DuckDBCourseNavigation::item:hover {background:#182235;}"
        )
        self.exercise_list.currentItemChanged.connect(self._exercise_selected)
        self.navigation_card.layout.addWidget(self.exercise_list, 1)
        self.main_splitter.addWidget(self.navigation_card)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.setObjectName("DuckDBLearnPracticeSplitter")
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.setOpaqueResize(True)
        self.workspace_splitter.setHandleWidth(7)
        self.workspace_splitter.setStyleSheet(
            "QSplitter#DuckDBLearnPracticeSplitter::handle {background:#303a52;"
            "border-radius:2px;margin:4px 1px;}"
            "QSplitter#DuckDBLearnPracticeSplitter::handle:hover {background:#8b5cf6;}"
        )

        self.learn_card = Card()
        self.learn_card.setMinimumWidth(340)
        self.learn_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.learn_card.layout.setContentsMargins(8, 8, 8, 8)
        self.learn_card.layout.setSpacing(0)
        self.learn_view = CoursePageWidget()
        self.learn_view.setMinimumWidth(0)
        self.learn_view.backRequested.connect(self.previous_exercise)
        self.learn_view.continueRequested.connect(self.next_exercise)
        self.learn_view.bookmarkToggled.connect(self._bookmark_changed)
        self.learn_view.overflowRequested.connect(self._show_page_menu)
        self.learn_card.layout.addWidget(self.learn_view, 1)
        self.workspace_splitter.addWidget(self.learn_card)

        self.practice_card = Card()
        self.practice_card.setMinimumWidth(380)
        self.practice_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.practice_card.layout.setContentsMargins(12, 12, 12, 12)
        self.practice_card.layout.setSpacing(9)
        practice_heading = QHBoxLayout()
        practice_title = QLabel("Practice")
        practice_title.setStyleSheet("font-size:13pt;font-weight:700;color:#f4f6fb;")
        practice_heading.addWidget(practice_title)
        practice_heading.addStretch()
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(duckdb_workspace.VALID_STATUSES))
        self.status_combo.setMinimumWidth(126)
        self.status_combo.setToolTip("Exercise status")
        practice_heading.addWidget(self.status_combo)
        self.practice_card.layout.addLayout(practice_heading)

        selector_row = QHBoxLayout()
        selector_label = QLabel("Question")
        selector_label.setObjectName("Muted")
        selector_row.addWidget(selector_label)
        self.question_combo = QComboBox()
        self.question_combo.setMinimumContentsLength(18)
        self.question_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.question_combo.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed
        )
        self.question_combo.view().setTextElideMode(Qt.TextElideMode.ElideRight)
        self.question_combo.currentIndexChanged.connect(self._question_changed)
        selector_row.addWidget(self.question_combo, 1)
        self.dataset_label = QLabel("")
        self.dataset_label.setObjectName("Muted")
        selector_row.addWidget(self.dataset_label)
        self.practice_card.layout.addLayout(selector_row)

        self.question_prompt = QLabel("")
        self.question_prompt.setWordWrap(True)
        self.question_prompt.setStyleSheet(
            "background:#181c31;border:1px solid #3b3f61;border-radius:8px;"
            "color:#d9def0;padding:8px 10px;"
        )
        self.practice_card.layout.addWidget(self.question_prompt)

        self.sql_editor = SqlCodeEditor()
        self.sql_editor.setObjectName("DuckDBExerciseSqlEditor")
        self.sql_editor.setPlaceholderText(
            "Write the SQL answer for the selected question. Each question is saved independently."
        )
        self.sql_editor.setMinimumHeight(240)
        self.sql_editor.textChanged.connect(self._answer_changed)
        self.practice_card.layout.addWidget(self.sql_editor, 3)

        first_actions = QHBoxLayout()
        self.run_button = QPushButton("▶ Run Question")
        self.run_button.setObjectName("Secondary")
        self.run_button.clicked.connect(self.run_question)
        self.check_question_button = QPushButton("✓ Check Question")
        self.check_question_button.setObjectName("Secondary")
        self.check_question_button.clicked.connect(self.check_question)
        self.check_exercise_button = QPushButton("Check Exercise")
        self.check_exercise_button.setObjectName("Secondary")
        self.check_exercise_button.clicked.connect(self.check_exercise)
        first_actions.addWidget(self.run_button)
        first_actions.addWidget(self.check_question_button)
        first_actions.addWidget(self.check_exercise_button)
        first_actions.addStretch()
        self.practice_card.layout.addLayout(first_actions)

        self.feedback = FeedbackBanner()
        self.practice_card.layout.addWidget(self.feedback)

        self.result_table = QTableWidget()
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setShowGrid(False)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setMinimumHeight(150)
        self.result_table.setStyleSheet(
            "QTableWidget {background:#111827;alternate-background-color:#182235;"
            "color:#eef2fa;border:1px solid #303a52;border-radius:8px;}"
            "QHeaderView::section {background:#202b40;color:#f4f6fb;padding:7px;"
            "border:none;border-right:1px solid #34405a;font-weight:650;}"
        )
        self.practice_card.layout.addWidget(self.result_table, 2)

        notes_label = QLabel("Notes & reasoning")
        notes_label.setStyleSheet("font-weight:650;color:#e7ebf5;")
        self.practice_card.layout.addWidget(notes_label)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Record what the query does, mistakes you corrected, and why the final answer works."
        )
        self.notes.setMaximumHeight(92)
        self.notes.textChanged.connect(self._notes_changed)
        self.notes.setStyleSheet(
            "QTextEdit {background:#151c2b;border:1px solid #343c55;border-radius:8px;padding:7px;}"
        )
        self.practice_card.layout.addWidget(self.notes)

        reference_row = QHBoxLayout()
        for label, callback in (
            ("Instructions", lambda: self.open_reference("instructions")),
            ("Starter", lambda: self.open_reference("starter")),
            ("Validation", lambda: self.open_reference("validation")),
            ("Datasets", self.open_dataset_folder),
        ):
            button = QPushButton(label)
            button.setObjectName("Secondary")
            button.clicked.connect(callback)
            reference_row.addWidget(button)
        reference_row.addStretch()
        self.practice_card.layout.addLayout(reference_row)

        submission_row = QHBoxLayout()
        self.save_button = QPushButton("Save Submission")
        self.save_button.setObjectName("Secondary")
        self.save_button.clicked.connect(self.save_progress)
        self.submit_button = QPushButton("Submit Exercise")
        self.submit_button.setObjectName("Primary")
        self.submit_button.clicked.connect(self.submit_exercise)
        submission_row.addWidget(self.save_button)
        submission_row.addWidget(self.submit_button)
        submission_row.addStretch()
        self.practice_card.layout.addLayout(submission_row)

        self.workspace_splitter.addWidget(self.practice_card)
        self.workspace_splitter.setStretchFactor(0, 1)
        self.workspace_splitter.setStretchFactor(1, 1)
        self.workspace_splitter.splitterMoved.connect(self._remember_workspace_split)
        self.main_splitter.addWidget(self.workspace_splitter)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([330, 1080])
        outer.addWidget(self.main_splitter, 1)
        QTimer.singleShot(0, self._apply_workspace_split)

    def refresh(self, *, preserve_number: bool = True) -> None:
        preferred = self.current_number if preserve_number else None
        if preferred is None:
            preferred = int(self._settings.value("duckdb_exercises/current_number", 1))
        statuses: dict[int, dict[str, Any]] = {}
        completed = 0
        for number in sorted(DUCKDB_EXERCISES):
            try:
                progress = duckdb_workspace.progress(self.conn, self.root, number)
            except Exception:
                progress = {"status": "Not Started", "notes": ""}
            statuses[number] = progress
            if progress.get("status") == "Completed":
                completed += 1
        self.progress_count.setText(f"{completed}/{len(DUCKDB_EXERCISES)}")
        self.progress_bar.setValue(round(completed / max(len(DUCKDB_EXERCISES), 1) * 100))

        self._loading = True
        self.exercise_list.clear()
        target_row = 0
        for row, number in enumerate(sorted(DUCKDB_EXERCISES)):
            item = DUCKDB_EXERCISES[number]
            status = statuses[number].get("status", "Not Started")
            marker = "●" if status == "Completed" else "◐" if status == "In Progress" else "○"
            list_item = QListWidgetItem(
                f"{marker}  EXERCISE {number:02d}\n     {item['title']}"
            )
            list_item.setData(Qt.ItemDataRole.UserRole, number)
            list_item.setToolTip(f"{item['concepts']} • {item['minutes']} minutes")
            self.exercise_list.addItem(list_item)
            if number == preferred:
                target_row = row
        if self.exercise_list.count():
            self.exercise_list.setCurrentRow(target_row)
            current = self.exercise_list.currentItem()
        else:
            current = None
        self._loading = False
        if current is not None:
            self._load_exercise(int(current.data(Qt.ItemDataRole.UserRole)))

    def select_exercise(self, number: int) -> None:
        """Select the requested exercise and always refresh its workspace."""
        for row in range(self.exercise_list.count()):
            item = self.exercise_list.item(row)
            if int(item.data(Qt.ItemDataRole.UserRole)) != int(number):
                continue
            if self.exercise_list.currentRow() != row:
                self.exercise_list.setCurrentRow(row)
            else:
                self._load_exercise(int(number))
            return

    def _exercise_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if self._loading or current is None:
            return
        self._load_exercise(int(current.data(Qt.ItemDataRole.UserRole)))

    def _apply_workspace_split(self) -> None:
        total = sum(self.workspace_splitter.sizes()) or self.workspace_splitter.width()
        if total <= 0:
            return
        saved = self._settings.value("duckdb_exercises/learn_width", None)
        preferred = int(saved) if saved not in (None, "") else round(total / 2)
        left = min(max(preferred, 340), max(total - 380, 340))
        self.workspace_splitter.setSizes([left, max(total - left, 380)])

    def _remember_workspace_split(self, _position: int, _index: int) -> None:
        sizes = self.workspace_splitter.sizes()
        if len(sizes) >= 2 and sizes[0] >= 340 and sizes[1] >= 380:
            self._settings.setValue("duckdb_exercises/learn_width", sizes[0])

    def _question_note_key(self, question_number: int) -> str:
        return f"duckdb_exercises/question_notes/{self.current_number}/{question_number}"

    def _question_pass_key(self, question_number: int) -> str:
        return f"duckdb_exercises/question_pass_digest/{self.current_number}/{question_number}"

    @staticmethod
    def _answer_digest(sql: str) -> str:
        return hashlib.sha256(str(sql or "").strip().encode("utf-8")).hexdigest()

    def _question_passed(self, question_number: int) -> bool:
        answer = self._question_answers.get(question_number, "")
        if not answer.strip():
            return False
        saved = str(self._settings.value(self._question_pass_key(question_number), "") or "")
        return bool(saved) and saved == self._answer_digest(answer)

    def _set_question_passed(self, question_number: int, passed: bool) -> None:
        key = self._question_pass_key(question_number)
        if passed:
            self._settings.setValue(
                key, self._answer_digest(self._question_answers.get(question_number, ""))
            )
        else:
            self._settings.remove(key)
        self._update_question_labels()

    def _question_label(self, question: runner.QuestionBlock) -> str:
        marker = "✓" if self._question_passed(question.number) else "○"
        return f"{marker}  Q{question.number}: {question.prompt}"

    def _update_question_labels(self) -> None:
        for index, question in enumerate(self._question_definitions):
            if index < self.question_combo.count():
                self.question_combo.setItemText(index, self._question_label(question))

    def _capture_current_question(self) -> None:
        if self._loading or self._active_question_number is None:
            return
        number = self._active_question_number
        self._question_answers[number] = self.sql_editor.toPlainText().strip()
        self._question_notes[number] = self.notes.toPlainText()
        self._settings.setValue(self._question_note_key(number), self._question_notes[number])

    def _combined_notes(self) -> str:
        notes: list[str] = []
        for question in self._question_definitions:
            value = self._question_notes.get(question.number, "").strip()
            if value:
                notes.append(f"Q{question.number}: {value}")
        return "\n\n".join(notes)

    def _full_submission_sql(self) -> str:
        if self.current_number is None:
            return ""
        self._capture_current_question()
        return runner.compose_submission(
            self.root, self.current_number, dict(self._question_answers)
        )

    def _persist_submission_draft(self) -> Path | None:
        if self.current_number is None:
            return None
        return runner.save_submission(
            self.root, self.current_number, self._full_submission_sql()
        )

    def _load_exercise(self, number: int) -> None:
        if self.current_number is not None and self._question_definitions:
            try:
                self._persist_submission_draft()
            except Exception:
                pass

        self.current_number = int(number)
        self._settings.setValue("duckdb_exercises/current_number", number)
        item = DUCKDB_EXERCISES[number]
        try:
            markdown = runner.instructions_markdown(self.root, number)
            self._question_definitions = runner.question_definitions(self.root, number)
            self._question_answers = runner.question_answers(self.root, number)
        except runner.DuckDBExerciseRunnerError as exc:
            markdown = (
                f"# {item['title']}\n\n> **Exercise files missing:** {exc}\n\n"
                "Run the repository setup or restore the `practice/duckdb` folder."
            )
            self._question_definitions = [runner.QuestionBlock(1, "Exercise query", "")]
            self._question_answers = {1: ""}
        progress = duckdb_workspace.progress(self.conn, self.root, number)
        bookmarked = self._settings.value(
            f"duckdb_exercises/bookmarks/{number}", False, type=bool
        )
        inventory = runner.dataset_inventory(self.root, number)
        question_count = len(self._question_definitions)
        subtitle = (
            f"Week {item['week']} • {item['minutes']} minutes • "
            f"{question_count} question{'s' if question_count != 1 else ''} • "
            f"{len(inventory)} dataset{'s' if len(inventory) != 1 else ''} • {item['concepts']}"
        )
        self.learn_view.set_markdown(
            markdown,
            eyebrow="DuckDB Exercise",
            subtitle=subtitle,
            bookmarked=bookmarked,
        )
        next_item = DUCKDB_EXERCISES.get(number + 1)
        self.learn_view.set_navigation(
            next_title=next_item["title"] if next_item else None,
            show_back=number > min(DUCKDB_EXERCISES),
            continue_text="Next Exercise  →",
        )
        self.breadcrumb.setText(
            f"SQL Companion  ›  DuckDB Exercises  ›  Exercise {number:02d}  ›  {item['title']}"
        )

        self._question_notes = {}
        legacy_notes = str(progress.get("notes") or "")
        for question in self._question_definitions:
            saved_note = str(
                self._settings.value(self._question_note_key(question.number), "") or ""
            )
            self._question_notes[question.number] = saved_note
        if legacy_notes and not any(value.strip() for value in self._question_notes.values()):
            first = self._question_definitions[0].number
            self._question_notes[first] = legacy_notes

        self._loading = True
        self.status_combo.setCurrentText(str(progress.get("status") or "Not Started"))
        self.question_combo.clear()
        for question in self._question_definitions:
            self.question_combo.addItem(self._question_label(question), question.number)
        preferred = int(
            self._settings.value(
                f"duckdb_exercises/current_question/{number}",
                self._question_definitions[0].number,
            )
        )
        index = next(
            (
                idx
                for idx, question in enumerate(self._question_definitions)
                if question.number == preferred
            ),
            0,
        )
        self.question_combo.setCurrentIndex(index)
        self._loading = False
        self._active_question_number = None
        self._load_question(self.current_question_number())

        self.dataset_label.setText(
            f"{len(inventory)} dataset{'s' if len(inventory) != 1 else ''}"
        )
        self.back_button.setEnabled(number > min(DUCKDB_EXERCISES))
        QTimer.singleShot(0, self._apply_workspace_split)

    def current_question_number(self) -> int:
        value = self.question_combo.currentData()
        if value is not None:
            return int(value)
        if self._question_definitions:
            return self._question_definitions[0].number
        return 1

    def _load_question(self, number: int) -> None:
        definition = next(
            (item for item in self._question_definitions if item.number == int(number)),
            None,
        )
        if definition is None:
            return
        self._active_question_number = definition.number
        self._settings.setValue(
            f"duckdb_exercises/current_question/{self.current_number}", definition.number
        )
        self._loading = True
        self.question_prompt.setText(definition.prompt)
        self.sql_editor.setPlainText(self._question_answers.get(definition.number, ""))
        self.notes.setPlainText(self._question_notes.get(definition.number, ""))
        self._loading = False
        self.feedback.hide()
        self._populate_result(self._question_results.get(definition.number))
        if self._question_passed(definition.number):
            self.feedback.show_message(
                "This saved answer previously passed its validation checkpoint.",
                "success",
            )

    def _question_changed(self, _index: int = -1) -> None:
        if self._loading:
            return
        self._capture_current_question()
        try:
            self._persist_submission_draft()
        except Exception:
            pass
        self._load_question(self.current_question_number())

    def _answer_changed(self) -> None:
        if self._loading or self._active_question_number is None:
            return
        number = self._active_question_number
        new_answer = self.sql_editor.toPlainText().strip()
        previous = self._question_answers.get(number, "")
        self._question_answers[number] = new_answer
        if new_answer != previous:
            self._question_results.pop(number, None)
            self._set_question_passed(number, False)
            self.feedback.hide()
            self._populate_result(None)

    def _notes_changed(self) -> None:
        if self._loading or self._active_question_number is None:
            return
        number = self._active_question_number
        self._question_notes[number] = self.notes.toPlainText()
        self._settings.setValue(self._question_note_key(number), self._question_notes[number])

    def _populate_result(self, run: dict[str, Any] | None) -> None:
        result = run.get("last_result") if run else None
        self.result_table.clear()
        if not result:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
        columns = list(result.get("columns") or [])
        rows = list(result.get("rows") or [])
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        self.result_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.result_table.setItem(
                    row_index, column_index, QTableWidgetItem("NULL" if value is None else str(value))
                )
        self.result_table.resizeRowsToContents()

    @staticmethod
    def _checklist_text(checklist: list[dict[str, Any]]) -> str:
        return "\n".join(
            f"{'✓' if item.get('passed') else '•'} {item.get('label')}: {item.get('detail')}"
            for item in checklist
        )

    def run_question(self) -> None:
        if self.current_number is None:
            return
        question_number = self.current_question_number()
        full_sql = self._full_submission_sql()
        try:
            run = runner.run_question(
                self.root, self.current_number, full_sql, question_number
            )
        except runner.DuckDBExerciseRunnerError as exc:
            message = str(exc)
            self.feedback.show_message(message, "error")
            self.sql_editor.navigate_to_error(message)
            return
        self._question_results[question_number] = run
        self._populate_result(run)
        result = run["last_result"]
        suffix = " Results were limited." if result.get("truncated") else ""
        self.feedback.show_message(
            f"Query ran successfully and returned {len(result['rows'])} displayed row(s).{suffix}",
            "success",
        )

    def check_question(self) -> None:
        if self.current_number is None:
            return
        question_number = self.current_question_number()
        full_sql = self._full_submission_sql()
        try:
            result = runner.check_question(
                self.root, self.current_number, full_sql, question_number
            )
        except runner.DuckDBExerciseRunnerError as exc:
            self._set_question_passed(question_number, False)
            self.feedback.show_message(str(exc), "error")
            return
        if result.get("run"):
            self._question_results[question_number] = result["run"]
        self._populate_result(result.get("run"))
        self._set_question_passed(question_number, bool(result["passed"]))
        self.feedback.show_message(
            self._checklist_text(result["checklist"]),
            "success" if result["passed"] else "hint",
        )

    def check_exercise(self) -> dict[str, Any] | None:
        if self.current_number is None:
            return None
        full_sql = self._full_submission_sql()
        try:
            result = runner.check_exercise(self.root, self.current_number, full_sql)
        except runner.DuckDBExerciseRunnerError as exc:
            self.feedback.show_message(str(exc), "error")
            return None
        failed_details: list[str] = []
        for question_result in result["questions"]:
            question = question_result["question"]
            self._set_question_passed(question.number, bool(question_result["passed"]))
            if question_result.get("run"):
                self._question_results[question.number] = question_result["run"]
            if question_result["passed"]:
                continue
            failed = [
                item["label"]
                for item in question_result["checklist"]
                if not item.get("passed")
            ]
            failed_details.append(f"Q{question.number}: {', '.join(failed)}")
        message = f"{result['passed_count']} of {result['total_count']} questions passed."
        if failed_details:
            message += "\n" + "\n".join(failed_details)
        self.feedback.show_message(message, "success" if result["passed"] else "hint")
        selected_number = self.current_question_number()
        selected = next(
            (
                item
                for item in result["questions"]
                if item["question"].number == selected_number
            ),
            result["questions"][0] if result["questions"] else None,
        )
        if selected is not None:
            self._populate_result(selected.get("run"))
        return result

    def save_progress(self, *, show_confirmation: bool = True) -> None:
        if self.current_number is None:
            return
        try:
            path = self._persist_submission_draft()
            status = self.status_combo.currentText()
            if status == "Not Started":
                status = "In Progress"
                self.status_combo.setCurrentText(status)
            duckdb_workspace.save_progress(
                self.conn,
                self.root,
                self.current_number,
                status=status,
                notes=self._combined_notes(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Could not save exercise", str(exc))
            return
        if show_confirmation and path is not None:
            self.feedback.show_message(
                f"All question drafts were saved to {path.name}.", "success"
            )
        self.changed.emit()

    def submit_exercise(self) -> None:
        if self.current_number is None:
            return
        try:
            self._persist_submission_draft()
        except Exception as exc:
            QMessageBox.critical(self, "Could not submit exercise", str(exc))
            return
        result = self.check_exercise()
        if not result or not result["passed"]:
            QMessageBox.information(
                self,
                "Exercise not ready",
                "The submission was saved, but every question must pass before the exercise can be completed.",
            )
            return
        try:
            duckdb_workspace.save_progress(
                self.conn,
                self.root,
                self.current_number,
                status="Completed",
                notes=self._combined_notes(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Could not submit exercise", str(exc))
            return
        self.status_combo.setCurrentText("Completed")
        self.feedback.show_message(
            f"All {result['total_count']} questions passed. Exercise submitted and marked complete.",
            "success",
        )
        self.changed.emit()
        self.refresh()

    def previous_exercise(self) -> None:
        if self.current_number is None:
            return
        numbers = sorted(DUCKDB_EXERCISES)
        index = numbers.index(self.current_number)
        if index > 0:
            self.select_exercise(numbers[index - 1])

    def next_exercise(self) -> None:
        if self.current_number is None:
            return
        numbers = sorted(DUCKDB_EXERCISES)
        index = numbers.index(self.current_number)
        if index + 1 < len(numbers):
            self.select_exercise(numbers[index + 1])

    def _bookmark_changed(self, bookmarked: bool) -> None:
        if self.current_number is not None:
            self._settings.setValue(
                f"duckdb_exercises/bookmarks/{self.current_number}", bool(bookmarked)
            )

    def _show_page_menu(self) -> None:
        if self.current_number is None:
            return
        menu = QMenu(self)
        open_submission = menu.addAction("Open submission file")
        reset = menu.addAction("Reload saved submission")
        selected = menu.exec(self.mapToGlobal(self.rect().center()))
        if selected is open_submission:
            self.open_submission_file()
        elif selected is reset:
            self._load_exercise(self.current_number)

    def open_submission_file(self) -> None:
        if self.current_number is None:
            return
        path = self._persist_submission_draft()
        if path is None:
            return
        self._open_path(path)

    def open_reference(self, key: str) -> None:
        if self.current_number is None:
            return
        path = runner.exercise_paths(self.root, self.current_number).get(key)
        if path is None or not path.exists():
            QMessageBox.information(self, "File not found", f"The {key} file was not found.")
            return
        self._open_path(path)

    def open_dataset_folder(self) -> None:
        if self.current_number is None:
            return
        path = runner.exercise_paths(self.root, self.current_number)["datasets"]
        path.mkdir(parents=True, exist_ok=True)
        self._open_path(path)

    def open_practice_folder(self) -> None:
        path = self.root / "practice" / "duckdb"
        path.mkdir(parents=True, exist_ok=True)
        self._open_path(path)

    @staticmethod
    def _open_path(path: Path) -> None:
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as exc:
            QMessageBox.warning(None, "Could not open path", str(exc))
