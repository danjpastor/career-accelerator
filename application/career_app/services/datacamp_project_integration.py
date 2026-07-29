from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from career_app.services import datacamp_projects

_INSTALLED = False


def _asset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "task_icons" / "datacamp_project.svg"


def _open_project(window: Any, project: dict[str, Any]) -> None:
    url = str(project.get("url") or "").strip()
    if not url:
        QMessageBox.warning(window, "Project Link Missing", "This DataCamp project does not have a configured web address.")
        return
    if not QDesktopServices.openUrl(QUrl(url)):
        QMessageBox.warning(
            window,
            "Could Not Open DataCamp",
            "Your web browser could not open the DataCamp project.\n\n"
            f"Copy this address instead:\n{url}",
        )


def _build_optional_panel(window: Any) -> QFrame:
    panel = QFrame()
    panel.setObjectName("OptionalPracticeCard")
    panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    panel.setStyleSheet(
        "QFrame#OptionalPracticeCard {"
        "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #182238,stop:1 #272047);"
        "border:1px solid #5D4D8C;border-radius:14px;}"
    )
    outer = QHBoxLayout(panel)
    outer.setContentsMargins(14, 12, 14, 12)
    outer.setSpacing(12)

    icon = QLabel()
    icon.setFixedSize(38, 38)
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    path = _asset_path()
    if path.is_file():
        icon.setPixmap(QIcon(str(path)).pixmap(32, 32))
    else:
        icon.setText("🧩")
    outer.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

    text_layout = QVBoxLayout()
    text_layout.setContentsMargins(0, 0, 0, 0)
    text_layout.setSpacing(3)
    eyebrow = QLabel("OPTIONAL PRACTICE")
    eyebrow.setObjectName("Tiny")
    title = QLabel("More DataCamp practice")
    title.setObjectName("SectionTitle")
    title.setWordWrap(True)
    detail = QLabel("Your second project recommendation will appear after you log 18 hours this week.")
    detail.setObjectName("Muted")
    detail.setWordWrap(True)
    text_layout.addWidget(eyebrow)
    text_layout.addWidget(title)
    text_layout.addWidget(detail)
    outer.addLayout(text_layout, 1)

    action = QPushButton("Open Project")
    action.setObjectName("Primary")
    action.setProperty("workspace_open_button", True)
    action.clicked.connect(lambda _checked=False: _open_optional_project(window))
    outer.addWidget(action, 0, Qt.AlignmentFlag.AlignVCenter)

    window.datacamp_optional_panel = panel
    window.datacamp_optional_title = title
    window.datacamp_optional_detail = detail
    window.datacamp_optional_button = action
    window.datacamp_optional_project = None
    panel.hide()
    return panel


def _find_view_all_button(root: Any) -> QPushButton | None:
    find_children = getattr(root, "findChildren", None)
    if not callable(find_children):
        return None
    for button in find_children(QPushButton):
        if str(button.text()).strip().casefold() == "view all tasks":
            return button
    return None


def _candidate_roots(window: Any, page: Any | None) -> list[Any]:
    roots: list[Any] = []
    for root in (page, window):
        if root is not None and root not in roots:
            roots.append(root)
    central_widget = getattr(window, "centralWidget", None)
    if callable(central_widget):
        try:
            root = central_widget()
        except Exception:
            root = None
        if root is not None and root not in roots:
            roots.append(root)
    return roots


def _insert_after_button(button: QPushButton, panel: QFrame) -> bool:
    """Insert below the row/card containing View All Tasks.

    Some application builds expose dashboard_page as a QWidget factory while newer
    builds retain dashboard layouts directly on the window. Walking up the widget
    tree supports both structures without ever treating a QLayout as a callable.
    """
    child: Any = button
    parent = button.parentWidget()
    while parent is not None:
        layout_getter = getattr(parent, "layout", None)
        layout = layout_getter() if callable(layout_getter) else None
        if layout is not None:
            index_of = getattr(layout, "indexOf", None)
            insert_widget = getattr(layout, "insertWidget", None)
            if callable(index_of) and callable(insert_widget):
                index = int(index_of(child))
                if index >= 0:
                    insert_widget(index + 1, panel)
                    return True
        child = parent
        parent = parent.parentWidget()
    return False


def _ensure_optional_panel(window: Any, page: Any | None = None) -> None:
    existing = getattr(window, "datacamp_optional_panel", None)
    if existing is not None:
        return

    button = None
    for root in _candidate_roots(window, page):
        button = _find_view_all_button(root)
        if button is not None:
            break
    if button is None:
        return

    panel = _build_optional_panel(window)
    if not _insert_after_button(button, panel):
        # The panel has no parent if no compatible widget layout was found. Clean
        # up the temporary references so a later dashboard refresh can retry.
        panel.deleteLater()
        for name in (
            "datacamp_optional_panel",
            "datacamp_optional_title",
            "datacamp_optional_detail",
            "datacamp_optional_button",
            "datacamp_optional_project",
        ):
            try:
                delattr(window, name)
            except AttributeError:
                pass


def _open_optional_project(window: Any) -> None:
    project = getattr(window, "datacamp_optional_project", None)
    if project:
        _open_project(window, project)


def _current_week(window: Any, week: int | None = None) -> int:
    if week is not None:
        return int(week)
    state = getattr(window, "state", None)
    if isinstance(state, dict):
        return int(state.get("current_week") or 1)
    try:
        return int(state["current_week"])
    except Exception:
        return 1


