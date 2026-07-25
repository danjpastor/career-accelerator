"""Milestone-specific studio widgets embedded inside portfolio task workspaces."""

from __future__ import annotations

import csv
from pathlib import Path
import webbrowser
from typing import Any

from PySide6.QtCore import QObject, QEvent, QRunnable, QThreadPool, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.services import cleaning_workspace, google_sheets, portfolio_studios, project_data_workspace
from career_app.ui.cleaning_workspace import DataCleaningStudio
from career_app.ui.code_editor import AssistedTextEdit
from career_app.ui.course_ui import SqlHighlighter
from career_app.ui.notebook_workspace import IntegratedNotebookWidget
from career_app.ui.project_context import ProjectContextWidget
from career_app.ui.markdown_preview import raw_markdown_stylesheet


class _BackgroundJobSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class _BackgroundJob(QRunnable):
    """Run file and DuckDB work outside the UI thread."""

    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = _BackgroundJobSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.operation()
        except Exception as exc:
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class _BackgroundJobReceiver(QObject):
    """Marshal runnable results back onto the Qt UI thread."""

    def __init__(self, *, on_result, on_error, on_finished, parent=None):
        super().__init__(parent)
        self._on_result = on_result
        self._on_error = on_error
        self._on_finished = on_finished

    @Slot(object)
    def receive_result(self, payload) -> None:
        self._on_result(payload)

    @Slot(str)
    def receive_error(self, message: str) -> None:
        self._on_error(message)

    @Slot()
    def receive_finished(self) -> None:
        self._on_finished()


_STUDIO_IO_POOL: QThreadPool | None = None


def _studio_io_pool() -> QThreadPool:
    """Keep file and DuckDB jobs bounded so rapid field changes cannot saturate I/O."""
    global _STUDIO_IO_POOL
    if _STUDIO_IO_POOL is None:
        _STUDIO_IO_POOL = QThreadPool()
        _STUDIO_IO_POOL.setMaxThreadCount(2)
        _STUDIO_IO_POOL.setExpiryTimeout(15_000)
    return _STUDIO_IO_POOL


class StudioWidget(QWidget):
    saved = Signal(str)

    def __init__(self, context: portfolio_studios.StudioContext, parent=None):
        super().__init__(parent)
        self.context = context

    def status_message(self, message: str) -> None:
        if hasattr(self, "status"):
            self.status.setText(str(message))
        self.saved.emit(str(message))

    def prepare_for_completion(self) -> None:
        pass

    def completion_issues(self) -> list[str]:
        return []

    def shutdown(self) -> None:
        pass


def _studio_header(layout: QVBoxLayout, title: str, description: str) -> QLabel:
    heading = QLabel(title)
    heading.setObjectName("SectionTitle")
    layout.addWidget(heading)
    help_text = QLabel(description)
    help_text.setObjectName("Muted")
    help_text.setWordWrap(True)
    layout.addWidget(help_text)
    return help_text


def _text_field(minimum_height: int = 58) -> QTextEdit:
    widget = QTextEdit()
    widget.setAcceptRichText(False)
    widget.setMinimumHeight(minimum_height)
    return widget


class _CompactTextEdit(QTextEdit):
    """A one- or two-line editor that scrolls internally when text is longer."""

    def __init__(self, visible_lines: int = 2, parent=None):
        super().__init__(parent)
        self._visible_lines = max(1, int(visible_lines))
        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._apply_compact_height()

    def _apply_compact_height(self) -> None:
        line_height = self.fontMetrics().lineSpacing()
        document_padding = int(round(self.document().documentMargin() * 2))
        frame = self.frameWidth() * 2
        breathing_room = max(6, int(round(line_height * 0.3)))
        height = (
            line_height * self._visible_lines
            + document_padding
            + frame
            + breathing_room
        )
        self.setFixedHeight(max(34, height))

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() in (
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.ApplicationFontChange,
        ):
            self._apply_compact_height()


def _compact_text_field(visible_lines: int = 2) -> QTextEdit:
    return _CompactTextEdit(visible_lines)


def _configure_review_form(form: QFormLayout) -> None:
    """Keep labeled controls readable when the Studio becomes narrow."""
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    form.setLabelAlignment(
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
    )


def _scrollable_review_page(content: QWidget) -> QScrollArea:
    """Let a review tab grow to its natural height and scroll instead of clipping."""
    content_layout = content.layout()
    if content_layout is not None:
        content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
    content.setSizePolicy(
        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
    )

    scroll = QScrollArea()
    scroll.setObjectName("StudioReviewScrollArea")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    scroll.setVerticalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )
    scroll.setWidget(content)
    return scroll


class ProjectBriefStudio(StudioWidget):
    FIELDS = (
        ("business_problem", "Business problem", "What problem or opportunity is this project addressing?"),
        ("audience", "Audience", "Who will use the analysis?"),
        ("decision", "Decision to support", "What decision should the finished work make easier?"),
        ("goals", "Goals", "What should the project accomplish?"),
        ("questions", "Business questions", "Which questions must the analysis answer?"),
        ("scope", "In scope", "What is included?"),
        ("out_of_scope", "Out of scope", "What is intentionally excluded?"),
        ("deliverables", "Deliverables", "What will be handed to the audience?"),
        ("success_criteria", "Success criteria", "How will you know the project succeeded?"),
        ("assumptions", "Assumptions", "What is being assumed or still needs confirmation?"),
    )

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(9)
        _studio_header(
            layout,
            "Project Brief Studio",
            "Review the project in one place. The app keeps the structure tidy; you make the decisions and approve the wording.",
        )
        form = QFormLayout()
        form.setVerticalSpacing(8)
        self.fields: dict[str, QTextEdit] = {}
        defaults = portfolio_studios.project_brief_defaults(context)
        for key, label, placeholder in self.FIELDS:
            editor = _text_field(62)
            editor.setPlaceholderText(placeholder)
            editor.setPlainText(str(defaults.get(key) or ""))
            self.fields[key] = editor
            form.addRow(label, editor)
        layout.addLayout(form, 1)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Ready to review")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        validate = QPushButton("Check Brief")
        validate.clicked.connect(self.validate)
        actions.addWidget(validate)
        save = QPushButton("Save Approved Brief")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        actions.addWidget(save)
        layout.addLayout(actions)

    def values(self) -> dict[str, str]:
        return {key: editor.toPlainText().strip() for key, editor in self.fields.items()}

    def validate(self) -> list[str]:
        issues = portfolio_studios.project_brief_issues(self.values())
        self.status.setText("Ready to approve" if not issues else f"{len(issues)} item{'s' if len(issues) != 1 else ''} need attention")
        if issues:
            QMessageBox.information(self, "Project Brief Review", "\n".join(f"• {item}" for item in issues))
        return issues

    def prepare_for_completion(self) -> None:
        portfolio_studios.save_project_brief(self.context, self.values())

    def completion_issues(self) -> list[str]:
        return portfolio_studios.project_brief_issues(self.values())

    def save(self) -> None:
        try:
            path = portfolio_studios.save_project_brief(self.context, self.values())
            issues = self.validate()
            self.status_message(f"Saved {path.name}" + ("" if not issues else f" • {len(issues)} items still need review"))
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Brief", str(exc))


class DataSourceStudio(StudioWidget):
    FIELDS = (
        ("source_type", "Source type", "Public, licensed, internal, or synthetic"),
        ("provenance", "Where it came from", "Source, creator, retrieval date, or generation process"),
        ("permitted_use", "Permitted use", "How the data may be used or shared"),
        ("coverage", "Coverage", "Date range, geography, departments, products, or other boundaries"),
        ("grain", "Table grain", "What one row represents in each table"),
        ("required_fields", "Required fields", "Fields needed for the approved questions and KPIs"),
        ("known_limitations", "Known limitations", "Missing coverage, bias, synthetic rules, or other limits"),
        ("approval_notes", "Approval notes", "Why this source is suitable, or what must change"),
    )

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(9)
        _studio_header(
            layout,
            "Data Source Review Studio",
            "Review whether the proposed data can answer the approved questions. Detected files are shown below; approval remains your decision.",
        )
        values = portfolio_studios.data_source_defaults(context)
        form = QFormLayout()
        self.fields: dict[str, QTextEdit] = {}
        for key, label, placeholder in self.FIELDS:
            editor = _text_field(50)
            editor.setPlaceholderText(placeholder)
            editor.setPlainText(str(values.get(key) or ""))
            self.fields[key] = editor
            form.addRow(label, editor)
        layout.addLayout(form)
        self.approved = QCheckBox("I reviewed the source and approve it for this project")
        self.approved.setChecked(bool(values.get("approved")))
        layout.addWidget(self.approved)
        self.files = QTableWidget(0, 5)
        self.files.setHorizontalHeaderLabels(("Raw file", "Format", "Rows", "Columns", "Fingerprint"))
        self.files.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.files, 1)
        self.refresh_files()
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Review the detected files and source details")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        refresh = QPushButton("Refresh Detected Files")
        refresh.clicked.connect(self.refresh_files)
        actions.addWidget(refresh)
        save = QPushButton("Save Source Review")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        actions.addWidget(save)
        layout.addLayout(actions)

    def refresh_files(self) -> None:
        rows = portfolio_studios.raw_inventory(self.context)
        self.files.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = (
                row["path"],
                row["suffix"].lstrip(".").upper(),
                "" if row["row_count"] is None else str(row["row_count"]),
                "" if row["column_count"] is None else str(row["column_count"]),
                str(row["fingerprint"])[:12],
            )
            for column, value in enumerate(values):
                self.files.setItem(row_index, column, QTableWidgetItem(value))
        self.status.setText(f"{len(rows)} raw file{'s' if len(rows) != 1 else ''} detected")

    def prepare_for_completion(self) -> None:
        values = {key: editor.toPlainText().strip() for key, editor in self.fields.items()}
        values["approved"] = self.approved.isChecked()
        portfolio_studios.save_data_source_review(self.context, values)

    def completion_issues(self) -> list[str]:
        issues = []
        values = {key: editor.toPlainText().strip() for key, editor in self.fields.items()}
        if not values.get("source_type"):
            issues.append("Choose or describe the source type.")
        if not values.get("provenance"):
            issues.append("Record where the data came from or how it was generated.")
        if not values.get("coverage"):
            issues.append("Describe the data coverage, such as dates, regions, teams, or products.")
        if not values.get("grain"):
            issues.append("Describe what one row represents in each planned table.")
        if not values.get("required_fields"):
            issues.append("List the fields needed for the approved questions and KPIs.")
        if not self.approved.isChecked():
            issues.append("Review and approve the data source.")
        return issues

    def save(self) -> None:
        values = {key: editor.toPlainText().strip() for key, editor in self.fields.items()}
        values["approved"] = self.approved.isChecked()
        try:
            review, manifest = portfolio_studios.save_data_source_review(self.context, values)
            self.status_message(f"Saved {review.name} and {manifest.name}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Source Review", str(exc))


class DataIntakeStudio(StudioWidget):
    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(9)
        _studio_header(
            layout,
            "Data Intake Studio",
            "Bring the real raw files into the project, inspect their basic shape, and keep an inventory. Files are copied; the originals are not changed.",
        )
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(("File", "Format", "Size", "Rows", "Columns", "Modified", "Fingerprint"))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("No scan run yet")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        add = QPushButton("Add Raw Files")
        add.setObjectName("Primary")
        add.clicked.connect(self.add_files)
        actions.addWidget(add)
        refresh = QPushButton("Refresh Inventory")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        manifest = QPushButton("Save Source Manifest")
        manifest.clicked.connect(self.save_manifest)
        actions.addWidget(manifest)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self) -> None:
        rows = portfolio_studios.raw_inventory(self.context)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = (
                row["path"],
                row["suffix"].lstrip(".").upper(),
                f"{row['size_bytes'] / 1024:.1f} KB",
                "" if row["row_count"] is None else str(row["row_count"]),
                "" if row["column_count"] is None else str(row["column_count"]),
                row["modified_at"],
                row["fingerprint"][:12],
            )
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(str(value)))
        self.status.setText(f"{len(rows)} raw file{'s' if len(rows) != 1 else ''} registered")

    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Raw Data Files",
            str(Path.home()),
            "Data files (*.csv *.parquet *.json *.jsonl *.ndjson *.xlsx *.xls *.ods);;All files (*)",
        )
        if not paths:
            return
        try:
            created = portfolio_studios.import_raw_files(self.context, [Path(path) for path in paths])
            self.refresh()
            self.status_message(f"Added {len(created)} raw file{'s' if len(created) != 1 else ''}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Add Raw Files", str(exc))

    def prepare_for_completion(self) -> None:
        portfolio_studios.save_source_manifest(self.context)

    def completion_issues(self) -> list[str]:
        issues = []
        if not portfolio_studios.raw_inventory(self.context):
            issues.append("Add or register the raw project files.")
        manifest = self.context.project_dir / "documentation" / "data_source_manifest.csv"
        if not manifest.is_file():
            issues.append("Save the source manifest after the final raw files are in place.")
        return issues

    def save_manifest(self) -> None:
        try:
            manifest = portfolio_studios.save_source_manifest(self.context)
            self.status_message(f"Saved {manifest.name}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Manifest", str(exc))


