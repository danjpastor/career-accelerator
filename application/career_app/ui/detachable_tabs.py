"""Reusable detachable workspace tabs.

Tabs are moved between their original workspace and a lightweight top-level
window.  The existing widget instance is always reparented rather than copied,
so editor state, notebook kernels, outputs, forms, and scroll positions remain
intact.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import sys
import uuid

from PySide6.QtCore import QMimeData, QPoint, QRect, QSettings, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QDrag, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

_MIME_TYPE = "application/x-career-accelerator-workspace-tab"
_ACTIVE_DRAGS: dict[str, "_DragPayload"] = {}


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    return text or "tab"


def _settings_namespace(workspace_key: str) -> str:
    digest = hashlib.sha1(str(workspace_key).encode("utf-8")).hexdigest()[:16]
    return f"detachable-tabs/{digest}"


def _windows_guid(value: str, guid_type=None):
    """Create a ctypes GUID without importing Windows-only modules elsewhere."""
    import ctypes
    import uuid as uuid_module

    parsed = uuid_module.UUID(value)

    if guid_type is None:
        class GUID(ctypes.Structure):
            _fields_ = (
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8),
            )
        guid_type = GUID

    return guid_type(
        parsed.time_low,
        parsed.time_mid,
        parsed.time_hi_version,
        (ctypes.c_ubyte * 8)(*parsed.bytes[8:]),
    ), guid_type


def _set_windows_app_user_model_id(hwnd: int, app_id: str) -> None:
    """Assign a per-window taskbar group so detached tabs stay separate."""
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    iid_store, guid_type = _windows_guid(
        "886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"
    )
    app_id_guid, _ = _windows_guid(
        "9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3",
        guid_type,
    )

    class PROPERTYKEY(ctypes.Structure):
        _fields_ = (("fmtid", guid_type), ("pid", wintypes.DWORD))

    class _PROPVARIANT_VALUE(ctypes.Union):
        _fields_ = (("pwszVal", wintypes.LPWSTR), ("pointer", ctypes.c_void_p))

    class PROPVARIANT(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (
            ("vt", ctypes.c_ushort),
            ("reserved1", ctypes.c_ushort),
            ("reserved2", ctypes.c_ushort),
            ("reserved3", ctypes.c_ushort),
            ("value", _PROPVARIANT_VALUE),
        )

    class IPropertyStore(ctypes.Structure):
        pass

    query_interface = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.POINTER(IPropertyStore),
        ctypes.POINTER(guid_type),
        ctypes.POINTER(ctypes.c_void_p),
    )
    add_ref = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(IPropertyStore))
    release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(IPropertyStore))
    get_count = ctypes.WINFUNCTYPE(
        ctypes.c_long, ctypes.POINTER(IPropertyStore), ctypes.POINTER(wintypes.DWORD)
    )
    get_at = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.POINTER(IPropertyStore),
        wintypes.DWORD,
        ctypes.POINTER(PROPERTYKEY),
    )
    get_value = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.POINTER(IPropertyStore),
        ctypes.POINTER(PROPERTYKEY),
        ctypes.POINTER(PROPVARIANT),
    )
    set_value = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.POINTER(IPropertyStore),
        ctypes.POINTER(PROPERTYKEY),
        ctypes.POINTER(PROPVARIANT),
    )
    commit = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.POINTER(IPropertyStore))

    class IPropertyStoreVTable(ctypes.Structure):
        _fields_ = (
            ("QueryInterface", query_interface),
            ("AddRef", add_ref),
            ("Release", release),
            ("GetCount", get_count),
            ("GetAt", get_at),
            ("GetValue", get_value),
            ("SetValue", set_value),
            ("Commit", commit),
        )

    IPropertyStore._fields_ = (("lpVtbl", ctypes.POINTER(IPropertyStoreVTable)),)

    shell32 = ctypes.windll.shell32
    function = shell32.SHGetPropertyStoreForWindow
    function.argtypes = (
        wintypes.HWND,
        ctypes.POINTER(guid_type),
        ctypes.POINTER(ctypes.POINTER(IPropertyStore)),
    )
    function.restype = ctypes.c_long

    store = ctypes.POINTER(IPropertyStore)()
    result = function(
        wintypes.HWND(hwnd),
        ctypes.byref(iid_store),
        ctypes.byref(store),
    )
    if result < 0 or not store:
        return

    value_buffer = ctypes.c_wchar_p(str(app_id)[:128])
    value = PROPVARIANT()
    value.vt = 31  # VT_LPWSTR
    value.pwszVal = value_buffer
    key = PROPERTYKEY(app_id_guid, 5)  # PKEY_AppUserModel_ID
    try:
        if store.contents.lpVtbl.contents.SetValue(
            store, ctypes.byref(key), ctypes.byref(value)
        ) >= 0:
            store.contents.lpVtbl.contents.Commit(store)
    finally:
        store.contents.lpVtbl.contents.Release(store)


def _force_windows_taskbar_entry(
    window: QWidget,
    app_user_model_id: str = "",
) -> None:
    """Show a detached tab as an independent Windows taskbar/Alt-Tab item."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(window.winId())
        user32 = ctypes.windll.user32
        get_style = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        set_style = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        gwl_exstyle = -20
        ws_ex_appwindow = 0x00040000
        ws_ex_toolwindow = 0x00000080
        style = int(get_style(hwnd, gwl_exstyle))
        style = (style | ws_ex_appwindow) & ~ws_ex_toolwindow
        set_style(hwnd, gwl_exstyle, style)
        if app_user_model_id:
            _set_windows_app_user_model_id(hwnd, app_user_model_id)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020,
        )
    except Exception:
        # The tab still functions as a normal top-level Qt window when the
        # platform taskbar properties cannot be changed.
        return


