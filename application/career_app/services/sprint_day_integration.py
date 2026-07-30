from __future__ import annotations

"""PySide integration for the day-based Current Sprint dialog."""

from typing import Any, Callable

from career_app.services import sprint_day_planner

_INSTALLED = False


def _patch_unified_tasks() -> None:
    from career_app.services import unified_tasks

    original_daily_plan: Callable[..., Any] = unified_tasks.daily_plan
    if not getattr(original_daily_plan, "_sprint_promotion_wrapped", False):
        def daily_plan(conn: Any, current_week: int, max_items: int = 5) -> list[dict[str, Any]]:
            base = list(original_daily_plan(conn, current_week, max_items))
            promoted = sprint_day_planner.promoted_tasks(conn, current_week)
            seen = {int(item.get("id") or item.get("task_id") or 0) for item in base}
            for item in promoted:
                task_id = int(item.get("id") or item.get("task_id") or 0)
                if task_id and task_id not in seen:
                    base.append(item)
                    seen.add(task_id)
            return base
        daily_plan._sprint_promotion_wrapped = True  # type: ignore[attr-defined]
        unified_tasks.daily_plan = daily_plan

    original_summary: Callable[..., Any] = unified_tasks.completion_summary
    if not getattr(original_summary, "_sprint_promotion_wrapped", False):
        def completion_summary(conn: Any, active_items: list[dict[str, Any]]) -> dict[str, Any]:
            result = dict(original_summary(conn, active_items))
            promoted = sprint_day_planner.promotion_summary(conn)
            if promoted["total"]:
                result["total_count"] = int(result.get("total_count") or 0) + promoted["total"]
                result["completed_count"] = int(result.get("completed_count") or 0) + promoted["completed"]
                result["planned_minutes"] = int(result.get("planned_minutes") or 0) + promoted["minutes"]
            return result
        completion_summary._sprint_promotion_wrapped = True  # type: ignore[attr-defined]
        unified_tasks.completion_summary = completion_summary


