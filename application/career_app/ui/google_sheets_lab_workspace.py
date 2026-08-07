"""Guided Google Sheets Analyst Studio for Applied Lab 01."""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
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


_GOOGLE_SHEETS_URL = re.compile(
    r"^https://docs\.google\.com/spreadsheets(?:/u/\d+)?/d/[A-Za-z0-9_-]+(?:/.*)?$",
    re.IGNORECASE,
)


def _is_google_sheets_url(value: str) -> bool:
    return bool(_GOOGLE_SHEETS_URL.match(str(value or "").strip()))


STEPS: tuple[dict[str, Any], ...] = (
    {
        "title": "Set up the sheet and analysis table",
        "purpose": "Create the small workbook structure and one formula-driven row per order.",
        "actions": (
            "Create a Google Sheet with Raw Orders, Targets, Analysis, and Summary tabs, then import the two supplied CSV files without editing the source tabs.",
            "In Analysis, reference the order rows and create only four calculated fields: Clean Region, Gross Sales, Processing Fee, and Net Sales.",
            "Use one fixed fee-rate cell on Summary and copy the formulas through every order row.",
        ),
        "output": "A four-tab sheet with one Analysis row per order and four copied calculated fields.",
        "validation": (
            "The Analysis and Raw Orders row counts match.",
            "Cancelled orders do not contribute sales.",
            "Changing the fee-rate cell changes fee and net sales but not gross sales.",
        ),
        "evidence": "Record the share link, Analysis row count, and one manually checked order.",
        "pitfalls": (
            "Typing cleaned values or sales totals manually.",
            "Using a moving reference for the single fee-rate cell.",
        ),
    },
    {
        "title": "Build the small summary",
        "purpose": "Create only the controls and outputs needed for one management question.",
        "actions": (
            "Create a region dropdown containing All and the cleaned regions.",
            "Create three KPI cells: Completed Orders, Net Sales, and Regional Sales Target. Make the first two respond to the region selection and use an exact-match lookup for the target.",
            "Create one pivot table of Gross Sales by Clean Region and one simple column chart from that pivot.",
        ),
        "output": "A Summary tab with one dropdown, three KPIs, one pivot table, and one chart.",
        "validation": (
            "The region dropdown changes Completed Orders and Net Sales.",
            "The target lookup changes by region and does not show an error for All.",
            "The all-region pivot total agrees with the Analysis gross-sales total.",
        ),
        "evidence": "Record two region selections tested and the pivot-total comparison.",
        "pitfalls": (
            "Adding extra KPIs, tabs, or charts that are not required.",
            "Building the chart from raw orders instead of the pivot summary.",
        ),
        "hints": (
            "Build the All-region and selected-region calculation separately before combining them.",
            "Use the cleaned region field everywhere on Summary.",
        ),
    },
    {
        "title": "Check the result and write the takeaway",
        "purpose": "Confirm the small summary works and explain one supported finding.",
        "actions": (
            "Reconcile the source, Analysis, and unique-order counts.",
            "Check one completed order manually and compare one regional Net Sales subtotal with the Summary KPI.",
            "Write two or three sentences describing the strongest regional pattern, why it matters, and one limitation or next question.",
        ),
        "output": "A checked shareable sheet and a short evidence-based takeaway.",
        "validation": (
            "The manual order and regional subtotal agree with the formulas.",
            "The share link opens and the required tabs are readable.",
            "The takeaway describes an observed pattern without claiming a cause.",
        ),
        "evidence": "Record the two checks, final takeaway, and one limitation.",
        "pitfalls": (
            "Treating a plausible number as validated.",
            "Expanding the lab into a polished dashboard or portfolio workbook.",
        ),
    },
)