@dataclass
class _TabRecord:
    tab_id: str
    widget: QWidget
    title: str
    icon: QIcon
    tool_tip: str
    whats_this: str
    enabled: bool
    original_index: int


@dataclass
class _DragPayload:
    source_tabs: "DetachableTabWidget"
    home_tabs: "DetachableTabWidget"
    record: _TabRecord


class _TabDragPreview(QFrame):
    """Non-interactive floating preview shown while a tab leaves its workspace."""

    def __init__(self, record: _TabRecord, owner_window=None):
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowOpacity(0.88)
        self.setObjectName("DetachedTabDragPreview")
        self.setStyleSheet(
            "QFrame#DetachedTabDragPreview {background:#101A2C;"
            "border:2px solid #8A5CFF;border-radius:10px;}"
            "QLabel {color:#F3F6FF;background:transparent;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        title = QLabel(record.title)
        title.setStyleSheet("font-size:11pt;font-weight:700;")
        layout.addWidget(title)
        detail = QLabel("Release to open this tab in its own window")
        detail.setStyleSheet("color:#B8C4D8;")
        layout.addWidget(detail)
        if owner_window is not None:
            size = owner_window.size()
            self.resize(
                max(460, int(size.width() * 0.56)),
                max(280, int(size.height() * 0.52)),
            )
        else:
            self.resize(720, 440)

    def follow_cursor(self, cursor: QPoint) -> None:
        self.move(cursor - QPoint(70, 20))


class DetachableTabBar(QTabBar):
    """Tab bar that supports process-local drag, drop, and external detach."""

    def __init__(self, tabs: "DetachableTabWidget"):
        super().__init__(tabs)
        self._tabs = tabs
        self._press_pos = QPoint()
        self._press_index = -1
        self.setAcceptDrops(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setUsesScrollButtons(True)

    def mousePressEvent(self, event):  # noqa: N802 - Qt API
        self._press_pos = event.position().toPoint()
        self._press_index = self.tabAt(self._press_pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802 - Qt API
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return
        if self._press_index < 0:
            super().mouseMoveEvent(event)
            return
        if (
            event.position().toPoint() - self._press_pos
        ).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        index = self._press_index
        self._press_index = -1
        widget = self._tabs.widget(index)
        if widget is None:
            return
        record = self._tabs.record_for_widget(widget)
        if record is None:
            return

        token = uuid.uuid4().hex
        payload = _DragPayload(
            source_tabs=self._tabs,
            home_tabs=self._tabs.home_tabs,
            record=record,
        )
        _ACTIVE_DRAGS[token] = payload

        mime = QMimeData()
        mime.setData(_MIME_TYPE, token.encode("ascii"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        rect = self.tabRect(index)
        pixmap = self.grab(rect)
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint() - rect.topLeft())

        owner = self._tabs.owner_window
        owner_rect = (
            QRect(owner.mapToGlobal(QPoint(0, 0)), owner.size())
            if owner is not None
            else QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
        )
        preview = _TabDragPreview(record, owner)
        preview_timer = QTimer(self)
        preview_timer.setInterval(16)

        def update_preview():
            cursor = QCursor.pos()
            if owner_rect.contains(cursor):
                preview.hide()
                return
            preview.follow_cursor(cursor)
            if not preview.isVisible():
                preview.show()

        preview_timer.timeout.connect(update_preview)
        preview_timer.start()
        update_preview()
        result = drag.exec(Qt.DropAction.MoveAction)
        preview_timer.stop()
        cursor = QCursor.pos()
        preview_was_visible = preview.isVisible()
        preview_position = preview.pos()
        preview.close()
        preview.deleteLater()
        _ACTIVE_DRAGS.pop(token, None)

        if (
            result != Qt.DropAction.MoveAction
            and not owner_rect.contains(cursor)
        ):
            self._tabs.detach_widget(
                widget,
                preview_position if preview_was_visible else cursor,
                position_is_window_origin=preview_was_visible,
            )

    def dragEnterEvent(self, event):  # noqa: N802 - Qt API
        payload = self._payload(event.mimeData())
        if payload is not None and self._tabs.can_accept(payload):
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def dragMoveEvent(self, event):  # noqa: N802 - Qt API
        payload = self._payload(event.mimeData())
        if payload is not None and self._tabs.can_accept(payload):
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def dropEvent(self, event):  # noqa: N802 - Qt API
        payload = self._payload(event.mimeData())
        if payload is None or not self._tabs.can_accept(payload):
            event.ignore()
            return
        index = self._drop_index(event.position().toPoint())
        self._tabs.accept_drag(payload, index)
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def _drop_index(self, position: QPoint) -> int:
        index = self.tabAt(position)
        if index < 0:
            return self.count()
        rect = self.tabRect(index)
        if position.x() > rect.center().x():
            return index + 1
        return index

    @staticmethod
    def _payload(mime: QMimeData) -> _DragPayload | None:
        if not mime.hasFormat(_MIME_TYPE):
            return None
        try:
            token = bytes(mime.data(_MIME_TYPE)).decode("ascii")
        except Exception:
            return None
        return _ACTIVE_DRAGS.get(token)


class DetachedTabWindow(QMainWindow):
    """Top-level host for one moved workspace tab."""

    def __init__(
        self,
        *,
        home_tabs: "DetachableTabWidget",
        record: _TabRecord,
        position: QPoint | None = None,
        geometry=None,
        position_is_window_origin: bool = False,
    ):
        owner = home_tabs.owner_window
        # Keep the workspace ownership so detached tabs remain interactive
        # while the task dialog is modal.  A Windows native style is applied
        # after show so the detached tab still receives its own taskbar entry.
        super().__init__(owner, Qt.WindowType.Window)
        self._workspace_owner = owner
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setProperty("detachedWorkspaceWindow", True)
        self.home_tabs = home_tabs
        self.record = record
        taskbar_digest = hashlib.sha1(
            f"{home_tabs.workspace_key}:{record.tab_id}".encode("utf-8")
        ).hexdigest()[:20]
        self._windows_app_user_model_id = (
            "CareerAccelerator.Detached." + taskbar_digest
        )
        self._suppress_return = False
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(record.title)
        self.setMinimumSize(640, 420)
        if owner is not None:
            self.setWindowIcon(owner.windowIcon())
            self.setStyleSheet(owner.styleSheet())

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        controls = QHBoxLayout()
        title = QLabel(record.title)
        title.setObjectName("SectionTitle")
        title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        controls.addWidget(title, 1)
        return_button = QPushButton("Return to Workspace")
        return_button.setObjectName("Ghost")
        return_button.clicked.connect(self.return_to_workspace)
        controls.addWidget(return_button)
        layout.addLayout(controls)

        self.host_tabs = DetachableTabWidget(
            self,
            workspace_key=home_tabs.workspace_key,
            group_id=home_tabs.group_id,
            owner_window=owner,
            home_tabs=home_tabs,
            detached_host=True,
        )
        self.host_tabs._detached_window = self
        self.host_tabs._insert_record(record, 0)
        layout.addWidget(self.host_tabs, 1)
        self.setCentralWidget(central)

        if geometry is not None and self.restoreGeometry(geometry):
            self._ensure_visible()
        else:
            owner_size = owner.size() if owner is not None else None
            width = max(720, int(owner_size.width() * 0.74)) if owner_size else 900
            height = max(520, int(owner_size.height() * 0.74)) if owner_size else 650
            self.resize(width, height)
            if position is not None:
                self.move(
                    position
                    if position_is_window_origin
                    else position - QPoint(60, 24)
                )

        # Creating the native handle before show allows Windows Explorer to
        # assign a unique taskbar group before the window first appears.
        _force_windows_taskbar_entry(
            self,
            self._windows_app_user_model_id,
        )

    def showEvent(self, event):  # noqa: N802 - Qt API
        super().showEvent(event)
        QTimer.singleShot(
            0,
            lambda: _force_windows_taskbar_entry(
                self,
                self._windows_app_user_model_id,
            ),
        )

    def return_to_workspace(self):
        if self.host_tabs.indexOf(self.record.widget) >= 0:
            self.host_tabs._remove_record_widget(self.record)
            self.home_tabs._insert_record(
                self.record,
                self.home_tabs._home_insert_index(self.record.tab_id),
            )
            self.home_tabs.setCurrentWidget(self.record.widget)
        self.home_tabs.mark_attached(self.record.tab_id)
        self._suppress_return = True
        self.close()

    def collect_for_workspace_close(self):
        """Reparent the widget home while preserving detached-state settings."""
        self.home_tabs.save_detached_geometry(self.record.tab_id, self.saveGeometry())
        if self.host_tabs.indexOf(self.record.widget) >= 0:
            self.host_tabs._remove_record_widget(self.record)
            self.home_tabs._insert_record(
                self.record,
                self.home_tabs._home_insert_index(self.record.tab_id),
            )
        self._suppress_return = True
        self.close()

    def closeEvent(self, event):  # noqa: N802 - Qt API
        self.home_tabs.save_detached_geometry(self.record.tab_id, self.saveGeometry())
        if not self._suppress_return:
            if self.host_tabs.indexOf(self.record.widget) >= 0:
                self.host_tabs._remove_record_widget(self.record)
                self.home_tabs._insert_record(
                    self.record,
                    self.home_tabs._home_insert_index(self.record.tab_id),
                )
                self.home_tabs.setCurrentWidget(self.record.widget)
            self.home_tabs.mark_attached(self.record.tab_id)
        self.home_tabs._detached_window_closed(self.record.tab_id)
        super().closeEvent(event)

    def _ensure_visible(self):
        frame = self.frameGeometry()
        if any(frame.intersects(screen.availableGeometry()) for screen in QApplication.screens()):
            return
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(available.center() - self.rect().center())


class DetachableTabWidget(QTabWidget):
    """QTabWidget with detachable, reorderable, restorable tab instances."""

    tabDetached = Signal(str)
    tabAttached = Signal(str)

    def __init__(
        self,
        parent=None,
        *,
        workspace_key: str,
        group_id: str | None = None,
        owner_window=None,
        home_tabs: "DetachableTabWidget | None" = None,
        detached_host: bool = False,
    ):
        super().__init__(parent)
        self.workspace_key = str(workspace_key)
        self.group_id = str(group_id or workspace_key)
        self.owner_window = owner_window or parent
        self._home_tabs = home_tabs or self
        self._detached_host = bool(detached_host)
        self._detached_window: DetachedTabWindow | None = None
        self._records: dict[str, _TabRecord] = {} if home_tabs is None else home_tabs._records
        self._tab_order: list[str] = [] if home_tabs is None else home_tabs._tab_order
        self._detached_windows: dict[str, DetachedTabWindow] = (
            {} if home_tabs is None else home_tabs._detached_windows
        )
        self._settings = QSettings("CareerAccelerator", "CareerAccelerator")
        self._settings_root = _settings_namespace(self.workspace_key)
        self._layout_restored = False if home_tabs is None else home_tabs._layout_restored

        self.setTabBar(DetachableTabBar(self))
        self.tabBar().setToolTip(
            "Drag a tab outside the workspace to open it in its own window. "
            "Drag it back here or close the detached window to return it."
        )
        self.setTabsClosable(False)
        self.setTabBarAutoHide(False)
        self.setDocumentMode(False)
        self.tabBarDoubleClicked.connect(self._double_click_detach)

    @property
    def home_tabs(self) -> "DetachableTabWidget":
        return self._home_tabs

    def addTab(self, widget, *args):  # noqa: N802 - Qt API
        index = super().addTab(widget, *args)
        self._register_widget(widget, index)
        return index

    def insertTab(self, index, widget, *args):  # noqa: N802 - Qt API
        index = super().insertTab(index, widget, *args)
        self._register_widget(widget, index)
        return index

    def _register_widget(self, widget: QWidget, index: int):
        home = self.home_tabs
        existing_id = widget.property("detachableTabId")
        title = self.tabText(index)
        tab_id = str(existing_id or _slug(title))
        candidate = tab_id
        suffix = 2
        while candidate in home._records and home._records[candidate].widget is not widget:
            candidate = f"{tab_id}-{suffix}"
            suffix += 1
        tab_id = candidate
        widget.setProperty("detachableTabId", tab_id)
        if tab_id in home._records:
            return
        home._records[tab_id] = _TabRecord(
            tab_id=tab_id,
            widget=widget,
            title=title,
            icon=self.tabIcon(index),
            tool_tip=self.tabToolTip(index),
            whats_this=self.tabWhatsThis(index),
            enabled=self.isTabEnabled(index),
            original_index=index,
        )
        home._insert_new_tab_order(tab_id, index)

    def _visible_tab_ids(self) -> list[str]:
        ids = []
        for index in range(self.count()):
            widget = self.widget(index)
            if widget is None:
                continue
            tab_id = widget.property("detachableTabId")
            if tab_id:
                ids.append(str(tab_id))
        return ids

    def _insert_new_tab_order(self, tab_id: str, visible_index: int):
        home = self.home_tabs
        if tab_id in home._tab_order:
            return
        visible = home._visible_tab_ids()
        next_ids = visible[visible_index + 1 :]
        for next_id in next_ids:
            if next_id in home._tab_order:
                home._tab_order.insert(home._tab_order.index(next_id), tab_id)
                if home._layout_restored:
                    home._persist_tab_order()
                return
        home._tab_order.append(tab_id)
        if home._layout_restored:
            home._persist_tab_order()

    def _persist_tab_order(self):
        home = self.home_tabs
        home._settings.setValue(
            f"{home._settings_root}/order",
            list(home._tab_order),
        )
        home._settings.sync()

    def _stored_tab_order(self) -> list[str]:
        home = self.home_tabs
        stored = home._settings.value(
            f"{home._settings_root}/order",
            [],
        )
        if stored is None:
            return []
        if isinstance(stored, str):
            return [stored]
        try:
            return [str(value) for value in stored]
        except TypeError:
            return []

    def _restore_tab_order(self):
        home = self.home_tabs
        stored = home._stored_tab_order()
        desired = [tab_id for tab_id in stored if tab_id in home._records]
        desired.extend(
            tab_id
            for tab_id in home._tab_order
            if tab_id not in desired
        )
        home._tab_order[:] = desired

        current_widget = home.currentWidget()
        visible_desired = [
            tab_id
            for tab_id in desired
            if home.indexOf(home._records[tab_id].widget) >= 0
        ]
        for target_index, tab_id in enumerate(visible_desired):
            record = home._records[tab_id]
            current_index = home.indexOf(record.widget)
            if current_index < 0 or current_index == target_index:
                continue
            home._remove_record_widget(record)
            home._insert_record(record, target_index)
        if current_widget is not None and home.indexOf(current_widget) >= 0:
            home.setCurrentWidget(current_widget)
        home._layout_restored = True
        home._persist_tab_order()

    def _sync_tab_order_from_visible(self):
        home = self.home_tabs
        visible = home._visible_tab_ids()
        if not visible:
            return
        visible_set = set(visible)
        iterator = iter(visible)
        updated = []
        for tab_id in home._tab_order:
            if tab_id in visible_set:
                updated.append(next(iterator))
            else:
                updated.append(tab_id)
        for tab_id in iterator:
            updated.append(tab_id)
        home._tab_order[:] = updated
        if home._layout_restored:
            home._persist_tab_order()

    def _home_insert_index(self, tab_id: str) -> int:
        home = self.home_tabs
        try:
            order_index = home._tab_order.index(str(tab_id))
        except ValueError:
            return home.count()
        prior = set(home._tab_order[:order_index])
        return sum(
            1
            for visible_id in home._visible_tab_ids()
            if visible_id in prior
        )

    def record_for_widget(self, widget: QWidget) -> _TabRecord | None:
        tab_id = widget.property("detachableTabId")
        if not tab_id:
            return None
        return self.home_tabs._records.get(str(tab_id))

    def can_accept(self, payload: _DragPayload) -> bool:
        if payload.home_tabs.group_id != self.home_tabs.group_id:
            return False
        if self._detached_host and payload.source_tabs is not self:
            return False
        return True

    def accept_drag(self, payload: _DragPayload, insert_index: int):
        record = payload.record
        source = payload.source_tabs
        current = source.indexOf(record.widget)
        if current < 0:
            return

        if source is self:
            source._remove_record_widget(record)
            if insert_index > current:
                insert_index -= 1
            inserted = self._insert_record(
                record,
                min(insert_index, self.count()),
            )
            if self is self.home_tabs:
                record.original_index = inserted
                self._sync_tab_order_from_visible()
            self.setCurrentWidget(record.widget)
            return

        source._remove_record_widget(record)
        inserted = self._insert_record(
            record,
            min(insert_index, self.count()),
        )
        self.setCurrentWidget(record.widget)

        if self is payload.home_tabs:
            record.original_index = inserted
            payload.home_tabs._sync_tab_order_from_visible()
            payload.home_tabs.mark_attached(record.tab_id)
        elif not self._detached_host:
            # A tab can only persist as detached relative to its original home.
            payload.home_tabs.mark_detached(record.tab_id)

        source._after_widget_transferred(record)

    def detach_widget(
        self,
        widget: QWidget,
        position: QPoint | None = None,
        *,
        position_is_window_origin: bool = False,
    ):
        if self._detached_host:
            return
        index = self.indexOf(widget)
        if index < 0:
            return
        record = self.record_for_widget(widget)
        if record is None:
            return
        record.original_index = index
        record.title = self.tabText(index)
        record.icon = self.tabIcon(index)
        record.tool_tip = self.tabToolTip(index)
        record.whats_this = self.tabWhatsThis(index)
        record.enabled = self.isTabEnabled(index)
        self._remove_record_widget(record)

        # A manual drag uses the current drop location.  Stored geometry is
        # used only when restoring a previously detached layout.
        geometry = (
            None
            if position is not None
            else self.detached_geometry(record.tab_id)
        )
        window = DetachedTabWindow(
            home_tabs=self.home_tabs,
            record=record,
            position=position,
            geometry=geometry,
            position_is_window_origin=position_is_window_origin,
        )
        self.home_tabs._detached_windows[record.tab_id] = window
        self.home_tabs.mark_detached(record.tab_id)
        window.show()
        window.raise_()
        window.activateWindow()
        self.home_tabs.tabDetached.emit(record.tab_id)

    def _double_click_detach(self, index: int):
        if index < 0 or self._detached_host:
            return
        widget = self.widget(index)
        if widget is not None:
            self.detach_widget(widget, QCursor.pos())

    def _remove_record_widget(self, record: _TabRecord):
        index = self.indexOf(record.widget)
        if index >= 0:
            super().removeTab(index)

    def _insert_record(self, record: _TabRecord, index: int):
        index = max(0, min(index, self.count()))
        if not record.icon.isNull():
            inserted = super().insertTab(index, record.widget, record.icon, record.title)
        else:
            inserted = super().insertTab(index, record.widget, record.title)
        self.setTabToolTip(inserted, record.tool_tip)
        self.setTabWhatsThis(inserted, record.whats_this)
        self.setTabEnabled(inserted, record.enabled)
        return inserted

    def _after_widget_transferred(self, record: _TabRecord):
        if not self._detached_host or self._detached_window is None:
            return
        self._detached_window._suppress_return = True
        self._detached_window.close()

    def _detached_window_closed(self, tab_id: str):
        self.home_tabs._detached_windows.pop(str(tab_id), None)

    def mark_detached(self, tab_id: str):
        self._settings.setValue(
            f"{self._settings_root}/{tab_id}/detached",
            True,
        )
        self._settings.sync()

    def mark_attached(self, tab_id: str):
        self._settings.setValue(
            f"{self._settings_root}/{tab_id}/detached",
            False,
        )
        self._settings.sync()
        self.tabAttached.emit(str(tab_id))

    def save_detached_geometry(self, tab_id: str, geometry):
        self._settings.setValue(
            f"{self._settings_root}/{tab_id}/geometry",
            geometry,
        )
        self._settings.sync()

    def detached_geometry(self, tab_id: str):
        return self._settings.value(
            f"{self._settings_root}/{tab_id}/geometry",
            None,
        )

    def restore_detached_tabs(self):
        if self._detached_host:
            return
        self._restore_tab_order()
        for tab_id in list(self._tab_order):
            record = self._records.get(tab_id)
            if record is None:
                continue
            value = self._settings.value(
                f"{self._settings_root}/{record.tab_id}/detached",
                False,
                type=bool,
            )
            if not value:
                continue
            if self.indexOf(record.widget) < 0:
                continue
            self.detach_widget(record.widget)

    def prepare_workspace_close(self):
        """Collect detached widgets without losing the saved detached layout."""
        if self._detached_host:
            return
        for window in list(self._detached_windows.values()):
            window.collect_for_workspace_close()
        self._detached_windows.clear()

    def schedule_restore(self):
        if not self._detached_host:
            QTimer.singleShot(0, self.restore_detached_tabs)
