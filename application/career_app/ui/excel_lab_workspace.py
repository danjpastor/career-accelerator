"""Guided Excel Workbook Studio for Applied Lab 07."""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from career_app.services import applied_workspace
from career_app.theme import COLORS


STEPS: tuple[dict[str, Any], ...] = (
    {
        "title": "Define the workbook and source grain",
        "purpose": "Decide what every row represents before importing or joining anything. This protects the workbook from accidental duplication.",
        "actions": (
            "Create or open the workbook in the Applied Labs submissions folder.",
            "Review every CSV in the Source Data tab.",
            "Record the grain and candidate key for each source.",
            "Confirm that Orders is the one-row-per-order foundation for Order Analysis.",
        ),
        "output": "A saved workbook and a visible source map that states the grain and key of every file.",
        "validation": "The Orders row count is 12 and order_id is unique. No workbook calculation has been built yet.",
        "pitfalls": "Do not begin with lookups or PivotTables before you understand which files can contain multiple rows per order.",
    },
    {
        "title": "Import and profile the source files",
        "purpose": "Build a refreshable input layer and document quality issues before changing values.",
        "actions": (
            "Use Data > Get Data > From Text/CSV to import each supplied CSV with Power Query.",
            "Rename each query clearly and verify data types.",
            "Standardize region values without editing the packaged CSV files.",
            "Record row counts before and after transformations.",
            "Load the sources as named tables or connection-only queries where appropriate.",
        ),
        "output": "Seven named, refreshable sources with documented row counts and data types.",
        "validation": "Refresh All returns the same source row counts and does not append duplicate records.",
        "pitfalls": "Do not overwrite the source CSV files or silently remove rows that fail a type conversion.",
    },
    {
        "title": "Build the Order Analysis table",
        "purpose": "Create one dependable order-level table that brings together customer, product, return, and revenue information.",
        "actions": (
            "Start from the 12-row Orders table so one row continues to represent one order.",
            "Add customer and product attributes using XLOOKUP or Power Query merges.",
            "Aggregate returns to one row per order before joining returned quantities.",
            "Calculate gross revenue and net revenue from source fields.",
            "Flag unmatched lookup keys and calculation errors instead of hiding them.",
        ),
        "output": "An Order Analysis table with exactly 12 rows and readable analytical fields.",
        "validation": "Order count remains 12; every order_id is unique; unmatched customer_id and product_id counts are visible.",
        "pitfalls": "Joining Returns directly can duplicate an order when more than one return record exists. Aggregate first.",
    },
    {
        "title": "Create the Controls sheet",
        "purpose": "Make filters, metric rules, assumptions, and refresh instructions visible to the next analyst.",
        "actions": (
            "Add Month and Region dropdown controls with an All option.",
            "Document the definition of each KPI before creating its formula.",
            "List assumptions, exclusions, and the workbook refresh steps.",
            "Use clear input-cell formatting so controls are easy to find.",
        ),
        "output": "A Controls sheet that explains how the workbook works and which cells the user can change.",
        "validation": "The selected month and region are valid values and the definitions identify numerator, denominator, date rule, and missing-data behavior.",
        "pitfalls": "Avoid hidden filter logic or unexplained hardcoded values in report formulas.",
    },
    {
        "title": "Build the Management Summary",
        "purpose": "Turn the order-level analysis into a one-page decision view for the operations director.",
        "actions": (
            "Create five KPIs: orders, gross revenue, net revenue, return rate, and on-time ticket rate.",
            "Build a regional comparison that responds to the controls.",
            "Add two charts that answer a named management question.",
            "Use titles that include the selected period or filter context.",
            "Keep the page readable at normal laptop resolution.",
        ),
        "output": "A one-page Management Summary with five KPIs, one regional comparison, and two useful charts.",
        "validation": "Changing Month or Region changes the expected values without breaking titles, units, or chart ranges.",
        "pitfalls": "Do not add visuals merely because the data is available. Every visual should support a decision.",
    },
    {
        "title": "Reconcile revenue and test refresh",
        "purpose": "Prove that the workbook totals are controlled and explain any difference from the independent finance report.",
        "actions": (
            "Create a monthly reconciliation table.",
            "Compare calculated revenue with finance_report.csv.",
            "Show the numeric difference and a Pass/Investigate status.",
            "Run Refresh All twice and confirm the counts and totals do not change unexpectedly.",
            "Test at least two Month/Region combinations and record the results.",
        ),
        "output": "A visible reconciliation with expected, actual, difference, status, and explanation fields.",
        "validation": "Every finance month is present and each unresolved difference has a documented likely cause and impact.",
        "pitfalls": "Never force a difference to zero or hide a mismatch just to make the workbook appear complete.",
    },
    {
        "title": "Complete the analyst handoff",
        "purpose": "Package the workbook so a reviewer can reopen it, refresh it, inspect the evidence, and understand the decision it supports.",
        "actions": (
            "Save the final workbook as 07_operations_analyst_workbook.xlsx.",
            "Capture a readable screenshot of the Management Summary.",
            "Reopen the workbook and verify that formulas, queries, and controls still work.",
            "Complete the final review checklist in this Studio.",
            "Record the stakeholder takeaway and any limitation in the submission record.",
        ),
        "output": "A reopenable workbook, summary screenshot, completed evidence record, and honest limitations statement.",
        "validation": "Another analyst can find the source files, refresh the workbook, understand each KPI, and reproduce the main result.",
        "pitfalls": "Do not mark the lab complete while artifact paths, validation evidence, or unresolved differences are blank.",
    },
)