class DataDictionaryStudio(StudioWidget):
    """A focused, step-by-step review workflow for project data dictionaries."""

    EXPECTED_TYPES = (
        "Text",
        "Identifier text",
        "Category text",
        "Integer",
        "Decimal",
        "Currency / decimal",
        "Percentage",
        "Boolean",
        "Date",
        "Timestamp",
        "Review required",
    )
    NULL_RULES = (
        "No nulls allowed",
        "Nulls allowed",
        "Conditionally nullable",
        "Observed only — rule needs confirmation",
    )
    KEY_ROLES = (
        "Not a key",
        "Primary key",
        "Foreign key",
        "Self-referencing foreign key",
        "Composite key component",
        "Primary key candidate",
        "Foreign key candidate",
    )
    UNIQUENESS_RULES = (
        "Required",
        "Not required",
        "Unique when present",
        "Composite uniqueness",
        "Review required",
    )
    SEVERITY_RANK = {
        "Blocking": 0,
        "Documentation": 1,
        "Review": 2,
        "Suggestion": 3,
    }

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._rows: list[dict[str, Any]] = []
        self._tables: dict[str, dict[str, Any]] = {}
        self._current_table = ""
        self._current_field_index: int | None = None
        self._loading = False
        self._dirty = False
        self._closing = False
        self._load_generation = 0
        self._load_worker = None
        self._load_receiver = None
        self._evidence_workers: dict[int, _BackgroundJob] = {}
        self._evidence_receivers: dict[int, _BackgroundJobReceiver] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        _studio_header(
            root,
            "Data Dictionary Review",
            "Work through three clear steps: define each table, review its fields one at a time, then run the final check and generate the document.",
        )

        progress_card = QFrame()
        progress_card.setObjectName("SoftPanel")
        progress_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, progress_card)
        progress_layout.setContentsMargins(12, 8, 12, 8)
        progress_layout.setSpacing(10)
        progress_text = QVBoxLayout()
        progress_text.setSpacing(2)
        self.progress_label = QLabel("Loading dictionary…")
        self.progress_label.setObjectName("SectionTitle")
        progress_text.addWidget(self.progress_label)
        self.issue_summary = QLabel("")
        self.issue_summary.setObjectName("Muted")
        self.issue_summary.setWordWrap(True)
        progress_text.addWidget(self.issue_summary)
        progress_layout.addLayout(progress_text, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setMaximumWidth(240)
        progress_layout.addWidget(self.progress)
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.setToolTip(
            "Re-scan the project data without replacing your definitions or review decisions."
        )
        self.refresh_button.clicked.connect(self.rescan)
        progress_layout.addWidget(self.refresh_button)
        self.save_button = QPushButton("Save Progress")
        self.save_button.clicked.connect(self.save_progress)
        progress_layout.addWidget(self.save_button)
        root.addWidget(progress_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        self._build_navigator(splitter)
        self._build_review_steps(splitter)
        splitter.setSizes([300, 1050])

        footer = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Scanning project schema…")
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        footer.addWidget(self.status, 1)
        root.addLayout(footer)

        self.load_rows(refresh=False)

    # ------------------------------------------------------------------ UI builders
    def _build_navigator(self, splitter: QSplitter) -> None:
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setMinimumWidth(260)
        panel.setMaximumWidth(390)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Review Navigator")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        help_text = QLabel(
            "Choose a table first. Its fields appear below when you are ready for Step 2."
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        tables_label = QLabel("Tables")
        tables_label.setObjectName("Muted")
        layout.addWidget(tables_label)
        self.table_list = QListWidget()
        self.table_list.setObjectName("SprintBacklogList")
        self.table_list.setWordWrap(True)
        self.table_list.currentItemChanged.connect(self._on_table_selection_changed)
        layout.addWidget(self.table_list, 1)

        field_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.fields_title = QLabel("Fields")
        self.fields_title.setObjectName("Muted")
        field_row.addWidget(self.fields_title, 1)
        self.only_unreviewed = QCheckBox("Only unresolved")
        self.only_unreviewed.toggled.connect(self._populate_field_list)
        field_row.addWidget(self.only_unreviewed)
        layout.addLayout(field_row)

        self.field_list = QListWidget()
        self.field_list.setObjectName("SprintBacklogList")
        self.field_list.setWordWrap(True)
        self.field_list.currentItemChanged.connect(self._on_field_selection_changed)
        layout.addWidget(self.field_list, 2)

        splitter.addWidget(panel)

    def _build_review_steps(self, splitter: QSplitter) -> None:
        panel = QFrame()
        panel.setObjectName("Card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.review_steps = QTabWidget()
        self.review_steps.addTab(self._build_table_step(), "1  Table Setup")
        self.review_steps.addTab(self._build_field_step(), "2  Field Review")
        self.review_steps.addTab(self._build_finalize_step(), "3  Finalize")
        layout.addWidget(self.review_steps, 1)
        splitter.addWidget(panel)

    def _step_intro(self, title: str, text: str) -> QWidget:
        card = QFrame()
        card.setObjectName("SoftPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(3)
        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        detail = QLabel(text)
        detail.setObjectName("Muted")
        detail.setWordWrap(True)
        layout.addWidget(detail)
        return card

    def _build_table_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(9)
        layout.addWidget(
            self._step_intro(
                "Step 1: Confirm the prior table decisions",
                "Table purpose, grain, and expected primary key are filled from the approved specification and relationship-validation work. Review them here and adjust only when your earlier conclusion changed.",
            )
        )

        self.table_title = QLabel("Select a table")
        self.table_title.setObjectName("SectionTitle")
        self.table_title.setWordWrap(True)
        layout.addWidget(self.table_title)
        self.table_observed = QLabel("Choose a table from the navigator.")
        self.table_observed.setObjectName("Muted")
        self.table_observed.setWordWrap(True)
        layout.addWidget(self.table_observed)

        form = QFormLayout()
        form.setVerticalSpacing(6)
        _configure_review_form(form)
        self.table_business_name = QLineEdit()
        self.table_business_name.setPlaceholderText("Friendly display name, such as Artists")
        self.table_description = _compact_text_field(2)
        self.table_description.setPlaceholderText(
            "What information does this table contain, and why does the project need it?"
        )
        self.table_grain = _compact_text_field(2)
        self.table_grain.setPlaceholderText("One row represents…")
        self.table_primary_key = QComboBox()
        self.table_primary_key.setEditable(True)
        form.addRow("Business name", self.table_business_name)
        form.addRow("Table purpose *", self.table_description)
        form.addRow("One row represents *", self.table_grain)
        form.addRow("Expected primary key *", self.table_primary_key)
        layout.addLayout(form)

        self.table_guidance = QLabel("Prior milestone decisions will appear here automatically.")
        self.table_guidance.setObjectName("Muted")
        self.table_guidance.setWordWrap(True)
        layout.addWidget(self.table_guidance)

        context_tabs = QTabWidget()
        context_tabs.setMinimumHeight(155)
        context_page = QWidget()
        context_layout = QVBoxLayout(context_page)
        context_layout.setContentsMargins(8, 8, 8, 8)
        context_layout.setSpacing(6)
        relationship_label = QLabel("Detected relationships — read only")
        relationship_label.setObjectName("Muted")
        context_layout.addWidget(relationship_label)
        self.table_relationships = QTextBrowser()
        self.table_relationships.setMaximumHeight(86)
        self.table_relationships.setPlaceholderText(
            "No relationships were detected for this table."
        )
        context_layout.addWidget(self.table_relationships)
        context_tabs.addTab(context_page, "Detected Relationships")

        notes_page = QWidget()
        notes_layout = QVBoxLayout(notes_page)
        notes_layout.setContentsMargins(8, 8, 8, 8)
        notes_layout.setSpacing(6)
        notes_label = QLabel("Optional table-level context or limitations")
        notes_label.setObjectName("Muted")
        notes_layout.addWidget(notes_label)
        self.table_notes = _compact_text_field(2)
        notes_layout.addWidget(self.table_notes)
        context_tabs.addTab(notes_page, "Optional Notes")
        layout.addWidget(context_tabs, 1)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        actions.addStretch()
        save = QPushButton("Save Table Details")
        save.clicked.connect(self.save_progress)
        actions.addWidget(save)
        continue_button = QPushButton("Continue to Field Review")
        continue_button.setObjectName("Primary")
        continue_button.clicked.connect(self.continue_to_fields)
        actions.addWidget(continue_button)
        layout.addLayout(actions)

        self._table_editors = (
            self.table_business_name,
            self.table_description,
            self.table_grain,
            self.table_primary_key,
            self.table_notes,
        )
        for editor in self._table_editors:
            signal = getattr(editor, "textChanged", None) or getattr(
                editor, "currentTextChanged", None
            )
            if signal is not None:
                signal.connect(self._mark_dirty)
        return _scrollable_review_page(page)

    def _build_field_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(9)
        layout.addWidget(
            self._step_intro(
                "Step 2: Review one field at a time",
                "Start with the required business decisions. Open Evidence & Exceptions only when you need samples, warnings, or cleaning notes.",
            )
        )

        heading_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        heading_text = QVBoxLayout()
        heading_text.setSpacing(2)
        self.field_title = QLabel("Select a field")
        self.field_title.setObjectName("SectionTitle")
        self.field_title.setWordWrap(True)
        heading_text.addWidget(self.field_title)
        self.field_state = QLabel("Choose a field from the navigator to begin.")
        self.field_state.setObjectName("Muted")
        self.field_state.setWordWrap(True)
        heading_text.addWidget(self.field_state)
        heading_row.addLayout(heading_text, 1)
        self.field_position = QLabel("")
        self.field_position.setObjectName("Muted")
        heading_row.addWidget(self.field_position)
        layout.addLayout(heading_row)

        self.field_guidance = QLabel("Select a field to see the next required decision.")
        self.field_guidance.setObjectName("SoftPanel")
        self.field_guidance.setWordWrap(True)
        self.field_guidance.setMargin(10)
        layout.addWidget(self.field_guidance)

        summary = QFrame()
        summary.setObjectName("SoftPanel")
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(12, 8, 12, 8)
        summary_layout.setHorizontalSpacing(18)
        summary_layout.setVerticalSpacing(3)
        self.field_summary_labels: dict[str, QLabel] = {}
        for column, (key, label_text) in enumerate(
            (
                ("observed_type", "Observed type"),
                ("row_count", "Rows"),
                ("null_count", "Nulls"),
                ("distinct_count", "Distinct"),
                ("duplicate_count", "Repeated"),
            )
        ):
            label = QLabel(label_text)
            label.setObjectName("Muted")
            value = QLabel("—")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            summary_layout.addWidget(label, 0, column)
            summary_layout.addWidget(value, 1, column)
            self.field_summary_labels[key] = value
            summary_layout.setColumnStretch(column, 1)
        layout.addWidget(summary)

        self.field_detail_tabs = QTabWidget()
        self.field_detail_tabs.setMinimumHeight(470)
        required_page = QWidget()
        required_layout = QVBoxLayout(required_page)
        required_layout.setContentsMargins(8, 8, 8, 8)
        required_layout.setSpacing(8)
        required_form = QFormLayout()
        required_form.setVerticalSpacing(6)
        _configure_review_form(required_form)
        self.definition = _compact_text_field(2)
        self.definition.setPlaceholderText(
            "Explain what this field means in the business or project context."
        )
        self.expected_type = QComboBox()
        self.expected_type.setEditable(True)
        self.expected_type.addItems(self.EXPECTED_TYPES)
        self.nullable = QComboBox()
        self.nullable.setEditable(True)
        self.nullable.addItems(self.NULL_RULES)
        self.key_role = QComboBox()
        self.key_role.setEditable(True)
        self.key_role.addItems(self.KEY_ROLES)
        self.expected_unique = QComboBox()
        self.expected_unique.setEditable(True)
        self.expected_unique.addItems(self.UNIQUENESS_RULES)
        self.relationship = QLineEdit()
        self.relationship.setPlaceholderText(
            "Required for foreign keys, using table.column"
        )
        required_form.addRow("Business definition *", self.definition)
        required_form.addRow("Expected logical type *", self.expected_type)
        required_form.addRow("Null rule *", self.nullable)
        required_form.addRow("Key role *", self.key_role)
        required_form.addRow("Uniqueness rule *", self.expected_unique)
        required_form.addRow("Parent relationship", self.relationship)
        required_layout.addLayout(required_form)
        required_layout.addStretch()
        self.field_detail_tabs.addTab(required_page, "Required Review")

        evidence_page = QWidget()
        evidence_layout = QVBoxLayout(evidence_page)
        evidence_layout.setContentsMargins(8, 8, 8, 8)
        evidence_layout.setSpacing(8)
        evidence_splitter = QSplitter(Qt.Orientation.Vertical)
        evidence_splitter.setChildrenCollapsible(False)

        evidence_top = QWidget()
        evidence_top_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, evidence_top)
        evidence_top_layout.setContentsMargins(0, 0, 0, 0)
        evidence_top_layout.setSpacing(8)
        self.samples = QTextBrowser()
        self.samples.setMinimumHeight(150)
        self.samples.setPlaceholderText("Observed samples will appear here.")
        evidence_top_layout.addWidget(self.samples, 1)
        self.field_issues = QTextBrowser()
        self.field_issues.setMinimumHeight(150)
        self.field_issues.setPlaceholderText("Detected issues will appear here.")
        evidence_top_layout.addWidget(self.field_issues, 1)
        evidence_splitter.addWidget(evidence_top)

        exception_body = QWidget()
        exception_form = QFormLayout(exception_body)
        exception_form.setContentsMargins(0, 0, 0, 0)
        exception_form.setVerticalSpacing(6)
        _configure_review_form(exception_form)
        self.valid_values = _compact_text_field(2)
        self.unit = QLineEdit()
        self.notes = _compact_text_field(2)
        self.cleaning_expectation = _compact_text_field(2)
        self.warning_resolution = _compact_text_field(2)
        exception_form.addRow("Allowed values / format", self.valid_values)
        exception_form.addRow("Unit of measurement", self.unit)
        exception_form.addRow("Data-quality notes", self.notes)
        exception_form.addRow("Cleaning expectation", self.cleaning_expectation)
        exception_form.addRow(
            "Explain warning / decision", self.warning_resolution
        )
        evidence_splitter.addWidget(exception_body)
        evidence_splitter.setMinimumHeight(430)
        evidence_splitter.setSizes([170, 260])
        evidence_layout.addWidget(evidence_splitter, 1)
        self.field_detail_tabs.addTab(evidence_page, "Evidence & Exceptions")
        layout.addWidget(self.field_detail_tabs, 1)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        previous = QPushButton("Previous Field")
        previous.clicked.connect(self.previous_field)
        actions.addWidget(previous)
        next_unresolved = QPushButton("Next Unresolved")
        next_unresolved.clicked.connect(self.next_unresolved_field)
        actions.addWidget(next_unresolved)
        actions.addStretch()
        self.check_field_button = QPushButton("Check Field")
        self.check_field_button.clicked.connect(self.check_current_field)
        self.check_field_button.setEnabled(False)
        actions.addWidget(self.check_field_button)
        self.mark_field_button = QPushButton("Save, Review, and Continue")
        self.mark_field_button.setObjectName("Primary")
        self.mark_field_button.clicked.connect(self.mark_field_reviewed)
        self.mark_field_button.setEnabled(False)
        actions.addWidget(self.mark_field_button)
        layout.addLayout(actions)

        self._field_editors = (
            self.definition,
            self.expected_type,
            self.nullable,
            self.key_role,
            self.expected_unique,
            self.relationship,
            self.valid_values,
            self.unit,
            self.notes,
            self.cleaning_expectation,
            self.warning_resolution,
        )
        for editor in self._field_editors:
            signal = getattr(editor, "textChanged", None) or getattr(
                editor, "currentTextChanged", None
            )
            if signal is not None:
                signal.connect(self._mark_dirty)
        return _scrollable_review_page(page)

    def _build_finalize_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        layout.addWidget(
            self._step_intro(
                "Step 3: Finish the current table and the full dictionary",
                "Mark each table reviewed after all of its fields are complete. When every table is done, run the full check and generate the final Markdown document.",
            )
        )

        self.finalize_table_title = QLabel("Current table")
        self.finalize_table_title.setObjectName("SectionTitle")
        layout.addWidget(self.finalize_table_title)
        self.finalize_table_summary = QLabel("Select a table to see its readiness.")
        self.finalize_table_summary.setObjectName("Muted")
        self.finalize_table_summary.setWordWrap(True)
        layout.addWidget(self.finalize_table_summary)
        self.mark_table_button = QPushButton("Mark Current Table Reviewed")
        self.mark_table_button.clicked.connect(self.mark_table_reviewed)
        layout.addWidget(self.mark_table_button, 0, Qt.AlignmentFlag.AlignLeft)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(divider)

        overall_title = QLabel("Full dictionary")
        overall_title.setObjectName("SectionTitle")
        layout.addWidget(overall_title)
        self.finalize_overall_summary = QLabel("")
        self.finalize_overall_summary.setWordWrap(True)
        layout.addWidget(self.finalize_overall_summary)

        checklist = QLabel(
            "Final order:\n"
            "1. Review every field.\n"
            "2. Mark every table reviewed.\n"
            "3. Run Check Full Dictionary.\n"
            "4. Generate Final Document after the last edit."
        )
        checklist.setObjectName("SoftPanel")
        checklist.setWordWrap(True)
        checklist.setMargin(12)
        layout.addWidget(checklist)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        actions.addStretch()
        check = QPushButton("Check Full Dictionary")
        check.clicked.connect(self.validate)
        actions.addWidget(check)
        generate = QPushButton("Generate Final Document")
        generate.setObjectName("Primary")
        generate.clicked.connect(self.generate_document)
        actions.addWidget(generate)
        layout.addLayout(actions)
        layout.addStretch()
        return _scrollable_review_page(page)

    # ------------------------------------------------------------------ loading and selection
    def _set_loading_state(self, active: bool, message: str = "") -> None:
        self.table_list.setEnabled(not active)
        self.field_list.setEnabled(not active)
        self.review_steps.setEnabled(not active)
        self.refresh_button.setEnabled(not active)
        self.save_button.setEnabled(not active and bool(self._rows))
        if active:
            self.progress.setRange(0, 0)
            self.progress_label.setText("Loading project data…")
            self.issue_summary.setText(
                "The Studio is open and responsive while schema profiling runs in the background."
            )
        else:
            self.progress.setRange(0, 100)
        if message:
            self.status.setText(message)

    def load_rows(self, *, refresh: bool) -> None:
        self._commit_current_field()
        self._commit_current_table()
        previous_table = self._current_table
        self._load_generation += 1
        generation = self._load_generation
        self._set_loading_state(
            True,
            "Refreshing observed project data…" if refresh else "Loading dictionary in the background…",
        )

        def load_dictionary():
            if self._closing or generation != self._load_generation:
                return None
            return portfolio_studios.dictionary_snapshot(
                self.context,
                refresh=refresh,
            )

        worker = _BackgroundJob(load_dictionary)
        self._load_worker = worker

        def apply_result(payload) -> None:
            if (
                payload is None
                or self._closing
                or generation != self._load_generation
            ):
                return
            rows, tables = payload
            self._apply_loaded_rows(
                rows,
                tables,
                previous_table,
                refreshed=refresh,
            )

        def apply_error(message: str) -> None:
            if self._closing or generation != self._load_generation:
                return
            self._rows = []
            self._tables = {}
            self._set_loading_state(False, f"Could not scan project data: {message}")
            self._clear_table_review()
            self._clear_field_review()

        receiver = None

        def finish() -> None:
            if generation == self._load_generation:
                self._load_worker = None
                self._load_receiver = None
            if receiver is not None:
                receiver.deleteLater()

        receiver = _BackgroundJobReceiver(
            on_result=apply_result,
            on_error=apply_error,
            on_finished=finish,
            parent=self,
        )
        self._load_receiver = receiver
        worker.signals.result.connect(receiver.receive_result)
        worker.signals.error.connect(receiver.receive_error)
        worker.signals.finished.connect(receiver.receive_finished)
        _studio_io_pool().start(worker)

    def _apply_loaded_rows(
        self,
        rows: list[dict[str, Any]],
        tables: dict[str, dict[str, Any]],
        previous_table: str,
        *,
        refreshed: bool,
    ) -> None:
        self._rows = rows
        self._tables = tables
        self._current_field_index = None
        self._current_table = ""
        self._loading = True
        self.table_list.clear()
        self.field_list.clear()
        for table_name in self._tables:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, table_name)
            self.table_list.addItem(item)
        self._loading = False
        self._refresh_table_list_labels()

        target = previous_table if previous_table in self._tables else next(
            iter(self._tables), ""
        )
        if target:
            self._select_table_item(target)
        else:
            self._clear_table_review()
            self._clear_field_review()
        self._dirty = False
        self._set_loading_state(False)
        self._update_progress()
        if refreshed:
            self.status.setText(
                "Observed project data refreshed; definitions and review decisions "
                "were preserved"
            )
        else:
            self.status.setText(
                f"Loaded {len(self._tables)} table(s) and {len(self._rows)} field(s)"
            )

    def _select_table_item(self, table_name: str) -> bool:
        for index in range(self.table_list.count()):
            item = self.table_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == table_name:
                self.table_list.setCurrentItem(item)
                return True
        return False

    def _on_table_selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if self._loading or current is None:
            return
        self._commit_current_field()
        self._commit_current_table()
        self._current_table = str(current.data(Qt.ItemDataRole.UserRole) or "")
        self._current_field_index = None
        self._load_table_review(self._current_table)
        self._populate_field_list(select_first=False)
        self._clear_field_review(
            "Complete Step 1, then choose Continue to Field Review."
        )
        self.review_steps.setCurrentIndex(0)
        self._update_progress()

    def _load_table_review(self, table_name: str) -> None:
        table = self._tables.get(table_name, {})
        table_rows = self._rows_for_table(table_name)
        self._loading = True
        self.table_title.setText(table_name or "Select a table")
        self.table_business_name.setText(str(table.get("business_name") or ""))
        self.table_description.setPlainText(str(table.get("description") or ""))
        self.table_grain.setPlainText(str(table.get("grain") or ""))
        self.table_primary_key.clear()
        self.table_primary_key.addItems(
            ["Review required", "No single-column primary key"]
            + [str(row.get("column") or "") for row in table_rows]
        )
        self.table_primary_key.setCurrentText(
            str(table.get("expected_primary_key") or "Review required")
        )
        self.table_notes.setPlainText(str(table.get("notes") or ""))
        self.table_relationships.setPlainText(str(table.get("relationships") or ""))
        row_count = table.get("row_count")
        source = str(table.get("source_path") or "Not available")
        observed_lines = [
            f"Observed rows: {row_count if row_count is not None else 'Unknown'}  •  "
            f"Fields: {len(table_rows)}",
            f"Source: {source}",
        ]
        autofilled_fields = table.get("autofilled_fields") or []
        autofill_source = str(table.get("autofill_source") or "").strip()
        if autofilled_fields:
            observed_lines.append(
                "Autofilled from prior milestones: "
                + ", ".join(str(item) for item in autofilled_fields)
            )
        if autofill_source:
            observed_lines.append("Prior milestone evidence: " + autofill_source)
        self.table_observed.setText("\n".join(observed_lines))
        self._loading = False
        self._update_table_guidance()

    def _clear_table_review(self) -> None:
        self.table_title.setText("Select a table")
        self.table_observed.setText("Choose a table from the navigator.")
        self.table_guidance.setText("Prior milestone decisions will appear here automatically.")

    def _populate_field_list(self, *_args, select_first: bool = False) -> None:
        if self._loading:
            return
        self._commit_current_field()
        preserve = self._current_field_index
        unresolved_only = self.only_unreviewed.isChecked()
        candidates: list[tuple[int, dict[str, Any], list[dict[str, str]]]] = []
        for index, row in enumerate(self._rows):
            if str(row.get("table") or "") != self._current_table:
                continue
            issues = portfolio_studios.dictionary_field_issues(
                row, include_review_status=True
            )
            unresolved = any(issue["severity"] != "Suggestion" for issue in issues)
            if unresolved_only and not unresolved:
                continue
            candidates.append((index, row, issues))

        self._loading = True
        self.field_list.clear()
        selected_item = None
        for index, row, issues in candidates:
            status = self._field_status(row, issues)
            issue_text = self._main_issue(row, issues)
            item = QListWidgetItem(
                f"{status}  {row.get('column') or ''}\n     {issue_text}"
            )
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setToolTip(
                "\n".join(issue["message"] for issue in issues)
                or "No unresolved issues"
            )
            self.field_list.addItem(item)
            if index == preserve:
                selected_item = item
        self.fields_title.setText(
            f"Fields in {self._current_table or 'selected table'} ({len(candidates)})"
        )
        self._loading = False

        if selected_item is not None:
            self.field_list.setCurrentItem(selected_item)
        elif self.field_list.count() and (select_first or unresolved_only):
            self.field_list.setCurrentRow(0)

    def _on_field_selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if self._loading or current is None:
            return
        index = current.data(Qt.ItemDataRole.UserRole)
        if index is None:
            return
        self._commit_current_field()
        self._load_field(int(index))
        self.review_steps.setCurrentIndex(1)

    def _load_field(self, index: int) -> None:
        if not 0 <= index < len(self._rows):
            self._clear_field_review()
            return
        row = self._rows[index]
        self._current_field_index = index
        self._loading = True
        self.field_title.setText(f"{row.get('table')}.{row.get('column')}")
        for key, label in self.field_summary_labels.items():
            value = row.get(key)
            label.setText("—" if value is None or value == "" else str(value))

        self._render_field_evidence(row)
        if not bool(row.get("evidence_loaded")):
            self._start_field_evidence_load(index)

        self.definition.setPlainText(str(row.get("definition") or ""))
        self.expected_type.setCurrentText(str(row.get("expected_type") or ""))
        self.nullable.setCurrentText(str(row.get("nullable") or ""))
        self.key_role.setCurrentText(str(row.get("key") or "Not a key"))
        self.expected_unique.setCurrentText(
            str(row.get("expected_unique") or "Review required")
        )
        self.relationship.setText(str(row.get("relationship") or ""))
        self.valid_values.setPlainText(str(row.get("valid_values") or ""))
        self.unit.setText(str(row.get("unit") or ""))
        self.notes.setPlainText(str(row.get("notes") or ""))
        self.cleaning_expectation.setPlainText(
            str(row.get("cleaning_expectation") or "")
        )
        self.warning_resolution.setPlainText(
            str(row.get("warning_resolution") or "")
        )
        self._loading = False
        self._refresh_current_field_issues()
        self._update_field_position()
        self.check_field_button.setEnabled(True)
        self.mark_field_button.setEnabled(True)

    def _render_field_evidence(self, row: dict[str, Any]) -> None:
        loading = not bool(row.get("evidence_loaded"))
        samples = str(
            row.get("sample_values")
            or ("Loading examples…" if loading else "No sample values available")
        )
        top = str(
            row.get("top_values")
            or ("Loading frequencies…" if loading else "No value frequencies available")
        )
        duplicates = str(
            row.get("duplicate_values")
            or (
                "Loading repeated values…"
                if loading
                else "No repeated values detected in the sample profile"
            )
        )
        orphans = str(
            row.get("orphan_values")
            or (
                "Loading relationship examples…"
                if loading
                else "No unmatched relationship values detected"
            )
        )
        range_text = str(
            row.get("observed_range")
            or ("Loading…" if loading else "Not available")
        )
        referenced_by = str(row.get("referenced_by") or "None detected")
        source = str(row.get("source_path") or "Not available")
        evidence_error = str(row.get("evidence_error") or "").strip()
        invalid = row.get("invalid_value_count")
        blank = row.get("blank_count")
        orphan_count = row.get("orphan_count")
        self.samples.setPlainText(
            "Sample values\n-------------\n"
            + samples
            + "\n\nMost common values\n------------------\n"
            + top
            + "\n\nRepeated values\n---------------\n"
            + duplicates
            + "\n\nUnmatched relationship values\n-----------------------------\n"
            + orphans
            + "\n\nAdditional observed facts\n-------------------------\n"
            + f"Blank strings: {blank if blank is not None else 'Unknown'}\n"
            + f"Values failing expected rule: {invalid if invalid is not None else 'Unknown'}\n"
            + f"Unmatched relationship count: {orphan_count if orphan_count is not None else 'Unknown'}\n"
            + f"Observed range: {range_text}\n"
            + f"Referenced by: {referenced_by}\n"
            + f"Source: {source}"
            + (f"\nEvidence load note: {evidence_error}" if evidence_error else "")
        )

    def _start_field_evidence_load(self, index: int) -> None:
        if self._closing or index in self._evidence_workers:
            return
        if not 0 <= index < len(self._rows):
            return
        row_snapshot = dict(self._rows[index])
        def load_evidence():
            if self._closing:
                return None
            return portfolio_studios.dictionary_field_evidence(
                self.context, row_snapshot
            )

        worker = _BackgroundJob(load_evidence)
        self._evidence_workers[index] = worker

        def apply_result(evidence) -> None:
            if (
                evidence is None
                or self._closing
                or not 0 <= index < len(self._rows)
            ):
                return
            self._rows[index].update(dict(evidence or {}))
            if self._current_field_index == index:
                self._render_field_evidence(self._rows[index])

        def apply_error(message: str) -> None:
            if self._closing or not 0 <= index < len(self._rows):
                return
            self._rows[index]["evidence_loaded"] = True
            self._rows[index]["evidence_error"] = message
            if self._current_field_index == index:
                self._render_field_evidence(self._rows[index])

        receiver = None

        def finish() -> None:
            self._evidence_workers.pop(index, None)
            self._evidence_receivers.pop(index, None)
            if receiver is not None:
                receiver.deleteLater()

        receiver = _BackgroundJobReceiver(
            on_result=apply_result,
            on_error=apply_error,
            on_finished=finish,
            parent=self,
        )
        self._evidence_receivers[index] = receiver
        worker.signals.result.connect(receiver.receive_result)
        worker.signals.error.connect(receiver.receive_error)
        worker.signals.finished.connect(receiver.receive_finished)
        _studio_io_pool().start(worker)

    def _clear_field_review(
        self, message: str = "Choose a field from the navigator to begin."
    ) -> None:
        self._current_field_index = None
        self.field_title.setText("Select a field")
        self.field_state.setText(message)
        self.field_position.setText("")
        self.field_guidance.setText("Select a field to see the next required decision.")
        for label in getattr(self, "field_summary_labels", {}).values():
            label.setText("—")
        if hasattr(self, "samples"):
            self._loading = True
            self.samples.clear()
            self.field_issues.clear()
            self.definition.clear()
            self.expected_type.setCurrentText("")
            self.nullable.setCurrentText("")
            self.key_role.setCurrentText("")
            self.expected_unique.setCurrentText("")
            self.relationship.clear()
            self.valid_values.clear()
            self.unit.clear()
            self.notes.clear()
            self.cleaning_expectation.clear()
            self.warning_resolution.clear()
            self._loading = False
            self.check_field_button.setEnabled(False)
            self.mark_field_button.setEnabled(False)

    # ------------------------------------------------------------------ committing edits
    def _mark_dirty(self, *_args) -> None:
        if self._loading:
            return
        sender = self.sender()
        if (
            sender in getattr(self, "_field_editors", ())
            and self._current_field_index is not None
        ):
            self._rows[self._current_field_index]["reviewed"] = "No"
            if self._current_table in self._tables:
                self._tables[self._current_table]["reviewed"] = "No"
        elif (
            sender in getattr(self, "_table_editors", ())
            and self._current_table in self._tables
        ):
            self._tables[self._current_table]["reviewed"] = "No"
        self._dirty = True
        self.status.setText("Unsaved dictionary changes")
        self.saved.emit("Unsaved dictionary changes")

    def _commit_current_field(self) -> None:
        if self._loading or self._current_field_index is None:
            return
        if not 0 <= self._current_field_index < len(self._rows):
            return
        self._rows[self._current_field_index].update(
            {
                "definition": self.definition.toPlainText().strip(),
                "expected_type": self.expected_type.currentText().strip(),
                "nullable": self.nullable.currentText().strip(),
                "key": self.key_role.currentText().strip(),
                "expected_unique": self.expected_unique.currentText().strip(),
                "relationship": self.relationship.text().strip(),
                "valid_values": self.valid_values.toPlainText().strip(),
                "unit": self.unit.text().strip(),
                "notes": self.notes.toPlainText().strip(),
                "cleaning_expectation": self.cleaning_expectation.toPlainText().strip(),
                "warning_resolution": self.warning_resolution.toPlainText().strip(),
            }
        )

    def _commit_current_table(self) -> None:
        if (
            self._loading
            or not self._current_table
            or self._current_table not in self._tables
        ):
            return
        self._tables[self._current_table].update(
            {
                "business_name": self.table_business_name.text().strip(),
                "description": self.table_description.toPlainText().strip(),
                "grain": self.table_grain.toPlainText().strip(),
                "expected_primary_key": self.table_primary_key.currentText().strip(),
                "notes": self.table_notes.toPlainText().strip(),
            }
        )

    # ------------------------------------------------------------------ status helpers
    def _rows_for_table(self, table_name: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self._rows
            if str(row.get("table") or "") == table_name
        ]

    def _field_status(
        self,
        row: dict[str, Any],
        issues: list[dict[str, str]] | None = None,
    ) -> str:
        issues = issues if issues is not None else portfolio_studios.dictionary_field_issues(row)
        meaningful = [issue for issue in issues if issue["code"] != "not_reviewed"]
        if any(issue["severity"] == "Blocking" for issue in meaningful):
            return "!"
        if any(issue["severity"] == "Documentation" for issue in meaningful):
            return "⚠"
        if portfolio_studios._is_reviewed(row.get("reviewed")):
            return "✓"
        return "○"

    def _main_issue(
        self,
        row: dict[str, Any],
        issues: list[dict[str, str]] | None = None,
    ) -> str:
        issues = issues if issues is not None else portfolio_studios.dictionary_field_issues(row)
        meaningful = [issue for issue in issues if issue["code"] != "not_reviewed"]
        if meaningful:
            issue = sorted(
                meaningful,
                key=lambda item: self.SEVERITY_RANK.get(item["severity"], 99),
            )[0]
            prefix = f"{row.get('table')}.{row.get('column')} "
            return issue["message"].split(prefix, 1)[-1]
        if portfolio_studios._is_reviewed(row.get("reviewed")):
            return "Complete"
        return "Ready to review"

    def _refresh_current_field_issues(self) -> None:
        if self._current_field_index is None:
            return
        row = self._rows[self._current_field_index]
        issues = portfolio_studios.dictionary_field_issues(
            row, include_review_status=False
        )
        required = [issue for issue in issues if issue["severity"] != "Suggestion"]
        suggestions = [issue for issue in issues if issue["severity"] == "Suggestion"]
        if issues:
            self.field_issues.setPlainText(
                "\n\n".join(
                    f"{issue['severity']}: {issue['message']}" for issue in issues
                )
            )
        else:
            self.field_issues.setPlainText(
                "No blocking or documentation issues remain. This field is ready to review."
            )

        reviewed = portfolio_studios._is_reviewed(row.get("reviewed"))
        if required:
            next_issue = required[0]
            self.field_guidance.setText(
                "Next required action:\n" + next_issue["message"]
            )
            self.field_state.setText(
                f"{'Reviewed' if reviewed else 'Not reviewed'}  •  "
                f"{len(required)} required item{'s' if len(required) != 1 else ''} remain"
            )
        elif suggestions:
            self.field_guidance.setText(
                "Required review is complete. The Evidence & Exceptions tab contains "
                f"{len(suggestions)} documented observation{'s' if len(suggestions) != 1 else ''}."
            )
            self.field_state.setText(
                f"{'Reviewed' if reviewed else 'Ready to review'}  •  "
                "No required items remain"
            )
        else:
            self.field_guidance.setText(
                "This field has all required documentation. Choose Save, Review, and Continue."
            )
            self.field_state.setText(
                "Reviewed" if reviewed else "Ready to review"
            )

    def _update_field_position(self) -> None:
        if self._current_field_index is None or not self._current_table:
            self.field_position.setText("")
            return
        indices = [
            index
            for index, row in enumerate(self._rows)
            if str(row.get("table") or "") == self._current_table
        ]
        try:
            position = indices.index(self._current_field_index) + 1
        except ValueError:
            self.field_position.setText("")
            return
        self.field_position.setText(f"Field {position} of {len(indices)}")

    def _update_table_guidance(self) -> None:
        if not self._current_table:
            return
        self._commit_current_table()
        table = self._tables[self._current_table]
        rows = self._rows_for_table(self._current_table)
        issues = portfolio_studios.dictionary_table_issues(
            table, rows, include_review_status=False
        )
        if issues:
            self.table_guidance.setText(
                "Next required action:\n" + issues[0]["message"]
            )
        else:
            autofilled = self._tables.get(self._current_table, {}).get("autofilled_fields", [])
            if autofilled:
                self.table_guidance.setText(
                    "Loaded from earlier milestones: "
                    + ", ".join(str(item) for item in autofilled)
                    + ". Confirm these decisions, then continue to the field review."
                )
            else:
                self.table_guidance.setText(
                    "Table setup is complete. Continue to review its fields."
                )

    def _refresh_table_list_labels(self) -> None:
        for index in range(self.table_list.count()):
            item = self.table_list.item(index)
            table_name = str(item.data(Qt.ItemDataRole.UserRole) or "")
            rows = self._rows_for_table(table_name)
            reviewed_fields = sum(
                portfolio_studios._is_reviewed(row.get("reviewed")) for row in rows
            )
            field_issues: list[dict[str, str]] = []
            for row in rows:
                field_issues.extend(
                    portfolio_studios.dictionary_field_issues(
                        row, include_review_status=False
                    )
                )
            blockers = sum(
                issue["severity"] == "Blocking" for issue in field_issues
            )
            docs = sum(
                issue["severity"] == "Documentation" for issue in field_issues
            )
            table = self._tables.get(table_name, {})
            table_reviewed = portfolio_studios._is_reviewed(table.get("reviewed"))
            icon = (
                "✓"
                if table_reviewed
                and reviewed_fields == len(rows)
                and not blockers
                and not docs
                else ("!" if blockers else "○")
            )
            suffix = f"{reviewed_fields}/{len(rows)} fields reviewed"
            if blockers:
                suffix += f"  •  {blockers} blocking"
            elif docs:
                suffix += f"  •  {docs} to document"
            item.setText(f"{icon}  {table_name}\n     {suffix}")
            item.setToolTip(suffix)

    def _refresh_field_list_labels(self) -> None:
        for index in range(self.field_list.count()):
            item = self.field_list.item(index)
            row_index = item.data(Qt.ItemDataRole.UserRole)
            if row_index is None or not 0 <= int(row_index) < len(self._rows):
                continue
            row = self._rows[int(row_index)]
            issues = portfolio_studios.dictionary_field_issues(
                row, include_review_status=True
            )
            item.setText(
                f"{self._field_status(row, issues)}  {row.get('column') or ''}\n"
                f"     {self._main_issue(row, issues)}"
            )
            item.setToolTip(
                "\n".join(issue["message"] for issue in issues)
                or "No unresolved issues"
            )

    def _update_finalize_summary(self) -> None:
        if self._current_table and self._current_table in self._tables:
            table = self._tables[self._current_table]
            rows = self._rows_for_table(self._current_table)
            reviewed_fields = sum(
                portfolio_studios._is_reviewed(row.get("reviewed")) for row in rows
            )
            issues = [
                issue
                for issue in portfolio_studios.dictionary_table_issues(
                    table, rows, include_review_status=True
                )
                if issue["code"] != "table_not_reviewed"
                and issue["severity"] != "Suggestion"
            ]
            table_reviewed = portfolio_studios._is_reviewed(table.get("reviewed"))
            self.finalize_table_title.setText(
                f"Current table: {self._current_table}"
            )
            if table_reviewed:
                text = f"Reviewed  •  {reviewed_fields}/{len(rows)} fields complete"
            elif issues:
                text = (
                    f"{reviewed_fields}/{len(rows)} fields reviewed. "
                    f"{len(issues)} item{'s' if len(issues) != 1 else ''} remain before the table can be reviewed."
                )
            else:
                text = "All table and field requirements are complete. Mark this table reviewed."
            self.finalize_table_summary.setText(text)
            self.mark_table_button.setText(
                "Table Reviewed" if table_reviewed else "Mark Current Table Reviewed"
            )
            self.mark_table_button.setEnabled(not table_reviewed)
        else:
            self.finalize_table_title.setText("Current table")
            self.finalize_table_summary.setText("Select a table to see its readiness.")
            self.mark_table_button.setEnabled(False)

        total_fields = len(self._rows)
        reviewed_fields = sum(
            portfolio_studios._is_reviewed(row.get("reviewed")) for row in self._rows
        )
        reviewed_tables = sum(
            portfolio_studios._is_reviewed(table.get("reviewed"))
            for table in self._tables.values()
        )
        validation = portfolio_studios.dictionary_validation(
            self._rows, self._tables, include_review_status=True
        )
        unresolved = [
            issue for issue in validation if issue["severity"] != "Suggestion"
        ]
        self.finalize_overall_summary.setText(
            f"{reviewed_fields}/{total_fields} fields reviewed  •  "
            f"{reviewed_tables}/{len(self._tables)} tables reviewed  •  "
            f"{len(unresolved)} unresolved requirement{'s' if len(unresolved) != 1 else ''}"
        )

    def _update_progress(self) -> None:
        self._commit_current_field()
        self._commit_current_table()
        total = len(self._rows)
        reviewed = sum(
            portfolio_studios._is_reviewed(row.get("reviewed")) for row in self._rows
        )
        validation = portfolio_studios.dictionary_validation(
            self._rows, self._tables, include_review_status=True
        )
        unresolved = [
            issue for issue in validation if issue["severity"] != "Suggestion"
        ]
        table_reviewed = sum(
            portfolio_studios._is_reviewed(table.get("reviewed"))
            for table in self._tables.values()
        )
        self.progress_label.setText(f"{reviewed} of {total} fields reviewed")
        self.progress.setValue(round((reviewed / total) * 100) if total else 0)
        self.issue_summary.setText(
            f"{table_reviewed}/{len(self._tables)} tables reviewed  •  "
            f"{len(unresolved)} unresolved requirement{'s' if len(unresolved) != 1 else ''}"
        )
        self._refresh_table_list_labels()
        self._refresh_field_list_labels()
        self._update_table_guidance()
        self._refresh_current_field_issues()
        self._update_finalize_summary()

    # ------------------------------------------------------------------ guided actions
    def continue_to_fields(self) -> None:
        self._commit_current_table()
        if not self._current_table:
            return
        table = self._tables[self._current_table]
        rows = self._rows_for_table(self._current_table)
        issues = portfolio_studios.dictionary_table_issues(
            table, rows, include_review_status=False
        )
        if issues:
            self._update_table_guidance()
            self.status.setText(issues[0]["message"])
            return
        self._write_progress(silent=True)
        unresolved = [
            index
            for index, row in enumerate(self._rows)
            if str(row.get("table") or "") == self._current_table
            and portfolio_studios.dictionary_field_issues(
                row, include_review_status=True
            )
        ]
        target = unresolved[0] if unresolved else next(
            (
                index
                for index, row in enumerate(self._rows)
                if str(row.get("table") or "") == self._current_table
            ),
            None,
        )
        self._populate_field_list(select_first=False)
        if target is None:
            self.review_steps.setCurrentIndex(2)
            return
        self._select_field_index(target)
        self.review_steps.setCurrentIndex(1)

    def check_current_field(self) -> None:
        self._commit_current_field()
        if self._current_field_index is None:
            return
        self._refresh_current_field_issues()
        row = self._rows[self._current_field_index]
        issues = [
            issue
            for issue in portfolio_studios.dictionary_field_issues(
                row, include_review_status=False
            )
            if issue["severity"] != "Suggestion"
        ]
        if issues:
            self.status.setText(
                f"{len(issues)} required item{'s' if len(issues) != 1 else ''} remain for "
                f"{row.get('table')}.{row.get('column')}"
            )
        else:
            self.status.setText(
                f"{row.get('table')}.{row.get('column')} is ready to review"
            )
        self._update_progress()

    def mark_field_reviewed(self) -> None:
        self._commit_current_field()
        if self._current_field_index is None:
            return
        row = self._rows[self._current_field_index]
        issues = [
            issue
            for issue in portfolio_studios.dictionary_field_issues(
                row, include_review_status=False
            )
            if issue["severity"] != "Suggestion"
        ]
        if issues:
            self._refresh_current_field_issues()
            self.field_detail_tabs.setCurrentIndex(0)
            self.status.setText(
                "Field still needs work: " + issues[0]["message"]
            )
            return

        current_index = self._current_field_index
        current_table = self._current_table
        row["reviewed"] = "Yes"
        self._dirty = True
        self._write_progress(silent=True)
        self._update_progress()

        same_table = [
            index
            for index, candidate in enumerate(self._rows)
            if str(candidate.get("table") or "") == current_table
            and index != current_index
            and portfolio_studios.dictionary_field_issues(
                candidate, include_review_status=True
            )
        ]
        later = [index for index in same_table if index > current_index]
        target = (later or same_table)[0] if (later or same_table) else None
        if target is not None:
            self._populate_field_list(select_first=False)
            self._select_field_index(target)
            self.review_steps.setCurrentIndex(1)
        else:
            self._populate_field_list(select_first=False)
            self.review_steps.setCurrentIndex(2)
            self.status.setText(
                f"All fields in {current_table} are reviewed. Finish the table in Step 3."
            )

    def mark_table_reviewed(self) -> None:
        self._commit_current_field()
        self._commit_current_table()
        if not self._current_table:
            return
        table = self._tables[self._current_table]
        rows = self._rows_for_table(self._current_table)
        issues = [
            issue
            for issue in portfolio_studios.dictionary_table_issues(
                table, rows, include_review_status=True
            )
            if issue["code"] != "table_not_reviewed"
            and issue["severity"] != "Suggestion"
        ]
        if issues:
            self.status.setText(
                "Table still needs work: " + issues[0]["message"]
            )
            self._update_finalize_summary()
            return

        finished_table = self._current_table
        table["reviewed"] = "Yes"
        self._dirty = True
        self._write_progress(silent=True)
        self._update_progress()

        next_table = next(
            (
                name
                for name, metadata in self._tables.items()
                if not portfolio_studios._is_reviewed(metadata.get("reviewed"))
            ),
            None,
        )
        if next_table:
            self._select_table_item(next_table)
            self.review_steps.setCurrentIndex(0)
            self.status.setText(
                f"{finished_table} is complete. Continue with {next_table}."
            )
        else:
            self.review_steps.setCurrentIndex(2)
            self.status.setText(
                "Every table is reviewed. Run Check Full Dictionary."
            )

    # ------------------------------------------------------------------ validation and navigation
    def validate(self) -> list[str]:
        self._commit_current_field()
        self._commit_current_table()
        self._write_progress(silent=True)
        issues = portfolio_studios.dictionary_validation(
            self._rows, self._tables, include_review_status=True
        )
        portfolio_studios.record_dictionary_validation(
            self.context, self._rows, self._tables, issues
        )
        self._show_validation_results(issues)
        unresolved = [
            issue for issue in issues if issue["severity"] != "Suggestion"
        ]
        self.status.setText(
            "Dictionary check passed"
            if not unresolved
            else f"Dictionary check found {len(unresolved)} unresolved item(s)"
        )
        self.saved.emit(self.status.text())
        self._update_progress()
        return [issue["message"] for issue in unresolved]

    def _show_validation_results(self, issues: list[dict[str, str]]) -> None:
        if not issues:
            QMessageBox.information(
                self,
                "Dictionary Check",
                "All table and field requirements are complete. Generate the final document after the last edit.",
            )
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Dictionary Check Results")
        dialog.resize(900, 560)
        layout = QVBoxLayout(dialog)
        unresolved = [
            issue for issue in issues if issue["severity"] != "Suggestion"
        ]
        summary = QLabel(
            f"{len(unresolved)} unresolved requirement{'s' if len(unresolved) != 1 else ''}. "
            "Double-click an item to open the correct table or field."
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)
        results = QTableWidget(len(issues), 3)
        results.setHorizontalHeaderLabels(("Severity", "Location", "Issue"))
        results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        results.verticalHeader().setVisible(False)
        results.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        results.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        results.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        ordered = sorted(
            issues,
            key=lambda item: self.SEVERITY_RANK.get(item["severity"], 99),
        )
        for row_index, issue in enumerate(ordered):
            severity = QTableWidgetItem(issue["severity"])
            severity.setData(Qt.ItemDataRole.UserRole, issue)
            results.setItem(row_index, 0, severity)
            results.setItem(row_index, 1, QTableWidgetItem(issue["location"]))
            message = QTableWidgetItem(issue["message"])
            message.setToolTip(issue["message"])
            results.setItem(row_index, 2, message)
        layout.addWidget(results, 1)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)

        def open_issue(row: int, _column: int) -> None:
            item = results.item(row, 0)
            issue = item.data(Qt.ItemDataRole.UserRole) if item else None
            if issue:
                dialog.accept()
                self._navigate_to_issue(issue)

        results.cellDoubleClicked.connect(open_issue)
        dialog.exec()

    def _navigate_to_issue(self, issue: dict[str, str]) -> None:
        table = str(issue.get("table") or "")
        column = str(issue.get("column") or "")
        if table:
            self._select_table_item(table)
        if column:
            self.only_unreviewed.setChecked(False)
            self._populate_field_list(select_first=False)
            for index, row in enumerate(self._rows):
                if (
                    str(row.get("table") or "") == table
                    and str(row.get("column") or "") == column
                ):
                    self._select_field_index(index)
                    self.review_steps.setCurrentIndex(1)
                    return
        self.review_steps.setCurrentIndex(0)

    def _select_field_index(self, index: int) -> bool:
        for list_index in range(self.field_list.count()):
            item = self.field_list.item(list_index)
            if item.data(Qt.ItemDataRole.UserRole) == index:
                self.field_list.setCurrentItem(item)
                self._load_field(index)
                return True
        if self.only_unreviewed.isChecked():
            self.only_unreviewed.setChecked(False)
            self._populate_field_list(select_first=False)
            return self._select_field_index(index)
        return False

    def next_unresolved_field(self) -> None:
        self._commit_current_field()
        if not self._rows:
            return
        start = self._current_field_index if self._current_field_index is not None else -1
        order = list(range(start + 1, len(self._rows))) + list(
            range(0, start + 1)
        )
        for index in order:
            row = self._rows[index]
            if portfolio_studios.dictionary_field_issues(
                row, include_review_status=True
            ):
                table_name = str(row.get("table") or "")
                if table_name != self._current_table:
                    self._select_table_item(table_name)
                self._populate_field_list(select_first=False)
                self._select_field_index(index)
                self.review_steps.setCurrentIndex(1)
                return
        self.review_steps.setCurrentIndex(2)
        self.status.setText(
            "No unresolved fields remain. Finish any table-level reviews in Step 3."
        )

    def previous_field(self) -> None:
        self._commit_current_field()
        if self._current_field_index is None:
            return
        table_indices = [
            index
            for index, row in enumerate(self._rows)
            if str(row.get("table") or "") == self._current_table
        ]
        try:
            position = table_indices.index(self._current_field_index)
        except ValueError:
            return
        if position > 0:
            self._select_field_index(table_indices[position - 1])

    # ------------------------------------------------------------------ persistence
    def _write_progress(self, *, silent: bool) -> Path | None:
        self._commit_current_field()
        self._commit_current_table()
        try:
            path = portfolio_studios.save_dictionary_progress(
                self.context, self._rows, self._tables
            )
            self._dirty = False
            if not silent:
                self.status_message(f"Saved progress to {path.name}")
            return path
        except Exception as exc:
            QMessageBox.warning(
                self, "Could Not Save Dictionary Progress", str(exc)
            )
            return None

    def save_progress(self) -> None:
        path = self._write_progress(silent=False)
        if path is not None:
            self._update_progress()

    def generate_document(self) -> None:
        self._commit_current_field()
        self._commit_current_table()
        if self._write_progress(silent=True) is None:
            return
        try:
            path = portfolio_studios.generate_dictionary_markdown(
                self.context, self._rows, self._tables
            )
            self._dirty = False
            self.status_message(f"Generated {path.name}")
            self._update_progress()
        except Exception as exc:
            QMessageBox.warning(
                self, "Could Not Generate Data Dictionary", str(exc)
            )

    def rescan(self) -> None:
        self._commit_current_field()
        self._commit_current_table()
        if self._write_progress(silent=True) is None:
            return
        try:
            self.load_rows(refresh=True)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Refresh Observed Data", str(exc))

    def prepare_for_completion(self) -> None:
        self._commit_current_field()
        self._commit_current_table()
        portfolio_studios.save_dictionary_progress(
            self.context, self._rows, self._tables
        )

    def completion_issues(self) -> list[str]:
        self._commit_current_field()
        self._commit_current_table()
        return portfolio_studios.dictionary_completion_issues(
            self.context, self._rows, self._tables
        )

    def shutdown(self) -> None:
        self._closing = True
        self._load_generation += 1
        if not self._dirty:
            return
        try:
            self._commit_current_field()
            self._commit_current_table()
            portfolio_studios.save_dictionary_progress(
                self.context, self._rows, self._tables
            )
            self._dirty = False
        except Exception:
            pass

class CleaningFilesStudio(StudioWidget):
    METHODS = (
        "SQL in Cleaning Notebook",
        "Python in Cleaning Notebook",
        "Google Sheets",
        "Local Spreadsheet",
        "SQL file",
        "No cleaning required",
    )

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(
            layout,
            "Files & Outputs",
            "Choose how each table will be cleaned, keep raw files untouched, and register the cleaned outputs when your manual work is finished.",
        )
        self.google_status = QLabel("Google Sheets: checking connection…")
        self.google_status.setObjectName("Muted")
        layout.addWidget(self.google_status)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(("Table", "Method", "Raw source", "Working artifact", "Cleaned output", "Status", "Notes"))
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        first_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Select a table to manage its working files")
        self.status.setObjectName("Muted")
        first_actions.addWidget(self.status, 1)
        refresh = QPushButton("Refresh Files")
        refresh.clicked.connect(self.refresh_rows)
        first_actions.addWidget(refresh)
        save = QPushButton("Save Plan")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_rows)
        first_actions.addWidget(save)
        layout.addLayout(first_actions)
        second_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        working = QPushButton("Create Spreadsheet Working Copy")
        working.clicked.connect(self.create_working_copy)
        second_actions.addWidget(working)
        open_selected = QPushButton("Open Selected Artifact")
        open_selected.clicked.connect(self.open_selected)
        second_actions.addWidget(open_selected)
        register = QPushButton("Import Cleaned Dataset")
        register.clicked.connect(self.register_output)
        second_actions.addWidget(register)
        compare = QPushButton("Compare Raw and Cleaned")
        compare.clicked.connect(self.compare_selected)
        second_actions.addWidget(compare)
        second_actions.addStretch()
        layout.addLayout(second_actions)
        google_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        setup = QPushButton("Google Sheets Setup")
        setup.clicked.connect(self.open_google_setup)
        google_actions.addWidget(setup)
        connect = QPushButton("Connect Google Account")
        connect.clicked.connect(self.connect_google)
        google_actions.addWidget(connect)
        create_sheet = QPushButton("Create Google Sheets Working Copy")
        create_sheet.clicked.connect(self.create_google_sheet)
        google_actions.addWidget(create_sheet)
        open_sheet = QPushButton("Open Connected Sheet")
        open_sheet.clicked.connect(self.open_google_sheet)
        google_actions.addWidget(open_sheet)
        import_sheet = QPushButton("Import from Google Sheets")
        import_sheet.clicked.connect(self.import_google_sheet)
        google_actions.addWidget(import_sheet)
        google_actions.addStretch()
        layout.addLayout(google_actions)
        self.load_rows()
        self.refresh_google_status()

    def load_rows(self) -> None:
        rows = portfolio_studios.cleaning_rows(self.context)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row.get("table") or "")))
            method = QComboBox()
            method.addItems(self.METHODS)
            current = str(row.get("method") or self.METHODS[0])
            method.setCurrentText(current if current in self.METHODS else self.METHODS[0])
            self.table.setCellWidget(row_index, 1, method)
            for column, key in ((2, "source_path"), (3, "working_artifact"), (4, "cleaned_output"), (5, "status"), (6, "notes")):
                item = QTableWidgetItem(str(row.get(key) or ""))
                if key == "source_path":
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, dict(row))
                self.table.setItem(row_index, column, item)
        self.status.setText(f"{len(rows)} table{'s' if len(rows) != 1 else ''} in the cleaning plan")

    def refresh_rows(self) -> None:
        try:
            portfolio_studios.save_cleaning_rows(self.context, self.rows())
        except Exception:
            pass
        self.load_rows()

    def rows(self) -> list[dict[str, Any]]:
        result = []
        for row in range(self.table.rowCount()):
            metadata = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole) or {}
            combo = self.table.cellWidget(row, 1)
            values = dict(metadata)
            values.update(
                {
                    "table": self.table.item(row, 0).text().strip(),
                    "method": combo.currentText() if isinstance(combo, QComboBox) else "SQL in Cleaning Notebook",
                    "source_path": self.table.item(row, 2).text().strip(),
                    "working_artifact": self.table.item(row, 3).text().strip(),
                    "cleaned_output": self.table.item(row, 4).text().strip(),
                    "status": self.table.item(row, 5).text().strip(),
                    "notes": self.table.item(row, 6).text().strip(),
                }
            )
            result.append(values)
        return result

    def prepare_for_completion(self) -> None:
        portfolio_studios.save_cleaning_rows(self.context, self.rows())

    def completion_issues(self) -> list[str]:
        issues = []
        for row in self.rows():
            if row.get("method") == "No cleaning required":
                if not str(row.get("notes") or "").strip():
                    issues.append(f"{row.get('table')}: explain why no cleaning was required.")
            elif not str(row.get("cleaned_output") or "").strip():
                issues.append(f"{row.get('table')}: import or register the cleaned output.")
            else:
                output = self.context.project_dir / str(row.get("cleaned_output"))
                if not output.is_file():
                    issues.append(f"{row.get('table')}: the registered cleaned output cannot be found.")
        return issues

    def save_rows(self) -> None:
        try:
            portfolio_studios.save_cleaning_rows(self.context, self.rows())
            self.status_message("Cleaning plan saved")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Cleaning Plan", str(exc))

    def selected(self) -> tuple[int, dict[str, Any]] | tuple[None, None]:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select a Table", "Choose a table first.")
            return None, None
        return row, self.rows()[row]

    def create_working_copy(self) -> None:
        row_index, row = self.selected()
        if row is None:
            return
        try:
            target = portfolio_studios.create_spreadsheet_working_copy(self.context, row["source_path"])
            self.table.item(row_index, 3).setText(target.relative_to(self.context.project_dir).as_posix())
            self.table.item(row_index, 5).setText("Working copy created")
            self.save_rows()
            self.status_message(f"Created {target.name}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Create Working Copy", str(exc))

    def open_selected(self) -> None:
        _, row = self.selected()
        if row is None:
            return
        relative = row.get("working_artifact") or row.get("cleaned_output") or row.get("source_path")
        path = self.context.project_dir / str(relative)
        if not path.exists():
            QMessageBox.information(self, "Artifact Not Found", "Create or register the selected artifact first.")
            return
        try:
            portfolio_studios.open_path(self.context, path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Artifact", str(exc))

    def register_output(self) -> None:
        row_index, row = self.selected()
        if row is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select the Finished Cleaned Dataset",
            str(self.context.project_dir),
            "Data files (*.csv *.parquet *.json *.jsonl *.ndjson *.xlsx *.xls *.ods);;All files (*)",
        )
        if not path:
            return
        try:
            target = portfolio_studios.register_cleaned_output(self.context, Path(path), row["table"])
            relative = target.relative_to(self.context.project_dir).as_posix()
            self.table.item(row_index, 4).setText(relative)
            self.table.item(row_index, 5).setText("Output imported")
            self.save_rows()
            self.status_message(f"Imported {target.name}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Import Cleaned Dataset", str(exc))

    def compare_selected(self) -> None:
        _, row = self.selected()
        if row is None:
            return
        if not row.get("cleaned_output"):
            QMessageBox.information(self, "No Cleaned Output", "Import or register the cleaned dataset first.")
            return
        raw = self.context.project_dir / row["source_path"]
        cleaned = self.context.project_dir / row["cleaned_output"]
        result = portfolio_studios.compare_tabular_files(raw, cleaned)
        message = (
            f"Raw rows: {result['raw_rows']}\n"
            f"Cleaned rows: {result['cleaned_rows']}\n"
            f"Difference: {result['row_difference']}\n\n"
            f"Missing columns: {', '.join(result['missing_columns']) or 'None'}\n"
            f"New columns: {', '.join(result['new_columns']) or 'None'}"
        )
        QMessageBox.information(self, "Raw vs. Cleaned", message)

    def refresh_google_status(self) -> None:
        try:
            label = google_sheets.connection_label()
        except Exception as exc:
            label = str(exc)
        self.google_status.setText(f"Google Sheets: {label}")

    def open_google_setup(self) -> None:
        path = self.context.root / "documentation" / "GOOGLE_SHEETS_SETUP.md"
        if not path.is_file():
            QMessageBox.information(
                self,
                "Google Sheets Setup",
                "The Google Sheets setup guide was not found.",
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def connect_google(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Google OAuth Desktop Client JSON", str(Path.home()), "JSON files (*.json)")
        if not path:
            return
        try:
            label = google_sheets.connect(Path(path))
            self.google_status.setText(f"Google Sheets: connected as {label}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Connect Google Sheets", str(exc))

    def _csv_values(self, source: Path) -> tuple[list[str], list[list[str]]]:
        if source.suffix.casefold() != ".csv":
            raise ValueError("Google Sheets working copies currently start from CSV tables.")
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            rows = [list(row) for row in reader]
        return header, rows

    def create_google_sheet(self) -> None:
        row_index, row = self.selected()
        if row is None:
            return
        try:
            source = self.context.project_dir / row["source_path"]
            headers, values = self._csv_values(source)
            result = google_sheets.create_working_spreadsheet(
                title=f"{self.context.project_name} — {row['table']} Cleaning",
                table_name=row["table"],
                headers=headers,
                rows=values,
            )
            metadata = self.table.item(row_index, 2).data(Qt.ItemDataRole.UserRole) or {}
            metadata["google_sheet"] = result
            for column in range(self.table.columnCount()):
                item = self.table.item(row_index, column)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, metadata)
            self.table.item(row_index, 3).setText(result["spreadsheet_url"])
            method = self.table.cellWidget(row_index, 1)
            if isinstance(method, QComboBox):
                method.setCurrentText("Google Sheets")
            self.table.item(row_index, 5).setText("Google Sheet connected")
            self.save_rows()
            QDesktopServices.openUrl(QUrl(result["spreadsheet_url"]))
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Create Google Sheet", str(exc))

    def _selected_google_metadata(self) -> tuple[int | None, dict[str, Any] | None, dict[str, Any] | None]:
        row_index, row = self.selected()
        if row is None:
            return None, None, None
        metadata = self.table.item(row_index, 2).data(Qt.ItemDataRole.UserRole) or {}
        sheet = metadata.get("google_sheet") or row.get("google_sheet")
        if not isinstance(sheet, dict):
            QMessageBox.information(self, "No Connected Sheet", "Create a Google Sheets working copy for this table first.")
            return None, None, None
        return row_index, row, sheet

    def open_google_sheet(self) -> None:
        _, _, sheet = self._selected_google_metadata()
        if sheet:
            QDesktopServices.openUrl(QUrl(str(sheet.get("spreadsheet_url") or "")))

    def import_google_sheet(self) -> None:
        row_index, row, sheet = self._selected_google_metadata()
        if sheet is None:
            return
        try:
            values = google_sheets.read_sheet(sheet["spreadsheet_id"], sheet["cleaning_sheet"])
            if not values:
                raise ValueError("The cleaning sheet is empty.")
            staging = self.context.project_dir / "data" / "staging"
            staging.mkdir(parents=True, exist_ok=True)
            temporary = staging / f"{row['table']}_google_sheets_export.csv"
            with temporary.open("w", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerows(values)
            target = portfolio_studios.register_cleaned_output(self.context, temporary, row["table"])
            self.table.item(row_index, 4).setText(target.relative_to(self.context.project_dir).as_posix())
            self.table.item(row_index, 5).setText("Imported from Google Sheets")
            self.save_rows()
            self.status_message(f"Imported {target.name} from Google Sheets")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Import Google Sheet", str(exc))


class DatabaseBuildStudio(StudioWidget):
    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(
            layout,
            "Analytical Database Build",
            "Write and control the build script yourself. Career Accelerator runs it, shows the result, and keeps the process repeatable.",
        )
        self.script_path = portfolio_studios.ensure_database_build_script(context)
        path_label = QLabel(str(self.script_path))
        path_label.setObjectName("Muted")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        self.editor = AssistedTextEdit(
            language="sql",
            project_dir=self.context.project_dir,
        )
        self._sql_highlighter = SqlHighlighter(self.editor.document())
        self.editor.setAcceptRichText(False)
        self.editor.setPlainText(self.script_path.read_text(encoding="utf-8"))
        layout.addWidget(self.editor, 2)
        self.output = QTextBrowser()
        self.output.setPlaceholderText("Build output will appear here.")
        layout.addWidget(self.output, 1)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Edit the script, then run it against the project analytical database")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        save = QPushButton("Save Build Script")
        save.clicked.connect(self.save_script)
        actions.addWidget(save)
        run = QPushButton("Rebuild from Script")
        run.setObjectName("Primary")
        run.clicked.connect(self.run_script)
        actions.addWidget(run)
        layout.addLayout(actions)

    def prepare_for_completion(self) -> None:
        self.script_path.write_text(self.editor.toPlainText(), encoding="utf-8")

    def completion_issues(self) -> list[str]:
        text = self.editor.toPlainText()
        issues = []
        if not portfolio_studios._sql_has_code(text):
            issues.append("Write the database build SQL instead of leaving only the starter comments.")
        status = portfolio_studios.database_build_status(self.context)
        current_hash = __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()
        if not status:
            issues.append("Run the build script and create the analytical database.")
        elif status.get("script_hash") != current_hash:
            issues.append("Run the database build again after the latest script changes.")
        elif not status.get("tables"):
            issues.append("The last database build did not create any analytical tables.")
        return issues

    def save_script(self) -> None:
        try:
            self.script_path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.status_message("Build script saved")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Build Script", str(exc))

    def run_script(self) -> None:
        self.save_script()
        try:
            result = portfolio_studios.run_database_build(self.context, self.editor.toPlainText())
            counts = result.get("table_counts") or {}
            tables = "\n".join(
                f"• {table}: {counts.get(table):,} rows"
                if isinstance(counts.get(table), int)
                else f"• {table}"
                for table in result["tables"]
            ) or "• No tables created"
            self.output.setPlainText(
                f"Database: {result['database']}\n"
                f"Built: {result.get('built_at', '')}\n"
                f"Statements run: {result['statements']}\n\n"
                f"Tables now present:\n{tables}"
            )
            self.status_message("Database build finished")
        except Exception as exc:
            self.output.setPlainText(str(exc))
            QMessageBox.warning(self, "Database Build Failed", str(exc))


class SQLAnalysisStudio(StudioWidget):
    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._loading = False
        self._loaded_query_path: Path | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(
            layout,
            "SQL Analysis Workspace",
            "Write the project queries yourself. Career Accelerator keeps the files, database, results, and interpretations together.",
        )
        file_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        file_row.addWidget(QLabel("Query file"))
        self.query_combo = QComboBox()
        self.query_combo.currentIndexChanged.connect(self.load_selected)
        file_row.addWidget(self.query_combo, 1)
        new_query = QPushButton("New Query")
        new_query.clicked.connect(self.new_query)
        file_row.addWidget(new_query)
        open_query = QPushButton("Open SQL File Externally")
        open_query.clicked.connect(self.open_query)
        file_row.addWidget(open_query)
        layout.addLayout(file_row)

        self.editor = AssistedTextEdit(
            language="sql",
            project_dir=self.context.project_dir,
        )
        self._sql_highlighter = SqlHighlighter(self.editor.document())
        self.editor.setStyleSheet(raw_markdown_stylesheet())
        self.editor.setPlaceholderText("Write the final SQL query here.")
        layout.addWidget(self.editor, 2)

        self.results = QTableWidget(0, 0)
        self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results.setAlternatingRowColors(True)
        layout.addWidget(self.results, 1)

        self.interpretation = QTextEdit()
        self.interpretation.setAcceptRichText(False)
        self.interpretation.setMaximumHeight(110)
        self.interpretation.setPlaceholderText(
            "What does this result answer? Note the output grain, the important result, and any limitation or follow-up check."
        )
        layout.addWidget(self.interpretation)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Choose a query file or create a new one")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        save = QPushButton("Save Query")
        save.clicked.connect(self.save)
        actions.addWidget(save)
        run = QPushButton("Run Query")
        run.setObjectName("Primary")
        run.clicked.connect(self.run_query)
        actions.addWidget(run)
        layout.addLayout(actions)
        self.refresh_queries()

    def current_path(self) -> Path | None:
        value = self.query_combo.currentData()
        return Path(value) if value else None

    def refresh_queries(self, selected: Path | None = None) -> None:
        current = selected or self.current_path()
        self._loading = True
        self.query_combo.clear()
        for path in portfolio_studios.analysis_query_files(self.context):
            self.query_combo.addItem(path.name, str(path))
        if current is not None:
            index = self.query_combo.findData(str(current))
            if index >= 0:
                self.query_combo.setCurrentIndex(index)
        self._loading = False
        self.load_selected()

    def load_selected(self, *_args) -> None:
        if self._loading:
            return
        path = self.current_path()
        if (
            self._loaded_query_path is not None
            and path != self._loaded_query_path
            and self._loaded_query_path.is_file()
        ):
            try:
                portfolio_studios.save_analysis_query(
                    self.context,
                    self._loaded_query_path.name,
                    self.editor.toPlainText(),
                    self.interpretation.toPlainText(),
                )
            except Exception:
                pass
        if path is None or not path.is_file():
            self._loaded_query_path = None
            self.editor.clear()
            self.interpretation.clear()
            return
        self._loaded_query_path = path
        self.editor.setPlainText(path.read_text(encoding="utf-8", errors="replace"))
        self.interpretation.setPlainText(
            portfolio_studios.analysis_interpretation(self.context, path.name)
        )
        self.status.setText(f"Editing {path.name}")


    def new_query(self) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "New Analysis Query",
            "Short file name:",
            text=f"{self.query_combo.count() + 1:02d}_analysis",
        )
        if not accepted or not str(name).strip():
            return
        path = portfolio_studios.save_analysis_query(
            self.context,
            str(name),
            "-- Business question:\n-- Intended output grain:\n-- Validation check:\n\n",
            "",
        )
        self.refresh_queries(path)

    def _save_current(self, *, announce: bool) -> Path | None:
        path = self.current_path()
        if path is None:
            return None
        saved = portfolio_studios.save_analysis_query(
            self.context,
            path.name,
            self.editor.toPlainText(),
            self.interpretation.toPlainText(),
        )
        if announce:
            self.status_message(f"Saved {saved.name}")
        return saved

    def save(self) -> None:
        try:
            self._save_current(announce=True)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Query", str(exc))

    def run_query(self) -> None:
        try:
            self._save_current(announce=False)
            result = portfolio_studios.run_analysis_query(
                self.context,
                self.editor.toPlainText(),
            )
            columns = list(result.get("columns") or [])
            rows = list(result.get("rows") or [])
            self.results.setColumnCount(len(columns))
            self.results.setHorizontalHeaderLabels(columns)
            self.results.setRowCount(len(rows))
            for row_index, values in enumerate(rows):
                for column, value in enumerate(values):
                    self.results.setItem(row_index, column, QTableWidgetItem("" if value is None else str(value)))
            if columns:
                self.results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                self.results.horizontalHeader().setStretchLastSection(True)
            suffix = " • first 500 rows shown" if result.get("truncated") else ""
            self.status_message(f"Query finished • {len(rows)} row{'s' if len(rows) != 1 else ''}{suffix}")
        except Exception as exc:
            QMessageBox.warning(self, "Query Failed", str(exc))

    def open_query(self) -> None:
        path = self.current_path()
        if path is None:
            return
        try:
            portfolio_studios.open_path(self.context, path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open SQL File", str(exc))

    def prepare_for_completion(self) -> None:
        self._save_current(announce=False)

    def completion_issues(self) -> list[str]:
        try:
            self._save_current(announce=False)
        except Exception as exc:
            return [str(exc)]
        return portfolio_studios.sql_analysis_issues(self.context)


class ReviewChecklistStudio(StudioWidget):
    def __init__(
        self,
        context,
        *,
        title: str,
        description: str,
        checklist_key: str,
        items: tuple[str, ...],
        screenshot_category: str,
        parent=None,
    ):
        super().__init__(context, parent)
        self.checklist_key = checklist_key
        self.item_labels = tuple(items)
        self.screenshot_category = screenshot_category
        values = portfolio_studios.review_checklist_values(
            context,
            checklist_key,
            self.item_labels,
        )
        self.screenshots = list(values.get("screenshots") or [])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(layout, title, description)
        self.checks: dict[str, QCheckBox] = {}
        for item in self.item_labels:
            checkbox = QCheckBox(item)
            checkbox.setChecked(bool(values["checked"].get(item)))
            self.checks[item] = checkbox
            layout.addWidget(checkbox)

        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setPlaceholderText(
            "Record test results, values checked, feedback received, and anything that still needs attention."
        )
        self.notes.setPlainText(str(values.get("notes") or ""))
        layout.addWidget(self.notes, 1)

        self.screenshot_label = QLabel()
        self.screenshot_label.setObjectName("Muted")
        self.screenshot_label.setWordWrap(True)
        layout.addWidget(self.screenshot_label)
        self._refresh_screenshots()

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Complete the review while you work in Power BI")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        open_power_bi = QPushButton("Open Power BI File")
        open_power_bi.clicked.connect(self.open_power_bi)
        actions.addWidget(open_power_bi)
        add_screenshot = QPushButton("Add Review Screenshot")
        add_screenshot.clicked.connect(self.add_screenshot)
        actions.addWidget(add_screenshot)
        save = QPushButton("Save Review")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        actions.addWidget(save)
        layout.addLayout(actions)

    def _refresh_screenshots(self) -> None:
        if self.screenshots:
            self.screenshot_label.setText(
                "Saved screenshots: " + ", ".join(Path(path).name for path in self.screenshots)
            )
        else:
            self.screenshot_label.setText("No review screenshots saved yet.")

    def open_power_bi(self) -> None:
        path = portfolio_studios.find_power_bi_file(self.context)
        target = path or (self.context.project_dir / "power-bi")
        try:
            portfolio_studios.open_path(self.context, target)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Power BI", str(exc))

    def add_screenshot(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a Power BI Review Screenshot",
            str(self.context.project_dir),
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return
        try:
            target = portfolio_studios.register_review_screenshot(
                self.context,
                Path(path),
                self.screenshot_category,
            )
            relative = target.relative_to(self.context.project_dir).as_posix()
            if relative not in self.screenshots:
                self.screenshots.append(relative)
            self._refresh_screenshots()
            self.save()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Add Screenshot", str(exc))

    def checked_values(self) -> dict[str, bool]:
        return {label: checkbox.isChecked() for label, checkbox in self.checks.items()}

    def save(self) -> None:
        try:
            portfolio_studios.save_review_checklist(
                self.context,
                self.checklist_key,
                self.checked_values(),
                self.notes.toPlainText(),
                self.screenshots,
            )
            self.status_message("Review saved")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Review", str(exc))

    def prepare_for_completion(self) -> None:
        portfolio_studios.save_review_checklist(
            self.context,
            self.checklist_key,
            self.checked_values(),
            self.notes.toPlainText(),
            self.screenshots,
        )

    def completion_issues(self) -> list[str]:
        issues = [label for label, checked in self.checked_values().items() if not checked]
        if not self.screenshots:
            issues.append("Save at least one screenshot that shows the reviewed Power BI work.")
        if not self.notes.toPlainText().strip():
            issues.append("Add a short review note with the values or behavior you checked.")
        return issues


MODEL_REVIEW_ITEMS = (
    "Every required table is loaded from the reviewed analytical layer.",
    "Table grains and key columns were checked before creating relationships.",
    "Relationship cardinality and filter direction are intentional.",
    "A proper date table is present and marked as the date table.",
    "Final measures are explicit, named clearly, and formatted consistently.",
    "Technical fields that should not be used in reports are hidden.",
    "Headline totals match the approved SQL results.",
    "Filters and combined selections were tested for unexpected totals.",
)

REPORT_REVIEW_ITEMS = (
    "Every required report page is present and answers an approved question.",
    "Headline KPI values match the validated model and SQL results.",
    "Filters and slicers work alone and in realistic combinations.",
    "Cross-highlighting, drill-through, and navigation behave as intended.",
    "Titles, labels, units, and time periods are clear.",
    "Color, contrast, text size, and keyboard order were reviewed for accessibility.",
    "Empty and no-result states are understandable.",
    "The report was reviewed at the presentation size used for screenshots or sharing.",
)


class ResultsVerificationStudio(StudioWidget):
    KEYS = ("metric", "sql_value", "python_value", "power_bi_value", "tolerance", "status", "resolution")

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(
            layout,
            "Results Verification",
            "Compare only the headline metrics that will be published. You still run the calculations in each tool and investigate every mismatch.",
        )
        self.table = QTableWidget(0, len(self.KEYS))
        self.table.setHorizontalHeaderLabels(("Metric", "SQL", "Python", "Power BI", "Tolerance", "Status", "Resolution"))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        for row in portfolio_studios.results_verification_rows(context):
            self.add_row(row)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Add the final metrics that need cross-tool confirmation")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        add = QPushButton("Add Metric")
        add.clicked.connect(lambda: self.add_row({}))
        actions.addWidget(add)
        remove = QPushButton("Remove Selected")
        remove.clicked.connect(self.remove_selected)
        actions.addWidget(remove)
        save = QPushButton("Save Verification Matrix")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        actions.addWidget(save)
        layout.addLayout(actions)

    def add_row(self, values: dict[str, Any]) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, key in enumerate(self.KEYS):
            self.table.setItem(row, column, QTableWidgetItem(str(values.get(key) or "")))

    def remove_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def rows(self) -> list[dict[str, str]]:
        result = []
        for row in range(self.table.rowCount()):
            result.append({key: self.table.item(row, column).text().strip() if self.table.item(row, column) else "" for column, key in enumerate(self.KEYS)})
        return result

    @staticmethod
    def _status(row: dict[str, str]) -> str:
        values = [row.get(key, "").strip() for key in ("sql_value", "python_value", "power_bi_value")]
        present = [value for value in values if value]
        if len(present) < 3:
            return "Needs values"
        try:
            numbers = [float(value.replace(",", "").replace("%", "")) for value in present]
            tolerance = float((row.get("tolerance") or "0").replace("%", ""))
        except ValueError:
            return "Match" if len(set(present)) == 1 else "Investigate"
        return "Match" if max(numbers) - min(numbers) <= tolerance else "Investigate"

    def prepare_for_completion(self) -> None:
        rows = self.rows()
        for index, row in enumerate(rows):
            row["status"] = self._status(row)
            self.table.item(index, 5).setText(row["status"])
        portfolio_studios.save_results_verification(self.context, rows)

    def completion_issues(self) -> list[str]:
        rows = self.rows()
        issues = []
        if not rows:
            issues.append("Add the headline metrics that will be published.")
        for row in rows:
            status = self._status(row)
            if not row.get("metric"):
                issues.append("Every verification row needs a metric name.")
            if status != "Match":
                issues.append(f"{row.get('metric') or 'A metric'} is not confirmed across tools.")
            if status == "Investigate" and not row.get("resolution"):
                issues.append(f"{row.get('metric') or 'A metric'} needs a mismatch resolution note.")
        return issues

    def save(self) -> None:
        rows = self.rows()
        for index, row in enumerate(rows):
            row["status"] = self._status(row)
            self.table.item(index, 5).setText(row["status"])
        try:
            csv_path, md_path = portfolio_studios.save_results_verification(self.context, rows)
            mismatches = sum(1 for row in rows if row["status"] == "Investigate")
            self.status_message(f"Saved {csv_path.name} and {md_path.name} • {mismatches} mismatch{'es' if mismatches != 1 else ''}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Verification", str(exc))


class FindingsStudio(StudioWidget):
    KEYS = ("finding", "evidence", "impact", "recommendation", "owner", "limitations")

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(
            layout,
            "Findings & Recommendations Studio",
            "Build the final narrative from validated evidence. The app keeps the pieces connected; you write the finding, business meaning, and recommendation.",
        )
        self.intro = QTextEdit()
        self.intro.setAcceptRichText(False)
        self.intro.setPlaceholderText("Write a short opening that states the business problem, audience, and decision.")
        state = portfolio_studios.load_state(context).get("data", {})
        self.intro.setPlainText(str(state.get("executive_summary_intro") or ""))
        self.intro.setMaximumHeight(100)
        layout.addWidget(self.intro)
        self.table = QTableWidget(0, len(self.KEYS))
        self.table.setHorizontalHeaderLabels(("Finding", "Evidence", "Why it matters", "Recommendation", "Owner / next action", "Limitations"))
        for column in range(len(self.KEYS)):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        for row in portfolio_studios.findings_rows(context):
            self.add_row(row)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Use three to five strong, validated findings")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        add = QPushButton("Add Finding")
        add.clicked.connect(lambda: self.add_row({}))
        actions.addWidget(add)
        remove = QPushButton("Remove Selected")
        remove.clicked.connect(self.remove_selected)
        actions.addWidget(remove)
        save = QPushButton("Save Executive Summary")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        actions.addWidget(save)
        layout.addLayout(actions)

    def add_row(self, values: dict[str, Any]) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, key in enumerate(self.KEYS):
            self.table.setItem(row, column, QTableWidgetItem(str(values.get(key) or "")))

    def remove_selected(self) -> None:
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    def rows(self) -> list[dict[str, str]]:
        return [
            {key: self.table.item(row, column).text().strip() if self.table.item(row, column) else "" for column, key in enumerate(self.KEYS)}
            for row in range(self.table.rowCount())
        ]

    def prepare_for_completion(self) -> None:
        portfolio_studios.save_findings(
            self.context,
            self.rows(),
            self.intro.toPlainText().strip(),
        )

    def completion_issues(self) -> list[str]:
        rows = self.rows()
        issues = []
        if len(self.intro.toPlainText().split()) < 12:
            issues.append("Write a short opening that states the problem, audience, and decision.")
        if len(rows) < 3:
            issues.append("Add at least three strong findings.")
        if len(rows) > 5:
            issues.append("Keep the executive summary focused on no more than five findings.")
        for index, row in enumerate(rows, 1):
            for key, label in (
                ("finding", "finding"),
                ("evidence", "supporting evidence"),
                ("impact", "business impact"),
                ("recommendation", "recommendation"),
                ("owner", "owner or next action"),
            ):
                if not row.get(key):
                    issues.append(f"Finding {index} needs a {label}.")
        return issues

    def save(self) -> None:
        rows = self.rows()
        issues = []
        for index, row in enumerate(rows, 1):
            if not row["finding"]:
                issues.append(f"Finding {index} needs a clear statement.")
            if not row["evidence"]:
                issues.append(f"Finding {index} needs supporting evidence.")
            if not row["impact"]:
                issues.append(f"Finding {index} needs a business impact.")
            if row["recommendation"] and not row["owner"]:
                issues.append(f"Recommendation {index} needs an owner or next action.")
        try:
            path = portfolio_studios.save_findings(self.context, rows, self.intro.toPlainText().strip())
            self.status_message(f"Saved {path.name}" + ("" if not issues else f" • {len(issues)} writing items remain"))
            if issues:
                QMessageBox.information(self, "Writing Review", "\n".join(f"• {item}" for item in issues))
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Summary", str(exc))


class PublisherStudio(StudioWidget):
    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        _studio_header(
            layout,
            "Case Study Publisher",
            "Review the employer-facing project as one package. The publisher checks the repository; you decide what belongs in the final story and approve the release.",
        )
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(("Publication check", "Status"))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)
        self.preview = QTextBrowser()
        self.preview.setPlaceholderText("README preview will appear here.")
        layout.addWidget(self.preview, 1)
        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status = QLabel("Run the publication review before the final release")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status, 1)
        refresh = QPushButton("Run Publication Checks")
        refresh.setObjectName("Primary")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        draft = QPushButton("Build Case Study Draft")
        draft.clicked.connect(self.build_draft)
        actions.addWidget(draft)
        use_draft = QPushButton("Use Reviewed Draft as README")
        use_draft.clicked.connect(self.use_draft)
        actions.addWidget(use_draft)
        open_readme = QPushButton("Open README")
        open_readme.clicked.connect(self.open_readme)
        actions.addWidget(open_readme)
        open_folder = QPushButton("Open Project Folder")
        open_folder.clicked.connect(lambda: portfolio_studios.open_path(self.context, self.context.project_dir))
        actions.addWidget(open_folder)
        layout.addLayout(actions)
        self.refresh()

    def completion_issues(self) -> list[str]:
        return [item["label"] for item in portfolio_studios.publisher_checks(self.context) if not item["passed"]]

    def refresh(self) -> None:
        checks = portfolio_studios.publisher_checks(self.context)
        self.table.setRowCount(len(checks))
        for row, check in enumerate(checks):
            self.table.setItem(row, 0, QTableWidgetItem(check["label"]))
            self.table.setItem(row, 1, QTableWidgetItem("Ready" if check["passed"] else "Needs attention"))
        readme = self.context.project_dir / "README.md"
        if readme.is_file():
            from career_app.ui.markdown_preview import render_markdown_html
            self.preview.setHtml(render_markdown_html(readme.read_text(encoding="utf-8", errors="replace")))
        passed = sum(1 for item in checks if item["passed"])
        self.status.setText(f"{passed} of {len(checks)} publication checks passed")

    def build_draft(self) -> None:
        try:
            path = portfolio_studios.generate_case_study_draft(self.context)
            from career_app.ui.markdown_preview import render_markdown_html
            self.preview.setHtml(
                render_markdown_html(path.read_text(encoding="utf-8", errors="replace"))
            )
            self.status_message(f"Built {path.name} for review")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Build Draft", str(exc))

    def use_draft(self) -> None:
        answer = QMessageBox.question(
            self,
            "Use Draft as README",
            (
                "Replace the project README with the reviewed case-study draft?\n\n"
                "The current README will be backed up first."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            path = portfolio_studios.apply_case_study_draft(self.context)
            self.status_message(f"Updated {path.name}; previous README backed up")
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Update README", str(exc))

    def open_readme(self) -> None:
        readme = self.context.project_dir / "README.md"
        try:
            portfolio_studios.open_path(self.context, readme)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open README", str(exc))


def build_studio_tabs(
    tabs: QTabWidget,
    *,
    context: portfolio_studios.StudioContext,
    data_workspace=None,
) -> list[QWidget]:
    """Add only the tools that belong to the active milestone workspace."""
    widgets: list[QWidget] = []
    key = context.milestone_key

    def add(widget: QWidget, label: str) -> None:
        tabs.addTab(widget, label)
        widgets.append(widget)

    if key == "project_brief":
        add(ProjectBriefStudio(context), "Project Brief Studio")
    elif key == "data_source_spec":
        add(DataSourceStudio(context), "Data Source Studio")
    elif key == "raw_dataset":
        add(DataIntakeStudio(context), "Data Intake Studio")
    elif key == "validate_relationships":
        plan = data_workspace or project_data_workspace.prepare_project_data_workspace(
            context.root, context.project_id, build=True
        )
        if plan.notebook_path and Path(plan.notebook_path).is_file():
            add(
                IntegratedNotebookWidget(
                    Path(plan.notebook_path),
                    project_dir=context.project_dir,
                    completion_policy="relationship",
                ),
                "Relationship Notebook",
            )
    elif key == "data_dictionary_review":
        add(DataDictionaryStudio(context), "Data Dictionary Studio")
    elif key == "clean_analytical_data":
        notebook_records = cleaning_workspace.ensure_table_notebooks(context)
        if notebook_records:
            notebook_paths = [Path(item["notebook"]) for item in notebook_records]
            notebook_labels = {
                str(Path(item["notebook"])): item["business_name"]
                for item in notebook_records
            }
            cleaning_studio = DataCleaningStudio(context)
            add(cleaning_studio, "Data Cleaning Studio")
            notebook_tab_index = tabs.count()
            notebook_widget = IntegratedNotebookWidget(
                notebook_paths[0],
                notebook_paths=notebook_paths,
                notebook_labels=notebook_labels,
                project_dir=context.project_dir,
                completion_policy="",
            )
            add(notebook_widget, "Cleaning Notebook")

            def open_table_notebook(table_name: str) -> None:
                notebook_widget.select_notebook(table_name)
                tabs.setCurrentIndex(notebook_tab_index)

            cleaning_studio.open_notebook_requested.connect(
                open_table_notebook
            )

            def import_table_notebook(
                table_name: str,
                source_path: str,
            ) -> None:
                try:
                    record = cleaning_workspace.table_record(
                        context,
                        table_name,
                    )
                    target = context.project_dir / record["notebook_path"]
                    if not notebook_widget.prepare_notebook_replacement(
                        target
                    ):
                        return
                    result = cleaning_workspace.import_cleaning_notebook(
                        context,
                        table_name,
                        Path(source_path),
                    )
                    if not notebook_widget.reload_notebook(
                        Path(result["target"])
                    ):
                        raise RuntimeError(
                            "The notebook was imported, but the integrated "
                            "notebook tab could not reload it. Close and reopen "
                            "the milestone to load the imported file."
                        )
                    cleaning_studio.refresh()
                    tabs.setCurrentIndex(notebook_tab_index)
                    backup = result.get("backup")
                    message = (
                        f"Imported {Path(result['target']).name} for "
                        f"{record['business_name']}."
                    )
                    if backup:
                        try:
                            backup_text = Path(backup).relative_to(
                                context.project_dir
                            ).as_posix()
                        except ValueError:
                            backup_text = str(backup)
                        message += (
                            "\n\nThe previous in-application notebook was "
                            f"backed up to:\n{backup_text}"
                        )
                    QMessageBox.information(
                        cleaning_studio,
                        "Cleaning Notebook Imported",
                        message,
                    )
                except Exception as exc:
                    QMessageBox.warning(
                        cleaning_studio,
                        "Could Not Import Cleaning Notebook",
                        str(exc),
                    )

            cleaning_studio.import_notebook_requested.connect(
                import_table_notebook
            )
        else:
            add(DataCleaningStudio(context), "Data Cleaning Studio")
    elif key == "analytical_database":
        add(DatabaseBuildStudio(context), "Database Build")
    elif key == "sql_analysis":
        add(SQLAnalysisStudio(context), "SQL Analysis")
    elif key == "exploratory_analysis":
        notebook = portfolio_studios.ensure_eda_notebook(context)
        add(
            IntegratedNotebookWidget(
                notebook,
                project_dir=context.project_dir,
                completion_policy="eda",
            ),
            "EDA Notebook",
        )
    elif key == "validate_findings":
        add(ResultsVerificationStudio(context), "Results Verification")
    elif key == "power_bi_model":
        add(
            ReviewChecklistStudio(
                context,
                title="Power BI Model Review",
                description=(
                    "Build the semantic model in Power BI. Use this companion to keep the approved relationships, checks, notes, and review evidence together."
                ),
                checklist_key="power_bi_model_review",
                items=MODEL_REVIEW_ITEMS,
                screenshot_category="power-bi-model",
            ),
            "Model Review",
        )
    elif key == "power_bi_report":
        add(
            ReviewChecklistStudio(
                context,
                title="Power BI Report Review",
                description=(
                    "Build the report in Power BI. Use this companion to test the finished pages, interactions, accessibility, and final presentation."
                ),
                checklist_key="power_bi_report_review",
                items=REPORT_REVIEW_ITEMS,
                screenshot_category="power-bi-report",
            ),
            "Report Review",
        )
    elif key == "executive_summary":
        add(FindingsStudio(context), "Findings & Recommendations")
    elif key == "publish_case_study":
        add(PublisherStudio(context), "Case Study Publisher")

    if key != "project_brief":
        add(ProjectContextWidget(context), "Previous Milestones")

    return widgets
