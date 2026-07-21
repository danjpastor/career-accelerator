"""Guided portfolio milestone workspace."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QBoxLayout,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.services import portfolio_workspace
from career_app.theme import stylesheet
from career_app.ui.markdown_preview import (
    path_field_stylesheet, raw_markdown_stylesheet, render_markdown_html,
)


class PortfolioTaskWorkspaceDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        conn,
        root: Path,
        task_id: int,
        completion_callback=None,
        refresh_callback=None,
    ):
        super().__init__(parent)
        self.conn = conn
        self.root = Path(root)
        self.task_id = int(task_id)
        self.completion_callback = completion_callback
        self.refresh_callback = refresh_callback
        self.workspace = portfolio_workspace.ensure_document(
            self.conn,
            self.root,
            self.task_id,
        )
        self.task = self.workspace["task"]
        self.document_path = self.workspace["document_path"]
        self._dirty = False

        self.setWindowTitle(
            f"Portfolio Milestone — {self.task['label']}"
        )
        self.setMinimumSize(780, 600)
        parent_width = max(820, parent.width() if parent is not None else 1180)
        parent_height = max(640, parent.height() if parent is not None else 860)
        self.resize(min(1180, parent_width - 44), min(860, parent_height - 44))
        self.setStyleSheet(
            stylesheet(
                getattr(parent, "_ui_scale", 1.0),
                getattr(parent, "_content_scale", 1.0),
            )
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(10)

        title = QLabel(str(self.task["label"]))
        title.setObjectName("Hero")
        title.setWordWrap(True)
        root_layout.addWidget(title)

        meta = QLabel(
            f"{self.workspace['project_name']} • {self.task['stage']} • "
            f"About {int(self.task['estimated_minutes'] or 45)} minutes"
        )
        meta.setObjectName("Muted")
        meta.setWordWrap(True)
        root_layout.addWidget(meta)

        guide = QGridLayout()
        guide.setHorizontalSpacing(14)
        guide.setVerticalSpacing(8)
        guide.addWidget(QLabel("What you are doing"), 0, 0)
        description = QLabel(
            str(self.task["description"] or "Complete this portfolio milestone.")
        )
        description.setWordWrap(True)
        description.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        guide.addWidget(description, 0, 1)

        guide.addWidget(QLabel("Done when"), 1, 0)
        definition = QLabel(
            str(
                self.task["definition_of_done"]
                or "Review the work, save the result, and confirm it meets the project goal."
            )
        )
        definition.setWordWrap(True)
        definition.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        guide.addWidget(definition, 1, 1)
        guide.setColumnStretch(1, 1)
        root_layout.addLayout(guide)

        path_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        path_row.addWidget(QLabel("Task guide"))
        self.path_field = QLineEdit(str(self.document_path))
        self.path_field.setReadOnly(True)
        self.path_field.setStyleSheet(path_field_stylesheet())
        path_row.addWidget(self.path_field, 1)
        open_external = QPushButton("Open Guide Externally")
        open_external.clicked.connect(self.open_external)
        path_row.addWidget(open_external)
        open_folder = QPushButton("Open Project Folder")
        open_folder.clicked.connect(self.open_folder)
        path_row.addWidget(open_folder)
        root_layout.addLayout(path_row)

        self.data_workspace = self.workspace.get("data_workspace")
        self.data_workspace_row = QWidget()
        data_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.data_workspace_row)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.setSpacing(8)
        self.data_workspace_status = QLabel()
        self.data_workspace_status.setObjectName("Muted")
        self.data_workspace_status.setWordWrap(True)
        data_layout.addWidget(self.data_workspace_status, 1)
        self.open_starter_button = QPushButton("Open Notebook in VS Code")
        self.open_starter_button.setObjectName("Primary")
        self.open_starter_button.clicked.connect(self.open_relationship_notebook)
        data_layout.addWidget(self.open_starter_button)
        self.refresh_data_button = QPushButton("Refresh Project Data")
        self.refresh_data_button.clicked.connect(self.refresh_data_workspace)
        data_layout.addWidget(self.refresh_data_button)
        root_layout.addWidget(self.data_workspace_row)
        self._refresh_data_workspace_status()

        self.document_views = QTabWidget()
        self.document_views.setMinimumWidth(0)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setPlaceholderText("The rendered milestone guide will appear here.")
        self.document_views.addTab(self.preview, "Visual Guide")

        self.editor = QTextEdit()
        self.editor.setStyleSheet(raw_markdown_stylesheet())
        self.editor.setPlainText(self.workspace["content"])
        self.editor.setPlaceholderText(
            "Edit the raw Markdown, record decisions, and complete the milestone here."
        )
        self.editor.textChanged.connect(self._changed)
        self.document_views.addTab(self.editor, "Raw Markdown")
        root_layout.addWidget(self.document_views, 1)

        self.guide_setup = QWidget()
        setup_layout = QVBoxLayout(self.guide_setup)
        setup_layout.setContentsMargins(0, 2, 0, 0)
        setup_layout.setSpacing(6)
        setup_title = QLabel("Set up files and folders from this guide")
        setup_title.setObjectName("SectionTitle")
        setup_layout.addWidget(setup_title)
        self.reference_help = QLabel(
            "Select the items you need, then create them in the correct project folder."
        )
        self.reference_help.setObjectName("Muted")
        self.reference_help.setWordWrap(True)
        setup_layout.addWidget(self.reference_help)
        self.reference_list = QListWidget()
        self.reference_list.setWordWrap(True)
        self.reference_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.reference_list.setMaximumHeight(150)
        setup_layout.addWidget(self.reference_list)

        setup_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        create_selected = QPushButton("Create Selected")
        create_selected.setObjectName("Primary")
        create_selected.clicked.connect(self.create_selected_references)
        create_all = QPushButton("Create All Missing")
        create_all.clicked.connect(self.create_all_references)
        open_selected = QPushButton("Open Selected")
        open_selected.clicked.connect(self.open_selected_reference)
        open_base = QPushButton("Open Project Folder")
        open_base.clicked.connect(self.open_reference_base)
        setup_buttons.addWidget(create_selected)
        setup_buttons.addWidget(create_all)
        setup_buttons.addWidget(open_selected)
        setup_buttons.addWidget(open_base)
        setup_buttons.addStretch()
        setup_layout.addLayout(setup_buttons)
        root_layout.addWidget(self.guide_setup)

        bottom = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.save_state = QLabel("Saved")
        self.save_state.setObjectName("Muted")
        bottom.addWidget(self.save_state)
        bottom.addStretch()

        save_button = QPushButton("Save Markdown")
        save_button.setObjectName("Primary")
        save_button.clicked.connect(self.save_document)
        bottom.addWidget(save_button)

        self.complete_button = QPushButton(
            "Reopen Milestone" if bool(self.task["completed"]) else "Mark Complete"
        )
        self.complete_button.clicked.connect(self.toggle_complete)
        bottom.addWidget(self.complete_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        bottom.addWidget(close_button)
        root_layout.addLayout(bottom)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(1400)
        self.autosave_timer.timeout.connect(self.save_document)
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(180)
        self.preview_timer.timeout.connect(self._update_markdown_preview)

        self._update_markdown_preview()
        self._refresh_guide_references()
        self.document_views.setCurrentIndex(0)

    def _refresh_data_workspace_status(self):
        plan = getattr(self, "data_workspace", None)
        self.data_workspace_row.setVisible(plan is not None)
        if plan is None:
            return
        from career_app.services import project_data_workspace

        self.data_workspace_status.setText(
            "Portfolio SQL workspace: " + project_data_workspace.plan_summary(plan)
        )
        self.open_starter_button.setEnabled(
            bool(
                plan.database_ready
                and plan.notebook_path
                and Path(plan.notebook_path).is_file()
                and plan.workspace_path
                and Path(plan.workspace_path).is_file()
            )
        )

    def refresh_data_workspace(self):
        try:
            updated = portfolio_workspace.refresh_data_workspace(
                self.conn, self.root, self.task_id
            )
            self.workspace = updated
            self.data_workspace = updated.get("data_workspace")
            self.document_path = updated["document_path"]
            self.path_field.setText(str(self.document_path))
            self.editor.blockSignals(True)
            self.editor.setPlainText(updated["content"])
            self.editor.blockSignals(False)
            self._dirty = False
            self.save_state.setText("Project data refreshed")
            self._update_markdown_preview()
            self._refresh_data_workspace_status()
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Refresh Project Data", str(exc))

    def open_relationship_notebook(self):
        try:
            opened_with = portfolio_workspace.open_relationship_notebook(
                self.conn, self.root, self.task_id
            )
            self.save_state.setText(f"Notebook opened in {opened_with}")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Notebook", str(exc))

    def _changed(self):
        self._dirty = True
        self.save_state.setText("Unsaved changes")
        self.preview_timer.start()
        self.autosave_timer.start()

    def _update_markdown_preview(self):
        content = self.editor.toPlainText()
        self.preview.setHtml(render_markdown_html(content))
        self._refresh_guide_references()

    def _guide_reference_rows(self):
        return portfolio_workspace.task_workspace.guide_referenced_paths(
            self.root,
            self.document_path,
            self.editor.toPlainText(),
        )

    def _refresh_guide_references(self):
        if not hasattr(self, "reference_list"):
            return
        if getattr(self, "data_workspace", None) is not None:
            self.reference_list.clear()
            self.guide_setup.setVisible(False)
            return
        checked = set()
        for index in range(self.reference_list.count()):
            item = self.reference_list.item(index)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if item.checkState() == Qt.CheckState.Checked:
                checked.add(str(data.get("display_path", "")))
        rows = self._guide_reference_rows()
        self.reference_list.clear()
        for row in rows:
            kind = "Folder" if row["is_directory"] else "File"
            prefix = "✓" if row["exists"] else "○"
            item = QListWidgetItem(
                f"{prefix} {row['display_path']}  •  {kind}"
                + ("  •  Already exists" if row["exists"] else "")
            )
            item.setData(Qt.ItemDataRole.UserRole, row)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            should_check = (
                not row["exists"]
                and (not checked or row["display_path"] in checked)
            )
            item.setCheckState(
                Qt.CheckState.Checked if should_check else Qt.CheckState.Unchecked
            )
            self.reference_list.addItem(item)
        self.guide_setup.setVisible(bool(rows))
        if rows:
            base = rows[0]["base_path"]
            try:
                base_text = base.relative_to(self.root).as_posix()
            except ValueError:
                base_text = str(base)
            self.reference_help.setText(
                "These paths were found in the guide. New relative paths will be "
                f"created under {base_text}. Existing work is never overwritten."
            )

    def _create_reference_rows(self, rows):
        created = []
        for row in rows:
            if row.get("exists"):
                continue
            created.append(
                portfolio_workspace.task_workspace.create_guide_reference(
                    self.root,
                    self.document_path,
                    row["reference"],
                    is_directory=bool(row["is_directory"]),
                    starter_content=row.get("starter_content"),
                )
            )
        self._refresh_guide_references()
        if created:
            self.save_state.setText(
                f"Created {len(created)} guide item{'s' if len(created) != 1 else ''}"
            )
        else:
            self.save_state.setText("Everything selected already exists")

    def create_selected_references(self):
        rows = []
        for index in range(self.reference_list.count()):
            item = self.reference_list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    rows.append(data)
        if not rows:
            QMessageBox.information(
                self,
                "Nothing Selected",
                "Select one or more missing files or folders first.",
            )
            return
        try:
            self._create_reference_rows(rows)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Create Guide Items", str(exc))

    def create_all_references(self):
        try:
            self._create_reference_rows(
                [row for row in self._guide_reference_rows() if not row["exists"]]
            )
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Create Guide Items", str(exc))

    def open_selected_reference(self):
        item = self.reference_list.currentItem()
        if item is None:
            QMessageBox.information(
                self,
                "Select a File or Folder",
                "Choose an item from the setup list first.",
            )
            return
        row = item.data(Qt.ItemDataRole.UserRole) or {}
        path = row.get("resolved_path")
        if path is None or not Path(path).exists():
            QMessageBox.information(
                self,
                "Create This Item First",
                "Create the selected file or folder before opening it.",
            )
            return
        try:
            portfolio_workspace.task_workspace.open_artifact(path, root=self.root)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Item", str(exc))

    def open_reference_base(self):
        rows = self._guide_reference_rows()
        base = rows[0]["base_path"] if rows else self.document_path.parent
        try:
            portfolio_workspace.task_workspace.open_artifact(base, root=self.root)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Project Folder", str(exc))

    def save_document(self):
        try:
            portfolio_workspace.save_document(
                self.conn,
                self.root,
                self.task_id,
                self.editor.toPlainText(),
            )
            self._dirty = False
            self._update_markdown_preview()
            self.save_state.setText("Saved")
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Save", str(exc))

    def open_external(self):
        self.save_document()
        try:
            portfolio_workspace.open_document(self.document_path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Document", str(exc))

    def open_folder(self):
        try:
            portfolio_workspace.open_folder(self.document_path)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Folder", str(exc))

    def toggle_complete(self):
        completed = not bool(self.task["completed"])
        self.save_document()
        try:
            if self.completion_callback is not None:
                self.completion_callback(self.task_id, completed)
            else:
                portfolio_workspace.set_completed(
                    self.conn,
                    self.task_id,
                    completed,
                )
            self.task = portfolio_workspace.project_task_record(
                self.conn,
                self.task_id,
            )
            self.complete_button.setText(
                "Reopen Milestone" if completed else "Mark Complete"
            )
            if self.refresh_callback is not None:
                self.refresh_callback()
            self.save_state.setText(
                "Milestone completed" if completed else "Milestone reopened"
            )
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Update Milestone", str(exc))

    def accept(self):
        if self._dirty:
            self.save_document()
        super().accept()