SOURCE_MAP: dict[str, dict[str, str]] = {
    "customers.csv": {"grain": "One row per customer", "key": "customer_id", "purpose": "Customer name, region, and segment"},
    "finance_report.csv": {"grain": "One row per reporting month", "key": "month", "purpose": "Independent revenue reconciliation"},
    "orders.csv": {"grain": "One row per order", "key": "order_id", "purpose": "Order-level analytical foundation"},
    "products.csv": {"grain": "One row per product", "key": "product_id", "purpose": "Product attributes, cost, and price"},
    "returns.csv": {"grain": "One row per return event", "key": "return_id", "purpose": "Returned quantity and reason; aggregate by order before joining"},
    "targets.csv": {"grain": "One row per region", "key": "region", "purpose": "Revenue, return-rate, and SLA targets"},
    "tickets.csv": {"grain": "One row per support ticket", "key": "ticket_id", "purpose": "Service and on-time ticket performance"},
}

SHEET_PLAN: tuple[tuple[str, str, str], ...] = (
    ("START HERE", "Handoff instructions", "Purpose, source location, refresh order, and definition of done"),
    ("Controls", "User inputs and definitions", "Month and Region selectors, KPI definitions, assumptions, refresh instructions"),
    ("Order Analysis", "One row per order", "Customer/product fields, returned quantity, gross and net revenue, quality flags"),
    ("Management Summary", "One-page decision view", "Five KPIs, regional comparison, two charts, filter-aware titles"),
    ("Reconciliation", "Independent control", "Calculated monthly revenue, finance revenue, difference, status, explanation"),
    ("Data Dictionary", "Source and output definitions", "Grain, key, field meaning, data type, and calculation notes"),
)

FINAL_CHECKS: tuple[str, ...] = (
    "Order Analysis has 12 unique order rows.",
    "Lookups, returns, revenue, and KPIs are formula- or query-driven.",
    "Month and Region controls update the summary correctly.",
    "Refresh All does not duplicate source rows or change totals unexpectedly.",
    "Revenue is reconciled to finance_report.csv and differences are explained.",
    "Metric definitions, assumptions, refresh steps, and limitations are visible.",
    "The workbook and Management Summary screenshot can be reopened.",
)