def lab01_guide_markdown() -> str:
    lines = [
        "# Applied Lab 01: Create a Google Sheets sales summary",
        "",
        "> This is one of the five required integration labs. It is designed for about 40 minutes and should remain a small spreadsheet exercise, not a project.",
        "",
        "## Assignment",
        "",
        "Use the supplied Orders and Targets files to create one formula-driven Analysis table and one small Summary tab with a region selector, three KPIs, one pivot table, and one chart.",
        "",
    ]
    for index, stage in enumerate(STEPS, start=1):
        lines.extend([f"## Stage {index}: {stage['title']}", "", stage['purpose'], "", "### What to do", ""])
        lines.extend(f"{n}. {value}" for n, value in enumerate(stage['actions'], start=1))
        lines.extend(["", "### Required output", "", stage['output'], "", "### Check your work", ""])
        lines.extend(f"- {value}" for value in stage['validation'])
        lines.extend(["", "### Evidence to record", "", stage['evidence'], "", "### Common mistakes", ""])
        lines.extend(f"- {value}" for value in stage['pitfalls'])
        if stage.get('hints'):
            lines.extend(["", "### Progressive hints", ""])
            lines.extend(f"- {value}" for value in stage['hints'])
        lines.append("")
    lines.extend([
        "## Completion rule",
        "",
        "Complete the three Studio stages, save the shareable Google Sheets link, verify the final checklist, and write a two-to-three-sentence takeaway with one limitation. Extra tabs, KPIs, and charts are not required.",
        "",
    ])
    return "\n".join(lines)


SOURCE_MAP: dict[str, dict[str, str]] = {
    "orders.csv": {
        "grain": "One row per order",
        "key": "order_id",
        "purpose": "Dates, regions, products, status, quantity, and unit price",
    },
    "targets.csv": {
        "grain": "One row per region",
        "key": "region",
        "purpose": "Regional sales targets for VLOOKUP practice",
    },
}

SHEET_PLAN: tuple[tuple[str, str, str], ...] = (
    ("Raw Orders", "Untouched imported source", "Order-level source fields only; no cleaning or calculated answers"),
    ("Targets", "Untouched lookup source", "One region and target per row"),
    ("Analysis", "One row per order", "Connected source fields, cleaned fields, formula-driven sales, and quality checks"),
    ("Summary", "Small decision view", "Fee input, region dropdown, three KPIs, pivot table, chart, and takeaway"),
)

FINAL_CHECKS: tuple[str, ...] = (
    "Raw Orders and Analysis row counts match, and the source tabs were not edited.",
    "One manually checked order and one regional subtotal agree with the formulas.",
    "The region dropdown updates the required KPIs and the pivot total reconciles.",
    "The share link opens and the takeaway states one result and one limitation.",
)


