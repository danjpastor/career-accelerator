"""Native, file-preserving Jupyter notebook editor for milestone workspaces."""

from __future__ import annotations

import math
import queue
import re
from urllib.parse import quote
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.services import notebook_workspace
from career_app.ui.code_editor import EditorAssistMixin, detect_notebook_language
from career_app.ui.markdown_preview import render_markdown_html, raw_markdown_stylesheet


class NotebookKernelWorker(QThread):
    cell_started = Signal(int)
    cell_finished = Signal(int, object, object, str)
    kernel_status = Signal(str)

    def __init__(self, *, cwd: Path, kernel_name: str = "career-accelerator", parent=None):
        super().__init__(parent)
        self.cwd = Path(cwd)
        self.kernel_name = str(kernel_name or "career-accelerator")
        self.commands: queue.Queue = queue.Queue()
        self._stop_requested = False

    def execute_cell(self, index: int, source: str) -> None:
        self.commands.put((int(index), str(source)))

    def request_shutdown(self) -> None:
        self._stop_requested = True
        self.commands.put(None)

    def _start_kernel(self):
        try:
            from jupyter_client import KernelManager
        except ImportError as exc:
            raise RuntimeError(
                "The integrated notebook needs jupyter_client. Run the Career "
                "Accelerator launcher once while online to update requirements."
            ) from exc
        last_error = None
        for name in (self.kernel_name, "python3"):
            manager = None
            try:
                manager = KernelManager(kernel_name=name)
                manager.start_kernel(cwd=str(self.cwd))
                client = manager.blocking_client()
                client.start_channels()
                client.wait_for_ready(timeout=30)
                return manager, client
            except Exception as exc:
                last_error = exc
                if manager is not None:
                    try:
                        manager.shutdown_kernel(now=True)
                    except Exception:
                        pass
        raise RuntimeError(f"A Jupyter kernel could not be started: {last_error}")

    @staticmethod
    def _output_from_message(message: dict[str, Any]) -> dict[str, Any] | None:
        message_type = str(message.get("msg_type") or "")
        content = message.get("content") or {}
        if message_type == "stream":
            return {
                "output_type": "stream",
                "name": str(content.get("name") or "stdout"),
                "text": str(content.get("text") or ""),
            }
        if message_type in {"display_data", "execute_result"}:
            output = {
                "output_type": message_type,
                "data": content.get("data") or {},
                "metadata": content.get("metadata") or {},
            }
            if message_type == "execute_result":
                output["execution_count"] = content.get("execution_count")
            return output
        if message_type == "error":
            return {
                "output_type": "error",
                "ename": str(content.get("ename") or "Error"),
                "evalue": str(content.get("evalue") or ""),
                "traceback": list(content.get("traceback") or []),
            }
        return None

    def _preferred_database_path(self) -> Path | None:
        candidates = (
            self.cwd / "data" / "working" / "project.duckdb",
            self.cwd / "data" / "working" / "analytical.duckdb",
            self.cwd / "project.duckdb",
            self.cwd / "data" / "project.duckdb",
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        try:
            discovered = sorted(self.cwd.rglob("*.duckdb"))
        except OSError:
            discovered = []
        return discovered[0].resolve() if discovered else None

    @staticmethod
    def _duckdb_url(path: Path | None) -> str:
        if path is None:
            return "duckdb:///:memory:"
        value = path.resolve().as_posix()
        encoded = quote(value, safe="/:")
        if re.match(r"^[A-Za-z]:/", value):
            return "duckdb:///" + encoded
        return "duckdb:////" + encoded.lstrip("/")

    def _configure_kernel(self, client) -> dict[str, Any]:
        """Create a persistent DuckDB connection and notebook SQL helper."""
        database = self._preferred_database_path()
        database_value = str(database.resolve()) if database is not None else ":memory:"
        setup_code = f"""
_dca_kernel_setup_status = {{"sql_ready": False, "error": ""}}
try:
    import pandas as _dca_pandas
    _dca_pandas.set_option("display.max_rows", 25)
    _dca_pandas.set_option("display.min_rows", 10)
    _dca_pandas.set_option("display.max_columns", None)
    _dca_pandas.set_option("display.max_colwidth", 120)
    _dca_pandas.set_option("display.width", 160)
except Exception:
    _dca_pandas = None

try:
    import duckdb as _dca_duckdb
    from IPython.display import display as _dca_display

    _dca_duckdb_connection = _dca_duckdb.connect({database_value!r})

    def _dca_execute_sql(query):
        query = str(query or "").strip()
        if not query:
            raise ValueError("The SQL cell is empty.")
        cursor = _dca_duckdb_connection.execute(query)
        description = cursor.description
        if description is not None:
            frame = cursor.fetchdf()
            _dca_display(frame)
        else:
            print("Query completed successfully.")
        return None

    _dca_kernel_setup_status["sql_ready"] = True
except Exception as _dca_sql_error:
    _dca_kernel_setup_status["error"] = str(_dca_sql_error)

try:
    _dca_ipython = get_ipython()
    if _dca_ipython is not None:
        _dca_ipython.run_line_magic("load_ext", "sql")
        _dca_ipython.run_line_magic("config", "SqlMagic.displaylimit = 25")
        _dca_ipython.run_line_magic("config", "SqlMagic.autopandas = True")
        _dca_ipython.run_line_magic("config", "SqlMagic.feedback = 0")
except Exception:
    pass
""".strip()
        result = {
            "ready": False,
            "sql_ready": False,
            "database": database.name if database is not None else "memory",
            "error": "",
        }
        try:
            message_id = client.execute(
                setup_code,
                silent=False,
                store_history=False,
                allow_stdin=False,
                user_expressions={
                    "dca_setup": "repr(_dca_kernel_setup_status)",
                },
            )
            while True:
                message = client.get_iopub_msg(timeout=30)
                parent = message.get("parent_header") or {}
                if parent.get("msg_id") != message_id:
                    continue
                if (
                    message.get("msg_type") == "status"
                    and (message.get("content") or {}).get(
                        "execution_state"
                    ) == "idle"
                ):
                    break
            while True:
                reply = client.get_shell_msg(timeout=30)
                parent = reply.get("parent_header") or {}
                if parent.get("msg_id") == message_id:
                    break
            content = reply.get("content") or {}
            result["ready"] = content.get("status") == "ok"
            expression = (
                (content.get("user_expressions") or {})
                .get("dca_setup", {})
                .get("data", {})
                .get("text/plain", "")
            )
            if expression:
                import ast

                try:
                    parsed = ast.literal_eval(expression)
                    if isinstance(parsed, str):
                        parsed = ast.literal_eval(parsed)
                    if isinstance(parsed, dict):
                        result["sql_ready"] = bool(parsed.get("sql_ready"))
                        result["error"] = str(parsed.get("error") or "")
                except (ValueError, SyntaxError):
                    pass
            return result
        except Exception as exc:
            result["error"] = str(exc)
            return result

    def run(self) -> None:
        manager = None
        client = None
        execution_count = 0
        try:
            self.kernel_status.emit("Starting kernel…")
            manager, client = self._start_kernel()
            setup = self._configure_kernel(client)
            if setup.get("sql_ready"):
                self.kernel_status.emit(
                    "Kernel ready • SQL connected to "
                    f"{setup.get('database') or 'DuckDB'}"
                )
            elif setup.get("error"):
                self.kernel_status.emit(
                    "Kernel ready • SQL unavailable: "
                    f"{setup['error']}"
                )
            else:
                self.kernel_status.emit("Kernel ready")
            while not self._stop_requested:
                command = self.commands.get()
                if command is None:
                    break
                index, source = command
                self.cell_started.emit(index)
                outputs: list[dict[str, Any]] = []
                error_message = ""
                try:
                    message_id = client.execute(source, store_history=True, allow_stdin=False)
                    while True:
                        message = client.get_iopub_msg(timeout=120)
                        parent = message.get("parent_header") or {}
                        if parent.get("msg_id") != message_id:
                            continue
                        if message.get("msg_type") == "status" and (message.get("content") or {}).get("execution_state") == "idle":
                            break
                        output = self._output_from_message(message)
                        if output is not None:
                            outputs.append(output)
                    while True:
                        reply = client.get_shell_msg(timeout=30)
                        reply_parent = reply.get("parent_header") or {}
                        if reply_parent.get("msg_id") == message_id:
                            break
                    reply_content = reply.get("content") or {}
                    execution_count = int(reply_content.get("execution_count") or execution_count + 1)
                    if reply_content.get("status") == "error":
                        error_message = str(reply_content.get("evalue") or "Cell execution failed.")
                except Exception as exc:
                    error_message = str(exc)
                    outputs.append(
                        {
                            "output_type": "error",
                            "ename": type(exc).__name__,
                            "evalue": str(exc),
                            "traceback": [str(exc)],
                        }
                    )
                self.cell_finished.emit(index, outputs, execution_count, error_message)
        except Exception as exc:
            self.kernel_status.emit(str(exc))
        finally:
            if client is not None:
                try:
                    client.stop_channels()
                except Exception:
                    pass
            if manager is not None:
                try:
                    manager.shutdown_kernel(now=True)
                except Exception:
                    pass
            self.kernel_status.emit("Kernel stopped")




_DETACHED_NOTEBOOK_WORKERS: set[NotebookKernelWorker] = set()


def _release_detached_worker(worker: NotebookKernelWorker) -> None:
    """Release a kernel worker after an asynchronous workspace close."""
    _DETACHED_NOTEBOOK_WORKERS.discard(worker)
    worker.deleteLater()


class AutoHeightTextEdit(QTextEdit):
    """Notebook source editor that grows to show the complete cell."""

    def __init__(self, *, minimum_height: int = 90, parent=None):
        super().__init__(parent)
        self._minimum_content_height = max(
            1,
            int(minimum_height),
        )
        self.setMinimumHeight(self._minimum_content_height)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.document().contentsChanged.connect(
            self._schedule_height_update
        )
        QTimer.singleShot(0, self.refresh_height)

    def _schedule_height_update(self, *_args) -> None:
        QTimer.singleShot(0, self.refresh_height)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._schedule_height_update()

    def refresh_height(self) -> None:
        document_height = math.ceil(
            self.document().size().height()
        )
        margins = self.contentsMargins()
        desired = (
            document_height
            + (self.frameWidth() * 2)
            + margins.top()
            + margins.bottom()
            + 10
        )
        desired = max(
            self._minimum_content_height,
            desired,
        )
        if self.height() != desired:
            self.setFixedHeight(desired)




class NotebookSourceEditor(EditorAssistMixin, AutoHeightTextEdit):
    """Notebook editor with VS Code-style editing and contextual completion."""

    def __init__(
        self,
        *,
        minimum_height: int = 90,
        language: str = "python",
        project_dir: Path | None = None,
        parent=None,
    ):
        AutoHeightTextEdit.__init__(
            self,
            minimum_height=minimum_height,
            parent=parent,
        )
        self._init_editor_assist(
            language=language,
            project_dir=project_dir,
        )
        self.setToolTip(
            "VS Code-style editor: Ctrl+Space autocomplete, Ctrl+/ comments, "
            "Ctrl+K Ctrl+C / Ctrl+K Ctrl+U, paired quotes and brackets."
        )

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self.handle_editor_assist_key(event):
            return
        super().keyPressEvent(event)


class AutoHeightTextBrowser(QTextBrowser):
    """Notebook preview/output that grows to show the complete block."""

    double_clicked = Signal()

    def __init__(self, *, minimum_height: int = 40, parent=None):
        super().__init__(parent)
        self._minimum_content_height = max(
            1,
            int(minimum_height),
        )
        self.setMinimumHeight(self._minimum_content_height)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.document().contentsChanged.connect(
            self._schedule_height_update
        )
        QTimer.singleShot(0, self.refresh_height)

    def _schedule_height_update(self, *_args) -> None:
        QTimer.singleShot(0, self.refresh_height)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._schedule_height_update()

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit()
        event.accept()

    def refresh_height(self) -> None:
        document_height = math.ceil(
            self.document().size().height()
        )
        margins = self.contentsMargins()
        horizontal_height = (
            self.horizontalScrollBar().sizeHint().height()
            if self.horizontalScrollBar().isVisible()
            else 0
        )
        desired = (
            document_height
            + horizontal_height
            + (self.frameWidth() * 2)
            + margins.top()
            + margins.bottom()
            + 10
        )
        desired = max(
            self._minimum_content_height,
            desired,
        )
        if self.height() != desired:
            self.setFixedHeight(desired)


class NotebookCellWidget(QFrame):
    changed = Signal()
    run_requested = Signal(object)
    delete_requested = Signal(object)
    add_code_requested = Signal(object)
    add_sql_requested = Signal(object)
    add_markdown_requested = Signal(object)

    def __init__(
        self,
        cell: dict[str, Any],
        *,
        project_dir: Path | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.cell = cell
        self.project_dir = Path(project_dir) if project_dir is not None else None
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)

        toolbar = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.kind_label = QLabel()
        self.kind_label.setObjectName("SectionTitle")
        toolbar.addWidget(self.kind_label)
        toolbar.addStretch()

        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.toggle_preview)
        toolbar.addWidget(self.preview_button)

        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("Primary")
        self.run_button.clicked.connect(lambda: self.run_requested.emit(self))
        toolbar.addWidget(self.run_button)

        add_code = QPushButton("+ Python")
        add_code.clicked.connect(lambda: self.add_code_requested.emit(self))
        toolbar.addWidget(add_code)
        add_sql = QPushButton("+ SQL")
        add_sql.setToolTip("Add a JupySQL cell beginning with %%sql.")
        add_sql.clicked.connect(lambda: self.add_sql_requested.emit(self))
        toolbar.addWidget(add_sql)
        add_markdown = QPushButton("+ Markdown")
        add_markdown.clicked.connect(lambda: self.add_markdown_requested.emit(self))
        toolbar.addWidget(add_markdown)
        delete = QPushButton("Remove Cell")
        delete.clicked.connect(lambda: self.delete_requested.emit(self))
        toolbar.addWidget(delete)
        layout.addLayout(toolbar)

        source_text = notebook_workspace._source_text(cell)
        source_language = (
            "markdown"
            if str(cell.get("cell_type") or "code") == "markdown"
            else detect_notebook_language(source_text)
        )
        self.editor = NotebookSourceEditor(
            minimum_height=90,
            language=source_language,
            project_dir=self.project_dir,
        )
        self.editor.setStyleSheet(raw_markdown_stylesheet())
        self.editor.setAcceptRichText(False)
        self.editor.setPlainText(source_text)
        self.editor.textChanged.connect(self._editor_changed)
        layout.addWidget(self.editor)

        self.markdown_preview = AutoHeightTextBrowser(
            minimum_height=90
        )
        self.markdown_preview.setOpenExternalLinks(True)
        self.markdown_preview.double_clicked.connect(self.show_editor)
        self.markdown_preview.setVisible(False)
        layout.addWidget(self.markdown_preview)

        self.output = AutoHeightTextBrowser(
            minimum_height=40
        )
        self.output.setOpenExternalLinks(True)
        self.output.setStyleSheet(
            "QTextBrowser {background:#0B1324;color:#E5EDF8;"
            "border:1px solid #334155;border-radius:8px;padding:4px;}"
        )
        layout.addWidget(self.output)
        self.refresh_from_cell()

    @property
    def cell_type(self) -> str:
        return str(self.cell.get("cell_type") or "code")

    def _editor_changed(self) -> None:
        source = self.editor.toPlainText()
        notebook_workspace.set_source_text(self.cell, source)
        if self.cell_type == "markdown":
            self.editor.set_language("markdown")
            if self.markdown_preview.isVisible():
                self.markdown_preview.setHtml(render_markdown_html(source))
        else:
            self.editor.set_language(detect_notebook_language(source))
            execution = self.cell.get("execution_count")
            language_label = (
                "SQL"
                if self.editor.language() == "sql"
                else "Python"
            )
            self.kind_label.setText(
                f"{language_label} [{execution if execution is not None else ' '}]"
            )
        self.changed.emit()

    def refresh_from_cell(self) -> None:
        if self.cell_type == "markdown":
            self.kind_label.setText("Markdown")
            self.run_button.setVisible(True)
            self.run_button.setText("Render")
            self.preview_button.setVisible(True)
            self.output.setVisible(False)
            self.show_rendered()
        else:
            execution = self.cell.get("execution_count")
            language_label = (
                "SQL"
                if self.editor.language() == "sql"
                else "Python"
            )
            self.kind_label.setText(
                f"{language_label} [{execution if execution is not None else ' '}]"
            )
            self.run_button.setText("Run")
            self.run_button.setVisible(True)
            self.preview_button.setVisible(False)
            self.editor.setVisible(True)
            self.markdown_preview.setVisible(False)
            outputs = list(self.cell.get("outputs") or [])
            self.output.setHtml(notebook_workspace.outputs_html(outputs) or "<span style='color:#94A3B8'>No output yet.</span>")
            self.output.setVisible(True)
        QTimer.singleShot(0, self.refresh_heights)

    def refresh_heights(self) -> None:
        self.editor.refresh_height()
        self.markdown_preview.refresh_height()
        self.output.refresh_height()

    def show_rendered(self) -> None:
        if self.cell_type != "markdown":
            return
        self.markdown_preview.setHtml(render_markdown_html(self.editor.toPlainText()))
        self.markdown_preview.setVisible(True)
        self.editor.setVisible(False)
        self.preview_button.setText("Edit")
        QTimer.singleShot(0, self.refresh_heights)

    def show_editor(self) -> None:
        if self.cell_type != "markdown":
            return
        self.markdown_preview.setVisible(False)
        self.editor.setVisible(True)
        self.preview_button.setText("Render")
        self.editor.setFocus()
        QTimer.singleShot(0, self.refresh_heights)

    def toggle_preview(self) -> None:
        if self.markdown_preview.isVisible():
            self.show_editor()
        else:
            self.show_rendered()

    def set_running(self, running: bool) -> None:
        self.run_button.setEnabled(not running)
        if self.cell_type == "code":
            execution = self.cell.get("execution_count")
            language_label = (
                "SQL"
                if self.editor.language() == "sql"
                else "Python"
            )
            self.kind_label.setText(
                f"{language_label} [*]"
                if running
                else f"{language_label} [{execution if execution is not None else ' '}]"
            )