def _refresh_optional_panel(window: Any, week: int | None = None) -> None:
    panel = getattr(window, "datacamp_optional_panel", None)
    conn = getattr(window, "conn", None)
    if panel is None or conn is None:
        return
    project = datacamp_projects.optional_practice_recommendation(conn, _current_week(window, week))
    window.datacamp_optional_project = project
    if project is None:
        panel.hide()
        return
    hours = float(project.get("weekly_hours") or 18.0)
    window.datacamp_optional_title.setText(str(project["title"]))
    window.datacamp_optional_detail.setText(
        f"You have logged {hours:g} hours this week. Keep practicing with this optional "
        f"{project['tool']} project ({int(project['estimated_minutes'])} min)."
    )
    panel.show()


def _patch_task_workspace_support() -> None:
    try:
        from career_app.services import task_workspace
    except Exception:
        return
    original = getattr(task_workspace, "workspace_supported_task_id", None)
    if not callable(original) or getattr(original, "_datacamp_wrapped", False):
        return

    def wrapped(conn: Any, task_id: int, *args: Any, **kwargs: Any) -> bool:
        if datacamp_projects.project_for_task(conn, task_id) is not None:
            return True
        return bool(original(conn, task_id, *args, **kwargs))

    wrapped._datacamp_wrapped = True  # type: ignore[attr-defined]
    task_workspace.workspace_supported_task_id = wrapped


def _patch_track_presentations() -> None:
    try:
        from career_app.services import tracks
    except Exception:
        return

    original_source = getattr(tracks, "source_for_task", None)
    if callable(original_source) and not getattr(original_source, "_datacamp_wrapped", False):

        def source_for_task(conn: Any, task_id: int, *args: Any, **kwargs: Any) -> Any:
            source = datacamp_projects.source_for_task(conn, task_id)
            if source:
                return source
            return original_source(conn, task_id, *args, **kwargs)

        source_for_task._datacamp_wrapped = True  # type: ignore[attr-defined]
        tracks.source_for_task = source_for_task

    original_focus = getattr(tracks, "focus_presentation", None)
    if callable(original_focus) and not getattr(original_focus, "_datacamp_wrapped", False):

        def focus_presentation(conn: Any, item: dict[str, Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
            project = datacamp_projects.project_for_task(conn, item.get("task_id"))
            if project is None:
                return original_focus(conn, item, *args, **kwargs)
            return {
                "title": "DataCamp Project",
                "detail": f"{project['title']} • {int(project['estimated_minutes'])}m",
                "style_category": "Learning",
            }

        focus_presentation._datacamp_wrapped = True  # type: ignore[attr-defined]
        tracks.focus_presentation = focus_presentation


def _call_original_refresh(original: Any, instance: Any) -> None:
    if not callable(original):
        return
    try:
        parameters = inspect.signature(original).parameters
    except (TypeError, ValueError):
        parameters = {}
    if "sync_tracks" in parameters:
        original(instance, sync_tracks=False)
    else:
        original(instance)


def install(CareerAccelerator: type) -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    _patch_task_workspace_support()
    _patch_track_presentations()

    original_dashboard_page = getattr(CareerAccelerator, "dashboard_page", None)
    original_refresh_all = getattr(CareerAccelerator, "refresh_all", None)
    original_refresh_dashboard = getattr(CareerAccelerator, "refresh_dashboard", None)
    original_open_task_workspace = getattr(CareerAccelerator, "open_task_workspace", None)
    original_dashboard_task_source = getattr(CareerAccelerator, "dashboard_task_source", None)
    original_init = getattr(CareerAccelerator, "__init__", None)

    if callable(original_dashboard_page):

        def dashboard_page(self: Any, *args: Any, **kwargs: Any) -> Any:
            page = original_dashboard_page(self, *args, **kwargs)
            _ensure_optional_panel(self, page)
            return page

        CareerAccelerator.dashboard_page = dashboard_page

    if callable(original_refresh_all):

        def refresh_all(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                datacamp_projects.sync_tasks(self.conn, getattr(self, "state", None))
            except Exception as exc:
                setattr(self, "datacamp_project_sync_error", str(exc))
            result = original_refresh_all(self, *args, **kwargs)
            _ensure_optional_panel(self, self)
            return result

        CareerAccelerator.refresh_all = refresh_all

    if callable(original_refresh_dashboard):

        def refresh_dashboard(self: Any, *args: Any, **kwargs: Any) -> Any:
            result = original_refresh_dashboard(self, *args, **kwargs)
            _ensure_optional_panel(self, self)
            _refresh_optional_panel(self)
            return result

        CareerAccelerator.refresh_dashboard = refresh_dashboard

    if callable(original_open_task_workspace):

        def open_task_workspace(self: Any, *args: Any, **kwargs: Any) -> Any:
            task_id = kwargs.get("task_id")
            if task_id is None and args:
                task_id = args[0]
            project = datacamp_projects.project_for_task(self.conn, task_id)
            if project is not None:
                _open_project(self, project)
                return None
            return original_open_task_workspace(self, *args, **kwargs)

        CareerAccelerator.open_task_workspace = open_task_workspace

    if callable(original_dashboard_task_source):

        def dashboard_task_source(self: Any, row: Any, *args: Any, **kwargs: Any) -> str:
            try:
                source = datacamp_projects.source_for_task(self.conn, int(row["id"]))
            except Exception:
                source = None
            if source:
                return source
            return original_dashboard_task_source(self, row, *args, **kwargs)

        CareerAccelerator.dashboard_task_source = dashboard_task_source

    if callable(original_init):

        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            try:
                datacamp_projects.sync_tasks(self.conn, getattr(self, "state", None))
                _call_original_refresh(original_refresh_all, self)
                _ensure_optional_panel(self, self)
                _refresh_optional_panel(self)
            except Exception as exc:
                setattr(self, "datacamp_project_sync_error", str(exc))

        CareerAccelerator.__init__ = __init__

    _INSTALLED = True
