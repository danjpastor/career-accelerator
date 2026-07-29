"""Integrated guided workspace for Career Accelerator Python exercises."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QFontDatabase, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.data.python_exercises import PYTHON_EXERCISES
from career_app.services import python_exercise_runner as runner
from career_app.services import python_workspace, roadmap_mastery
from career_app.ui.code_editor import AssistedPlainTextEdit
from career_app.ui.course_ui import CoursePageWidget
from career_app.ui.widgets import Card


class PythonFeedbackBanner(QLabel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        self.hide()

    def show_message(self, text: str, kind: str = "neutral") -> None:
        palette = {
            "success": ("#17392f", "#63dfa9", "#9af0ca"),
            "error": ("#3a202d", "#FF4DB8", "#FFD0EC"),
            "hint": ("#292342", "#A56CFF", "#DCCEFF"),
            "neutral": ("#172333", "#4b6688", "#cbd8ea"),
        }
        background, border, foreground = palette.get(kind, palette["neutral"])
        self.setStyleSheet(
            f"background:{background};border:1px solid {border};color:{foreground};"
            "border-radius:8px;padding:8px 10px;"
        )
        self.setText(str(text or ""))
        self.setVisible(bool(text))


class PythonExercisesWidget(QWidget):
    """Course navigation, guide, integrated editor, runner, and validation."""

    changed = Signal()

    def __init__(self, conn, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.conn = conn
        self.root = Path(root)
        self.current_number: int | None = None
        self._loading = False
        self._last_check_passed = False
        self._last_run: dict[str, Any] | None = None
        self._settings = QSettings("CareerAccelerator", "CareerAccelerator")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        toolbar = QFrame()
        toolbar.setObjectName("PythonExerciseToolbar")
        toolbar.setStyleSheet(
            "QFrame#PythonExerciseToolbar {background:#111a29;border:1px solid #263754;"
            "border-radius:10px;}"
        )
        self.toolbar_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, toolbar)
        self.toolbar_layout.setContentsMargins(10, 7, 10, 7)
        self.toolbar_layout.setSpacing(8)
        self.back_button = QPushButton("‹")
        self.back_button.setObjectName("Secondary")
        self.back_button.setFixedSize(36, 34)
        self.back_button.clicked.connect(self.previous_exercise)
        self.toolbar_layout.addWidget(self.back_button)
        self.breadcrumb = QLabel("Learning  ›  Practice  ›  Python Exercises")
        self.breadcrumb.setStyleSheet("color:#c4cde0;font-size:9.5pt;")
        self.toolbar_layout.addWidget(self.breadcrumb, 1)
        open_folder = QPushButton("Open Practice Folder")
        open_folder.setObjectName("Secondary")
        open_folder.clicked.connect(self.open_practice_folder)
        self.toolbar_layout.addWidget(open_folder)
        outer.addWidget(toolbar)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(4)
        self.main_splitter.setMinimumWidth(0)

        nav = Card()
        nav.setMinimumWidth(250)
        nav.layout.setContentsMargins(12, 12, 12, 12)
        nav.layout.setSpacing(9)
        heading = QHBoxLayout()
        title = QLabel("🐍  Python Exercises")
        title.setStyleSheet("font-size:13pt;font-weight:700;color:#FFFFFF;")
        heading.addWidget(title, 1)
        self.progress_count = QLabel("0/13")
        self.progress_count.setObjectName("Muted")
        heading.addWidget(self.progress_count)
        nav.layout.addLayout(heading)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(7)
        nav.layout.addWidget(self.progress_bar)
        caption = QLabel(
            "Work through the Week 8 Python sequence inside Career Accelerator. "
            "Each submission is saved locally and checked without uploading code."
        )
        caption.setObjectName("Muted")
        caption.setWordWrap(True)
        nav.layout.addWidget(caption)
        self.exercise_list = QListWidget()
        self.exercise_list.setWordWrap(True)
        self.exercise_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.exercise_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.exercise_list.setStyleSheet(
            "QListWidget {background:transparent;border:none;outline:none;}"
            "QListWidget::item {padding:9px 8px;border-radius:7px;border-left:3px solid transparent;}"
            "QListWidget::item:selected {background:#16253D;border-left:3px solid #8A5CFF;color:#ffffff;}"
            "QListWidget::item:hover {background:#121F34;}"
        )
        self.exercise_list.currentItemChanged.connect(self._exercise_selected)
        nav.layout.addWidget(self.exercise_list, 1)
        self.main_splitter.addWidget(nav)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.setHandleWidth(7)
        self.workspace_splitter.setMinimumWidth(0)
        self.workspace_splitter.setStyleSheet(
            "QSplitter::handle {background:#263754;border-radius:2px;margin:4px 1px;}"
            "QSplitter::handle:hover {background:#8A5CFF;}"
        )

        learn_card = Card()
        learn_card.layout.setContentsMargins(8, 8, 8, 8)
        learn_card.layout.setSpacing(0)
        self.learn_view = CoursePageWidget()
        self.learn_view.backRequested.connect(self.previous_exercise)
        self.learn_view.continueRequested.connect(self.next_exercise)
        self.learn_view.bookmarkToggled.connect(self._bookmark_changed)
        learn_card.layout.addWidget(self.learn_view, 1)
        self.workspace_splitter.addWidget(learn_card)

        practice_card = Card()
        practice_card.layout.setContentsMargins(8, 8, 8, 8)
        practice_card.layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(9)
        scroll.setWidget(content)
        practice_card.layout.addWidget(scroll, 1)

        top = QHBoxLayout()
        practice_title = QLabel("Practice")
        practice_title.setStyleSheet("font-size:13pt;font-weight:700;color:#FFFFFF;")
        top.addWidget(practice_title, 1)
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(python_workspace.VALID_STATUSES))
        self.status_combo.setMinimumWidth(126)
        top.addWidget(self.status_combo)
        layout.addLayout(top)

        self.task_prompt = QLabel(
            "Complete the task sections in the starter file. Run often, inspect the output, and use Check Exercise when you are ready for validation."
        )
        self.task_prompt.setWordWrap(True)
        self.task_prompt.setStyleSheet(
            "background:#111A2D;border:1px solid #3b3f61;border-radius:8px;"
            "color:#d9def0;padding:8px 10px;"
        )
        layout.addWidget(self.task_prompt)

        self.editor = AssistedPlainTextEdit(language="python", project_dir=self.root)
        self.editor.setObjectName("PythonExerciseEditor")
        self.editor.setLineWrapMode(AssistedPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setMinimumHeight(260)
        fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed.setPointSize(10)
        self.editor.setFont(fixed)
        self.editor.setStyleSheet(
            "QPlainTextEdit {background:#0B1220;color:#EEF4FF;border:1px solid #32425F;"
            "border-radius:8px;padding:8px;selection-background-color:#5B3FA8;}"
        )
        self.editor.textChanged.connect(self._editor_changed)
        layout.addWidget(self.editor, 3)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.actions_layout = actions
        self.run_button = QPushButton("▶ Run")
        self.run_button.setObjectName("Secondary")
        self.run_button.clicked.connect(self.run_code)
        self.check_button = QPushButton("✓ Check Exercise")
        self.check_button.setObjectName("Secondary")
        self.check_button.clicked.connect(self.check_exercise)
        self.save_button = QPushButton("Save Draft")
        self.save_button.setObjectName("Secondary")
        self.save_button.clicked.connect(self.save_draft)
        self.submit_button = QPushButton("Submit Exercise")
        self.submit_button.setObjectName("Primary")
        self.submit_button.clicked.connect(self.submit_exercise)
        for button in (self.run_button, self.check_button, self.save_button, self.submit_button):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        self.feedback = PythonFeedbackBanner()
        layout.addWidget(self.feedback)

        output_label = QLabel("Output")
        output_label.setStyleSheet("font-weight:650;color:#E9EFFA;")
        layout.addWidget(output_label)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(120)
        self.output.setMaximumHeight(230)
        self.output.setFont(fixed)
        self.output.setPlaceholderText("Run the code to see printed output and errors here.")
        self.output.setStyleSheet(
            "QTextEdit {background:#0C1627;color:#EEF4FF;border:1px solid #263754;"
            "border-radius:8px;padding:7px;}"
        )
        layout.addWidget(self.output)

        self.chart_label = QLabel()
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_label.setMinimumHeight(0)
        self.chart_label.setStyleSheet(
            "QLabel {background:#0C1627;border:1px solid #263754;border-radius:8px;padding:6px;}"
        )
        self.chart_label.hide()
        layout.addWidget(self.chart_label)

        notes_label = QLabel("Notes & reasoning")
        notes_label.setStyleSheet("font-weight:650;color:#E9EFFA;")
        layout.addWidget(notes_label)
        self.notes = QTextEdit()
        self.notes.setMinimumHeight(70)
        self.notes.setMaximumHeight(130)
        self.notes.setPlaceholderText(
            "Record what you changed, how you validated it, and what the output means."
        )
        layout.addWidget(self.notes)

        references = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.references_layout = references
        self.instructions_button = QPushButton("Open Instructions")
        self.instructions_button.setObjectName("Secondary")
        self.instructions_button.clicked.connect(lambda: self.open_reference("instructions"))
        self.starter_button = QPushButton("Open Starter")
        self.starter_button.setObjectName("Secondary")
        self.starter_button.clicked.connect(lambda: self.open_reference("starter"))
        self.dataset_button = QPushButton("Open Dataset Folder")
        self.dataset_button.setObjectName("Secondary")
        self.dataset_button.clicked.connect(self.open_dataset_folder)
        self.submission_folder_button = QPushButton("Open Submissions Folder")
        self.submission_folder_button.setObjectName("Secondary")
        self.submission_folder_button.clicked.connect(self.open_submissions_folder)
        for button in (
            self.instructions_button,
            self.starter_button,
            self.dataset_button,
            self.submission_folder_button,
        ):
            references.addWidget(button)
        references.addStretch()
        layout.addLayout(references)

        self.workspace_splitter.addWidget(practice_card)
        self.workspace_splitter.setStretchFactor(0, 1)
        self.workspace_splitter.setStretchFactor(1, 1)
        self.main_splitter.addWidget(self.workspace_splitter)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([300, 1050])
        self.workspace_splitter.setSizes([520, 590])
        outer.addWidget(self.main_splitter, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        width = max(0, self.width())
        self.toolbar_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if width < 760 else QBoxLayout.Direction.LeftToRight
        )
        direction = QBoxLayout.Direction.TopToBottom if width < 700 else QBoxLayout.Direction.LeftToRight
        self.actions_layout.setDirection(direction)
        self.references_layout.setDirection(direction)
        self.workspace_splitter.setOrientation(
            Qt.Orientation.Vertical if width < 1120 else Qt.Orientation.Horizontal
        )

    def _readiness(self, number: int | None = None) -> dict[str, Any]:
        return roadmap_mastery.python_exercise_readiness(
            self.conn, int(number if number is not None else self.current_number or 1)
        )

    def _ensure_ready(self, *, show_message: bool = True) -> bool:
        if self.current_number is None:
            return False
        readiness = self._readiness()
        if readiness.get("ready"):
            return True
        if show_message:
            self.feedback.show_message(
                "Exercise locked. " + str(readiness.get("reason") or "Complete the prerequisites first."),
                "hint",
            )
        return False

    def _apply_access_state(self, readiness: dict[str, Any], completed: bool) -> None:
        enabled = bool(completed or readiness.get("ready"))
        for widget in (
            self.status_combo,
            self.editor,
            self.run_button,
            self.check_button,
            self.save_button,
            self.submit_button,
            self.notes,
            self.instructions_button,
            self.starter_button,
            self.dataset_button,
            self.submission_folder_button,
        ):
            widget.setEnabled(enabled)
        if not enabled:
            reason = str(readiness.get("reason") or "Complete the prerequisites first.")
            self.feedback.show_message("Exercise locked. " + reason, "hint")
            self.editor.setPlaceholderText("Locked — complete the listed prerequisites first.")
        else:
            self.editor.setPlaceholderText("Write Python here. Your work is saved to a local submission file.")

    def refresh(self, *, preserve_number: bool = True) -> None:
        preferred = self.current_number if preserve_number else None
        if preferred is None:
            preferred = int(self._settings.value("python_exercises/current_number", 1))
        completed = 0
        statuses: dict[int, dict[str, Any]] = {}
        for number in sorted(PYTHON_EXERCISES):
            try:
                progress = python_workspace.progress(self.conn, self.root, number)
            except Exception:
                progress = {"status": "Not Started"}
            statuses[number] = progress
            if progress.get("status") == "Completed":
                completed += 1
        self.progress_count.setText(f"{completed}/{len(PYTHON_EXERCISES)}")
        self.progress_bar.setValue(round(completed / max(1, len(PYTHON_EXERCISES)) * 100))

        self._loading = True
        self.exercise_list.clear()
        target_row = 0
        for row, number in enumerate(sorted(PYTHON_EXERCISES)):
            item = PYTHON_EXERCISES[number]
            status = statuses[number].get("status", "Not Started")
            readiness = self._readiness(number)
            marker = (
                "●" if status == "Completed" else "🔒" if not readiness.get("ready")
                else "◐" if status == "In Progress" else "○"
            )
            list_item = QListWidgetItem(f"{marker}  EXERCISE {number:02d}\n     {item['title']}")
            list_item.setData(Qt.ItemDataRole.UserRole, number)
            tooltip = f"{item['concepts']} • {item['minutes']} minutes"
            if status != "Completed" and not readiness.get("ready"):
                tooltip += "\nLocked — " + str(readiness.get("reason") or "Complete prerequisites first.")
            list_item.setToolTip(tooltip)
            self.exercise_list.addItem(list_item)
            if number == preferred:
                target_row = row
        self._loading = False
        if self.exercise_list.count():
            self.exercise_list.setCurrentRow(target_row)
            current = self.exercise_list.currentItem()
            if current is not None:
                self._load_exercise(int(current.data(Qt.ItemDataRole.UserRole)))

    def select_exercise(self, number: int) -> None:
        for row in range(self.exercise_list.count()):
            item = self.exercise_list.item(row)
            if int(item.data(Qt.ItemDataRole.UserRole)) == int(number):
                if self.exercise_list.currentRow() != row:
                    self.exercise_list.setCurrentRow(row)
                else:
                    self._load_exercise(int(number))
                return

    def _exercise_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if self._loading or current is None:
            return
        self._save_editor_only(silent=True)
        self._load_exercise(int(current.data(Qt.ItemDataRole.UserRole)))

    def _load_exercise(self, number: int) -> None:
        self.current_number = int(number)
        self._settings.setValue("python_exercises/current_number", number)
        item = PYTHON_EXERCISES[number]
        try:
            markdown = runner.instructions_markdown(self.root, number)
        except Exception as exc:
            markdown = f"# {item['title']}\n\n> Exercise guide missing: {exc}"
        progress = python_workspace.progress(self.conn, self.root, number)
        path = python_workspace.submission_path(self.root, number)
        if path.is_file():
            code = path.read_text(encoding="utf-8")
        else:
            code = runner.starter_code(self.root, number)
        bookmarked = self._settings.value(f"python_exercises/bookmarks/{number}", False, type=bool)
        subtitle = f"Week {item['week']} • {item['minutes']} minutes • {item['concepts']}"
        self.learn_view.set_markdown(
            markdown,
            eyebrow="Python Exercise",
            subtitle=subtitle,
            bookmarked=bookmarked,
        )
        next_number = number + 1 if number < len(PYTHON_EXERCISES) else None
        self.learn_view.set_navigation(
            next_title=PYTHON_EXERCISES[next_number]["title"] if next_number else None,
            show_back=number > 1,
            continue_text="Next Exercise  →",
        )
        self.breadcrumb.setText(
            f"Learning  ›  Practice  ›  Python Exercises  ›  Exercise {number:02d}  ›  {item['title']}"
        )
        self._loading = True
        self.status_combo.setCurrentText(str(progress.get("status") or "Not Started"))
        self.editor.setPlainText(code)
        self.notes.setPlainText(str(progress.get("notes") or ""))
        self._loading = False
        self.output.setPlainText(str(progress.get("last_output") or ""))
        self.chart_label.hide()
        self.feedback.hide()
        self._last_check_passed = False
        self._last_run = None
        self.back_button.setEnabled(number > 1)
        self._apply_access_state(self._readiness(number), str(progress.get("status") or "") == "Completed")

    def _editor_changed(self) -> None:
        if self._loading:
            return
        self._last_check_passed = False
        self.feedback.hide()

    def _save_editor_only(self, *, silent: bool = False) -> Path | None:
        if self.current_number is None or not self._ensure_ready(show_message=not silent):
            return None
        path = python_workspace.save_code(self.root, self.current_number, self.editor.toPlainText())
        if not silent:
            self.feedback.show_message(f"Draft saved locally: {path.name}", "success")
        return path

    def _set_output(self, run: dict[str, Any] | None) -> None:
        self._last_run = run
        if not run:
            self.output.clear()
            self.chart_label.hide()
            return
        chunks: list[str] = []
        stdout = str(run.get("stdout") or "").rstrip()
        stderr = str(run.get("stderr") or "").rstrip()
        if stdout:
            chunks.append(stdout)
        if stderr:
            chunks.append(("ERROR\n" if not run.get("ok") else "MESSAGES\n") + stderr)
        chunks.append(f"Completed in {float(run.get('duration_seconds') or 0):.2f} seconds.")
        self.output.setPlainText("\n\n".join(chunks))
        images = list(run.get("images") or [])
        if images and Path(images[0]).is_file():
            pixmap = QPixmap(images[0])
            if not pixmap.isNull():
                self.chart_label.setPixmap(
                    pixmap.scaled(620, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
                self.chart_label.setToolTip(
                    f"{len(images)} chart image(s) were captured. Open the practice folder to review all files."
                )
                self.chart_label.show()
                return
        self.chart_label.hide()

    def _navigate_error(self, line_number: int | None) -> None:
        if not line_number:
            return
        block = self.editor.document().findBlockByLineNumber(max(0, int(line_number) - 1))
        if block.isValid():
            cursor = QTextCursor(block)
            self.editor.setTextCursor(cursor)
            self.editor.centerCursor()
            self.editor.setFocus()

    def run_code(self) -> None:
        if self.current_number is None or not self._ensure_ready():
            return
        try:
            result = runner.run_code(self.root, self.current_number, self.editor.toPlainText())
        except Exception as exc:
            self.feedback.show_message(str(exc), "error")
            return
        self._set_output(result)
        if result.get("ok"):
            self.feedback.show_message("Code ran successfully. Review the output before checking the exercise.", "success")
        else:
            self.feedback.show_message("Python stopped with an error. Use the output and highlighted line to correct it.", "error")
            self._navigate_error(result.get("error_line"))

    @staticmethod
    def _checklist_text(items) -> str:
        return "\n".join(
            f"{'✓' if item.passed else '•'} {item.label}: {item.detail}"
            for item in items
        )

    def check_exercise(self) -> dict[str, Any] | None:
        if self.current_number is None or not self._ensure_ready():
            return None
        try:
            result = runner.check_code(self.root, self.current_number, self.editor.toPlainText())
        except Exception as exc:
            self.feedback.show_message(str(exc), "error")
            return None
        self._set_output(result.get("run"))
        self._last_check_passed = bool(result.get("passed"))
        self.feedback.show_message(
            self._checklist_text(result.get("checklist") or []),
            "success" if self._last_check_passed else "hint",
        )
        run = result.get("run") or {}
        if not run.get("ok"):
            self._navigate_error(run.get("error_line"))
        return result

    def save_draft(self) -> None:
        if self.current_number is None or not self._ensure_ready():
            return
        try:
            path = python_workspace.save_code(self.root, self.current_number, self.editor.toPlainText())
            current = python_workspace.progress(self.conn, self.root, self.current_number)
            status = "Completed" if current.get("status") == "Completed" else "In Progress"
            python_workspace.save_progress(
                self.conn,
                self.root,
                self.current_number,
                status=status,
                notes=self.notes.toPlainText(),
                last_output=self.output.toPlainText(),
            )
            self.status_combo.setCurrentText(status)
            self.feedback.show_message(f"Draft and notes saved: {path.name}", "success")
        except Exception as exc:
            self.feedback.show_message(str(exc), "error")

    def submit_exercise(self) -> None:
        if self.current_number is None or not self._ensure_ready():
            return
        result = self.check_exercise()
        if not result or not result.get("passed"):
            self.feedback.show_message(
                "The exercise is not ready to submit. Complete the validation items shown above.",
                "hint",
            )
            return
        try:
            python_workspace.save_progress(
                self.conn,
                self.root,
                self.current_number,
                status="Completed",
                notes=self.notes.toPlainText(),
                last_output=self.output.toPlainText(),
            )
            self.status_combo.setCurrentText("Completed")
            self.feedback.show_message("Exercise completed and linked progress was updated.", "success")
            self.changed.emit()
            QTimer.singleShot(0, self.refresh)
        except Exception as exc:
            self.feedback.show_message(str(exc), "error")

    def _bookmark_changed(self, value: bool) -> None:
        if self.current_number is not None:
            self._settings.setValue(f"python_exercises/bookmarks/{self.current_number}", bool(value))

    def previous_exercise(self) -> None:
        if self.current_number and self.current_number > 1:
            self.select_exercise(self.current_number - 1)

    def next_exercise(self) -> None:
        if self.current_number and self.current_number < len(PYTHON_EXERCISES):
            self.select_exercise(self.current_number + 1)

    def open_reference(self, key: str) -> None:
        if self.current_number is None or not self._ensure_ready():
            return
        path = python_workspace.paths(self.root, self.current_number)[key]
        try:
            python_workspace.open_folder(path.parent)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open File", str(exc))

    def open_practice_folder(self) -> None:
        try:
            python_workspace.open_folder(self.root / "practice" / "python")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Folder", str(exc))

    def open_dataset_folder(self) -> None:
        if self.current_number is None or not self._ensure_ready():
            return
        try:
            python_workspace.open_folder(python_workspace.paths(self.root, self.current_number)["dataset"].parent)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Folder", str(exc))

    def open_submissions_folder(self) -> None:
        if self.current_number is None or not self._ensure_ready():
            return
        folder = python_workspace.paths(self.root, self.current_number)["submissions"]
        folder.mkdir(parents=True, exist_ok=True)
        try:
            python_workspace.open_folder(folder)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Folder", str(exc))