class GoogleSheetsAnalystLabStudio(QWidget):
    """A stateful, beginner-first workspace for Applied Lab 01."""

    changed = Signal(str)

    def __init__(self, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.root = Path(root)
        self.exercise_dir = self.root / "practice" / "applied" / "exercises" / "01_google_sheets_analyst_spreadsheet"
        self.dataset_dir = self.root / "practice" / "applied" / "datasets" / "spreadsheet_foundations"
        self.submissions_dir = self.root / "practice" / "applied" / "submissions"
        self.state_path = self.submissions_dir / "01_google_sheets_studio.json"
        self.screenshot_default = self.submissions_dir / "01_optional_summary_screenshot.png"
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
        title = QLabel("Google Sheets Analyst Studio")
        title.setObjectName("SectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        self.progress_text = QLabel("0 of 3 stages complete")
        self.progress_text.setObjectName("Muted")
        title_row.addWidget(self.progress_text)
        header_layout.addLayout(title_row)
        description = QLabel(
            "Apply the spreadsheet skills from Weeks 1–2 in three short stages. Build one analysis table and one small summary—not a portfolio-scale workbook."
        )
        description.setWordWrap(True)
        description.setObjectName("Muted")
        header_layout.addWidget(description)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(STEPS))
        self.progress_bar.setTextVisible(False)
        header_layout.addWidget(self.progress_bar)

        link_label = QLabel("Shareable Google Sheets link")
        link_label.setObjectName("SectionTitle")
        header_layout.addWidget(link_label)
        link_row = QHBoxLayout()
        self.share_link_input = QLineEdit()
        self.share_link_input.setPlaceholderText("https://docs.google.com/spreadsheets/d/…/edit?usp=sharing")
        self.share_link_input.returnPressed.connect(self.save_share_link)
        self.link_button = QPushButton("Save Sheet Link")
        self.link_button.setObjectName("Primary")
        self.link_button.clicked.connect(self.save_share_link)
        self.spreadsheet_button = QPushButton("Open Linked Sheet")
        self.spreadsheet_button.setObjectName("Secondary")
        self.spreadsheet_button.clicked.connect(self.open_spreadsheet)
        self.new_sheet_button = QPushButton("Open Blank Google Sheet")
        self.new_sheet_button.setObjectName("Secondary")
        self.new_sheet_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://sheets.new"))
        )
        link_row.addWidget(self.share_link_input, 1)
        link_row.addWidget(self.link_button)
        link_row.addWidget(self.spreadsheet_button)
        link_row.addWidget(self.new_sheet_button)
        header_layout.addLayout(link_row)
        self.link_status = QLabel(
            "Career Accelerator stores only the shareable link. It does not connect to your Google account or read the spreadsheet."
        )
        self.link_status.setObjectName("Muted")
        self.link_status.setWordWrap(True)
        header_layout.addWidget(self.link_status)

        actions = QHBoxLayout()
        self.source_button = QPushButton("Open Source Data")
        self.source_button.setObjectName("Secondary")
        self.source_button.clicked.connect(lambda: self._open_path(self.dataset_dir))
        self.record_button = QPushButton("Open Submission Record")
        self.record_button.setObjectName("Secondary")
        self.record_button.clicked.connect(self.open_submission_record)
        self.folder_button = QPushButton("Open Submissions Folder")
        self.folder_button.setObjectName("Secondary")
        self.folder_button.clicked.connect(lambda: self._open_path(self.submissions_dir))
        for button in (self.source_button, self.record_button, self.folder_button):
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
        rail_title = QLabel("Four guided stages")
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
        self.tabs.addTab(self._build_plan_tab(), "Spreadsheet Plan")
        self.tabs.addTab(self._build_final_review_tab(), "Final Review")
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([250, 760])
        layout.addWidget(self.splitter, 1)


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

        action_label = QLabel("Do this in Google Sheets")
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
            "Record the rows, cells, formulas, or checkpoints you verified and note any issue you still need to fix."
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
            "Preview the two small source files before importing them. One contains orders; the other is a regional lookup table."
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
        heading = QLabel("Required spreadsheet structure")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        help_text = QLabel(
            "Use only these four tabs. Stop after the required Analysis table, three KPIs, one pivot table, and one chart."
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
            "<li><b>Completed Orders:</b> count completed rows for All or the selected region.</li>"
            "<li><b>Net Sales:</b> sum the Analysis Net Sales values for All or the selected region.</li>"
            "<li><b>Regional Sales Target:</b> use an exact-match lookup for a selected region and a clear All message.</li>"
            "</ul>"
            "<p><b>Scope:</b> these three KPIs, one pivot table, and one chart are enough. Reconcile one subtotal and stop.</p>"
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
            "Check only items you personally verified, then write a short takeaway. This is a learning lab, so a polished portfolio handoff is not required."
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addWidget(QLabel("Shareable Google Sheets URL"))
        self.artifact_path = QLineEdit()
        self.artifact_path.setPlaceholderText("https://docs.google.com/spreadsheets/d/…/edit")
        layout.addWidget(self.artifact_path)
        self.screenshot_path = QLineEdit()
        self.screenshot_path.setVisible(False)
        layout.addWidget(QLabel("Two-to-three-sentence takeaway"))
        self.final_notes = QTextEdit()
        self.final_notes.setAcceptRichText(False)
        self.final_notes.setMinimumHeight(95)
        self.final_notes.setPlaceholderText(
            "State which region produced the most gross sales, what the result means, and one useful question you would investigate next."
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
            "spreadsheet_id": "",
            "spreadsheet_url": "",
            "artifact_path": "",
            "screenshot_path": str(self.screenshot_default),
            "final_notes": "",
            "final_checks": [False] * len(FINAL_CHECKS),
            "updated_at": None,
        }

    def _load_state(self) -> dict[str, Any]:
        default = self._default_state()
        source = self.state_path
        legacy = self.submissions_dir / "07_excel_workbook_studio.json"
        if not source.exists() and legacy.exists():
            source = legacy
        if not source.exists():
            return default
        try:
            loaded = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return default
        if not isinstance(loaded, dict):
            return default
        default.update({key: value for key, value in loaded.items() if key in default})
        old_artifact = str(loaded.get("artifact_path") or "")
        if old_artifact.startswith("http") and not default.get("spreadsheet_url"):
            default["spreadsheet_url"] = old_artifact
            default["artifact_path"] = old_artifact
        steps = default.get("steps") if isinstance(default.get("steps"), dict) else {}
        default["steps"] = {
            str(i): {
                "complete": bool((steps.get(str(i)) or {}).get("complete", False)),
                "evidence": str((steps.get(str(i)) or {}).get("evidence", "")),
            }
            for i in range(1, len(STEPS) + 1)
        }
        checks = list(default.get("final_checks") or [])
        default["final_checks"] = [bool(checks[i]) if i < len(checks) else False for i in range(len(FINAL_CHECKS))]
        return default

    def refresh(self) -> None:
        self._loading = True
        try:
            current = max(0, self.stage_list.currentRow())
            self._state = self._load_state()
            self._update_stage_list()
            self._update_source_map()
            url = str(self._state.get("spreadsheet_url") or self._state.get("artifact_path") or "")
            self.share_link_input.setText(url)
            self.artifact_path.setText(url)
            self.screenshot_path.setText(str(self._state.get("screenshot_path") or self.screenshot_default))
            self.final_notes.setPlainText(str(self._state.get("final_notes") or ""))
            checks = list(self._state.get("final_checks") or [])
            for index in range(self.final_checks.count()):
                self.final_checks.item(index).setCheckState(
                    Qt.CheckState.Checked if index < len(checks) and checks[index] else Qt.CheckState.Unchecked
                )
            self.stage_list.setCurrentRow(min(current, len(STEPS) - 1))
            self._update_progress()
            linked = _is_google_sheets_url(url)
            self.spreadsheet_button.setEnabled(linked)
            self.link_status.setText(
                "Shareable Google Sheets link saved. Career Accelerator stores only the link and does not access the spreadsheet."
                if linked
                else "Paste a shareable Google Sheets link above. Career Accelerator will store only the link; no Google account connection is required."
            )
        finally:
            self._loading = False

    def _update_stage_list(self) -> None:
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

    def _update_source_map(self) -> None:
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
            self.changed.emit(f"Could not preview {filename}: {exc}")
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
        self._update_stage_list()
        self.stage_list.setCurrentRow(row)
        self._update_progress()

    def save_final_review(self) -> None:
        url = self.artifact_path.text().strip()
        self._state["spreadsheet_url"] = url
        self._state["artifact_path"] = url
        self.share_link_input.setText(url)
        self.spreadsheet_button.setEnabled(_is_google_sheets_url(url))
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
        url = self.artifact_path.text().strip()
        self._state["spreadsheet_url"] = url
        self._state["artifact_path"] = url
        self.share_link_input.setText(url)
        self.spreadsheet_button.setEnabled(_is_google_sheets_url(url))
        self._state["screenshot_path"] = self.screenshot_path.text().strip() or str(self.screenshot_default)
        self._state["final_notes"] = self.final_notes.toPlainText().strip()
        self._state["final_checks"] = [
            self.final_checks.item(i).checkState() == Qt.CheckState.Checked
            for i in range(self.final_checks.count())
        ]
        self._save_state("Google Sheets Analyst Studio progress saved.")

    def _save_state(self, message: str) -> None:
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        self._state["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.state_path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        self._sync_submission_record()
        self._update_progress()
        self.changed.emit(message)

    def _sync_submission_record(self) -> None:
        path, _created = applied_workspace.ensure_submission(self.root, 1)
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        begin = "<!-- BEGIN GOOGLE SHEETS STUDIO -->"
        end = "<!-- END GOOGLE SHEETS STUDIO -->"
        url = self._state.get("spreadsheet_url") or self._state.get("artifact_path") or "Not created yet"
        lines = [
            begin,
            "## Google Sheets Analyst Studio progress",
            "",
            f"- Shared Google Sheet: {url}",
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
                lines.append(f"  - Evidence: {evidence.replace(chr(10), ' / ')}")
        lines.extend(["", "### Final verification", ""])
        checks = list(self._state.get("final_checks") or [])
        for index, label in enumerate(FINAL_CHECKS):
            mark = "x" if index < len(checks) and checks[index] else " "
            lines.append(f"- [{mark}] {label}")
        final_notes = str(self._state.get("final_notes") or "").strip()
        lines.extend(["", "### Short business takeaway", "", final_notes or "Not recorded yet.", end])
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
        url = str(self._state.get("spreadsheet_url") or self._state.get("artifact_path") or "").strip()
        if not _is_google_sheets_url(url):
            issues.append("Paste and save a valid shareable Google Sheets URL in the Studio.")
        incomplete = [str(i) for i in range(1, len(STEPS) + 1) if not self._state.get("steps", {}).get(str(i), {}).get("complete")]
        if incomplete:
            issues.append("Complete guided stages: " + ", ".join(incomplete) + ".")
        checks = list(self._state.get("final_checks") or [])
        missing_checks = [str(i + 1) for i in range(len(FINAL_CHECKS)) if i >= len(checks) or not checks[i]]
        if missing_checks:
            issues.append("Verify final-review items: " + ", ".join(missing_checks) + ".")
        if not str(self._state.get("final_notes") or "").strip():
            issues.append("Write the required two-to-three-sentence takeaway.")
        return issues

    def save_share_link(self) -> None:
        url = self.share_link_input.text().strip()
        if not _is_google_sheets_url(url):
            QMessageBox.warning(
                self,
                "Invalid Google Sheets Link",
                "Paste a shareable Google Sheets URL that starts with "
                "https://docs.google.com/spreadsheets/ and includes the spreadsheet ID.",
            )
            return
        self._state["spreadsheet_id"] = ""
        self._state["spreadsheet_url"] = url
        self._state["artifact_path"] = url
        self.artifact_path.setText(url)
        self.spreadsheet_button.setEnabled(True)
        self._save_state("Shareable Google Sheets link saved for Applied Lab 01.")
        self.link_status.setText(
            "Shareable Google Sheets link saved. Career Accelerator stores only the link and does not access the spreadsheet."
        )

    def open_spreadsheet(self) -> None:
        url = str(
            self._state.get("spreadsheet_url")
            or self.share_link_input.text()
            or self.artifact_path.text()
            or ""
        ).strip()
        if not _is_google_sheets_url(url):
            QMessageBox.information(
                self,
                "Link a Google Sheet First",
                "Paste and save the shareable Google Sheets link before opening it from the Studio.",
            )
            return
        QDesktopServices.openUrl(QUrl(url))

    def open_submission_record(self) -> None:
        path, _created = applied_workspace.ensure_submission(self.root, 1)
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
