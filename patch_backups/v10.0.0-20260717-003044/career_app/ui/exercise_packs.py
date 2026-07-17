from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QSettings, QSize, Qt, Signal
from PySide6.QtGui import QFontDatabase, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
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

from career_app.services import exercise_packs
from career_app.theme import COLORS
from career_app.ui.course_ui import CoursePageWidget
from career_app.ui.widgets import Card


class RotatedLabel(QLabel):
    """A label painted counterclockwise for the collapsed library rail."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(hint.height(), hint.width())

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(hint.height(), hint.width())

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.translate(0, self.height())
        painter.rotate(-90)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(
            0,
            0,
            self.height(),
            self.width(),
            int(self.alignment().value),
            self.text(),
        )


class FeedbackLabel(QLabel):
    """A compact state-aware banner for hints, errors, and success feedback."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setMinimumHeight(46)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.setContentsMargins(12, 8, 12, 8)
        self.setText("")

    def setText(self, text: str) -> None:  # noqa: N802 - Qt API name
        super().setText(text)
        purple = COLORS.get("purple", "#8b5cf6")
        if text.startswith("✅"):
            background, border, foreground = "#15382d", "#2fa67d", "#d8fff0"
        elif text.startswith("❌") or text.startswith("Not quite"):
            background, border, foreground = "#3a2028", "#d25b76", "#ffe4ea"
        elif text.startswith("💡"):
            background, border, foreground = "#29223f", purple, "#f2eaff"
        elif text:
            background, border, foreground = "#20283b", "#52627f", "#e7ecf8"
        else:
            background, border, foreground = (
                "transparent",
                "transparent",
                COLORS.get("muted", "#aeb0c5"),
            )
        self.setStyleSheet(
            "QLabel {"
            f"background:{background};color:{foreground};border:1px solid {border};"
            "border-radius:8px;font-size:9.5pt;"
            "}"
        )
        self.setVisible(bool(text))


