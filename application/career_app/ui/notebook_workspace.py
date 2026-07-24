"""Native, file-preserving Jupyter notebook editor for milestone workspaces."""

from __future__ import annotations

import math
import queue
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

    @staticmethod
    def _configure_default_table_display(client) -> bool:
        """Set readable table defaults without limiting non-table output."""
        setup_code = """
try:
    import pandas as _dca_pandas
    _dca_pandas.set_option("display.max_rows", 10)
    _dca_pandas.set_option("display.min_rows", 10)
    _dca_pandas.set_option("display.max_columns", None)
    _dca_pandas.set_option("display.max_colwidth", None)
except Exception:
    pass

try:
    _dca_ipython = get_ipython()
    if _dca_ipython is not None:
        _dca_ipython.config.SqlMagic.displaylimit = 10
        try:
            _dca_ipython.run_line_magic(
                "config",
                "SqlMagic.displaylimit = 10",
            )
        except Exception:
            pass
except Exception:
    pass
""".strip()
        try:
            message_id = client.execute(
                setup_code,
                silent=True,
                store_history=False,
                allow_stdin=False,
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
            return (
                (reply.get("content") or {}).get("status")
                == "ok"
            )
        except Exception:
            return False

    def run(self) -> None:
        manager = None
        client = None
        execution_count = 0
        try:
            self.kernel_status.emit("Starting kernel…")
            manager, client = self._start_kernel()
            table_limit_ready = self._configure_default_table_display(client)
            if table_limit_ready:
                self.kernel_status.emit(
                    "Kernel ready • tables show up to 10 rows"
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




class NotebookSourceEditor(AutoHeightTextEdit):
    """Notebook code editor with VS Code-compatible line comments."""

    def __init__(
        self,
        *,
        minimum_height: int = 90,
        comment_prefix: str | None = "#",
        parent=None,
    ):
        super().__init__(
            minimum_height=minimum_height,
            parent=parent,
        )
        self.comment_prefix = (
            str(comment_prefix)
            if comment_prefix
            else None
        )
        self._comment_chord_active = False
        self._comment_chord_timer = QTimer(self)
        self._comment_chord_timer.setSingleShot(True)
        self._comment_chord_timer.setInterval(1600)
        self._comment_chord_timer.timeout.connect(
            self._clear_comment_chord
        )
        if self.comment_prefix:
            self.setToolTip(
                "VS Code line-comment shortcuts: Ctrl+/ toggles; "
                "Ctrl+K, Ctrl+C comments; Ctrl+K, Ctrl+U uncomments."
            )

    def _clear_comment_chord(self) -> None:
        self._comment_chord_active = False

    def _selected_block_numbers(self) -> tuple[int, int, bool]:
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        had_selection = cursor.hasSelection()

        if had_selection and end > start:
            end_block = self.document().findBlock(end)
            if end_block.isValid() and end == end_block.position():
                end -= 1

        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(max(start, end))
        return (
            max(0, start_block.blockNumber()),
            max(0, end_block.blockNumber()),
            had_selection,
        )

    def _line_comment_state(
        self,
        start_number: int,
        end_number: int,
    ) -> tuple[bool, bool]:
        any_content = False
        all_commented = True
        for number in range(start_number, end_number + 1):
            block = self.document().findBlockByNumber(number)
            if not block.isValid():
                continue
            text = block.text()
            stripped = text.lstrip(" \t")
            if not stripped:
                continue
            any_content = True
            if not stripped.startswith(self.comment_prefix):
                all_commented = False
        return any_content, all_commented

    def _apply_line_comments(self, action: str) -> None:
        if not self.comment_prefix:
            return

        current = self.textCursor()
        original_block_number = current.blockNumber()
        original_column = current.positionInBlock()
        start_number, end_number, had_selection = (
            self._selected_block_numbers()
        )

        any_content, all_commented = self._line_comment_state(
            start_number,
            end_number,
        )
        if action == "toggle":
            action = "uncomment" if any_content and all_commented else "comment"

        cursor_delta = 0
        editor = QTextCursor(self.document())
        editor.beginEditBlock()
        try:
            for number in range(end_number, start_number - 1, -1):
                block = self.document().findBlockByNumber(number)
                if not block.isValid():
                    continue
                line = block.text()
                indent = len(line) - len(line.lstrip(" \t"))
                stripped = line[indent:]
                position = block.position() + indent

                if action == "comment":
                    addition = self.comment_prefix + " "
                    editor.setPosition(position)
                    editor.insertText(addition)
                    if number == original_block_number:
                        cursor_delta += len(addition)
                elif action == "uncomment":
                    if stripped.startswith(self.comment_prefix + " "):
                        remove_count = len(self.comment_prefix) + 1
                    elif stripped.startswith(self.comment_prefix):
                        remove_count = len(self.comment_prefix)
                    else:
                        continue
                    editor.setPosition(position)
                    editor.setPosition(
                        position + remove_count,
                        QTextCursor.MoveMode.KeepAnchor,
                    )
                    editor.removeSelectedText()
                    if number == original_block_number:
                        cursor_delta -= remove_count
        finally:
            editor.endEditBlock()

        restored = QTextCursor(self.document())
        if had_selection:
            first = self.document().findBlockByNumber(start_number)
            last = self.document().findBlockByNumber(end_number)
            if first.isValid() and last.isValid():
                restored.setPosition(first.position())
                restored.setPosition(
                    last.position() + len(last.text()),
                    QTextCursor.MoveMode.KeepAnchor,
                )
        else:
            block = self.document().findBlockByNumber(
                original_block_number
            )
            if block.isValid():
                target_column = max(
                    0,
                    min(
                        len(block.text()),
                        original_column + cursor_delta,
                    ),
                )
                restored.setPosition(block.position() + target_column)
        self.setTextCursor(restored)

    def toggle_line_comments(self) -> None:
        self._apply_line_comments("toggle")

    def comment_selected_lines(self) -> None:
        self._apply_line_comments("comment")

    def uncomment_selected_lines(self) -> None:
        self._apply_line_comments("uncomment")

    def keyPressEvent(self, event) -> None:
        control = bool(
            event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        )

        if (
            self.comment_prefix
            and control
            and event.key() == Qt.Key.Key_Slash
        ):
            self._clear_comment_chord()
            self._comment_chord_timer.stop()
            self.toggle_line_comments()
            event.accept()
            return

        if (
            self.comment_prefix
            and control
            and event.key() == Qt.Key.Key_K
        ):
            self._comment_chord_active = True
            self._comment_chord_timer.start()
            event.accept()
            return

        if self.comment_prefix and self._comment_chord_active:
            self._clear_comment_chord()
            self._comment_chord_timer.stop()
            if control and event.key() == Qt.Key.Key_C:
                self.comment_selected_lines()
                event.accept()
                return
            if control and event.key() == Qt.Key.Key_U:
                self.uncomment_selected_lines()
                event.accept()
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
    add_markdown_requested = Signal(object)

    def __init__(self, cell: dict[str, Any], parent=None):
        super().__init__(parent)
        self.cell = cell
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

        add_code = QPushButton("+ Code")
        add_code.clicked.connect(lambda: self.add_code_requested.emit(self))
        toolbar.addWidget(add_code)
        add_markdown = QPushButton("+ Markdown")
        add_markdown.clicked.connect(lambda: self.add_markdown_requested.emit(self))
        toolbar.addWidget(add_markdown)
        delete = QPushButton("Remove Cell")
        delete.clicked.connect(lambda: self.delete_requested.emit(self))
        toolbar.addWidget(delete)
        layout.addLayout(toolbar)

        self.editor = NotebookSourceEditor(
            minimum_height=90,
            comment_prefix=(
                None
                if str(cell.get("cell_type") or "code") == "markdown"
                else "#"
            ),
        )
        self.editor.setStyleSheet(raw_markdown_stylesheet())
        self.editor.setAcceptRichText(False)
        self.editor.setPlainText(notebook_workspace._source_text(cell))
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
        layout.addWidget(self.output)
        self.refresh_from_cell()

    @property
    def cell_type(self) -> str:
        return str(self.cell.get("cell_type") or "code")

    def _editor_changed(self) -> None:
        notebook_workspace.set_source_text(self.cell, self.editor.toPlainText())
        if self.cell_type == "markdown" and self.markdown_preview.isVisible():
            self.markdown_preview.setHtml(render_markdown_html(self.editor.toPlainText()))
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
            self.kind_label.setText(f"Code [{execution if execution is not None else ' '}]")
            self.run_button.setText("Run")
            self.run_button.setVisible(True)
            self.preview_button.setVisible(False)
            self.editor.setVisible(True)
            self.markdown_preview.setVisible(False)
            outputs = list(self.cell.get("outputs") or [])
            self.output.setHtml(notebook_workspace.outputs_html(outputs) or "<span style='color:#888'>No output yet.</span>")
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
            self.kind_label.setText("Code [*]" if running else f"Code [{execution if execution is not None else ' '}]")


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
        self._rebuild_cells()

    def _rebuild_cells(self) -> None:
        while self.cells_layout.count() > 1:
            item = self.cells_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.cell_widgets.clear()
        for cell in self.payload.get("cells", []):
            widget = NotebookCellWidget(cell)
            widget.changed.connect(self._changed)
            widget.run_requested.connect(self.run_cell)
            widget.delete_requested.connect(self.delete_cell)
            widget.add_code_requested.connect(lambda current, kind="code": self.add_cell_after(current, kind))
            widget.add_markdown_requested.connect(lambda current, kind="markdown": self.add_cell_after(current, kind))
            self.cells_layout.insertWidget(self.cells_layout.count() - 1, widget)
            self.cell_widgets.append(widget)

    def _changed(self) -> None:
        self._dirty = True
        self.autosave.start()

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
        worker.kernel_status.connect(self.kernel_label.setText)
        self.worker = worker
        worker.start()
        return worker

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

    def run_cell(self, widget: NotebookCellWidget) -> None:
        if widget not in self.cell_widgets:
            return
        self.save_notebook()
        if widget.cell_type == "markdown":
            widget.show_rendered()
            QTimer.singleShot(0, lambda current=widget: self._scroll_to_cell_bottom(current))
            return
        index = self.cell_widgets.index(widget)
        self._ensure_worker().execute_cell(
            index,
            widget.editor.toPlainText(),
        )

    def run_all(self) -> None:
        self.save_notebook()
        for index, widget in enumerate(self.cell_widgets):
            if widget.cell_type == "markdown":
                widget.show_rendered()
            else:
                self._ensure_worker().execute_cell(
                    index,
                    widget.editor.toPlainText(),
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
        if error_message:
            self.kernel_label.setText(f"Cell finished with an error: {error_message}")

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
        cell = notebook_workspace.new_markdown_cell() if kind == "markdown" else notebook_workspace.new_code_cell()
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

