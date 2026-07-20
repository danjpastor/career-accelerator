"""Unified Task Workspace dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.services import (
    sql_workspace,
    task_workspace as workspace_service,
    tracks,
)
from career_app.theme import stylesheet


class TaskWorkspaceDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        conn,
        root: Path,
        state,
        task_id: int | None = None,
        workspace_key: str | None = None,
        complete_callback=None,
        refresh_callback=None,
        start_session_callback=None,
        edit_task_callback=None,
    ):
        super().__init__(parent)
        self.conn = conn
        self.root = Path(root)
        self.program_state = state
        self.complete_callback = complete_callback
        self.refresh_callback = refresh_callback
        self.start_session_callback = start_session_callback
        self.edit_task_callback = edit_task_callback
        self._loading = False
        self._dirty = False

        self.workspace = workspace_service.ensure_workspace(
            self.conn,
            self.root,
            task_id=task_id,
            workspace_key=workspace_key,
            current_project=int(state["current_project"]),
        )
        self.workspace_key = self.workspace["workspace_key"]
        self.task_id = self.workspace["task_id"]

        self.setWindowTitle(
            f"Task Workspace — {self.workspace['task_label']}"
        )
        self.setMinimumSize(720, 540)
        parent_width = max(760, parent.width() if parent is not None else 1120)
        parent_height = max(580, parent.height() if parent is not None else 820)
        self.resize(min(1120, parent_width - 48), min(820, parent_height - 48))
        self.setStyleSheet(
            stylesheet(
                getattr(parent, "_ui_scale", 1.0),
                getattr(parent, "_content_scale", 1.0),
            )
        )
        self._responsive_rows: list[QBoxLayout] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(10)

        title = QLabel(self.workspace["task_label"])
        title.setObjectName("Hero")
        title.setWordWrap(True)
        root_layout.addWidget(title)

        self.summary = QLabel("")
        self.summary.setObjectName("Muted")
        self.summary.setWordWrap(True)
        root_layout.addWidget(self.summary)

        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(0)
        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )
        self.tabs.addTab(self._document_tab(), "Document")
        self.tabs.addTab(self._task_tab(), "Task & Schedule")
        self.tabs.addTab(self._evidence_tab(), "Artifacts & Sessions")
        root_layout.addWidget(self.tabs, 1)

        bottom = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(bottom)
        self.save_state = QLabel("Saved")
        self.save_state.setObjectName("Muted")
        bottom.addWidget(self.save_state)
        bottom.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        bottom.addWidget(close_button)
        root_layout.addLayout(bottom)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(1400)
        self.autosave_timer.timeout.connect(self.save_document)

        self._load_workspace()

    def _document_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(9)

        path_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(path_row)
        path_row.addWidget(QLabel("Document"))
        self.path_label = QLineEdit()
        self.path_label.setReadOnly(True)
        path_row.addWidget(self.path_label, 1)
        layout.addLayout(path_row)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Write notes, a reflection, a retrospective, or a study plan here."
        )
        self.editor.textChanged.connect(self._document_changed)
        layout.addWidget(self.editor, 1)

        buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(buttons)
        save_button = QPushButton("Save")
        save_button.setObjectName("Primary")
        save_button.clicked.connect(self.save_document)
        reload_button = QPushButton("Reload From File")
        reload_button.clicked.connect(self.reload_document)
        external_button = QPushButton("Open Externally")
        external_button.clicked.connect(self.open_external)
        folder_button = QPushButton("Open Folder")
        folder_button.clicked.connect(self.open_folder)
        buttons.addWidget(save_button)
        buttons.addWidget(reload_button)
        buttons.addWidget(external_button)
        buttons.addWidget(folder_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        return tab

    def _task_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(10)

        info = QGridLayout()
        self.info_week = QLabel("—")
        self.info_category = QLabel("—")
        self.info_eligibility = QLabel("—")
        self.info_eligibility.setWordWrap(True)
        self.info_description = QLabel("—")
        self.info_description.setWordWrap(True)
        self.info_definition = QLabel("—")
        self.info_definition.setWordWrap(True)
        info.addWidget(QLabel("Roadmap week"), 0, 0)
        info.addWidget(self.info_week, 0, 1)
        info.addWidget(QLabel("Category"), 1, 0)
        info.addWidget(self.info_category, 1, 1)
        info.addWidget(QLabel("Eligibility"), 2, 0)
        info.addWidget(self.info_eligibility, 2, 1)
        info.addWidget(QLabel("Task brief"), 3, 0, Qt.AlignmentFlag.AlignTop)
        info.addWidget(self.info_description, 3, 1)
        info.addWidget(QLabel("Done when"), 4, 0, Qt.AlignmentFlag.AlignTop)
        info.addWidget(self.info_definition, 4, 1)
        info.setColumnStretch(1, 1)
        layout.addLayout(info)

        form = QFormLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItems(
            [
                "Not Started",
                "In Progress",
                "Blocked",
                "Deferred",
                "Completed",
            ]
        )
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 3)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(5, 480)
        self.minutes_spin.setSuffix(" min")
        self.energy_combo = QComboBox()
        self.energy_combo.addItems(["Low", "Normal", "High"])
        self.scheduled_edit = QLineEdit()
        self.scheduled_edit.setPlaceholderText("YYYY-MM-DD")
        self.deferred_edit = QLineEdit()
        self.deferred_edit.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Status", self.status_combo)
        form.addRow("Priority", self.priority_spin)
        form.addRow("Estimated time", self.minutes_spin)
        form.addRow("Energy", self.energy_combo)
        form.addRow("Scheduled for", self.scheduled_edit)
        form.addRow("Deferred until", self.deferred_edit)
        layout.addLayout(form)

        hint = QLabel(
            "Scheduled for is your intended work date. Deferred until removes the task "
            "from active planning until that date."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(actions)
        save_task = QPushButton("Save Task & Schedule")
        save_task.setObjectName("Primary")
        save_task.clicked.connect(self.save_task_settings)
        complete = QPushButton("Mark Complete")
        complete.clicked.connect(self.mark_complete)
        edit = QPushButton("Open Detailed Task Editor")
        edit.clicked.connect(self.open_task_editor)
        start = QPushButton("Start Linked Study Session")
        start.clicked.connect(self.start_linked_session)
        actions.addWidget(save_task)
        actions.addWidget(complete)
        actions.addWidget(edit)
        actions.addWidget(start)
        layout.addLayout(actions)
        layout.addStretch()

        self.task_controls = [
            self.status_combo,
            self.priority_spin,
            self.minutes_spin,
            self.energy_combo,
            self.scheduled_edit,
            self.deferred_edit,
            save_task,
            complete,
            edit,
            start,
        ]
        return tab

    def _evidence_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(10)

        artifact_form = QGridLayout()
        self.artifact_label = QLineEdit()
        self.artifact_label.setPlaceholderText("Example: Dashboard screenshot")
        self.artifact_path = QLineEdit()
        self.artifact_path.setPlaceholderText("File or folder path")
        browse = QPushButton("Browse File")
        browse.clicked.connect(self.browse_artifact)
        browse_folder = QPushButton("Browse Folder")
        browse_folder.clicked.connect(self.browse_artifact_folder)
        add = QPushButton("Add Artifact")
        add.setObjectName("Primary")
        add.clicked.connect(self.add_artifact)
        artifact_form.addWidget(QLabel("Label"), 0, 0)
        artifact_form.addWidget(self.artifact_label, 0, 1, 1, 2)
        artifact_form.addWidget(QLabel("Path"), 1, 0)
        artifact_form.addWidget(self.artifact_path, 1, 1)
        browse_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(browse_row)
        browse_row.addWidget(browse)
        browse_row.addWidget(browse_folder)
        artifact_form.addLayout(browse_row, 1, 2)
        artifact_form.addWidget(add, 2, 2)
        artifact_form.setColumnStretch(1, 1)
        layout.addLayout(artifact_form)

        layout.addWidget(QLabel("Linked artifacts"))
        self.artifact_list = QListWidget()
        self.artifact_list.setWordWrap(True)
        self.artifact_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.artifact_list.itemDoubleClicked.connect(self.open_artifact)
        layout.addWidget(self.artifact_list, 1)

        artifact_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(artifact_buttons)
        open_artifact = QPushButton("Open Selected Artifact")
        open_artifact.clicked.connect(self.open_artifact)
        remove_artifact = QPushButton("Remove Link")
        remove_artifact.clicked.connect(self.remove_artifact)
        artifact_buttons.addWidget(open_artifact)
        artifact_buttons.addWidget(remove_artifact)
        artifact_buttons.addStretch()
        layout.addLayout(artifact_buttons)

        layout.addWidget(QLabel("Linked study sessions"))
        self.session_list = QListWidget()
        self.session_list.setWordWrap(True)
        self.session_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        layout.addWidget(self.session_list, 1)

        session_buttons = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._responsive_rows.append(session_buttons)
        link_recent = QPushButton("Link Most Recent Unlinked Session")
        link_recent.clicked.connect(self.link_recent_session)
        start_session = QPushButton("Start New Linked Session")
        start_session.setObjectName("Primary")
        start_session.clicked.connect(self.start_linked_session)
        unlink = QPushButton("Unlink Selected Session")
        unlink.clicked.connect(self.unlink_session)
        session_buttons.addWidget(link_recent)
        session_buttons.addWidget(start_session)
        session_buttons.addWidget(unlink)
        layout.addLayout(session_buttons)
        return tab

    def _load_workspace(self):
        self._loading = True
        try:
            self.workspace = workspace_service.ensure_workspace(
                self.conn,
                self.root,
                workspace_key=self.workspace_key,
                current_project=int(self.program_state["current_project"]),
            )
            self.path_label.setText(str(self.workspace["document_path"]))
            self.editor.setPlainText(self.workspace["content"])
            self.scheduled_edit.setText(self.workspace["scheduled_for"] or "")
            self.summary.setText(
                f"{self.workspace['workspace_type_label']} • "
                f"{self.workspace_key} • "
                + (
                    "Current roadmap task"
                    if self.workspace["is_current"]
                    else "Historical workspace — task controls are read-only"
                )
            )

            task = self.workspace["task"]
            if task is not None and self.workspace["is_current"]:
                self.task_id = int(task["id"])
                self.info_week.setText(f"Week {task['week']}")
                self.info_category.setText(task["category"] or "General")
                eligibility = task["prerequisite_state"] or "Ready"
                if task["prerequisite_reason"]:
                    eligibility += f" — {task['prerequisite_reason']}"
                self.info_eligibility.setText(eligibility)
                self.info_description.setText(
                    task["description"] or "Open the workspace for the guided task brief."
                )
                self.info_definition.setText(
                    task["definition_of_done"] or "Complete the work and save the result."
                )
                self.status_combo.setCurrentText(task["status"] or "Not Started")
                self.priority_spin.setValue(int(task["priority"] or 3))
                self.minutes_spin.setValue(int(task["estimated_minutes"] or 30))
                self.energy_combo.setCurrentText(task["energy"] or "Normal")
                self.deferred_edit.setText(task["deferred_until"] or "")
                for control in self.task_controls:
                    control.setEnabled(True)
            else:
                self.info_week.setText("Historical")
                self.info_category.setText(self.workspace["workspace_type_label"])
                self.info_eligibility.setText(
                    "The original adaptive assignment has moved on. The document, "
                    "artifacts, and sessions remain available."
                )
                self.info_description.setText(
                    "This workspace is retained as historical work."
                )
                self.info_definition.setText(
                    "No additional completion action is required."
                )
                for control in self.task_controls:
                    control.setEnabled(False)

            self._refresh_artifacts()
            self._refresh_sessions()
            self._dirty = False
            self.save_state.setText("Saved")
        finally:
            self._loading = False

    def _document_changed(self):
        if self._loading:
            return
        self._dirty = True
        self.save_state.setText("Autosaving…")
        self.autosave_timer.start()

    def save_document(self):
        if self._loading:
            return
        try:
            workspace_service.save_document(
                self.conn,
                self.root,
                self.workspace_key,
                self.editor.toPlainText(),
                scheduled_for=self.scheduled_edit.text(),
            )
        except Exception as exc:
            self.save_state.setText("Save failed")
            QMessageBox.warning(self, "Could Not Save Workspace", str(exc))
            return
        self._dirty = False
        self.save_state.setText("Saved")

    def reload_document(self):
        if self._dirty:
            answer = QMessageBox.question(
                self,
                "Reload Document",
                "Save current edits before reloading the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Yes:
                self.save_document()
        self._load_workspace()

    def open_external(self):
        self.save_document()
        try:
            editor = sql_workspace.open_in_editor(
                self.workspace["document_path"],
                root=self.root,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Document", str(exc))
            return
        self.save_state.setText(f"Opened in {editor}")

    def open_folder(self):
        try:
            app = workspace_service.open_folder(self.workspace["document_path"])
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Folder", str(exc))
            return
        self.save_state.setText(f"Opened in {app}")

    def save_task_settings(self):
        if not self.workspace["is_current"] or self.task_id is None:
            return
        selected_status = self.status_combo.currentText()
        if selected_status == "Completed" and not tracks.task_has_completion_evidence(
            self.conn, self.task_id
        ):
            self.mark_complete()
            return
        self.save_document()
        try:
            effective_id = workspace_service.save_task_settings(
                self.conn,
                self.program_state,
                self.task_id,
                status=selected_status,
                priority=self.priority_spin.value(),
                estimated_minutes=self.minutes_spin.value(),
                energy=self.energy_combo.currentText(),
                deferred_until=self.deferred_edit.text(),
                scheduled_for=self.scheduled_edit.text(),
                workspace_key=self.workspace_key,
            )
            self.task_id = effective_id
            if self.refresh_callback:
                self.refresh_callback()
            self.program_state = self.parent().state
            self._load_workspace()
        except Exception as exc:
            QMessageBox.warning(self, "Task Could Not Be Updated", str(exc))
            return
        self.save_state.setText("Task and schedule saved")

    def mark_complete(self):
        if not self.workspace["is_current"] or self.task_id is None:
            return
        self.save_document()
        try:
            if self.complete_callback:
                self.complete_callback(self.task_id)
            else:
                raise RuntimeError("Task completion is unavailable.")
        except Exception as exc:
            QMessageBox.warning(self, "Task Could Not Be Completed", str(exc))
            return
        self.accept()

    def open_task_editor(self):
        if self.edit_task_callback and self.task_id is not None:
            self.save_document()
            self.edit_task_callback(self.task_id)
            self.program_state = self.parent().state
            self._load_workspace()

    def start_linked_session(self):
        if self.start_session_callback and self.task_id is not None:
            self.save_document()
            self.start_session_callback(self.task_id)
            self.accept()

    def browse_artifact(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Artifact",
            str(self.root),
            "All files (*.*)",
        )
        if path:
            self.artifact_path.setText(path)
            if not self.artifact_label.text().strip():
                self.artifact_label.setText(Path(path).name)

    def browse_artifact_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Choose Artifact Folder",
            str(self.root),
        )
        if path:
            self.artifact_path.setText(path)
            if not self.artifact_label.text().strip():
                self.artifact_label.setText(Path(path).name)

    def add_artifact(self):
        try:
            workspace_service.add_artifact(
                self.conn,
                self.workspace_key,
                self.artifact_path.text(),
                self.artifact_label.text(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Link Artifact", str(exc))
            return
        self.artifact_label.clear()
        self.artifact_path.clear()
        self._refresh_artifacts()

    def _refresh_artifacts(self):
        self.artifact_list.clear()
        for row in workspace_service.artifacts(
            self.conn,
            self.workspace_key,
            root=self.root,
        ):
            label = row["label"] or Path(row["artifact_path"]).name
            automatic = (
                " • Automatic"
                if int(row["is_managed"] or 0)
                else ""
            )
            self.artifact_list.addItem(
                f"{label}{automatic}\n{row['artifact_path']}"
            )
            item = self.artifact_list.item(self.artifact_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
            item.setData(Qt.ItemDataRole.UserRole + 1, row["artifact_path"])
        if not self.artifact_list.count():
            self.artifact_list.addItem("No artifacts linked yet.")

    def open_artifact(self, *_args):
        item = self.artifact_list.currentItem()
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole + 1)
        if not path:
            return
        try:
            workspace_service.open_artifact(path, root=self.root)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Artifact", str(exc))

    def remove_artifact(self):
        item = self.artifact_list.currentItem()
        if item is None:
            return
        artifact_id = item.data(Qt.ItemDataRole.UserRole)
        if artifact_id is None:
            return
        try:
            workspace_service.remove_artifact(
                self.conn,
                int(artifact_id),
            )
        except Exception as exc:
            QMessageBox.information(
                self,
                "Automatic Artifact",
                str(exc),
            )
            return
        self._refresh_artifacts()

    def _refresh_sessions(self):
        self.session_list.clear()
        for row in workspace_service.sessions(self.conn, self.workspace_key):
            self.session_list.addItem(
                f"{row['session_date']} • {row['hours']:g}h • "
                f"Productivity {row['productivity_score'] or '-'}\n"
                f"{row['notes'] or 'No notes recorded.'}"
            )
            item = self.session_list.item(self.session_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
        if not self.session_list.count():
            self.session_list.addItem("No study sessions linked yet.")

    def link_recent_session(self):
        rows = workspace_service.recent_unlinked_sessions(self.conn, limit=1)
        if not rows:
            QMessageBox.information(
                self,
                "No Unlinked Sessions",
                "Every recent study session is already linked to a task.",
            )
            return
        workspace_service.link_session(
            self.conn,
            int(rows[0]["id"]),
            self.workspace_key,
        )
        self._refresh_sessions()
        if self.refresh_callback:
            self.refresh_callback()

    def unlink_session(self):
        item = self.session_list.currentItem()
        if item is None:
            return
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id is None:
            return
        workspace_service.unlink_session(self.conn, int(session_id))
        self._refresh_sessions()
        if self.refresh_callback:
            self.refresh_callback()

    def resizeEvent(self, event):  # noqa: N802 - Qt API
        super().resizeEvent(event)
        compact = self.width() < 780
        direction = (
            QBoxLayout.Direction.TopToBottom
            if compact
            else QBoxLayout.Direction.LeftToRight
        )
        for row in self._responsive_rows:
            row.setDirection(direction)
            row.setSpacing(7 if compact else 8)

    def closeEvent(self, event):
        if self._dirty:
            self.save_document()
        super().closeEvent(event)

    def accept(self):
        if self._dirty:
            self.save_document()
        super().accept()