class IntegratedNotebookWidget(QWidget):
    saved = Signal(str)
    notebook_changed = Signal(str)

    def __init__(
        self,
        notebook_path: Path,
        *,
        project_dir: Path,
        completion_policy: str = "",
        notebook_paths: list[Path] | None = None,
        notebook_labels: dict[str, str] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        primary = Path(notebook_path)
        supplied = [Path(path) for path in (notebook_paths or [primary])]
        if primary not in supplied:
            supplied.insert(0, primary)
        self.notebook_paths: list[Path] = []
        for path in supplied:
            if path not in self.notebook_paths:
                self.notebook_paths.append(path)
        self.notebook_labels = dict(notebook_labels or {})
        self.notebook_path = primary
        self.project_dir = Path(project_dir)
        self.completion_policy = str(completion_policy or "")
        self.payload = notebook_workspace.load_notebook(self.notebook_path)
        self.cell_widgets: list[NotebookCellWidget] = []
        self._dirty = False
        self._switching_notebook = False
        self._running_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.notebook_selector = QComboBox()
        for path in self.notebook_paths:
            label = self.notebook_labels.get(str(path), self.notebook_labels.get(path.name, path.stem.replace("_", " ").title()))
            self.notebook_selector.addItem(label, str(path))
        self.notebook_selector.setVisible(len(self.notebook_paths) > 1)
        self.notebook_selector.currentIndexChanged.connect(self._switch_notebook)
        header.addWidget(self.notebook_selector)
        self.path_label = QLabel(str(self.notebook_path))
        self.path_label.setObjectName("Muted")
        self.path_label.setWordWrap(True)
        header.addWidget(self.path_label, 1)
        self.kernel_label = QLabel("Kernel not started")
        self.kernel_label.setObjectName("Muted")
        self.kernel_label.setWordWrap(False)
        self.kernel_label.setMaximumWidth(230)
        self.kernel_label.setToolTip("The notebook kernel has not started yet.")
        header.addWidget(self.kernel_label)
        save = QPushButton("Save Notebook")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_notebook)
        header.addWidget(save)
        run_all = QPushButton("Run All Cells")
        run_all.clicked.connect(self.run_all)
        header.addWidget(run_all)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.cells_layout = QVBoxLayout(self.container)
        self.cells_layout.setContentsMargins(4, 4, 4, 4)
        self.cells_layout.setSpacing(10)
        self.cells_layout.addStretch()
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self._kernel_name = str(
            (self.payload.get("metadata") or {})
            .get("kernelspec", {})
            .get("name")
            or "career-accelerator"
        )
        self.worker: NotebookKernelWorker | None = None

        self.autosave = QTimer(self)
        self.autosave.setSingleShot(True)
        self.autosave.setInterval(1200)
        self.autosave.timeout.connect(self.save_notebook)
        self.completion_context_timer = QTimer(self)
        self.completion_context_timer.setSingleShot(True)
        self.completion_context_timer.setInterval(90)
        self.completion_context_timer.timeout.connect(
            self._refresh_peer_completion_context
        )
        self._rebuild_cells()

    def _rebuild_cells(self) -> None:
        while self.cells_layout.count() > 1:
            item = self.cells_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.cell_widgets.clear()
        for cell in self.payload.get("cells", []):
            widget = NotebookCellWidget(cell, project_dir=self.project_dir)
            widget.changed.connect(self._changed)
            widget.run_requested.connect(self.run_cell)
            widget.delete_requested.connect(self.delete_cell)
            widget.add_code_requested.connect(
                lambda current, kind="code": self.add_cell_after(current, kind)
            )
            widget.add_sql_requested.connect(
                lambda current, kind="sql": self.add_cell_after(current, kind)
            )
            widget.add_markdown_requested.connect(
                lambda current, kind="markdown": self.add_cell_after(current, kind)
            )
            self.cells_layout.insertWidget(self.cells_layout.count() - 1, widget)
            self.cell_widgets.append(widget)
        self._refresh_peer_completion_context()

    def _refresh_peer_completion_context(self) -> None:
        combined = "\n\n".join(
            current.editor.toPlainText()
            for current in self.cell_widgets
            if current.cell_type == "code"
        )
        for current in self.cell_widgets:
            current.editor.set_peer_text(combined)

    def _changed(self) -> None:
        self._dirty = True
        self.autosave.start()
        self.completion_context_timer.start()

    def save_notebook(
        self,
        *_args,
        silent: bool = False,
    ) -> bool:
        try:
            notebook_workspace.save_notebook(
                self.notebook_path,
                self.payload,
            )
            self._dirty = False
            self.saved.emit(
                f"Notebook saved • {self.notebook_path.name}"
            )
            return True
        except Exception as exc:
            if not silent:
                QMessageBox.warning(
                    self,
                    "Could Not Save Notebook",
                    str(exc),
                )
            return False

    def _ensure_worker(self) -> NotebookKernelWorker:
        if self.worker is not None and self.worker.isRunning():
            return self.worker

        worker = NotebookKernelWorker(
            cwd=self.project_dir,
            kernel_name=self._kernel_name,
            parent=self,
        )
        worker.cell_started.connect(self._cell_started)
        worker.cell_finished.connect(self._cell_finished)
        worker.kernel_status.connect(self._set_kernel_status)
        self.worker = worker
        worker.start()
        return worker

    def _set_kernel_status(self, message: str) -> None:
        """Keep detailed kernel errors out of the compact notebook toolbar."""
        detail = notebook_workspace.strip_ansi(str(message or "")).strip()
        lowered = detail.casefold()
        if lowered.startswith("starting kernel"):
            label = "Starting kernel…"
        elif "sql connected" in lowered:
            label = "Kernel ready • SQL connected"
        elif "sql unavailable" in lowered:
            label = "Kernel ready • SQL issue"
        elif lowered.startswith("kernel ready"):
            label = "Kernel ready"
        elif lowered.startswith("kernel stopped"):
            label = "Kernel stopped"
        elif detail:
            label = "Kernel issue"
        else:
            label = "Kernel status unavailable"
        self.kernel_label.setText(label)
        self.kernel_label.setToolTip(detail or label)

    def _switch_notebook(self, index: int) -> None:
        if self._switching_notebook or index < 0:
            return
        if self._running_count:
            self._switching_notebook = True
            try:
                self.notebook_selector.setCurrentIndex(
                    self.notebook_paths.index(self.notebook_path)
                )
            finally:
                self._switching_notebook = False
            QMessageBox.information(
                self,
                "Notebook Is Running",
                "Wait for the current notebook cells to finish before switching files.",
            )
            return
        value = self.notebook_selector.itemData(index)
        if not value:
            return
        target = Path(str(value))
        if target == self.notebook_path:
            return
        self.autosave.stop()
        self.save_notebook()
        try:
            payload = notebook_workspace.load_notebook(target)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Notebook", str(exc))
            self._switching_notebook = True
            try:
                current = self.notebook_paths.index(self.notebook_path)
                self.notebook_selector.setCurrentIndex(current)
            finally:
                self._switching_notebook = False
            return
        self.notebook_path = target
        self.payload = payload
        self._dirty = False
        self.path_label.setText(str(target))
        self._rebuild_cells()
        self.notebook_changed.emit(str(target))
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(0))

    def select_notebook(self, value: str | Path) -> bool:
        requested = str(value or "").casefold()
        for index, path in enumerate(self.notebook_paths):
            label = str(self.notebook_selector.itemText(index)).casefold()
            if requested in {str(path).casefold(), path.name.casefold(), path.stem.casefold(), label} or requested == path.stem.replace("_cleaning", "").casefold():
                self.notebook_selector.setCurrentIndex(index)
                return True
        return False

    def prepare_notebook_replacement(self, target: Path) -> bool:
        """Persist active edits before an externally imported file replaces a slot."""
        if self._running_count:
            QMessageBox.information(
                self,
                "Notebook Is Running",
                "Wait for the current notebook cells to finish before importing a notebook.",
            )
            return False
        self.autosave.stop()
        if self._dirty and not self.save_notebook():
            return False
        return True

    def reload_notebook(self, target: Path) -> bool:
        """Reload a managed notebook after the file was replaced externally."""
        target = Path(target)
        if self._running_count:
            return False
        try:
            payload = notebook_workspace.load_notebook(target)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open Notebook", str(exc))
            return False

        if target not in self.notebook_paths:
            self.notebook_paths.append(target)
            label = self.notebook_labels.get(
                str(target),
                target.stem.replace("_", " ").title(),
            )
            self.notebook_selector.addItem(label, str(target))
            self.notebook_selector.setVisible(len(self.notebook_paths) > 1)

        index = self.notebook_paths.index(target)
        self._switching_notebook = True
        try:
            self.notebook_selector.setCurrentIndex(index)
        finally:
            self._switching_notebook = False

        self.notebook_path = target
        self.payload = payload
        self._dirty = False
        self.path_label.setText(str(target))
        self._kernel_name = str(
            (self.payload.get("metadata") or {})
            .get("kernelspec", {})
            .get("name")
            or "career-accelerator"
        )
        self._rebuild_cells()
        self.notebook_changed.emit(str(target))
        QTimer.singleShot(
            0,
            lambda: self.scroll.verticalScrollBar().setValue(0),
        )
        self.saved.emit(f"Imported notebook loaded • {target.name}")
        return True

    def run_cell(self, widget: NotebookCellWidget) -> None:
        if widget not in self.cell_widgets:
            return
        self.save_notebook()
        if widget.cell_type == "markdown":
            widget.show_rendered()
            QTimer.singleShot(0, lambda current=widget: self._scroll_to_cell_bottom(current))
            return
        index = self.cell_widgets.index(widget)
        execution_source = notebook_workspace.prepare_execution_source(
            widget.editor.toPlainText(),
            widget.editor.language(),
        )
        self._ensure_worker().execute_cell(
            index,
            execution_source,
        )

    def run_all(self) -> None:
        self.save_notebook()
        for index, widget in enumerate(self.cell_widgets):
            if widget.cell_type == "markdown":
                widget.show_rendered()
            else:
                execution_source = notebook_workspace.prepare_execution_source(
                    widget.editor.toPlainText(),
                    widget.editor.language(),
                )
                self._ensure_worker().execute_cell(
                    index,
                    execution_source,
                )

    def _cell_started(self, index: int) -> None:
        self._running_count += 1
        if 0 <= index < len(self.cell_widgets):
            self.cell_widgets[index].set_running(True)

    def _cell_finished(self, index: int, outputs, execution_count, error_message: str) -> None:
        self._running_count = max(0, self._running_count - 1)
        if not 0 <= index < len(self.cell_widgets):
            return
        widget = self.cell_widgets[index]
        widget.cell["outputs"] = list(outputs or [])
        widget.cell["execution_count"] = execution_count
        widget.set_running(False)
        widget.refresh_from_cell()
        self._changed()
        self.save_notebook()
        QTimer.singleShot(0, lambda current=widget: self._scroll_to_cell_bottom(current))

    def _scroll_to_cell_bottom(self, widget: NotebookCellWidget) -> None:
        if widget not in self.cell_widgets:
            return
        bottom = widget.mapTo(self.container, QPoint(0, widget.height())).y()
        bar = self.scroll.verticalScrollBar()
        target = max(0, bottom - self.scroll.viewport().height() + 20)
        bar.setValue(min(bar.maximum(), target))

    def add_cell_after(self, widget: NotebookCellWidget, kind: str) -> None:
        try:
            index = self.cell_widgets.index(widget) + 1
        except ValueError:
            index = len(self.cell_widgets)
        if kind == "markdown":
            cell = notebook_workspace.new_markdown_cell()
        elif kind == "sql":
            cell = notebook_workspace.new_code_cell("%%sql\n\n")
        else:
            cell = notebook_workspace.new_code_cell()
        self.payload.setdefault("cells", []).insert(index, cell)
        self._rebuild_cells()
        self._changed()
        if 0 <= index < len(self.cell_widgets):
            new_widget = self.cell_widgets[index]
            QTimer.singleShot(0, lambda current=new_widget: self._scroll_to_cell_bottom(current))

    def delete_cell(self, widget: NotebookCellWidget) -> None:
        if len(self.cell_widgets) <= 1:
            QMessageBox.information(self, "Keep One Cell", "A notebook must keep at least one cell.")
            return
        try:
            index = self.cell_widgets.index(widget)
        except ValueError:
            return
        self.payload["cells"].pop(index)
        self._rebuild_cells()
        self._changed()

    def prepare_for_completion(self) -> None:
        self.save_notebook()

    def completion_issues(self) -> list[str]:
        if self._dirty:
            self.save_notebook()
        issues: list[str] = []
        for path in self.notebook_paths:
            payload = self.payload if path == self.notebook_path else notebook_workspace.load_notebook(path)
            for issue in notebook_workspace.notebook_completion_issues(payload, self.completion_policy):
                prefix = path.stem.replace("_cleaning", "").replace("_", " ").title()
                issues.append(f"{prefix}: {issue}" if len(self.notebook_paths) > 1 else issue)
        return issues

    def shutdown(self) -> None:
        """Save and release the kernel without blocking the main window."""
        self.autosave.stop()
        self.completion_context_timer.stop()
        if self._dirty:
            self.save_notebook(silent=True)

        worker = self.worker
        self.worker = None
        if worker is None:
            return

        if not worker.isRunning():
            worker.deleteLater()
            return

        worker.setParent(None)
        _DETACHED_NOTEBOOK_WORKERS.add(worker)
        worker.finished.connect(
            lambda current=worker: _release_detached_worker(current)
        )
        worker.request_shutdown()

