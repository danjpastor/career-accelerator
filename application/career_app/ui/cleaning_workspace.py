"""Guided Data Cleaning Studio embedded in portfolio milestone workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QFileDialog,
    QFrame,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.services import cleaning_workspace


class DataCleaningStudio(QWidget):
    """One guided cleaning workflow for every source table."""

    saved = Signal(str)
    open_notebook_requested = Signal(str)
    import_notebook_requested = Signal(str, str)

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.records = cleaning_workspace.table_records(context)
        self.current_table = ""
        self._loading = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        heading = QLabel("Data Cleaning Studio")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        intro = QLabel(
            "Clean one table at a time. Every table brief inherits the purpose, grain, keys, relationships, field rules, and approved decisions from the completed Data Dictionary milestone."
        )
        intro.setObjectName("Muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.progress = QLabel("")
        self.progress.setObjectName("Muted")
        layout.addWidget(self.progress)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        left = QFrame()
        left.setObjectName("Card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)
        left_title = QLabel("Project tables")
        left_title.setObjectName("SectionTitle")
        left_layout.addWidget(left_title)
        self.table_list = QListWidget()
        self.table_list.setWordWrap(True)
        self.table_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_list.currentItemChanged.connect(self._table_changed)
        left_layout.addWidget(self.table_list, 1)
        refresh = QPushButton("Refresh Table Status")
        refresh.clicked.connect(self.refresh)
        left_layout.addWidget(refresh)
        splitter.addWidget(left)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        right = QVBoxLayout(host)
        right.setContentsMargins(10, 4, 10, 12)
        right.setSpacing(10)

        self.title = QLabel("Select a table")
        self.title.setObjectName("SectionTitle")
        right.addWidget(self.title)
        self.status = QLabel("")
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        right.addWidget(self.status)

        context_title = QLabel("Inherited table brief")
        context_title.setStyleSheet("font-weight:700;")
        right.addWidget(context_title)
        self.context_view = QTextBrowser()
        self.context_view.setOpenExternalLinks(False)
        self.context_view.setMinimumHeight(150)
        right.addWidget(self.context_view)

        fields_title = QLabel("Field rules and cleaning plan")
        fields_title.setStyleSheet("font-weight:700;")
        right.addWidget(fields_title)
        self.fields = QTableWidget(0, 8)
        self.fields.setHorizontalHeaderLabels(
            (
                "Field",
                "Definition",
                "Expected type",
                "Null rule",
                "Key role",
                "Uniqueness",
                "Allowed values / format",
                "Cleaning expectation",
            )
        )
        self.fields.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.fields.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fields.setWordWrap(True)
        self.fields.verticalHeader().setVisible(False)
        self.fields.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.fields.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.fields.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.fields.setMinimumHeight(230)
        right.addWidget(self.fields)

        issues_title = QLabel("Known issues and approved decisions")
        issues_title.setStyleSheet("font-weight:700;")
        right.addWidget(issues_title)
        self.issues = QTextBrowser()
        self.issues.setMinimumHeight(100)
        right.addWidget(self.issues)

        summary_title = QLabel("Cleaning decisions and remaining exceptions *")
        summary_title.setStyleSheet("font-weight:700;")
        right.addWidget(summary_title)
        self.summary = QTextEdit()
        self.summary.setAcceptRichText(False)
        self.summary.setPlaceholderText(
            "Summarize what changed, why, how many records were affected, and anything later milestones must know."
        )
        self.summary.setMinimumHeight(105)
        right.addWidget(self.summary)

        first_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        notebook = QPushButton("Open This Table's Notebook")
        notebook.setObjectName("Primary")
        notebook.clicked.connect(self.open_notebook)
        first_actions.addWidget(notebook)
        import_notebook = QPushButton("Import Cleaning Notebook")
        import_notebook.clicked.connect(self.import_notebook)
        first_actions.addWidget(import_notebook)
        export_csv = QPushButton("Export Raw CSV")
        export_csv.clicked.connect(self.export_csv)
        first_actions.addWidget(export_csv)
        export_package = QPushButton("Export Cleaning Package")
        export_package.clicked.connect(self.export_package)
        first_actions.addWidget(export_package)
        first_actions.addStretch()
        right.addLayout(first_actions)

        second_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        import_data = QPushButton("Import Cleaned CSV")
        import_data.clicked.connect(self.import_cleaned)
        second_actions.addWidget(import_data)
        validate = QPushButton("Validate Processed Table")
        validate.clicked.connect(self.validate_processed)
        second_actions.addWidget(validate)
        save_summary = QPushButton("Save Table Summary")
        save_summary.clicked.connect(self.save_table_summary)
        second_actions.addWidget(save_summary)
        self.complete_button = QPushButton("Mark Table Complete")
        self.complete_button.clicked.connect(self.toggle_complete)
        second_actions.addWidget(self.complete_button)
        second_actions.addStretch()
        right.addLayout(second_actions)

        scroll.setWidget(host)
        splitter.addWidget(scroll)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([270, 850])

        self.refresh()

    def _record(self) -> dict[str, Any] | None:
        key = self.current_table.casefold()
        for record in self.records:
            if record["table"].casefold() == key:
                return record
        return None

    @staticmethod
    def _status_for(context, record: dict[str, Any]) -> str:
        state = cleaning_workspace.table_state(context, record["table"])
        if state.get("reviewed"):
            return "Complete"
        validation = state.get("validation") if isinstance(state.get("validation"), dict) else {}
        if validation and str(validation.get("dictionary_fingerprint") or "") != cleaning_workspace._dictionary_fingerprint(record):
            return "Needs revalidation"
        if validation.get("blocking"):
            return "Validation issues"
        if cleaning_workspace.discover_processed(context, record):
            return str(state.get("status") or "Ready for review")
        notebook = context.project_dir / record["notebook_path"]
        if notebook.is_file():
            return "Notebook ready"
        return "Not started"

    def refresh(self) -> None:
        selected = self.current_table
        self.records = cleaning_workspace.table_records(self.context)
        self.table_list.blockSignals(True)
        self.table_list.clear()
        complete = 0
        for record in self.records:
            status = self._status_for(self.context, record)
            if status == "Complete":
                complete += 1
            symbol = "✓" if status == "Complete" else "!" if status == "Validation issues" else "○"
            item = QListWidgetItem(f"{symbol} {record['business_name']}\n{status}")
            item.setData(Qt.ItemDataRole.UserRole, record["table"])
            self.table_list.addItem(item)
            if record["table"] == selected:
                self.table_list.setCurrentItem(item)
        self.table_list.blockSignals(False)
        self.progress.setText(f"{complete} of {len(self.records)} tables cleaned, validated, and reviewed")
        if self.table_list.count() and self.table_list.currentRow() < 0:
            self.table_list.setCurrentRow(0)
        elif self.table_list.currentItem() is not None:
            self._load_record(self._record())

    def _table_changed(self, current, _previous) -> None:
        if current is None:
            return
        self._save_summary_silent()
        self.current_table = str(current.data(Qt.ItemDataRole.UserRole) or "")
        self._load_record(self._record())

    def _load_record(self, record: dict[str, Any] | None) -> None:
        if record is None:
            return
        self._loading = True
        state = cleaning_workspace.table_state(self.context, record["table"])
        status = self._status_for(self.context, record)
        self.title.setText(record["business_name"])
        processed = cleaning_workspace.discover_processed(self.context, record)
        self.status.setText(
            f"Status: {status}  •  Raw: {record['source_path']}  •  "
            f"Processed: {processed.relative_to(self.context.project_dir).as_posix() if processed else record['processed_path']}"
        )
        relationships = "<br>".join(f"• {item}" for item in record["relationships"]) or "No parent relationship documented."
        self.context_view.setHtml(
            "<p><b>Purpose:</b> {}</p><p><b>One row represents:</b> {}</p>"
            "<p><b>Expected primary key:</b> <code>{}</code></p><p><b>Relationships:</b><br>{}</p>".format(
                record["purpose"], record["grain"], record["primary_key"] or "Not established", relationships
            )
        )
        self.fields.setRowCount(len(record["fields"]))
        keys = (
            "column", "definition", "expected_type", "nullable", "key",
            "expected_unique", "valid_values", "cleaning_expectation",
        )
        for row_index, field in enumerate(record["fields"]):
            for column_index, key in enumerate(keys):
                self.fields.setItem(row_index, column_index, QTableWidgetItem(str(field.get(key) or "")))
        self.fields.resizeRowsToContents()
        issue_lines = record["known_issues"] or ["No specific warning was documented. Run the standard profiling checks before cleaning."]
        self.issues.setHtml("<ul>" + "".join(f"<li>{item}</li>" for item in issue_lines) + "</ul>")
        self.summary.setPlainText(str(state.get("summary") or ""))
        self.complete_button.setText("Reopen Table" if state.get("reviewed") else "Mark Table Complete")
        self._loading = False

    def _save_summary_silent(self) -> None:
        if self._loading or not self.current_table:
            return
        text = self.summary.toPlainText().strip()
        if text:
            try:
                cleaning_workspace.save_summary(self.context, self.current_table, text)
            except Exception:
                pass

    def open_notebook(self) -> None:
        record = self._record()
        if record is not None:
            self.open_notebook_requested.emit(record["table"])

    def import_notebook(self) -> None:
        record = self._record()
        if record is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Finished Cleaning Notebook",
            str(self.context.project_dir),
            "Jupyter notebooks (*.ipynb)",
        )
        if not path:
            return
        try:
            inspection = cleaning_workspace.inspect_cleaning_notebook(
                self.context,
                Path(path),
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Read Cleaning Notebook",
                str(exc),
            )
            return

        detected = list(inspection.get("detected_tables") or [])
        selected = str(record["table"])
        if detected and selected not in detected:
            names = ", ".join(detected)
            QMessageBox.warning(
                self,
                "Notebook Does Not Match Selected Table",
                f"This notebook appears to reference {names}, but "
                f"{record['business_name']} is selected. Select the matching "
                "table first, or choose the correct notebook file.",
            )
            return

        if not detected:
            answer = QMessageBox.question(
                self,
                "Confirm Notebook Table",
                f"Career Accelerator could not identify a table name in this "
                f"notebook. Import it as the finished notebook for "
                f"{record['business_name']}?\n\n"
                f"Cells detected: {inspection['cell_count']}\n"
                f"Code cells: {inspection['code_cell_count']}",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.import_notebook_requested.emit(selected, str(Path(path)))

    def export_csv(self) -> None:
        record = self._record()
        if record is None:
            return
        suggested = f"{record['table']}_raw.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Raw CSV", str(Path.home() / suggested), "CSV files (*.csv)")
        if not path:
            return
        try:
            target = cleaning_workspace.export_raw_csv(self.context, record["table"], Path(path))
            self.saved.emit(f"Exported {target.name}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Export Raw CSV", str(exc))

    def export_package(self) -> None:
        record = self._record()
        if record is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose Export Folder", str(Path.home()))
        if not folder:
            return
        try:
            target = cleaning_workspace.export_cleaning_package(self.context, record["table"], Path(folder))
            self.saved.emit(f"Exported cleaning package • {target.name}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Export Cleaning Package", str(exc))

    @staticmethod
    def _report_text(report: dict[str, Any]) -> str:
        lines = [
            f"Raw rows: {report.get('raw_row_count') if report.get('raw_row_count') is not None else 'Unavailable'}",
            f"Processed rows: {report.get('row_count') if report.get('row_count') is not None else 'Unavailable'}",
            f"Row difference: {report.get('row_difference') if report.get('row_difference') is not None else 'Unavailable'}",
            f"Columns: {len(report.get('columns') or [])}",
            "",
            "Blocking issues:",
        ]
        lines.extend(f"• {item}" for item in (report.get("blocking") or []))
        if not report.get("blocking"):
            lines.append("• None")

        lines.extend(["", "Structural changes to review:"])
        lines.extend(f"• {item}" for item in (report.get("structural_changes") or []))
        if not report.get("structural_changes"):
            lines.append("• None")

        lines.extend(["", "Business-rule warnings:"])
        lines.extend(f"• {item}" for item in (report.get("warnings") or []))
        if not report.get("warnings"):
            lines.append("• None")

        information = report.get("information") or []
        if information:
            lines.extend(["", "Validation notes:"])
            lines.extend(f"• {item}" for item in information)
        return "\n".join(lines)

    def import_cleaned(self) -> None:
        record = self._record()
        if record is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import Cleaned CSV", str(self.context.project_dir), "CSV files (*.csv)")
        if not path:
            return
        try:
            report = cleaning_workspace.validate_csv(Path(path), record, self.context)
            if report["blocking"]:
                QMessageBox.warning(self, "Cleaned CSV Has Blocking Issues", self._report_text(report))
                return
            answer = QMessageBox.question(
                self,
                "Import Reviewed Cleaned CSV",
                self._report_text(report) + "\n\nImport this reviewed file and organize it under data/processed/csv/?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            target, _ = cleaning_workspace.import_cleaned_csv(self.context, record["table"], Path(path))
            self.saved.emit(f"Imported {target.name}")
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Import Cleaned CSV", str(exc))

    def validate_processed(self) -> None:
        record = self._record()
        if record is None:
            return
        try:
            report = cleaning_workspace.validate_processed(self.context, record["table"])
            QMessageBox.information(self, "Processed Table Validation", self._report_text(report))
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Validate Processed Table", str(exc))

    def save_table_summary(self) -> None:
        record = self._record()
        if record is None:
            return
        text = self.summary.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Summary Required", "Describe the cleaning decisions and remaining exceptions first.")
            return
        try:
            path = cleaning_workspace.save_summary(self.context, record["table"], text)
            self.saved.emit(f"Saved {path.name}")
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save Table Summary", str(exc))

    def toggle_complete(self) -> None:
        record = self._record()
        if record is None:
            return
        self._save_summary_silent()
        state = cleaning_workspace.table_state(self.context, record["table"])
        reviewed = not bool(state.get("reviewed"))
        issues = cleaning_workspace.mark_reviewed(self.context, record["table"], reviewed)
        if issues:
            QMessageBox.information(
                self,
                "Table Still Needs Work",
                "\n".join(f"• {item}" for item in issues),
            )
            return
        self.saved.emit("Table completed" if reviewed else "Table reopened")
        self.refresh()

    def prepare_for_completion(self) -> None:
        self._save_summary_silent()

    def completion_issues(self) -> list[str]:
        return cleaning_workspace.milestone_completion_issues(self.context)
