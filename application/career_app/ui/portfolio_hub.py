"""Portfolio Workspace command center."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from career_app.data.roadmap import PROJECT_NAMES
from career_app.services import portfolio_hub, task_workspace
from career_app.theme import COLORS
from career_app.ui.markdown_preview import render_markdown_html
from career_app.ui.portfolio_workspace import PortfolioTaskWorkspaceDialog


def _table(headers: list[str]) -> QTableWidget:
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setAlternatingRowColors(True)
    widget.verticalHeader().setVisible(False)
    widget.horizontalHeader().setStretchLastSection(True)
    return widget


def _item(value: Any, *, tooltip: str = "") -> QTableWidgetItem:
    cell = QTableWidgetItem("" if value is None else str(value))
    if tooltip:
        cell.setToolTip(tooltip)
    return cell


class PortfolioHubWidget(QWidget):
    changed = Signal()
    activeProjectChanged = Signal(int)

    def __init__(
        self,
        conn,
        root: Path,
        parent=None,
        *,
        completion_callback=None,
        active_project_callback=None,
        refresh_callback=None,
    ):
        super().__init__(parent)
        self.conn = conn
        self.root = Path(root)
        self.completion_callback = completion_callback
        self.active_project_callback = active_project_callback
        self.refresh_callback = refresh_callback
        self._dataset = {"tables": [], "relationships": [], "warnings": []}
        self._data_signature = None
        self._loaded_project_id = None
        self._inventory = {}
        self._milestones: list[dict[str, Any]] = []
        self._deliverables: list[dict[str, Any]] = []
        self._build()
        self.refresh_all()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(10)

        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Portfolio Workspace")
        title.setObjectName("Hero")
        subtitle = QLabel(
            "Manage milestones, inspect project data, open real artifacts, "
            "and see what the project demonstrates."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        heading.addLayout(title_box, 1)

        self.project_combo = QComboBox()
        for project_id, name in PROJECT_NAMES.items():
            self.project_combo.addItem(f"{project_id} — {name}", int(project_id))
        self.project_combo.currentIndexChanged.connect(self._project_changed)
        heading.addWidget(self.project_combo)

        self.active_button = QPushButton("Set Active Project")
        self.active_button.clicked.connect(self._set_active)
        heading.addWidget(self.active_button)

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_all)
        heading.addWidget(refresh)
        outer.addLayout(heading)

        self.status = QLabel()
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        outer.addWidget(self.tabs, 1)

        self._build_overview()
        self._build_milestones()
        self._build_data_explorer()
        self._build_workbench()
        self._build_deliverables()
        self._build_evidence()

    def project_id(self) -> int:
        return int(self.project_combo.currentData() or 1)

    def select_project(self, project_id: int):
        index = self.project_combo.findData(int(project_id))
        if index >= 0:
            self.project_combo.setCurrentIndex(index)

    def _build_overview(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        actions = QHBoxLayout()
        open_readme = QPushButton("Open README")
        open_readme.clicked.connect(self._open_readme)
        open_folder = QPushButton("Open Project Folder")
        open_folder.clicked.connect(self._open_project_folder)
        actions.addWidget(open_readme)
        actions.addWidget(open_folder)
        actions.addStretch()
        layout.addLayout(actions)

        self.overview = QTextBrowser()
        self.overview.setOpenExternalLinks(True)
        self.overview.setPlaceholderText("The rendered project README will appear here.")
        layout.addWidget(self.overview, 1)
        self.tabs.addTab(tab, "Overview")

    def _build_milestones(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        summary_row = QHBoxLayout()
        self.milestone_summary = QLabel()
        self.milestone_summary.setObjectName("SectionTitle")
        summary_row.addWidget(self.milestone_summary, 1)
        self.milestone_filter = QComboBox()
        self.milestone_filter.addItems(
            ["All", "Ready / Open", "Completed", "Discovery", "Dataset", "SQL", "Python", "Power BI", "GitHub", "README"]
        )
        self.milestone_filter.currentIndexChanged.connect(self._populate_milestones)
        summary_row.addWidget(self.milestone_filter)
        layout.addLayout(summary_row)

        self.milestone_progress = QProgressBar()
        self.milestone_progress.setRange(0, 100)
        layout.addWidget(self.milestone_progress)

        self.milestone_table = _table(
            ["Stage", "Milestone", "Status", "Estimate", "Artifact / Evidence"]
        )
        self.milestone_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.milestone_table.cellDoubleClicked.connect(lambda *_: self._open_selected_guide())
        layout.addWidget(self.milestone_table, 1)

        actions = QHBoxLayout()
        open_guide = QPushButton("Open Selected Guide")
        open_guide.setObjectName("Primary")
        open_guide.clicked.connect(self._open_selected_guide)
        toggle = QPushButton("Complete / Reopen")
        toggle.clicked.connect(self._toggle_selected_milestone)
        open_artifact = QPushButton("Open Detected Artifact")
        open_artifact.clicked.connect(self._open_selected_deliverable_artifact)
        actions.addWidget(open_guide)
        actions.addWidget(toggle)
        actions.addWidget(open_artifact)
        actions.addStretch()
        layout.addLayout(actions)
        self.tabs.addTab(tab, "Milestones")

    def _build_data_explorer(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        action_row = QHBoxLayout()
        self.data_summary = QLabel()
        self.data_summary.setObjectName("SectionTitle")
        action_row.addWidget(self.data_summary, 1)
        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self._populate_head)
        action_row.addWidget(QLabel("Preview table"))
        action_row.addWidget(self.table_combo)
        refresh = QPushButton("Refresh Data")
        refresh.clicked.connect(self._refresh_data_only)
        action_row.addWidget(refresh)
        open_data = QPushButton("Open Data Folder")
        open_data.clicked.connect(self._open_data_folder)
        action_row.addWidget(open_data)
        layout.addLayout(action_row)

        splitter = QSplitter(Qt.Orientation.Vertical)

        schema_host = QWidget()
        schema_layout = QVBoxLayout(schema_host)
        schema_layout.setContentsMargins(0, 0, 0, 0)
        schema_layout.addWidget(QLabel("All table schemas"))
        self.schema_table = _table(
            ["Table", "Column", "DuckDB type", "Nullable", "Key"]
        )
        self.schema_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        schema_layout.addWidget(self.schema_table)
        splitter.addWidget(schema_host)

        preview_host = QWidget()
        preview_layout = QVBoxLayout(preview_host)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_title = QLabel("First five rows")
        preview_layout.addWidget(self.preview_title)
        self.head_table = QTableWidget()
        self.head_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.head_table.setAlternatingRowColors(True)
        self.head_table.verticalHeader().setVisible(False)
        preview_layout.addWidget(self.head_table)
        splitter.addWidget(preview_host)

        relationship_host = QWidget()
        relationship_layout = QVBoxLayout(relationship_host)
        relationship_layout.setContentsMargins(0, 0, 0, 0)
        relationship_layout.addWidget(QLabel("Declared or inferred relationships"))
        self.relationship_table = _table(
            ["Child", "Child key", "Parent", "Parent key", "Cardinality"]
        )
        relationship_layout.addWidget(self.relationship_table)
        splitter.addWidget(relationship_host)

        splitter.setSizes([320, 280, 180])
        layout.addWidget(splitter, 1)
        self.tabs.addTab(tab, "Data Explorer")

    def _build_workbench(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        row = QHBoxLayout()
        self.workbench_summary = QLabel()
        self.workbench_summary.setObjectName("SectionTitle")
        row.addWidget(self.workbench_summary, 1)
        refresh = QPushButton("Refresh Files")
        refresh.clicked.connect(self._refresh_workbench_only)
        row.addWidget(refresh)
        layout.addLayout(row)

        self.workbench_tree = QTreeWidget()
        self.workbench_tree.setHeaderLabels(["Artifact", "Size", "Modified"])
        self.workbench_tree.setAlternatingRowColors(True)
        self.workbench_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.workbench_tree.itemDoubleClicked.connect(lambda *_: self._open_workbench_item())
        layout.addWidget(self.workbench_tree, 1)

        actions = QHBoxLayout()
        open_item = QPushButton("Open Selected")
        open_item.setObjectName("Primary")
        open_item.clicked.connect(self._open_workbench_item)
        open_folder = QPushButton("Open Project Folder")
        open_folder.clicked.connect(self._open_project_folder)
        actions.addWidget(open_item)
        actions.addWidget(open_folder)
        actions.addStretch()
        layout.addLayout(actions)
        self.tabs.addTab(tab, "Workbench")

    def _build_deliverables(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self.deliverable_summary = QLabel()
        self.deliverable_summary.setObjectName("SectionTitle")
        layout.addWidget(self.deliverable_summary)
        self.deliverable_table = _table(
            ["Stage", "Deliverable / Milestone", "Status", "Expected location", "Detected artifact"]
        )
        self.deliverable_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.deliverable_table.cellDoubleClicked.connect(
            lambda *_: self._open_selected_deliverable_artifact()
        )
        layout.addWidget(self.deliverable_table, 1)

        actions = QHBoxLayout()
        open_artifact = QPushButton("Open Selected Artifact")
        open_artifact.setObjectName("Primary")
        open_artifact.clicked.connect(self._open_selected_deliverable_artifact)
        open_guide = QPushButton("Open Milestone Guide")
        open_guide.clicked.connect(self._open_deliverable_guide)
        actions.addWidget(open_artifact)
        actions.addWidget(open_guide)
        actions.addStretch()
        layout.addLayout(actions)
        self.tabs.addTab(tab, "Deliverables")

    def _build_evidence(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        self.readiness_summary = QLabel()
        self.readiness_summary.setObjectName("SectionTitle")
        self.readiness_summary.setWordWrap(True)
        layout.addWidget(self.readiness_summary)

        splitter = QSplitter(Qt.Orientation.Vertical)

        skills_host = QWidget()
        skills_layout = QVBoxLayout(skills_host)
        skills_layout.setContentsMargins(0, 0, 0, 0)
        skills_layout.addWidget(QLabel("Skill readiness from project milestones and artifacts"))
        self.readiness_table = _table(
            ["Skill", "Status", "Milestone", "Artifact"]
        )
        self.readiness_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        skills_layout.addWidget(self.readiness_table)
        splitter.addWidget(skills_host)

        evidence_host = QWidget()
        evidence_layout = QVBoxLayout(evidence_host)
        evidence_layout.setContentsMargins(0, 0, 0, 0)
        evidence_layout.addWidget(QLabel("Recorded Demonstrated Evidence"))
        self.evidence_table = _table(
            ["Skill", "Source", "What it proves"]
        )
        self.evidence_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        evidence_layout.addWidget(self.evidence_table)
        splitter.addWidget(evidence_host)

        guide_host = QWidget()
        guide_layout = QVBoxLayout(guide_host)
        guide_layout.setContentsMargins(0, 0, 0, 0)
        guide_layout.addWidget(QLabel("Task-guide coverage"))
        self.guide_table = _table(["Milestone", "Guide status", "Details"])
        self.guide_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        guide_layout.addWidget(self.guide_table)
        splitter.addWidget(guide_host)

        splitter.setSizes([300, 220, 180])
        layout.addWidget(splitter, 1)
        self.tabs.addTab(tab, "Evidence & Readiness")

    def _project_changed(self, *_args):
        self.refresh_all()

    def _set_active(self):
        project_id = self.project_id()
        try:
            if self.active_project_callback is not None:
                self.active_project_callback(project_id)
            else:
                self.conn.execute(
                    "UPDATE program_state SET current_project=? WHERE id=1",
                    (project_id,),
                )
                self.conn.commit()
            self.activeProjectChanged.emit(project_id)
            self.status.setText(f"Project {project_id} is now the active portfolio project.")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Set Active Project", str(exc))

    def refresh_all(self, *_args, **_kwargs):
        try:
            project_id = self.project_id()
            self._milestones = portfolio_hub.milestone_rows(self.conn, project_id)
            self._deliverables = portfolio_hub.deliverable_rows(
                self.conn, self.root, project_id
            )
            self._refresh_overview()
            self._populate_milestones()
            signature = portfolio_hub.dataset_signature(
                self.root,
                project_id,
            )
            if signature != self._data_signature:
                self._refresh_data_only()
            if self._loaded_project_id != project_id:
                self._refresh_workbench_only()
                self._loaded_project_id = project_id
            self._populate_deliverables()
            self._populate_evidence()
            self.status.setText(
                f"{portfolio_hub.project_name(project_id)} refreshed • "
                "The workspace reads project files directly and does not replace them with application notes."
            )
        except Exception as exc:
            self.status.setText(f"Portfolio Workspace could not refresh: {exc}")

    def _refresh_overview(self):
        markdown, path = portfolio_hub.overview_markdown(self.root, self.project_id())
        self._readme_path = path
        self.overview.document().setBaseUrl(
            QUrl.fromLocalFile(str(path.parent.resolve()) + "/")
        )
        self.overview.setHtml(render_markdown_html(markdown))

    def _filtered_milestones(self):
        selected = self.milestone_filter.currentText()
        if selected == "All":
            return self._milestones
        if selected == "Ready / Open":
            return [row for row in self._milestones if not bool(row["completed"])]
        if selected == "Completed":
            return [row for row in self._milestones if bool(row["completed"])]
        return [row for row in self._milestones if str(row["stage"]) == selected]

    def _populate_milestones(self, *_args):
        summary = portfolio_hub.milestone_summary(self.conn, self.project_id())
        self.milestone_summary.setText(
            f"{summary['complete']} of {summary['total']} milestones complete • {summary['percent']}%"
        )
        self.milestone_progress.setValue(summary["percent"])
        artifact_by_task = {row["task_id"]: row for row in self._deliverables}
        rows = self._filtered_milestones()
        self.milestone_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            deliverable = artifact_by_task.get(int(row["id"]), {})
            self.milestone_table.setItem(index, 0, _item(row["stage"]))
            self.milestone_table.setItem(index, 1, _item(row["label"]))
            self.milestone_table.setItem(
                index, 2, _item("Completed" if row["completed"] else "Open")
            )
            self.milestone_table.setItem(
                index, 3, _item(f"{int(row['estimated_minutes'] or 45)} min")
            )
            artifact_text = (
                deliverable["artifacts"][0].name
                if deliverable.get("artifacts")
                else deliverable.get("status", "")
            )
            self.milestone_table.setItem(index, 4, _item(artifact_text))
            for column in range(self.milestone_table.columnCount()):
                self.milestone_table.item(index, column).setData(
                    Qt.ItemDataRole.UserRole, int(row["id"])
                )
        self.milestone_table.resizeRowsToContents()

    def _selected_task_id(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return int(value) if value is not None else None

    def _open_guide(self, task_id: int):
        wrapper = None
        if self.completion_callback is not None:
            wrapper = lambda selected_id, completed: self.completion_callback(
                selected_id,
                Qt.CheckState.Checked.value
                if completed
                else Qt.CheckState.Unchecked.value,
            )
        dialog = PortfolioTaskWorkspaceDialog(
            self,
            conn=self.conn,
            root=self.root,
            task_id=int(task_id),
            completion_callback=wrapper,
            refresh_callback=self.refresh_all,
        )
        dialog.exec()
        self.refresh_all()

    def _open_selected_guide(self):
        task_id = self._selected_task_id(self.milestone_table)
        if task_id is None:
            QMessageBox.information(self, "Select a Milestone", "Select a milestone first.")
            return
        self._open_guide(task_id)

    def _toggle_selected_milestone(self):
        task_id = self._selected_task_id(self.milestone_table)
        if task_id is None:
            QMessageBox.information(self, "Select a Milestone", "Select a milestone first.")
            return
        row = next((item for item in self._milestones if int(item["id"]) == task_id), None)
        if row is None:
            return
        completed = not bool(row["completed"])
        try:
            if self.completion_callback is not None:
                self.completion_callback(
                    task_id,
                    Qt.CheckState.Checked.value
                    if completed
                    else Qt.CheckState.Unchecked.value,
                )
            else:
                self.conn.execute(
                    "UPDATE project_tasks SET completed=? WHERE id=?",
                    (1 if completed else 0, task_id),
                )
                self.conn.commit()
            self.refresh_all()
            self.changed.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Update Milestone", str(exc))

    def _refresh_data_only(self):
        project_id = self.project_id()
        self._dataset = portfolio_hub.dataset_profiles(
            self.root,
            project_id,
            limit=5,
        )
        self._data_signature = portfolio_hub.dataset_signature(
            self.root,
            project_id,
        )
        tables = self._dataset["tables"]
        schema_rows = sum(len(table.columns) for table in tables)
        total_rows = sum(table.row_count for table in tables)
        self.data_summary.setText(
            f"{len(tables)} tables • {schema_rows} columns • {total_rows:,} source rows"
        )

        self.schema_table.setRowCount(schema_rows)
        row_index = 0
        for table in tables:
            for column in table.columns:
                self.schema_table.setItem(row_index, 0, _item(table.name))
                self.schema_table.setItem(row_index, 1, _item(column["name"]))
                self.schema_table.setItem(row_index, 2, _item(column["type"]))
                self.schema_table.setItem(row_index, 3, _item(column["nullable"]))
                self.schema_table.setItem(row_index, 4, _item(column["key"]))
                row_index += 1
        self.schema_table.resizeColumnsToContents()
        self.schema_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

        previous = self.table_combo.currentData()
        self.table_combo.blockSignals(True)
        self.table_combo.clear()
        for index, table in enumerate(tables):
            label = f"{table.name} • {table.row_count:,} rows"
            if table.error:
                label += " • error"
            self.table_combo.addItem(label, index)
        self.table_combo.blockSignals(False)
        if previous is not None and int(previous) < len(tables):
            self.table_combo.setCurrentIndex(int(previous))
        elif tables:
            self.table_combo.setCurrentIndex(0)
        self._populate_head()

        relationships = self._dataset["relationships"]
        self.relationship_table.setRowCount(len(relationships))
        for index, relation in enumerate(relationships):
            self.relationship_table.setItem(index, 0, _item(relation.get("child", "")))
            self.relationship_table.setItem(index, 1, _item(relation.get("child_key", "")))
            self.relationship_table.setItem(index, 2, _item(relation.get("parent", "")))
            self.relationship_table.setItem(index, 3, _item(relation.get("parent_key", "")))
            self.relationship_table.setItem(
                index, 4, _item(relation.get("cardinality", "one-to-many"))
            )

    def _populate_head(self, *_args):
        index = self.table_combo.currentData()
        tables = self._dataset.get("tables", [])
        if index is None or int(index) >= len(tables):
            self.head_table.clear()
            self.head_table.setRowCount(0)
            self.head_table.setColumnCount(0)
            self.preview_title.setText("First five rows")
            return
        table = tables[int(index)]
        self.preview_title.setText(
            f"`{table.name}` • {table.source_path} • first five rows"
            + (f" • {table.error}" if table.error else "")
        )
        self.head_table.setColumnCount(len(table.head_columns))
        self.head_table.setHorizontalHeaderLabels(table.head_columns)
        self.head_table.setRowCount(len(table.head_rows))
        for row_index, row in enumerate(table.head_rows):
            for column_index, value in enumerate(row):
                self.head_table.setItem(row_index, column_index, _item(value))
        self.head_table.resizeColumnsToContents()

    def _refresh_workbench_only(self):
        self._inventory = portfolio_hub.artifact_inventory(self.root, self.project_id())
        self.workbench_tree.clear()
        total = 0
        for category, rows in self._inventory.items():
            if not rows:
                continue
            parent = QTreeWidgetItem([f"{category} ({len(rows)})", "", ""])
            parent.setExpanded(category in {"Notebooks", "SQL", "Power BI", "Reports"})
            self.workbench_tree.addTopLevelItem(parent)
            for row in rows:
                total += 1
                modified = datetime.fromtimestamp(row["modified"]).strftime("%Y-%m-%d %H:%M")
                child = QTreeWidgetItem(
                    [
                        row["relative"],
                        self._format_size(row["size"]),
                        modified,
                    ]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, str(row["path"]))
                parent.addChild(child)
        self.workbench_summary.setText(f"{total} project artifacts detected")

    @staticmethod
    def _format_size(value: int) -> str:
        size = float(value)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{value} B"

    def _populate_deliverables(self):
        ready = sum(row["status"] == "Ready" for row in self._deliverables)
        self.deliverable_summary.setText(
            f"{ready} of {len(self._deliverables)} milestone deliverables are complete and detected"
        )
        self.deliverable_table.setRowCount(len(self._deliverables))
        for index, row in enumerate(self._deliverables):
            artifact = (
                row["artifacts"][0].relative_to(
                    portfolio_hub.project_directory(self.root, self.project_id())
                ).as_posix()
                if row["artifacts"]
                else ""
            )
            self.deliverable_table.setItem(index, 0, _item(row["stage"]))
            self.deliverable_table.setItem(index, 1, _item(row["label"]))
            self.deliverable_table.setItem(index, 2, _item(row["status"]))
            self.deliverable_table.setItem(index, 3, _item(row["expected"]))
            self.deliverable_table.setItem(index, 4, _item(artifact))
            for column in range(self.deliverable_table.columnCount()):
                self.deliverable_table.item(index, column).setData(
                    Qt.ItemDataRole.UserRole, int(row["task_id"])
                )
        self.deliverable_table.resizeRowsToContents()

    def _populate_evidence(self):
        readiness = portfolio_hub.readiness_rows(self.conn, self.root, self.project_id())
        evidence = portfolio_hub.evidence_rows(self.conn, self.project_id())
        guide_rows = portfolio_hub.guide_audit_rows(self.conn, self.root, self.project_id())

        demonstrated = sum(row["status"] == "Demonstrated" for row in readiness)
        gaps = sum(row["status"] == "Not yet demonstrated" for row in readiness)
        self.readiness_summary.setText(
            f"{demonstrated} skills have milestone-and-artifact support • "
            f"{gaps} are not yet demonstrated • "
            "Completed milestones without detected artifacts are flagged for evidence linking."
        )

        self.readiness_table.setRowCount(len(readiness))
        for index, row in enumerate(readiness):
            for column, key in enumerate(("skill", "status", "milestone", "artifact")):
                self.readiness_table.setItem(index, column, _item(row[key]))

        self.evidence_table.setRowCount(len(evidence))
        for index, row in enumerate(evidence):
            self.evidence_table.setItem(index, 0, _item(row.get("skill", "")))
            self.evidence_table.setItem(
                index, 1, _item(f"{row.get('source_type', '')} • {row.get('source_name', '')}")
            )
            self.evidence_table.setItem(index, 2, _item(row.get("description", "")))

        self.guide_table.setRowCount(len(guide_rows))
        for index, row in enumerate(guide_rows):
            self.guide_table.setItem(index, 0, _item(row["label"]))
            self.guide_table.setItem(index, 1, _item(row["status"]))
            self.guide_table.setItem(index, 2, _item("; ".join(row["issues"])))

    def _selected_deliverable(self):
        table = self.deliverable_table if self.tabs.currentWidget() is self.tabs.widget(4) else None
        if table is None:
            task_id = self._selected_task_id(self.milestone_table)
        else:
            task_id = self._selected_task_id(table)
        if task_id is None:
            return None
        return next(
            (row for row in self._deliverables if int(row["task_id"]) == int(task_id)),
            None,
        )

    def _open_selected_deliverable_artifact(self):
        row = self._selected_deliverable()
        if row is None:
            QMessageBox.information(self, "Select a Deliverable", "Select a milestone or deliverable first.")
            return
        if not row["artifacts"]:
            QMessageBox.information(
                self,
                "Artifact Not Detected",
                "No expected artifact was found yet. Open the milestone guide for its required output paths.",
            )
            return
        self._open_path(row["artifacts"][0])

    def _open_deliverable_guide(self):
        task_id = self._selected_task_id(self.deliverable_table)
        if task_id is None:
            QMessageBox.information(self, "Select a Deliverable", "Select a deliverable first.")
            return
        self._open_guide(task_id)

    def _open_workbench_item(self):
        item = self.workbench_tree.currentItem()
        if item is None:
            return
        value = item.data(0, Qt.ItemDataRole.UserRole)
        if not value:
            return
        self._open_path(Path(value))

    def _open_path(self, path: Path):
        try:
            task_workspace.open_artifact(path, root=self.root)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Artifact", str(exc))

    def _open_readme(self):
        self._open_path(self._readme_path)

    def _open_project_folder(self):
        self._open_path(portfolio_hub.project_directory(self.root, self.project_id()))

    def _open_data_folder(self):
        self._open_path(
            portfolio_hub.project_directory(self.root, self.project_id()) / "data"
        )