def _show_current_sprint_dialog(self: Any) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )

    week = int(self.state["current_week"])
    dialog = QDialog(self)
    dialog.setWindowTitle(f"Current Sprint — Week {week}")
    dialog.resize(860, 680)
    try:
        dialog.setStyleSheet(self.styleSheet())
    except Exception:
        pass
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    title = QLabel(f"Current Sprint — Week {week}")
    title.setObjectName("Hero")
    layout.addWidget(title)
    summary = QLabel(
        "Tasks are grouped by their original roadmap day. Select any future day and add "
        "its incomplete tasks to Today’s Focus after every prerequisite is finished. "
        "This is temporary: promoted tasks leave Today’s Focus at midnight and remain "
        "assigned to their original day."
    )
    summary.setObjectName("Muted")
    summary.setWordWrap(True)
    layout.addWidget(summary)

    task_list = QListWidget()
    task_list.setWordWrap(True)
    task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    layout.addWidget(task_list, 1)

    actions = QHBoxLayout()
    promote_button = QPushButton("Add Selected Day to Today")
    promote_button.setObjectName("Primary")
    open_button = QPushButton("Open Selected Task")
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)
    actions.addWidget(promote_button)
    actions.addStretch()
    actions.addWidget(open_button)
    actions.addWidget(close_button)
    layout.addLayout(actions)

    muted = QColor("#8c98ad")
    header_color = QColor("#d6deee")

    def selected_data() -> dict[str, Any] | None:
        item = task_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, dict) else None

    def selected_date() -> str | None:
        data = selected_data()
        if not data:
            return None
        return str(data.get("scheduled_date") or data.get("date") or "") or None

    def render(preferred_date: str | None = None) -> None:
        task_list.clear()
        groups = sprint_day_planner.current_sprint_day_groups(self.conn, week)
        selected_index = -1
        for group in groups:
            counts = []
            if group["incomplete_count"]:
                counts.append(f"{group['incomplete_count']} remaining")
            else:
                counts.append("complete")
            if group["blocked_count"]:
                counts.append(f"{group['blocked_count']} waiting on prerequisites")
            if group["all_promoted"]:
                counts.append("added to today")
            today_label = " • TODAY" if group["is_today"] else ""
            header = QListWidgetItem(
                f"{group['label'].upper()}{today_label}  —  " + " • ".join(counts)
            )
            header.setForeground(header_color)
            header.setData(
                Qt.ItemDataRole.UserRole,
                {"row_type": "day", "date": group["date"], "scheduled_date": group["date"]},
            )
            task_list.addItem(header)
            if preferred_date == group["date"] and selected_index < 0:
                selected_index = task_list.count() - 1

            if not group["tasks"]:
                empty = QListWidgetItem("    No tasks assigned")
                empty.setFlags(Qt.ItemFlag.NoItemFlags)
                empty.setForeground(muted)
                task_list.addItem(empty)
                continue

            for row in group["tasks"]:
                if bool(row.get("completed")):
                    icon, detail = "✓", "Completed"
                elif bool(row.get("promoted_today")):
                    icon, detail = "↗", "Added to Today’s Focus until midnight"
                elif bool(row.get("prerequisites_ready")):
                    icon, detail = "○", "Prerequisites complete"
                else:
                    icon = "🔒"
                    detail = str(row.get("prerequisite_reason") or "Complete the prerequisite first.")
                item = QListWidgetItem(
                    f"    {icon} {row.get('label') or 'Task'}\n"
                    f"       {detail}"
                )
                data = dict(row)
                data["row_type"] = "task"
                data["scheduled_date"] = group["date"]
                item.setData(Qt.ItemDataRole.UserRole, data)
                if not bool(row.get("prerequisites_ready")) and not bool(row.get("completed")):
                    item.setForeground(muted)
                task_list.addItem(item)
        if selected_index >= 0:
            task_list.setCurrentRow(selected_index)
        elif task_list.count():
            task_list.setCurrentRow(0)
        update_buttons()

    def update_buttons(*_args: Any) -> None:
        data = selected_data()
        is_task = bool(data and data.get("row_type") == "task")
        open_button.setEnabled(is_task)
        day_value = selected_date()
        if not day_value:
            promote_button.setEnabled(False)
            promote_button.setText("Add Selected Day to Today")
            return
        from datetime import date as _date
        try:
            chosen = _date.fromisoformat(day_value)
        except ValueError:
            promote_button.setEnabled(False)
            return
        if chosen == _date.today():
            promote_button.setEnabled(False)
            promote_button.setText("Already Scheduled for Today")
        else:
            promote_button.setEnabled(True)
            promote_button.setText(f"Add {chosen.strftime('%A')} to Today")

    def promote_selected(*_args: Any) -> None:
        day_value = selected_date()
        if not day_value:
            return
        result = sprint_day_planner.promote_day(self.conn, week, day_value)
        if not result.get("ok"):
            blockers = list(result.get("blockers") or [])
            message = str(result.get("reason") or "The selected day could not be added.")
            if blockers:
                message += "\n\n" + "\n".join(f"• {item}" for item in blockers)
            QMessageBox.warning(dialog, "Could Not Add Day", message)
            return
        try:
            self.refresh_dashboard(sync_tracks=False)
        except TypeError:
            self.refresh_dashboard()
        QMessageBox.information(dialog, "Tasks Added to Today", str(result["reason"]))
        render(day_value)

    def open_selected(*_args: Any) -> None:
        data = selected_data()
        if not data or data.get("row_type") != "task":
            return
        dialog.accept()
        self._open_get_ahead_target(data)

    promote_button.clicked.connect(promote_selected)
    open_button.clicked.connect(open_selected)
    close_button.clicked.connect(dialog.accept)
    task_list.currentItemChanged.connect(update_buttons)
    task_list.itemDoubleClicked.connect(open_selected)
    render()
    dialog.exec()


def install(CareerAccelerator: type) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _patch_unified_tasks()
    CareerAccelerator._show_current_sprint_dialog = _show_current_sprint_dialog
    _INSTALLED = True
