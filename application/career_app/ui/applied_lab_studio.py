"""Detailed, stateful Studio used by Applied Labs 02–36."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.data.applied_lab_guidance import LabStage, studio_stages


class GuidedAppliedLabStudio(QWidget):
    """One distinct persisted stage workspace for the selected Applied Lab."""

    changed = Signal(str)

    def __init__(self, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.root = Path(root)
        self.number: int | None = None
        self.item: dict[str, Any] | None = None
        self.stages: tuple[LabStage, ...] = ()
        self._state: dict[str, Any] = {}
        self._loading = False
        self._build_ui()

    @property
    def state_path(self) -> Path | None:
        if self.number is None:
            return None
        return (
            self.root
            / "practice"
            / "applied"
            / "submissions"
            / f"{self.number:02d}_guided_studio.json"
        )

    def _default_state(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "stages": [
                {"completed": False, "evidence": ""}
                for _stage in self.stages
            ],
            "artifact": "",
            "takeaway": "",
            "checks": [False, False, False, False],
        }

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QFrame()
        header.setObjectName("GuidedAppliedLabHeader")
        header.setStyleSheet(
            "QFrame#GuidedAppliedLabHeader {background:#101d31;border:1px solid #2a3b59;border-radius:10px;}"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        title_row = QHBoxLayout()
        self.title_label = QLabel("Applied Lab Studio")
        self.title_label.setObjectName("SectionTitle")
        title_row.addWidget(self.title_label, 1)
        self.progress_text = QLabel("")
        self.progress_text.setObjectName("Muted")
        title_row.addWidget(self.progress_text)
        header_layout.addLayout(title_row)
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("Muted")
        header_layout.addWidget(self.description_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        header_layout.addWidget(self.progress_bar)
        layout.addWidget(header)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        rail = QFrame()
        rail.setObjectName("GuidedAppliedLabRail")
        rail.setStyleSheet(
            "QFrame#GuidedAppliedLabRail {background:#101827;border:1px solid #263754;border-radius:10px;}"
        )
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(10, 10, 10, 10)
        rail_title = QLabel("Guided stages")
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
        self.tabs.addTab(self._build_stage_tab(), "Guided Stage")
        self.tabs.addTab(self._build_brief_tab(), "Lab Brief")
        self.tabs.addTab(self._build_final_tab(), "Final Review")
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([250, 760])
        layout.addWidget(self.splitter, 1)

    def _scroll(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        return scroll

    def _build_stage_tab(self) -> QScrollArea:
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

        self.stage_details = QTextBrowser()
        self.stage_details.setOpenExternalLinks(False)
        self.stage_details.setMinimumHeight(320)
        layout.addWidget(self.stage_details)

        evidence_label = QLabel("Evidence from this stage")
        evidence_label.setObjectName("SectionTitle")
        layout.addWidget(evidence_label)
        self.stage_evidence = QTextEdit()
        self.stage_evidence.setAcceptRichText(False)
        self.stage_evidence.setMinimumHeight(100)
        self.stage_evidence.setPlaceholderText(
            "Record what you built, what you checked, and the evidence that supports the stage. Do not paste a finished solution from another source."
        )
        layout.addWidget(self.stage_evidence)

        buttons = QHBoxLayout()
        self.save_stage_button = QPushButton("Save Stage Evidence")
        self.save_stage_button.setObjectName("Secondary")
        self.save_stage_button.clicked.connect(self.save_current_stage)
        self.complete_stage_button = QPushButton("Mark Stage Complete")
        self.complete_stage_button.setObjectName("Primary")
        self.complete_stage_button.clicked.connect(self.toggle_current_stage)
        buttons.addWidget(self.save_stage_button)
        buttons.addStretch()
        buttons.addWidget(self.complete_stage_button)
        layout.addLayout(buttons)
        layout.addStretch()
        return self._scroll(page)

    def _build_brief_tab(self) -> QScrollArea:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.brief_view = QTextBrowser()
        self.brief_view.setOpenExternalLinks(False)
        layout.addWidget(self.brief_view)
        return self._scroll(page)

    def _build_final_tab(self) -> QScrollArea:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        heading = QLabel("Final handoff review")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        intro = QLabel(
            "Check only items you personally verified. The Studio requires evidence and a changed artifact, but it never supplies the finished analytical answer."
        )
        intro.setWordWrap(True)
        intro.setObjectName("Muted")
        layout.addWidget(intro)

        layout.addWidget(QLabel("Artifact path or share link"))
        self.artifact_input = QLineEdit()
        self.artifact_input.setPlaceholderText(
            "Paste the saved submission path, notebook, report, dashboard link, or other lab artifact."
        )
        layout.addWidget(self.artifact_input)

        check_texts = (
            "I completed every requested deliverable and can reopen the saved artifact.",
            "I validated row grain, keys, filters, calculations, or model behavior using an independent check.",
            "I recorded assumptions, unresolved differences, and limitations instead of hiding them.",
            "My takeaway states the result, business meaning, next action, and an appropriate limitation.",
        )
        self.final_checks: list[QCheckBox] = []
        for text in check_texts:
            box = QCheckBox(text)
            self.final_checks.append(box)
            layout.addWidget(box)

        layout.addWidget(QLabel("Final takeaway and limitation"))
        self.takeaway_input = QTextEdit()
        self.takeaway_input.setAcceptRichText(False)
        self.takeaway_input.setMinimumHeight(120)
        self.takeaway_input.setPlaceholderText(
            "Write the result in plain language, explain why it matters, name one reasonable next action, and state one limitation."
        )
        layout.addWidget(self.takeaway_input)

        save_button = QPushButton("Save Final Review")
        save_button.setObjectName("Primary")
        save_button.clicked.connect(self.save_all)
        layout.addWidget(save_button, 0, Qt.AlignmentFlag.AlignRight)
        layout.addStretch()
        return self._scroll(page)

    def load_lab(self, number: int, item: dict[str, Any]) -> None:
        self.number = int(number)
        self.item = dict(item)
        self.stages = studio_stages(self.number, self.item)
        self.progress_bar.setRange(0, len(self.stages))
        self.title_label.setText(f"Applied Lab {self.number:02d} Studio")
        self.description_label.setText(
            f"{self.item['title']} • Work through each stage in order. Guidance explains decisions and checks without revealing the completed solution."
        )
        self._load_state()
        self._rebuild_stage_list()
        self._render_brief()
        self._load_final_fields()
        self.stage_list.setCurrentRow(0)
        self.refresh_progress()

    def _load_state(self) -> None:
        path = self.state_path
        state = self._default_state()
        if path is not None and path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    state.update(loaded)
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        rows = list(state.get("stages") or [])
        while len(rows) < len(self.stages):
            rows.append({"completed": False, "evidence": ""})
        state["stages"] = rows[: len(self.stages)]
        checks = list(state.get("checks") or [])
        while len(checks) < 4:
            checks.append(False)
        state["checks"] = checks[:4]
        self._state = state

    def _write_state(self) -> None:
        path = self.state_path
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")

    def _rebuild_stage_list(self) -> None:
        current = max(0, self.stage_list.currentRow())
        self.stage_list.blockSignals(True)
        self.stage_list.clear()
        state_rows = self._state.get("stages", [])
        for index, stage in enumerate(self.stages):
            completed = bool(state_rows[index].get("completed"))
            marker = "✓" if completed else "○"
            item = QListWidgetItem(f"{marker}  Stage {index + 1}\n     {stage.title}")
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.stage_list.addItem(item)
        self.stage_list.blockSignals(False)
        if self.stages:
            self.stage_list.setCurrentRow(min(current, len(self.stages) - 1))

    def _stage_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.stages):
            return
        stage = self.stages[row]
        state = self._state["stages"][row]
        self.stage_title.setText(f"Stage {row + 1}: {stage.title}")
        self.stage_purpose.setText(stage.purpose)
        parts = ["<h3>What to do</h3><ol>"]
        parts.extend(f"<li>{value}</li>" for value in stage.actions)
        parts.append("</ol><h3>Required output</h3>")
        parts.append(f"<p>{stage.output}</p><h3>Check your work</h3><ul>")
        parts.extend(f"<li>{value}</li>" for value in stage.validation)
        parts.append("</ul><h3>Evidence to record</h3>")
        parts.append(f"<p>{stage.evidence}</p><h3>Common mistakes</h3><ul>")
        parts.extend(f"<li>{value}</li>" for value in stage.pitfalls)
        parts.append("</ul>")
        if stage.hints:
            parts.append("<h3>Progressive hints</h3><ul>")
            parts.extend(f"<li>{value}</li>" for value in stage.hints)
            parts.append("</ul>")
        self.stage_details.setHtml("".join(parts))
        self.stage_evidence.setPlainText(str(state.get("evidence") or ""))
        self.complete_stage_button.setText(
            "Reopen Stage" if bool(state.get("completed")) else "Mark Stage Complete"
        )

    def save_current_stage(self) -> None:
        row = self.stage_list.currentRow()
        if row < 0 or row >= len(self.stages):
            return
        self._state["stages"][row]["evidence"] = self.stage_evidence.toPlainText().strip()
        self._write_state()
        self.changed.emit(f"Applied Lab {self.number:02d} Stage {row + 1} evidence saved.")

    def toggle_current_stage(self) -> None:
        row = self.stage_list.currentRow()
        if row < 0 or row >= len(self.stages):
            return
        evidence = self.stage_evidence.toPlainText().strip()
        state = self._state["stages"][row]
        if not bool(state.get("completed")) and len(evidence) < 20:
            self.changed.emit(
                "Record specific evidence from this stage before marking it complete."
            )
            return
        state["evidence"] = evidence
        state["completed"] = not bool(state.get("completed"))
        self._write_state()
        self._rebuild_stage_list()
        self._stage_selected(row)
        self.refresh_progress()
        self.changed.emit(
            f"Applied Lab {self.number:02d} Stage {row + 1} "
            + ("completed." if state["completed"] else "reopened.")
        )

    def _render_brief(self) -> None:
        if not self.item:
            return
        deliverables = "".join(
            f"<li>{value}</li>" for value in self.item.get("deliverables", [])
        )
        validation = "".join(
            f"<li>{value}</li>" for value in self.item.get("validation", [])
        )
        self.brief_view.setHtml(
            f"<h2>{self.item['title']}</h2>"
            f"<p><b>Objective:</b> {self.item.get('objective', '')}</p>"
            f"<p><b>Skills:</b> {self.item.get('concepts', '')}</p>"
            f"<p><b>Estimated time:</b> {self.item.get('minutes', 0)} minutes</p>"
            "<h3>Required deliverables</h3><ul>"
            + deliverables
            + "</ul><h3>Definition of done</h3><ul>"
            + validation
            + "</ul><p><b>Solution policy:</b> This Studio gives process guidance and validation prompts, not the finished formula, query, code, measure, or answer.</p>"
        )

    def _load_final_fields(self) -> None:
        self.artifact_input.setText(str(self._state.get("artifact") or ""))
        self.takeaway_input.setPlainText(str(self._state.get("takeaway") or ""))
        checks = list(self._state.get("checks") or [])
        for index, box in enumerate(self.final_checks):
            box.setChecked(bool(checks[index]) if index < len(checks) else False)

    def save_all(self) -> None:
        row = self.stage_list.currentRow()
        if 0 <= row < len(self.stages):
            self._state["stages"][row]["evidence"] = self.stage_evidence.toPlainText().strip()
        self._state["artifact"] = self.artifact_input.text().strip()
        self._state["takeaway"] = self.takeaway_input.toPlainText().strip()
        self._state["checks"] = [box.isChecked() for box in self.final_checks]
        self._write_state()
        self.refresh_progress()
        if self.number is not None:
            self.changed.emit(f"Applied Lab {self.number:02d} Studio saved.")

    def refresh_progress(self) -> None:
        complete = sum(
            1 for row in self._state.get("stages", []) if bool(row.get("completed"))
        )
        self.progress_bar.setValue(complete)
        self.progress_text.setText(f"{complete} of {len(self.stages)} stages complete")

    def completion_issues(self) -> list[str]:
        self.save_all()
        issues: list[str] = []
        incomplete = [
            index + 1
            for index, row in enumerate(self._state.get("stages", []))
            if not bool(row.get("completed"))
        ]
        if incomplete:
            issues.append(
                "Complete every Studio stage. Remaining: "
                + ", ".join(str(value) for value in incomplete)
                + "."
            )
        if not str(self._state.get("artifact") or "").strip():
            issues.append("Record the saved artifact path or share link in Final Review.")
        if len(str(self._state.get("takeaway") or "").strip()) < 60:
            issues.append("Write a specific final takeaway and limitation in Final Review.")
        if not all(bool(value) for value in self._state.get("checks", [])):
            issues.append("Verify every Final Review checkbox.")
        return issues