class ExerciseSuggestionPanel(QFrame):
    """Compact dashboard recommendation that is recalculated on every refresh."""

    def __init__(self, on_open: Callable[[str], None], parent: QWidget | None = None):
        super().__init__(parent)
        self._on_open = on_open
        self._pack_id: str | None = None
        self.setObjectName("ExerciseSuggestion")
        self.setFixedHeight(58)
        self.setMinimumWidth(360)
        self.setMaximumWidth(560)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setStyleSheet(
            "QFrame#ExerciseSuggestion {"
            f"background:{COLORS.get('surface_alt', '#20213a')};"
            f"border:1px solid {COLORS.get('purple', '#8b5cf6')};"
            "border-radius:9px;"
            "}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 8, 8)
        layout.setSpacing(8)
        icon = QLabel("🧩")
        icon.setStyleSheet("font-size:14pt;background:transparent;border:none;")
        layout.addWidget(icon)
        self.text = QLabel("")
        self.text.setWordWrap(False)
        self.text.setMinimumHeight(32)
        self.text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.text.setStyleSheet("background:transparent;border:none;font-size:9.5pt;")
        layout.addWidget(self.text, 1)
        self.open_button = QPushButton("Practice")
        self.open_button.setObjectName("Secondary")
        self.open_button.setFixedHeight(32)
        self.open_button.clicked.connect(self._open)
        layout.addWidget(self.open_button)
        self.hide()

    def _open(self) -> None:
        if self._pack_id:
            self._on_open(self._pack_id)

    def set_suggestion(self, suggestion: dict[str, Any] | None) -> None:
        if not suggestion:
            self._pack_id = None
            self.hide()
            return
        self._pack_id = suggestion["pack_id"]
        progress = suggestion.get("progress", {})
        progress_text = ""
        if progress.get("total"):
            progress_text = (
                f" • {progress.get('completed', 0)}/{progress.get('total', 0)} complete"
            )
        self.text.setText(f"Optional exercise: {suggestion['title']}{progress_text}")
        self.text.setToolTip(suggestion.get("reason", ""))
        self.show()
        self.updateGeometry()
        if self.parentWidget() is not None:
            self.parentWidget().updateGeometry()


class ExercisePacksWidget(QWidget):
    packsChanged = Signal()

    def __init__(self, conn, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.conn = conn
        self.root = Path(root)
        self.current_pack: dict[str, Any] | None = None
        self.current_exercise: dict[str, Any] | None = None
        self.current_lesson_context: dict[str, Any] | None = None
        self.current_exercise_valid = False
        self.current_content_kind: str | None = None
        self.current_content_id: str | None = None
        self._building_lists = False

        exercise_packs.ensure_schema(self.conn)
        exercise_packs.ensure_bundled_packs(self.root, self.conn)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(10)

        self.course_toolbar = Card()
        self.course_toolbar.layout.setContentsMargins(10, 7, 10, 7)
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(8)
        self.breadcrumb_back = QPushButton("‹")
        self.breadcrumb_back.setObjectName("Secondary")
        self.breadcrumb_back.setFixedSize(34, 34)
        self.breadcrumb_back.setToolTip("Back to pack overview")
        self.breadcrumb_back.clicked.connect(self.show_pack_overview)
        toolbar_row.addWidget(self.breadcrumb_back)
        self.breadcrumb_root = QLabel("Exercises")
        self.breadcrumb_root.setStyleSheet("color:#b8c3d8;font-size:9.5pt;")
        toolbar_row.addWidget(self.breadcrumb_root)
        self.breadcrumb_pack = QLabel("›  Select a pack")
        self.breadcrumb_pack.setStyleSheet("color:#b8c3d8;font-size:9.5pt;")
        toolbar_row.addWidget(self.breadcrumb_pack)
        self.breadcrumb_page = QLabel("")
        self.breadcrumb_page.setStyleSheet("color:#dce4f3;font-size:9.5pt;")
        toolbar_row.addWidget(self.breadcrumb_page)
        toolbar_row.addStretch()
        self.pack_selector = QComboBox()
        self.pack_selector.setMinimumWidth(245)
        self.pack_selector.setToolTip("Switch installed exercise pack")
        self.pack_selector.currentIndexChanged.connect(self._pack_selector_changed)
        toolbar_row.addWidget(self.pack_selector)
        self.manage_packs_button = QPushButton("⋮")
        self.manage_packs_button.setObjectName("Secondary")
        self.manage_packs_button.setFixedSize(34, 34)
        self.manage_packs_button.setToolTip("Manage exercise packs")
        self.manage_packs_button.clicked.connect(self._show_manage_packs_menu)
        toolbar_row.addWidget(self.manage_packs_button)
        self.course_toolbar.layout.addLayout(toolbar_row)
        root.addWidget(self.course_toolbar)

        self.exercise_splitter = QSplitter(Qt.Horizontal)
        self.exercise_splitter.setChildrenCollapsible(False)

        self._settings = QSettings("DanjPastor", "Career Accelerator")

        self.library_card = Card()
        self.library_card.setMinimumWidth(330)
        margins = self.library_card.layout.contentsMargins()
        self._library_expanded_margins = (
            margins.left(),
            margins.top(),
            margins.right(),
            margins.bottom(),
        )
        self.library_header_widget = QWidget()
        self.library_header = QHBoxLayout(self.library_header_widget)
        self.library_header.setContentsMargins(0, 0, 0, 0)
        self.library_header.setSpacing(8)
        self.library_title = QLabel("Installed Packs")
        self.library_title.setObjectName("SectionTitle")
        self.library_title.setWordWrap(True)
        self.library_header.addWidget(self.library_title, 1)
        self.library_card.layout.addWidget(self.library_header_widget)

        self.library_body = QWidget()
        library_body_layout = QVBoxLayout(self.library_body)
        library_body_layout.setContentsMargins(0, 4, 0, 0)
        library_body_layout.setSpacing(8)
        self.pack_list = QListWidget()
        self.pack_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pack_list.setSpacing(4)
        self.pack_list.setAlternatingRowColors(False)
        self.pack_list.currentItemChanged.connect(self._pack_selected)
        self.pack_list.setMaximumHeight(86)
        library_body_layout.addWidget(self.pack_list)
        self.pack_summary = QLabel("Select a pack to view its contents.")
        self.pack_summary.setObjectName("Muted")
        self.pack_summary.setWordWrap(True)
        self.pack_summary.setTextFormat(Qt.RichText)
        self.pack_summary.setStyleSheet("padding:4px 2px;")
        library_body_layout.addWidget(self.pack_summary)
        self.pack_overview_button = QPushButton("▣  View Pack Overview")
        self.pack_overview_button.setObjectName("Secondary")
        self.pack_overview_button.clicked.connect(self.show_pack_overview)
        library_body_layout.addWidget(self.pack_overview_button)

        progress_heading = QLabel("PACK PROGRESS")
        progress_heading.setStyleSheet(
            "color:#aebbd1;font-size:8.5pt;font-weight:700;"
        )
        library_body_layout.addWidget(progress_heading)
        self.pack_progress_text = QLabel("0%")
        self.pack_progress_text.setStyleSheet("color:#f5f7fb;font-size:20pt;font-weight:700;")
        library_body_layout.addWidget(self.pack_progress_text)
        self.pack_progress = QProgressBar()
        self.pack_progress.setRange(0, 100)
        self.pack_progress.setValue(0)
        self.pack_progress.setFormat("")
        self.pack_progress.setTextVisible(False)
        self.pack_progress.setMaximumHeight(8)
        library_body_layout.addWidget(self.pack_progress)
        content_label = QLabel("LEARNING PATH")
        content_label.setStyleSheet("color:#aebbd1;font-size:8.5pt;font-weight:700;")
        library_body_layout.addWidget(content_label)
        self.content_list = QListWidget()
        self.content_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.content_list.setSpacing(3)
        self.content_list.setAlternatingRowColors(False)
        self.content_list.currentItemChanged.connect(self._content_selected)
        library_body_layout.addWidget(self.content_list, 3)
        self.library_card.layout.addWidget(self.library_body, 1)
        self.exercise_splitter.addWidget(self.library_card)

        self.workspace_status = QLabel("")
        self.workspace_status.hide()

        self.workspace_splitter = QSplitter(Qt.Horizontal)
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.setHandleWidth(5)

        self.learn_card = Card("Learn")
        self.learn_card.layout.setContentsMargins(8, 8, 8, 8)
        self.read_tab = QWidget()
        read_layout = QVBoxLayout(self.read_tab)
        read_layout.setContentsMargins(0, 0, 0, 0)
        self.read_view = CoursePageWidget()
        self.read_view.backRequested.connect(self.show_pack_overview)
        self.read_view.continueRequested.connect(self._continue_to_next_content)
        self.read_view.bookmarkToggled.connect(self._bookmark_current)
        self.read_view.overflowRequested.connect(self._show_page_menu)
        read_layout.addWidget(self.read_view)
        self.learn_card.layout.addWidget(self.read_tab, 1)

        self.practice_card = Card("Practice")
        self.practice_card.layout.setContentsMargins(8, 8, 8, 8)
        self.practice_tab = QWidget()
        practice_layout = QVBoxLayout(self.practice_tab)
        practice_layout.setContentsMargins(4, 4, 4, 4)
        practice_layout.setSpacing(8)
        self.practice_title = QLabel("Your SQL")
        self.practice_title.setObjectName("SectionTitle")
        practice_layout.addWidget(self.practice_title)
        self.practice_intro = QLabel(
            "Build the smallest query first, run it often, and use Check Answer only when the output shape looks right."
        )
        self.practice_intro.setObjectName("Muted")
        self.practice_intro.setWordWrap(True)
        practice_layout.addWidget(self.practice_intro)
        self.sql_editor = QTextEdit()
        self.sql_editor.setPlaceholderText("Write one read-only SELECT or WITH query here.")
        self.sql_editor.setAcceptRichText(False)
        self.sql_editor.setLineWrapMode(QTextEdit.NoWrap)
        code_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        code_font.setPointSize(10)
        self.sql_editor.setFont(code_font)
        self.sql_editor.setTabStopDistance(28)
        self.sql_editor.setStyleSheet(
            f"QTextEdit {{background:#111321;color:#f3f4ff;"
            f"border:1px solid {COLORS.get('border', '#3b3e5b')};"
            "border-radius:9px;padding:10px;selection-background-color:#6747c7;}"
            f"QTextEdit:focus {{border:1px solid {COLORS.get('purple', '#8b5cf6')};}}"
        )
        self.sql_editor.textChanged.connect(self._answer_edited)
        practice_layout.addWidget(self.sql_editor, 2)

        action_row = QHBoxLayout()
        self.run_button = QPushButton("▶ Run Query")
        self.run_button.setObjectName("Secondary")
        self.run_button.clicked.connect(self.run_query)
        self.check_button = QPushButton("✓ Check Answer")
        self.check_button.setObjectName("Primary")
        self.check_button.clicked.connect(self.check_answer)
        self.hint_button = QPushButton("💡 Show Hint")
        self.hint_button.setObjectName("Secondary")
        self.hint_button.clicked.connect(self.show_next_hint)
        self.solution_button = QPushButton("View Solution")
        self.solution_button.setObjectName("Secondary")
        self.solution_button.clicked.connect(self.show_solution)
        action_row.addWidget(self.run_button)
        action_row.addWidget(self.check_button)
        action_row.addWidget(self.hint_button)
        action_row.addWidget(self.solution_button)
        action_row.addStretch()
        practice_layout.addLayout(action_row)

        self.feedback = FeedbackLabel()
        practice_layout.addWidget(self.feedback)

        self.result_table = QTableWidget()
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setShowGrid(False)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setStyleSheet(
            f"QTableWidget {{background:{COLORS.get('surface_alt', '#191a2c')};"
            f"alternate-background-color:#202238;color:{COLORS.get('text', '#f4f4fb')};"
            f"border:1px solid {COLORS.get('border', '#373955')};border-radius:8px;}}"
            "QHeaderView::section {background:#292b47;color:#f4f4fb;"
            "padding:7px;border:none;border-right:1px solid #3a3d5e;font-weight:600;}"
        )
        practice_layout.addWidget(self.result_table, 2)

        notes_label = QLabel("Notes")
        notes_label.setObjectName("SectionTitle")
        practice_layout.addWidget(notes_label)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Write what the inner query returns, what the outer query does, and anything that confused you."
        )
        self.notes.setMaximumHeight(105)
        self.notes.setStyleSheet(
            f"QTextEdit {{background:{COLORS.get('surface_alt', '#191a2c')};"
            f"border:1px solid {COLORS.get('border', '#373955')};"
            "border-radius:8px;padding:7px;}"
            f"QTextEdit:focus {{border:1px solid {COLORS.get('purple', '#8b5cf6')};}}"
        )
        practice_layout.addWidget(self.notes)

        save_row = QHBoxLayout()
        self.save_button = QPushButton("Save Progress")
        self.save_button.setObjectName("Secondary")
        self.save_button.clicked.connect(self.save_current_progress)
        self.complete_button = QPushButton("Mark Complete")
        self.complete_button.setObjectName("Primary")
        self.complete_button.clicked.connect(self.complete_current_exercise)
        save_row.addStretch()
        save_row.addWidget(self.save_button)
        save_row.addWidget(self.complete_button)
        practice_layout.addLayout(save_row)
        self.practice_card.layout.addWidget(self.practice_tab, 1)

        self.workspace_splitter.addWidget(self.learn_card)
        self.workspace_splitter.addWidget(self.practice_card)
        self.workspace_splitter.setStretchFactor(0, 47)
        self.workspace_splitter.setStretchFactor(1, 53)
        self.workspace_splitter.setSizes([470, 530])

        self.exercise_splitter.addWidget(self.workspace_splitter)
        self.exercise_splitter.setStretchFactor(0, 1)
        self.exercise_splitter.setStretchFactor(1, 3)
        root.addWidget(self.exercise_splitter, 1)

        self.library_card.setMinimumWidth(330)
        self.library_card.setMaximumWidth(430)
        self.exercise_splitter.setSizes([350, 1050])
        self._set_practice_enabled(False)

    def _set_course_markdown(
        self,
        view: CoursePageWidget,
        markdown: str,
        *,
        eyebrow: str,
        subtitle: str | None = None,
    ) -> None:
        bookmark_key = self._bookmark_key()
        bookmarked = bool(
            bookmark_key and self._settings.value(bookmark_key, False, type=bool)
        )
        view.set_markdown(
            markdown,
            eyebrow=eyebrow,
            subtitle=subtitle,
            bookmarked=bookmarked,
        )

    def _pack_selector_changed(self, index: int) -> None:
        if self._building_lists or index < 0:
            return
        pack_id = self.pack_selector.itemData(index)
        if pack_id:
            self.select_pack(str(pack_id))

    def _show_manage_packs_menu(self) -> None:
        menu = QMenu(self)
        install_zip_action = menu.addAction("Install Exercise Pack…")
        install_folder_action = menu.addAction("Install Folder…")
        menu.addSeparator()
        open_folder_action = menu.addAction("Open Packs Folder")
        chosen = menu.exec(
            self.manage_packs_button.mapToGlobal(
                self.manage_packs_button.rect().bottomLeft()
            )
        )
        if chosen == install_zip_action:
            self.install_zip()
        elif chosen == install_folder_action:
            self.install_folder()
        elif chosen == open_folder_action:
            self.open_packs_folder()

    def _bookmark_key(self) -> str | None:
        if not self.current_pack or not self.current_content_kind or not self.current_content_id:
            return None
        return (
            f"exercise_packs/bookmarks/{self.current_pack['pack_id']}/"
            f"{self.current_content_kind}/{self.current_content_id}"
        )

    def _bookmark_current(self, bookmarked: bool) -> None:
        key = self._bookmark_key()
        if key:
            self._settings.setValue(key, bool(bookmarked))

    def _show_page_menu(self) -> None:
        menu = QMenu(self)
        overview_action = menu.addAction("View Pack Overview")
        open_folder_action = menu.addAction("Open Pack Folder")
        reset_action = None
        if self.current_exercise:
            menu.addSeparator()
            reset_action = menu.addAction("Reset Current Exercise")
        chosen = menu.exec(self.read_view.mapToGlobal(self.read_view.rect().topRight()))
        if chosen == overview_action:
            self.show_pack_overview()
        elif chosen == open_folder_action and self.current_pack:
            path = Path(self.current_pack["path"])
            try:
                if sys.platform.startswith("win"):
                    os.startfile(path)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(path)])
                else:
                    subprocess.Popen(["xdg-open", str(path)])
            except OSError as exc:
                QMessageBox.warning(self, "Open Pack", str(exc))
        elif reset_action is not None and chosen == reset_action and self.current_exercise:
            answer = QMessageBox.question(
                self,
                "Reset Exercise",
                "Clear the saved SQL, notes, and completion state for this exercise?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                exercise_packs.save_progress(
                    self.conn,
                    self.current_exercise["pack_id"],
                    self.current_exercise["id"],
                    status="Not Started",
                    answer_sql="",
                    notes="",
                )
                self._show_exercise(self.current_exercise["id"])
                self.packsChanged.emit()

    def _ordered_content(self) -> list[tuple[str, str, str]]:
        if not self.current_pack:
            return []
        ordered: list[tuple[str, str, str]] = []
        ordered.extend(
            ("lesson", item["id"], item["title"])
            for item in self.current_pack.get("lessons", [])
        )
        ordered.extend(
            ("exercise", item["id"], item["title"])
            for item in self.current_pack.get("exercises", [])
        )
        return ordered

    def _next_content_title(self, kind: str, content_id: str) -> str | None:
        ordered = self._ordered_content()
        for index, item in enumerate(ordered):
            if item[0] == kind and item[1] == content_id:
                return ordered[index + 1][2] if index + 1 < len(ordered) else None
        return None

    def _continue_to_next_content(self) -> None:
        ordered = self._ordered_content()
        if self.current_content_kind == "overview" and ordered:
            next_kind, next_id, _ = ordered[0]
            self._select_content(next_kind, next_id)
            return
        for index, item in enumerate(ordered):
            if item[0] == self.current_content_kind and item[1] == self.current_content_id:
                if index + 1 < len(ordered):
                    next_kind, next_id, _ = ordered[index + 1]
                    self._select_content(next_kind, next_id)
                return

    def show_pack_overview(self) -> None:
        if not self.current_pack:
            return
        if self.current_content_kind == "lesson":
            self._save_lesson_sandbox()
        self.current_exercise = None
        self.current_lesson_context = None
        self.current_exercise_valid = False
        self.current_content_kind = "overview"
        self.current_content_id = self.current_pack["pack_id"]
        self.breadcrumb_page.setText("›  Pack Overview")
        lessons = self.current_pack.get("lessons", [])
        exercises = self.current_pack.get("exercises", [])
        concepts = ", ".join(self.current_pack.get("concepts", [])) or "SQL practice"
        markdown = (
            f"# {self.current_pack['title']}\n\n"
            f"> **Learning path:** {self.current_pack.get('description', '')}\n\n"
            "## What you will learn\n"
            f"{concepts}\n\n"
            "## Course structure\n"
            f"- {len(lessons)} guided lessons\n"
            f"- {len(exercises)} checked practice exercises\n"
            f"- Approximately {self.current_pack.get('estimated_minutes', 0)} minutes\n\n"
            "## How to use this pack\n"
            "1. Read each lesson and explain the examples in your own words.\n"
            "2. Complete the practice query without opening the solution first.\n"
            "3. Use hints progressively and record what changed your understanding.\n"
            "4. Revisit completed exercises until the query shape feels predictable.\n"
        )
        self._set_course_markdown(
            self.read_view,
            markdown,
            eyebrow="COURSE",
            subtitle=f"{len(lessons)} lessons • {len(exercises)} exercises",
        )
        first_title = (
            lessons[0]["title"]
            if lessons
            else (exercises[0]["title"] if exercises else None)
        )
        self.read_view.set_navigation(
            next_title=first_title,
            show_back=False,
            continue_text="Start Course  →",
        )
        self.practice_title.setText("Practice")
        self.practice_intro.setText(
            "Start the course or choose a guided exercise from the learning path. "
            "Lesson pages include a runnable sandbox; exercises add checking, hints, and solutions."
        )
        self.sql_editor.clear()
        self.notes.clear()
        self.feedback.setText("")
        self._set_workspace_focus(0)
        self._set_practice_enabled(False)

    def _update_hint_button(self) -> None:
        hints = self.current_exercise.get("hints", []) if self.current_exercise else []
        if not hints:
            self.hint_button.setText("💡 No Hints")
            self.hint_button.setEnabled(False)
            return
        self.hint_button.setEnabled(True)
        index = min(getattr(self, "_hint_index", 0), len(hints))
        if index >= len(hints):
            self.hint_button.setText(f"💡 Review Hint {len(hints)}/{len(hints)}")
        else:
            self.hint_button.setText(f"💡 Show Hint {index + 1}/{len(hints)}")

    def _set_workspace_focus(self, tab_index: int) -> None:
        """Keep both cards visible while directing keyboard focus appropriately."""
        if tab_index <= 0:
            self.read_view.setFocus()
        else:
            self.sql_editor.setFocus()

    def _set_practice_enabled(self, enabled: bool) -> None:
        for widget in (
            self.sql_editor,
            self.run_button,
            self.check_button,
            self.hint_button,
            self.solution_button,
            self.notes,
            self.save_button,
            self.complete_button,
        ):
            widget.setEnabled(enabled)
        if enabled:
            self._update_hint_button()
        if not enabled:
            self.hint_button.setText("💡 Show Hint")
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)

    def _restore_exercise_practice_labels(self) -> None:
        self.practice_title.setText("Your SQL")
        self.practice_intro.setText(
            "Build the smallest query first, run it often, and use Check Answer "
            "only when the output shape looks right."
        )
        self.run_button.setText("▶ Run Query")
        self.run_button.setToolTip("")
        self.check_button.setToolTip("")
        self.hint_button.setToolTip("")
        self.solution_button.setToolTip("")
        self.save_button.setToolTip("")
        self.complete_button.setToolTip("")

    def _lesson_sandbox_key(self, field: str) -> str | None:
        if (
            not self.current_pack
            or self.current_content_kind != "lesson"
            or not self.current_content_id
        ):
            return None
        return (
            f"exercise_packs/lesson_sandbox/{self.current_pack['pack_id']}/"
            f"{self.current_content_id}/{field}"
        )

    @staticmethod
    def _first_sql_code_block(markdown: str) -> str:
        match = re.search(
            r"```(?:sql|duckdb|sqlite)\s*\n(.*?)```",
            markdown,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1).strip() if match else ""

    def _build_lesson_sandbox_context(self) -> dict[str, Any] | None:
        """Load a safe union of the pack datasets for lesson experimentation."""
        if not self.current_pack:
            return None
        datasets_by_table: dict[str, dict[str, Any]] = {}
        for entry in self.current_pack.get("exercises", []):
            exercise_id = entry.get("id")
            if not exercise_id:
                continue
            try:
                exercise = exercise_packs.load_exercise(self.current_pack, exercise_id)
            except exercise_packs.ExercisePackError:
                continue
            for dataset in exercise.get("datasets", []):
                table = str(dataset.get("table", "")).strip()
                if table and table not in datasets_by_table:
                    datasets_by_table[table] = dataset
        if not datasets_by_table:
            return None
        return {
            "pack_path": self.current_pack["path"],
            "datasets": list(datasets_by_table.values()),
        }

    def _save_lesson_sandbox(self) -> None:
        sql_key = self._lesson_sandbox_key("sql")
        notes_key = self._lesson_sandbox_key("notes")
        if sql_key:
            self._settings.setValue(sql_key, self.sql_editor.toPlainText())
        if notes_key:
            self._settings.setValue(notes_key, self.notes.toPlainText())

    def _set_lesson_practice(self, markdown: str) -> None:
        self.current_lesson_context = self._build_lesson_sandbox_context()
        self.practice_title.setText("Lesson Sandbox")
        if self.current_lesson_context:
            self.practice_intro.setText(
                "Try the lesson example or write your own read-only query. Run Query "
                "uses this pack's practice tables; checked answers begin in the guided exercises."
            )
        else:
            self.practice_intro.setText(
                "Use this space as a SQL scratchpad. This lesson has no runnable dataset; "
                "checked answers begin in the guided exercises."
            )
        sql_key = self._lesson_sandbox_key("sql")
        notes_key = self._lesson_sandbox_key("notes")
        saved_sql = self._settings.value(sql_key, "", type=str) if sql_key else ""
        saved_notes = self._settings.value(notes_key, "", type=str) if notes_key else ""
        starter_sql = saved_sql or self._first_sql_code_block(markdown)
        self.sql_editor.blockSignals(True)
        self.sql_editor.setPlainText(starter_sql)
        self.sql_editor.blockSignals(False)
        self.notes.setPlainText(saved_notes)
        self.feedback.setText(
            "Lesson sandbox ready. Edit and run the example here; select a guided "
            "exercise when you are ready for answer checking."
        )
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.sql_editor.setEnabled(True)
        self.run_button.setEnabled(bool(self.current_lesson_context))
        self.run_button.setText("▶ Run Query")
        self.run_button.setToolTip(
            "Run this read-only query against the pack datasets."
            if self.current_lesson_context
            else "This lesson does not include a runnable dataset."
        )
        self.notes.setEnabled(True)
        self.save_button.setEnabled(True)
        for widget in (
            self.check_button,
            self.hint_button,
            self.solution_button,
            self.complete_button,
        ):
            widget.setEnabled(False)
        self.check_button.setToolTip("Answer checking is available in guided exercises.")
        self.hint_button.setText("💡 Exercise Hints")
        self.hint_button.setToolTip("Hints are available in guided exercises.")
        self.solution_button.setToolTip("Solutions are available in guided exercises.")
        self.complete_button.setToolTip("Complete the checked exercises to advance pack progress.")

    def refresh(self) -> None:
        previous_pack = self.current_pack.get("pack_id") if self.current_pack else None
        self._building_lists = True
        self.pack_list.clear()
        packs = exercise_packs.list_installed_packs(self.root, self.conn)
        row_to_select = None
        for row, pack in enumerate(packs):
            progress = pack.get("progress", {})
            item = QListWidgetItem(
                f"🧩  {pack['title']}\n"
                f"     {progress.get('completed', 0)}/{progress.get('total', 0)} exercises • "
                f"{progress.get('percent', 0)}% complete • v{pack['version']}"
            )
            item.setSizeHint(QSize(0, 58))
            item.setData(Qt.ItemDataRole.UserRole, pack["pack_id"])
            item.setToolTip(pack.get("description", ""))
            self.pack_list.addItem(item)
            if pack["pack_id"] == previous_pack:
                row_to_select = row
        self.pack_list.setVisible(len(packs) > 1)
        self.pack_selector.blockSignals(True)
        self.pack_selector.clear()
        selector_row = None
        for row, pack in enumerate(packs):
            self.pack_selector.addItem(f"▤  {pack['title']}", pack["pack_id"])
            if pack["pack_id"] == previous_pack:
                selector_row = row
        if self.pack_selector.count():
            self.pack_selector.setCurrentIndex(
                selector_row if selector_row is not None else 0
            )
        self.pack_selector.blockSignals(False)
        self._building_lists = False
        if self.pack_list.count() == 0:
            self.current_pack = None
            self.content_list.clear()
            self.pack_summary.setText(
                "No exercise packs are installed. Use Install Exercise Pack to add one."
            )
            self.pack_progress.setValue(0)
            self.pack_progress_text.setText("0%")
            self._clear_workspace()
            return
        self.pack_list.setCurrentRow(row_to_select if row_to_select is not None else 0)

    def select_pack(self, pack_id: str, exercise_id: str | None = None) -> None:
        for row in range(self.pack_list.count()):
            item = self.pack_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == pack_id:
                self.pack_list.setCurrentRow(row)
                if exercise_id:
                    self._select_content("exercise", exercise_id)
                elif self.current_pack:
                    progress = self.current_pack.get("progress", {})
                    any_started = any(
                        exercise_packs.progress_for(
                            self.conn, self.current_pack["pack_id"], item["id"]
                        )["status"]
                        != "Not Started"
                        for item in self.current_pack.get("exercises", [])
                    )
                    if progress.get("completed", 0) == 0 and not any_started:
                        return
                    next_id = progress.get("next_id")
                    if next_id:
                        self._select_content("exercise", next_id)
                return

    def _select_content(self, kind: str, content_id: str) -> None:
        """Select and load content even when its row is already highlighted.

        QListWidget only emits currentItemChanged when the row actually changes.
        Pack Overview intentionally leaves the first learning-path row selected, so
        Start Course previously selected that same row without rebuilding Learn.
        Explicitly dispatching the current row keeps navigation and Practice state
        synchronized in both same-row and different-row cases.
        """
        for row in range(self.content_list.count()):
            item = self.content_list.item(row)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") != kind or data.get("id") != content_id:
                continue
            if self.content_list.currentRow() != row:
                self.content_list.setCurrentRow(row)
            else:
                self._content_selected(item, item)
            return

    def _pack_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if self._building_lists or current is None:
            return
        pack_id = current.data(Qt.ItemDataRole.UserRole)
        try:
            self.current_pack = exercise_packs.get_pack(self.root, self.conn, pack_id)
        except exercise_packs.ExercisePackError as exc:
            QMessageBox.warning(self, "Exercise Pack Error", str(exc))
            return
        pack = self.current_pack
        progress = pack["progress"]
        self.library_title.setText(pack["title"])
        self.breadcrumb_pack.setText(f"›  {pack['title']}")
        selector_index = self.pack_selector.findData(pack_id)
        if selector_index >= 0 and selector_index != self.pack_selector.currentIndex():
            self.pack_selector.blockSignals(True)
            self.pack_selector.setCurrentIndex(selector_index)
            self.pack_selector.blockSignals(False)
        lesson_count = len(pack.get("lessons", []))
        exercise_count = len(pack.get("exercises", []))
        self.library_title.setText(f"▤  {pack['title']}")
        self.pack_summary.setText(
            f"{lesson_count} lessons • {exercise_count} exercises"
        )
        self.pack_progress.setValue(progress.get("percent", 0))
        self.pack_progress_text.setText(f"{progress.get('percent', 0)}%")
        self.content_list.blockSignals(True)
        self.content_list.clear()
        lessons = pack.get("lessons", [])
        for number, lesson in enumerate(lessons, start=1):
            item = QListWidgetItem(f"●  {lesson['title']}")
            item.setSizeHint(QSize(0, 44))
            item.setData(
                Qt.ItemDataRole.UserRole, {"kind": "lesson", "id": lesson["id"]}
            )
            self.content_list.addItem(item)
        any_started = False
        for number, exercise in enumerate(pack.get("exercises", []), start=1):
            saved = exercise_packs.progress_for(
                self.conn, pack["pack_id"], exercise["id"]
            )
            any_started = any_started or saved["status"] != "Not Started"
            icon = (
                "✅"
                if saved["status"] == "Completed"
                else ("◐" if saved["status"] == "In Progress" else "○")
            )
            item = QListWidgetItem(
                f"{icon}  {exercise['title']}"
            )
            item.setSizeHint(QSize(0, 44))
            item.setToolTip(
                f"{exercise.get('difficulty', 'Mixed')} • "
                f"{exercise.get('estimated_minutes', 0)} minutes"
            )
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"kind": "exercise", "id": exercise["id"]},
            )
            self.content_list.addItem(item)
        self.content_list.blockSignals(False)
        next_id = progress.get("next_id")
        if lessons and progress.get("completed", 0) == 0 and not any_started:
            self.content_list.setCurrentRow(0)
        elif next_id:
            self._select_content("exercise", next_id)
        elif self.content_list.count():
            self.content_list.setCurrentRow(0)

    def _content_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None or not self.current_pack:
            return
        if self.current_content_kind == "lesson":
            self._save_lesson_sandbox()
        data = current.data(Qt.ItemDataRole.UserRole) or {}
        if data.get("kind") == "lesson":
            self._show_lesson(data["id"])
        elif data.get("kind") == "exercise":
            self._show_exercise(data["id"])

    def _show_lesson(self, lesson_id: str) -> None:
        try:
            markdown = exercise_packs.load_lesson(self.current_pack, lesson_id)
        except exercise_packs.ExercisePackError as exc:
            QMessageBox.warning(self, "Lesson Error", str(exc))
            return
        self.current_exercise = None
        self.current_lesson_context = None
        self.current_exercise_valid = False
        self.current_content_kind = "lesson"
        self.current_content_id = lesson_id
        lesson_title = next(
            (item.get("title") for item in self.current_pack.get("lessons", []) if item.get("id") == lesson_id),
            "Lesson",
        )
        self.breadcrumb_page.setText(f"›  {lesson_title}")
        lesson_entry = next(
            (entry for entry in self.current_pack.get("lessons", []) if entry.get("id") == lesson_id),
            {},
        )
        self._set_course_markdown(
            self.read_view,
            markdown,
            eyebrow="LESSON",
            subtitle=lesson_entry.get("subtitle"),
        )
        self.read_view.set_navigation(
            next_title=self._next_content_title("lesson", lesson_id),
            show_back=True,
        )
        self._set_lesson_practice(markdown)
        self._set_workspace_focus(0)

    def _show_exercise(self, exercise_id: str) -> None:
        try:
            exercise = exercise_packs.load_exercise(self.current_pack, exercise_id)
        except exercise_packs.ExercisePackError as exc:
            QMessageBox.warning(self, "Exercise Error", str(exc))
            return
        self.current_exercise = exercise
        self.current_lesson_context = None
        self.current_exercise_valid = False
        self.current_content_kind = "exercise"
        self.current_content_id = exercise_id
        self.breadcrumb_page.setText(f"›  {exercise['title']}")
        saved = exercise_packs.progress_for(
            self.conn, exercise["pack_id"], exercise["id"]
        )
        concepts = ", ".join(exercise.get("concepts", []))
        why = exercise.get("why", "")
        explanation = exercise.get("explanation", "")
        takeaways = exercise.get("takeaways", [])
        learning_objective = exercise.get("learning_objective", "")
        recommended_lesson = exercise.get("recommended_lesson", "")
        expected_result = exercise.get("expected_result", "")
        build_steps = exercise.get("build_steps", [])
        common_mistakes = exercise.get("common_mistakes", [])
        reflection_questions = exercise.get("reflection_questions", [])
        stretch_goal = exercise.get("stretch_goal", "")

        stage = exercise.get("stage", "Practice exercise")
        markdown = (
            f"# {exercise['title']}\n\n"
            f"**Concepts:** {concepts}\n\n"
        )
        if learning_objective:
            markdown += f"## 🎯 Learning goal\n{learning_objective}\n\n"
        if recommended_lesson:
            markdown += f"> **Read first:** {recommended_lesson}\n\n"
        markdown += f"## Why this matters\n{why}\n\n"

        try:
            datasets = exercise_packs.describe_datasets(exercise)
        except exercise_packs.ExercisePackError:
            datasets = []
        if datasets:
            markdown += "## Available data\n\n| Table | Rows | Columns |\n|---|---:|---|\n"
            for dataset in datasets:
                columns = ", ".join(f"`{item}`" for item in dataset["columns"])
                markdown += (
                    f"| `{dataset['table']}` | {dataset['row_count']} | {columns} |\n"
                )
            markdown += "\n"

        markdown += f"## 📋 Your task\n> {exercise['prompt']}\n\n"
        if expected_result:
            markdown += f"### Expected output shape\n{expected_result}\n\n"
        if build_steps:
            markdown += "## Build it in small steps\n" + "\n".join(
                f"{index}. {item}" for index, item in enumerate(build_steps, start=1)
            ) + "\n\n"
        markdown += f"## How to think about it\n{explanation}\n"
        if common_mistakes:
            markdown += "\n## ⚠ Common mistakes\n" + "\n".join(
                f"- {item}" for item in common_mistakes
            ) + "\n"
        if takeaways:
            markdown += "\n## Remember\n" + "\n".join(
                f"- {item}" for item in takeaways
            ) + "\n"
        if reflection_questions:
            markdown += "\n## Check your understanding\n" + "\n".join(
                f"- {item}" for item in reflection_questions
            ) + "\n"
        if stretch_goal:
            markdown += f"\n## ⭐ Optional stretch\n{stretch_goal}\n"

        self._set_course_markdown(
            self.read_view,
            markdown,
            eyebrow="GUIDED EXERCISE",
            subtitle=exercise.get("subtitle") or stage,
        )
        self.read_view.set_navigation(
            next_title=self._next_content_title("exercise", exercise_id),
            show_back=True,
            continue_text="Next  →",
        )
        self._restore_exercise_practice_labels()
        self.workspace_status.setText(
            f"{saved['status']} • {exercise.get('stage', 'Practice exercise')} • "
            f"{exercise.get('difficulty', 'Mixed')} • "
            f"{exercise.get('estimated_minutes', 0)} minutes"
        )
        self.sql_editor.blockSignals(True)
        self.sql_editor.setPlainText(saved.get("answer_sql") or exercise["starter_sql"])
        self.sql_editor.blockSignals(False)
        self.notes.setPlainText(saved.get("notes", ""))
        self.feedback.setText("")
        self._hint_index = 0
        self._set_practice_enabled(True)
        self._update_hint_button()
        self.complete_button.setEnabled(saved["status"] == "Completed")
        self._set_workspace_focus(1)
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)

    def _answer_edited(self) -> None:
        self.current_exercise_valid = False
        if self.current_exercise:
            self.complete_button.setEnabled(False)

    def _display_result(self, result: dict[str, Any]) -> None:
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        self.result_table.clear()
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        self.result_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem("NULL" if value is None else str(value))
                self.result_table.setItem(row_index, column_index, item)
        self.result_table.resizeColumnsToContents()

    def run_query(self) -> None:
        query_context = self.current_exercise or self.current_lesson_context
        if not query_context:
            self.feedback.setText("This page does not include a runnable dataset.")
            return
        try:
            result = exercise_packs.execute_query(
                query_context, self.sql_editor.toPlainText()
            )
        except exercise_packs.ExercisePackError as exc:
            self.feedback.setText(f"❌ {exc}")
            return
        self._display_result(result)
        self.feedback.setText(
            f"Query ran successfully: {len(result['rows'])} row(s) returned."
        )
        if self.current_exercise:
            self._save_as_in_progress()
        else:
            self._save_lesson_sandbox()

    def check_answer(self) -> None:
        if not self.current_exercise:
            return
        try:
            result = exercise_packs.check_answer(
                self.current_exercise, self.sql_editor.toPlainText()
            )
        except exercise_packs.ExercisePackError as exc:
            self.feedback.setText(f"❌ {exc}")
            return
        self._display_result(result["user"])
        if result["correct"]:
            self.current_exercise_valid = True
            self.complete_button.setEnabled(True)
            self.feedback.setText(
                "✅ Correct. Your query returns the expected columns and rows "
                "and uses the requested SQL pattern. Mark the exercise complete "
                "when you are ready."
            )
            self._save_as_in_progress()
            return

        self.current_exercise_valid = False
        self.complete_button.setEnabled(False)
        details: list[str] = []
        if not result["columns_match"]:
            actual = ", ".join(result["user"].get("columns", [])) or "none"
            expected = ", ".join(result["expected"].get("columns", [])) or "none"
            details.append(f"expected columns [{expected}], but received [{actual}]")
        if not result["rows_match"]:
            actual_count = len(result["user"].get("rows", []))
            expected_count = len(result["expected"].get("rows", []))
            if actual_count != expected_count:
                details.append(
                    f"expected {expected_count} row(s), but received {actual_count}"
                )
            else:
                details.append(
                    "the row count is right, but one or more returned values differ"
                )
        if not result.get("style_match", True):
            missing = result.get("missing_keywords", [])
            required_any = result.get("required_any_keywords", [])
            if missing:
                details.append(
                    "the learning goal requires using " + ", ".join(missing)
                )
            if required_any:
                details.append(
                    "use at least one of these SQL patterns: "
                    + ", ".join(required_any)
                )
            forbidden = result.get("forbidden_keywords", [])
            if forbidden:
                details.append("avoid " + ", ".join(forbidden) + " for this exercise")
            if not result.get("select_count_match", True):
                details.append(
                    f"this nested exercise needs at least {result.get('minimum_select_count', 2)} "
                    f"SELECT statements, but {result.get('actual_select_count', 0)} were found"
                )
        self.feedback.setText(
            "Not quite yet: " + "; ".join(details) + ". "
            "Run the smallest inner query by itself and compare its output shape "
            "with the Learn card."
        )

    def show_next_hint(self) -> None:
        if not self.current_exercise:
            return
        hints = self.current_exercise.get("hints", [])
        if not hints:
            self.feedback.setText("This exercise does not include hints.")
            return
        index = min(getattr(self, "_hint_index", 0), len(hints) - 1)
        self.feedback.setText(f"💡 Hint {index + 1}/{len(hints)}: {hints[index]}")
        self._hint_index = min(index + 1, len(hints))
        self._update_hint_button()

    def show_solution(self) -> None:
        if not self.current_exercise:
            return
        confirmation = QMessageBox.question(
            self,
            "Show Solution",
            "Open the full solution? Try the progressive hints first when possible. "
            "Your current SQL will not be replaced unless you choose Copy to Editor.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        try:
            solution_path = exercise_packs._safe_relative(
                Path(self.current_exercise["pack_path"]),
                self.current_exercise["solution_file"],
            )
            solution = solution_path.read_text(encoding="utf-8")
        except exercise_packs.ExercisePackError as exc:
            self.feedback.setText(f"❌ {exc}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Solution Walkthrough • {self.current_exercise['title']}")
        dialog.resize(820, 700)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        solution_view = CoursePageWidget()
        explanation = self.current_exercise.get(
            "solution_explanation",
            "Read the solution from the innermost query outward. Identify the shape returned by each stage before reading the next stage.",
        )
        walkthrough = self.current_exercise.get("solution_walkthrough", [])
        solution_markdown = f"# Solution Walkthrough\n\n{explanation}\n\n"
        if walkthrough:
            solution_markdown += "## How the query works\n" + "\n".join(
                f"{index}. {item}" for index, item in enumerate(walkthrough, start=1)
            ) + "\n\n"
        solution_markdown += f"## Official query\n```sql\n{solution.strip()}\n```\n\n"
        solution_markdown += (
            "> **Do not memorize the query.** Identify what every SELECT returns "
            "and how the next stage uses that result."
        )
        self._set_course_markdown(
            solution_view,
            solution_markdown,
            eyebrow="SOLUTION WALKTHROUGH",
            subtitle="Compare the reasoning, not only the final query",
        )
        layout.addWidget(solution_view, 1)
        button_row = QHBoxLayout()
        copy_button = QPushButton("Copy to Editor")
        copy_button.setObjectName("Primary")
        close_button = QPushButton("Close")
        close_button.setObjectName("Secondary")
        button_row.addStretch()
        button_row.addWidget(copy_button)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

        def copy_solution() -> None:
            self.sql_editor.setPlainText(solution)
            self.feedback.setText(
                "Solution copied to the editor. Read it from the innermost query outward, "
                "then run it and explain each stage in your notes."
            )
            dialog.accept()

        copy_button.clicked.connect(copy_solution)
        close_button.clicked.connect(dialog.reject)
        dialog.exec()

    def _save_as_in_progress(self) -> None:
        if not self.current_exercise:
            return
        current = exercise_packs.progress_for(
            self.conn,
            self.current_exercise["pack_id"],
            self.current_exercise["id"],
        )
        status = "Completed" if current["status"] == "Completed" else "In Progress"
        exercise_packs.save_progress(
            self.conn,
            self.current_exercise["pack_id"],
            self.current_exercise["id"],
            status=status,
            answer_sql=self.sql_editor.toPlainText(),
            notes=self.notes.toPlainText(),
        )

    def save_current_progress(self) -> None:
        if self.current_exercise:
            self._save_as_in_progress()
            self.feedback.setText("Progress saved.")
            self._refresh_current_pack_preserving_exercise()
            return
        if self.current_content_kind == "lesson":
            self._save_lesson_sandbox()
            self.feedback.setText("Lesson sandbox saved.")

    def complete_current_exercise(self) -> None:
        if not self.current_exercise:
            return
        current = exercise_packs.progress_for(
            self.conn,
            self.current_exercise["pack_id"],
            self.current_exercise["id"],
        )
        if not self.current_exercise_valid and current["status"] != "Completed":
            self.feedback.setText("Check the answer successfully before marking it complete.")
            return
        exercise_packs.save_progress(
            self.conn,
            self.current_exercise["pack_id"],
            self.current_exercise["id"],
            status="Completed",
            answer_sql=self.sql_editor.toPlainText(),
            notes=self.notes.toPlainText(),
        )
        self.feedback.setText("✅ Exercise completed. The next exercise is now ready.")
        self.packsChanged.emit()
        self._refresh_current_pack_preserving_exercise(select_next=True)

    def _refresh_current_pack_preserving_exercise(self, select_next: bool = False) -> None:
        pack_id = self.current_pack["pack_id"] if self.current_pack else None
        exercise_id = self.current_exercise["id"] if self.current_exercise else None
        self.refresh()
        if pack_id:
            self.select_pack(pack_id, None if select_next else exercise_id)

    def _clear_workspace(self) -> None:
        self.current_exercise = None
        self.current_lesson_context = None
        self.read_view.clear()
        self.sql_editor.clear()
        self.notes.clear()
        self.feedback.clear()
        self.workspace_status.setText("Choose a lesson or exercise from the left.")
        self._set_practice_enabled(False)

    def install_zip(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Install Exercise Pack",
            str(Path.home()),
            "Exercise Packs (*.zip);;All Files (*)",
        )
        if path:
            self._install(Path(path))

    def install_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Install Exercise Pack Folder", str(Path.home())
        )
        if path:
            self._install(Path(path))

    def _install(self, path: Path) -> None:
        try:
            manifest = exercise_packs.install_pack(path, self.root, self.conn)
        except exercise_packs.ExercisePackError as exc:
            QMessageBox.warning(self, "Exercise Pack Not Installed", str(exc))
            return
        self.refresh()
        self.select_pack(manifest["pack_id"])
        self.packsChanged.emit()
        QMessageBox.information(
            self,
            "Exercise Pack Installed",
            f"{manifest['title']} v{manifest['version']} is ready in Learning → Exercises.",
        )

    def open_packs_folder(self) -> None:
        path = exercise_packs.installed_root(self.root)
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as exc:
            QMessageBox.warning(self, "Could Not Open Folder", str(exc))