class ExcelAnalystLabStudio(QWidget):
    """A stateful, portfolio-style workspace for Applied Lab 07."""

    changed = Signal(str)

    def __init__(self, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.root = Path(root)
        self.exercise_dir = self.root / "practice" / "applied" / "exercises" / "07_excel_analyst_workbook"
        self.dataset_dir = self.root / "practice" / "applied" / "datasets" / "operations"
        self.submissions_dir = self.root / "practice" / "applied" / "submissions"
        self.workbook_template = self.exercise_dir / "starter_workbook.xlsx"
        self.workbook_path = self.submissions_dir / "07_operations_analyst_workbook.xlsx"
        self.state_path = self.submissions_dir / "07_excel_workbook_studio.json"
        self.screenshot_default = self.submissions_dir / "07_management_summary.png"
        self._loading = False
        self._state: dict[str, Any] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QFrame()
        header.setObjectName("ExcelLabStudioHeader")
        header.setStyleSheet(
            "QFrame#ExcelLabStudioHeader {background:#101d31;border:1px solid #2a3b59;border-radius:10px;}"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        title_row = QHBoxLayout()
        title = QLabel("Excel Analyst Workbook Studio")
        title.setObjectName("SectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        self.progress_text = QLabel("0 of 7 stages complete")
        self.progress_text.setObjectName("Muted")
        title_row.addWidget(self.progress_text)
        header_layout.addLayout(title_row)
        description = QLabel(
            "Build the workbook in guided stages. The Studio keeps your plan, evidence, source checks, and final review together; Excel remains the place where you perform the actual analysis."
        )
        description.setWordWrap(True)
        description.setObjectName("Muted")
        header_layout.addWidget(description)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(STEPS))
        self.progress_bar.setTextVisible(False)
        header_layout.addWidget(self.progress_bar)

        actions = QHBoxLayout()
        self.workbook_button = QPushButton("Create / Open Workbook")
        self.workbook_button.setObjectName("Primary")
        self.workbook_button.clicked.connect(self.create_or_open_workbook)
        self.source_button = QPushButton("Open Source Data")
        self.source_button.setObjectName("Secondary")
        self.source_button.clicked.connect(lambda: self._open_path(self.dataset_dir))
        self.record_button = QPushButton("Open Submission Record")
        self.record_button.setObjectName("Secondary")
        self.record_button.clicked.connect(self.open_submission_record)
        self.folder_button = QPushButton("Open Submissions Folder")
        self.folder_button.setObjectName("Secondary")
        self.folder_button.clicked.connect(lambda: self._open_path(self.submissions_dir))
        for button in (self.workbook_button, self.source_button, self.record_button, self.folder_button):
            actions.addWidget(button)
        actions.addStretch()
        header_layout.addLayout(actions)
        layout.addWidget(header)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(5)

        rail = QFrame()
        rail.setObjectName("ExcelLabStageRail")
        rail.setStyleSheet(
            "QFrame#ExcelLabStageRail {background:#101827;border:1px solid #263754;border-radius:10px;}"
        )
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(10, 10, 10, 10)
        rail_title = QLabel("Workbook stages")
        rail_title.setObjectName("SectionTitle")
        rail_layout.addWidget(rail_title)
        self.stage_list = QListWidget()
        self.stage_list.setWordWrap(True)
        self.stage_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stage_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.stage_list.currentRowChanged.connect(self._stage_selected)
        rail_layout.addWidget(self.stage_list, 1)
        self.splitter.addWidget(rail)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_guided_step_tab(), "Guided Stage")
        self.tabs.addTab(self._build_source_tab(), "Source Data")
        self.tabs.addTab(self._build_plan_tab(), "Workbook Plan")
        self.tabs.addTab(self._build_final_review_tab(), "Final Review")
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([250, 760])
        layout.addWidget(self.splitter, 1)

        self.status = QLabel("")
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def _scroll_page(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        return scroll

    def _build_guided_step_tab(self) -> QScrollArea:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        self.stage_title = QLabel("")
        self.stage_title.setObjectName("SectionTitle")
        layout.addWidget(self.stage_title)
        self.stage_purpose = QLabel("")
        self.stage_purpose.setWordWrap(True)
        self.stage_purpose.setObjectName("Muted")
        layout.addWidget(self.stage_purpose)

        action_label = QLabel("Do this in Excel")
        action_label.setObjectName("SectionTitle")
        layout.addWidget(action_label)
        self.stage_actions = QListWidget()
        self.stage_actions.setWordWrap(True)
        self.stage_actions.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.stage_actions.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.stage_actions.setMinimumHeight(150)
        layout.addWidget(self.stage_actions)

        self.stage_output = QTextBrowser()
        self.stage_output.setOpenExternalLinks(False)
        self.stage_output.setMinimumHeight(130)
        layout.addWidget(self.stage_output)

        evidence_label = QLabel("Evidence from this stage")
        evidence_label.setObjectName("SectionTitle")
        layout.addWidget(evidence_label)
        self.stage_evidence = QTextEdit()
        self.stage_evidence.setAcceptRichText(False)
        self.stage_evidence.setPlaceholderText(
            "Record row counts, workbook cells or sheets checked, results, artifact paths, screenshots, assumptions, or an unresolved issue."
        )
        self.stage_evidence.setMinimumHeight(95)
        layout.addWidget(self.stage_evidence)

        buttons = QHBoxLayout()
        self.save_stage_button = QPushButton("Save Stage Evidence")
        self.save_stage_button.setObjectName("Secondary")
        self.save_stage_button.clicked.connect(self.save_current_stage)
        self.complete_stage_button = QPushButton("Mark Stage Complete")
        self.complete_stage_button.setObjectName("Primary")
        self.complete_stage_button.clicked.connect(self.toggle_current_stage_complete)
        buttons.addWidget(self.save_stage_button)
        buttons.addStretch()
        buttons.addWidget(self.complete_stage_button)
        layout.addLayout(buttons)
        layout.addStretch()
        return self._scroll_page(page)

    def _build_source_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        heading = QLabel("Source-file map and preview")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        help_text = QLabel(
            "Use this map before you import. It tells you what one row represents, which field should be unique, and where a join can change the grain."
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        self.source_map_table = QTableWidget()
        self.source_map_table.setColumnCount(5)
        self.source_map_table.setHorizontalHeaderLabels(["Source", "Rows", "Grain", "Candidate key", "Purpose / join warning"])
        self.source_map_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.source_map_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.source_map_table.verticalHeader().setVisible(False)
        self.source_map_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.source_map_table.horizontalHeader().setStretchLastSection(True)
        self.source_map_table.setMinimumHeight(230)
        layout.addWidget(self.source_map_table)

        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Preview source"))
        self.preview_combo = QComboBox()
        self.preview_combo.currentTextChanged.connect(self._load_preview)
        preview_row.addWidget(self.preview_combo, 1)
        self.preview_count = QLabel("")
        self.preview_count.setObjectName("Muted")
        preview_row.addWidget(self.preview_count)
        layout.addLayout(preview_row)

        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview_table, 1)
        return page

    def _build_plan_tab(self) -> QScrollArea:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        heading = QLabel("Required workbook structure")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        help_text = QLabel(
            "The starter workbook contains this structure but not the finished analysis. Keep these responsibilities separate so another analyst can trace inputs, calculations, controls, and validation."
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Sheet", "Role", "Required content"])
        table.setRowCount(len(SHEET_PLAN))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        for row, values in enumerate(SHEET_PLAN):
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        table.resizeRowsToContents()
        table.setMinimumHeight(245)
        layout.addWidget(table)

        metric_title = QLabel("Required metric decisions")
        metric_title.setObjectName("SectionTitle")
        layout.addWidget(metric_title)
        metric_text = QTextBrowser()
        metric_text.setHtml(
            "<ul>"
            "<li><b>Order count:</b> count unique order_id values after filters.</li>"
            "<li><b>Gross revenue:</b> ordered quantity multiplied by unit price before returns.</li>"
            "<li><b>Net revenue:</b> revenue after returned quantity is accounted for.</li>"
            "<li><b>Return rate:</b> choose and document whether the denominator is order count or quantity.</li>"
            "<li><b>On-time ticket rate:</b> define on time using closed_date compared with due_date and state how open tickets behave.</li>"
            "</ul>"
            "<p><b>Control rule:</b> type definitions and assumptions, but never type the final KPI values. They must be driven by tables, formulas, queries, or PivotTables.</p>"
        )
        metric_text.setMinimumHeight(190)
        layout.addWidget(metric_text)
        layout.addStretch()
        return self._scroll_page(page)

    def _build_final_review_tab(self) -> QScrollArea:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        heading = QLabel("Final handoff review")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        help_text = QLabel(
            "Record the finished artifacts and check only items you have personally verified. This review becomes part of the Applied Lab submission record."
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addWidget(QLabel("Workbook path"))
        self.artifact_path = QLineEdit()
        self.artifact_path.setPlaceholderText(str(self.workbook_path))
        layout.addWidget(self.artifact_path)
        layout.addWidget(QLabel("Management Summary screenshot"))
        self.screenshot_path = QLineEdit()
        self.screenshot_path.setPlaceholderText(str(self.screenshot_default))
        layout.addWidget(self.screenshot_path)
        layout.addWidget(QLabel("Stakeholder takeaway and remaining limitations"))
        self.final_notes = QTextEdit()
        self.final_notes.setAcceptRichText(False)
        self.final_notes.setMinimumHeight(95)
        self.final_notes.setPlaceholderText(
            "Explain the result, why it matters, the next action, and any unresolved reconciliation or data-quality limitation."
        )
        layout.addWidget(self.final_notes)

        checklist_title = QLabel("Verification checklist")
        checklist_title.setObjectName("SectionTitle")
        layout.addWidget(checklist_title)
        self.final_checks = QListWidget()
        self.final_checks.setWordWrap(True)
        self.final_checks.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.final_checks.setMinimumHeight(220)
        for label in FINAL_CHECKS:
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.final_checks.addItem(item)
        layout.addWidget(self.final_checks)

        save = QPushButton("Save Final Review")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_final_review)
        layout.addWidget(save, 0, Qt.AlignmentFlag.AlignRight)
        layout.addStretch()
        return self._scroll_page(page)

    def _default_state(self) -> dict[str, Any]:
        return {
            "steps": {str(i): {"complete": False, "evidence": ""} for i in range(1, len(STEPS) + 1)},
            "artifact_path": str(self.workbook_path),
            "screenshot_path": str(self.screenshot_default),
            "final_notes": "",
            "final_checks": [False] * len(FINAL_CHECKS),
            "updated_at": None,
        }

    def _load_state(self) -> dict[str, Any]:
        default = self._default_state()
        if not self.state_path.exists():
            return default
        try:
            loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return default
        if not isinstance(loaded, dict):
            return default
        default.update({key: value for key, value in loaded.items() if key in default})
        steps = default.get("steps") if isinstance(default.get("steps"), dict) else {}
        normalized: dict[str, dict[str, Any]] = {}
        for i in range(1, len(STEPS) + 1):
            row = steps.get(str(i), {}) if isinstance(steps, dict) else {}
            normalized[str(i)] = {
                "complete": bool(row.get("complete", False)) if isinstance(row, dict) else False,
                "evidence": str(row.get("evidence", "")) if isinstance(row, dict) else "",
            }
        default["steps"] = normalized
        checks = list(default.get("final_checks") or [])
        default["final_checks"] = [bool(checks[i]) if i < len(checks) else False for i in range(len(FINAL_CHECKS))]
        return default

    def refresh(self) -> None:
        self._loading = True
        try:
            current = max(0, self.stage_list.currentRow())
            self._state = self._load_state()
            self._refresh_stage_list()
            self._refresh_source_map()
            self.artifact_path.setText(str(self._state.get("artifact_path") or self.workbook_path))
            self.screenshot_path.setText(str(self._state.get("screenshot_path") or self.screenshot_default))
            self.final_notes.setPlainText(str(self._state.get("final_notes") or ""))
            checks = list(self._state.get("final_checks") or [])
            for index in range(self.final_checks.count()):
                self.final_checks.item(index).setCheckState(
                    Qt.CheckState.Checked if index < len(checks) and checks[index] else Qt.CheckState.Unchecked
                )
            self.stage_list.setCurrentRow(min(current, len(STEPS) - 1))
            self._update_progress()
            self.workbook_button.setText("Open Workbook" if self.workbook_path.exists() else "Create / Open Workbook")
        finally:
            self._loading = False

    def _refresh_stage_list(self) -> None:
        current = max(0, self.stage_list.currentRow())
        self.stage_list.blockSignals(True)
        self.stage_list.clear()
        for index, step in enumerate(STEPS, start=1):
            complete = bool(self._state.get("steps", {}).get(str(index), {}).get("complete"))
            icon = "✓" if complete else str(index)
            item = QListWidgetItem(f"{icon}  {step['title']}")
            item.setToolTip(step["purpose"])
            self.stage_list.addItem(item)
        self.stage_list.blockSignals(False)
        if self.stage_list.count():
            self.stage_list.setCurrentRow(min(current, self.stage_list.count() - 1))

    def _stage_selected(self, row: int) -> None:
        if row < 0 or row >= len(STEPS):
            return
        step = STEPS[row]
        self.stage_title.setText(f"Stage {row + 1}: {step['title']}")
        self.stage_purpose.setText(step["purpose"])
        self.stage_actions.clear()
        for action in step["actions"]:
            self.stage_actions.addItem(QListWidgetItem(f"•  {action}"))
        self.stage_output.setHtml(
            f"<p><b>Expected output</b><br>{step['output']}</p>"
            f"<p><b>Check before continuing</b><br>{step['validation']}</p>"
            f"<p><b>Common mistake</b><br>{step['pitfalls']}</p>"
        )
        record = self._state.get("steps", {}).get(str(row + 1), {})
        self.stage_evidence.blockSignals(True)
        self.stage_evidence.setPlainText(str(record.get("evidence") or ""))
        self.stage_evidence.blockSignals(False)
        complete = bool(record.get("complete"))
        self.complete_stage_button.setText("Reopen Stage" if complete else "Mark Stage Complete")

    def _refresh_source_map(self) -> None:
        files = sorted(self.dataset_dir.glob("*.csv"))
        self.source_map_table.setRowCount(len(files))
        self.preview_combo.blockSignals(True)
        selected = self.preview_combo.currentText()
        self.preview_combo.clear()
        for row, path in enumerate(files):
            count = self._csv_row_count(path)
            info = SOURCE_MAP.get(path.name, {})
            values = (
                path.name,
                str(count),
                info.get("grain", "Review and define"),
                info.get("key", "Review and define"),
                info.get("purpose", "Review source role"),
            )
            for column, value in enumerate(values):
                self.source_map_table.setItem(row, column, QTableWidgetItem(value))
            self.preview_combo.addItem(path.name)
        self.source_map_table.resizeRowsToContents()
        if selected:
            index = self.preview_combo.findText(selected)
            if index >= 0:
                self.preview_combo.setCurrentIndex(index)
        self.preview_combo.blockSignals(False)
        if self.preview_combo.count():
            self._load_preview(self.preview_combo.currentText())

    @staticmethod
    def _csv_row_count(path: Path) -> int:
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                return max(0, sum(1 for _ in csv.reader(handle)) - 1)
        except OSError:
            return 0

    def _load_preview(self, filename: str) -> None:
        path = self.dataset_dir / filename
        if not path.exists():
            return
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
                rows = []
                total = 0
                for row in reader:
                    total += 1
                    if len(rows) < 8:
                        rows.append(row)
        except OSError as exc:
            self.status.setText(f"Could not preview {filename}: {exc}")
            return
        self.preview_table.clear()
        self.preview_table.setColumnCount(len(header))
        self.preview_table.setHorizontalHeaderLabels(header)
        self.preview_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                if column_index < len(header):
                    self.preview_table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.preview_count.setText(f"{total} rows • showing first {len(rows)}")

    def save_current_stage(self) -> None:
        row = self.stage_list.currentRow()
        if row < 0:
            return
        self._state["steps"][str(row + 1)]["evidence"] = self.stage_evidence.toPlainText().strip()
        self._save_state("Stage evidence saved.")

    def toggle_current_stage_complete(self) -> None:
        row = self.stage_list.currentRow()
        if row < 0:
            return
        record = self._state["steps"][str(row + 1)]
        record["evidence"] = self.stage_evidence.toPlainText().strip()
        if not record.get("complete") and not record["evidence"]:
            QMessageBox.information(
                self,
                "Evidence Needed",
                "Record at least one result, validation check, artifact location, or unresolved issue before completing this stage.",
            )
            return
        record["complete"] = not bool(record.get("complete"))
        self._save_state("Stage reopened." if not record["complete"] else "Stage completed.")
        self._refresh_stage_list()
        self.stage_list.setCurrentRow(row)
        self._update_progress()

    def save_final_review(self) -> None:
        self._state["artifact_path"] = self.artifact_path.text().strip() or str(self.workbook_path)
        self._state["screenshot_path"] = self.screenshot_path.text().strip() or str(self.screenshot_default)
        self._state["final_notes"] = self.final_notes.toPlainText().strip()
        self._state["final_checks"] = [
            self.final_checks.item(i).checkState() == Qt.CheckState.Checked
            for i in range(self.final_checks.count())
        ]
        self._save_state("Final review saved to the Applied Lab submission record.")

    def save_all(self) -> None:
        row = self.stage_list.currentRow()
        if row >= 0:
            self._state["steps"][str(row + 1)]["evidence"] = self.stage_evidence.toPlainText().strip()
        self._state["artifact_path"] = self.artifact_path.text().strip() or str(self.workbook_path)
        self._state["screenshot_path"] = self.screenshot_path.text().strip() or str(self.screenshot_default)
        self._state["final_notes"] = self.final_notes.toPlainText().strip()
        self._state["final_checks"] = [
            self.final_checks.item(i).checkState() == Qt.CheckState.Checked
            for i in range(self.final_checks.count())
        ]
        self._save_state("Excel Workbook Studio progress saved.")

    def _save_state(self, message: str) -> None:
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        self._state["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.state_path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        self._sync_submission_record()
        self._update_progress()
        self.status.setText(message)
        self.changed.emit(message)

    def _sync_submission_record(self) -> None:
        path, _created = applied_workspace.ensure_submission(self.root, 7)
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        begin = "<!-- BEGIN EXCEL WORKBOOK STUDIO -->"
        end = "<!-- END EXCEL WORKBOOK STUDIO -->"
        lines = [
            begin,
            "## Excel Workbook Studio progress",
            "",
            f"- Workbook: `{self._state.get('artifact_path') or self.workbook_path}`",
            f"- Management Summary screenshot: `{self._state.get('screenshot_path') or self.screenshot_default}`",
            f"- Last Studio update: {self._state.get('updated_at') or 'Not saved yet'}",
            "",
            "### Guided stages",
            "",
        ]
        for index, step in enumerate(STEPS, start=1):
            record = self._state.get("steps", {}).get(str(index), {})
            mark = "x" if record.get("complete") else " "
            lines.append(f"- [{mark}] Stage {index}: {step['title']}")
            evidence = str(record.get("evidence") or "").strip()
            if evidence:
                compact = evidence.replace("\n", " / ")
                lines.append(f"  - Evidence: {compact}")
        lines.extend(["", "### Final verification", ""])
        checks = list(self._state.get("final_checks") or [])
        for index, label in enumerate(FINAL_CHECKS):
            mark = "x" if index < len(checks) and checks[index] else " "
            lines.append(f"- [{mark}] {label}")
        final_notes = str(self._state.get("final_notes") or "").strip()
        lines.extend(["", "### Stakeholder takeaway and limitations", "", final_notes or "Not recorded yet.", end])
        block = "\n".join(lines)
        if begin in text and end in text:
            prefix = text.split(begin, 1)[0].rstrip()
            suffix = text.split(end, 1)[1].lstrip()
            text = prefix + "\n\n" + block + ("\n\n" + suffix if suffix else "\n")
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
        path.write_text(text, encoding="utf-8")

    def _update_progress(self) -> None:
        completed = sum(1 for record in self._state.get("steps", {}).values() if record.get("complete"))
        self.progress_bar.setValue(completed)
        self.progress_text.setText(f"{completed} of {len(STEPS)} stages complete")

    def completion_issues(self) -> list[str]:
        self.save_all()
        issues: list[str] = []
        if not self.workbook_path.exists():
            issues.append("Create and save 07_operations_analyst_workbook.xlsx from the Studio.")
        incomplete = [str(i) for i in range(1, len(STEPS) + 1) if not self._state.get("steps", {}).get(str(i), {}).get("complete")]
        if incomplete:
            issues.append("Complete guided stages: " + ", ".join(incomplete) + ".")
        checks = list(self._state.get("final_checks") or [])
        missing_checks = [str(i + 1) for i in range(len(FINAL_CHECKS)) if i >= len(checks) or not checks[i]]
        if missing_checks:
            issues.append("Verify final-review items: " + ", ".join(missing_checks) + ".")
        if not str(self._state.get("final_notes") or "").strip():
            issues.append("Record the stakeholder takeaway and remaining limitations.")
        screenshot = Path(str(self._state.get("screenshot_path") or self.screenshot_default))
        if not screenshot.is_absolute():
            screenshot = self.root / screenshot
        if not screenshot.exists():
            issues.append("Save the Management Summary screenshot and record its path.")
        return issues

    def create_or_open_workbook(self) -> None:
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        if not self.workbook_path.exists():
            if not self.workbook_template.exists():
                QMessageBox.warning(self, "Starter Workbook Missing", f"Could not find {self.workbook_template.name}.")
                return
            shutil.copy2(self.workbook_template, self.workbook_path)
            self._state["artifact_path"] = str(self.workbook_path)
            self._save_state("Starter workbook created in Applied Labs submissions.")
        self._open_path(self.workbook_path)
        self.workbook_button.setText("Open Workbook")

    def open_submission_record(self) -> None:
        path, _created = applied_workspace.ensure_submission(self.root, 7)
        self._open_path(path)

    def _open_path(self, path: Path) -> None:
        path = Path(path).resolve()
        if not path.exists():
            QMessageBox.warning(self, "Could Not Open", f"The path does not exist:\n{path}")
            return
        try:
            if os.name == "nt":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                command = shutil.which("xdg-open")
                if not command:
                    raise RuntimeError("No supported file-opening command was found.")
                subprocess.Popen([command, str(path)])
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Open", str(exc))
