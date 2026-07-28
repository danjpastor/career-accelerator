from __future__ import annotations

"""Standalone weekly knowledge-check dialog."""

from typing import Callable
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from career_app.services import weekly_checks
from career_app.theme import COLORS


class WeeklyKnowledgeCheckDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        conn: sqlite3.Connection,
        week: int,
        passed_callback: Callable[[int, int], None] | None = None,
    ):
        super().__init__(parent)
        self.conn = conn
        self.week = int(week)
        self.check = weekly_checks.definition(self.week)
        self.passed_callback = passed_callback
        self.activities = list(self.check["activities"])
        self.answers: dict[str, str] = {}
        self.index = 0
        self.choice_group = QButtonGroup(self)
        self.choice_group.setExclusive(True)
        self.choice_buttons: list[QRadioButton] = []

        self.setWindowTitle(weekly_checks.title(self.week))
        self.setMinimumSize(760, 610)
        self.resize(860, 680)
        self._build_ui()
        self._show_question(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QFrame()
        header.setStyleSheet(
            "QFrame {background:#101d31;border:1px solid #2a3b59;border-radius:12px;}"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel(weekly_checks.title(self.week))
        title.setStyleSheet(f"font-size:17pt;font-weight:750;color:{COLORS['text']};")
        header_layout.addWidget(title)
        subtitle = QLabel(
            "Eight multiple-choice questions • Pass with 7 of 8 • Retake after reviewing missed topics"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color:{COLORS['muted']};")
        header_layout.addWidget(subtitle)
        self.progress = QProgressBar()
        self.progress.setRange(0, 8)
        self.progress.setTextVisible(True)
        header_layout.addWidget(self.progress)
        layout.addWidget(header)

        self.question_number = QLabel("")
        self.question_number.setStyleSheet(
            f"font-size:9pt;font-weight:700;color:{COLORS['purple']};"
        )
        layout.addWidget(self.question_number)

        self.question_title = QLabel("")
        self.question_title.setWordWrap(True)
        self.question_title.setStyleSheet(
            f"font-size:15pt;font-weight:750;color:{COLORS['text']};"
        )
        layout.addWidget(self.question_title)

        self.question_prompt = QLabel("")
        self.question_prompt.setWordWrap(True)
        self.question_prompt.setStyleSheet(
            f"font-size:11.5pt;color:{COLORS['text']};padding:4px 0 6px 0;"
        )
        layout.addWidget(self.question_prompt)

        answer_frame = QFrame()
        answer_frame.setStyleSheet(
            "QFrame {background:#0f1827;border:1px solid #263754;border-radius:10px;}"
        )
        answer_layout = QVBoxLayout(answer_frame)
        answer_layout.setContentsMargins(14, 12, 14, 12)
        answer_layout.setSpacing(8)
        for _ in range(4):
            button = QRadioButton("")
            button.setStyleSheet(
                f"QRadioButton {{color:{COLORS['text']};padding:8px;font-size:10.5pt;}}"
                "QRadioButton:hover {background:#18253a;border-radius:7px;}"
            )
            button.toggled.connect(self._answer_changed)
            self.choice_group.addButton(button)
            self.choice_buttons.append(button)
            answer_layout.addWidget(button)
        layout.addWidget(answer_frame)

        self.saved_status = QLabel("")
        self.saved_status.setStyleSheet(f"color:{COLORS['muted']};font-size:9pt;")
        layout.addWidget(self.saved_status)
        layout.addStretch(1)

        controls = QHBoxLayout()
        self.review_button = QPushButton("Review Last Attempt")
        self.review_button.setObjectName("Secondary")
        self.review_button.clicked.connect(self._review_last_attempt)
        self.review_button.setEnabled(weekly_checks.latest_attempt(self.conn, self.week) is not None)
        controls.addWidget(self.review_button)
        controls.addStretch(1)
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("Secondary")
        self.back_button.clicked.connect(self._back)
        controls.addWidget(self.back_button)
        self.next_button = QPushButton("Save & Continue →")
        self.next_button.setObjectName("Primary")
        self.next_button.clicked.connect(self._next_or_submit)
        controls.addWidget(self.next_button)
        layout.addLayout(controls)

    def _current_activity(self) -> dict:
        return self.activities[self.index]

    def _save_current_answer(self) -> None:
        checked = self.choice_group.checkedButton()
        if checked is None:
            return
        activity_id = str(self._current_activity()["activity_id"])
        self.answers[activity_id] = checked.text().strip()

    def _answer_changed(self, checked: bool) -> None:
        if checked:
            self._save_current_answer()
            answered = len([value for value in self.answers.values() if value.strip()])
            self.saved_status.setText(f"{answered} of 8 answers saved in this attempt.")
            self.progress.setValue(answered)

    def _show_question(self, index: int) -> None:
        self._save_current_answer()
        self.index = max(0, min(7, int(index)))
        item = self._current_activity()
        self.question_number.setText(f"QUESTION {self.index + 1} OF 8")
        self.question_title.setText(str(item.get("title") or f"Question {self.index + 1}"))
        self.question_prompt.setText(str(item.get("prompt") or ""))
        self.choice_group.setExclusive(False)
        for button in self.choice_buttons:
            button.setChecked(False)
        self.choice_group.setExclusive(True)
        selected = self.answers.get(str(item["activity_id"]), "")
        for button, option in zip(self.choice_buttons, item.get("answer_options") or []):
            button.setText(str(option))
            button.setChecked(str(option) == selected)
        self.back_button.setEnabled(self.index > 0)
        self.next_button.setText(
            "Submit Knowledge Check" if self.index == 7 else "Save & Continue →"
        )
        answered = len([value for value in self.answers.values() if value.strip()])
        self.progress.setValue(answered)
        self.saved_status.setText(f"{answered} of 8 answers saved in this attempt.")

    def _back(self) -> None:
        self._show_question(self.index - 1)

    def _next_or_submit(self) -> None:
        self._save_current_answer()
        if self.index < 7:
            self._show_question(self.index + 1)
            return
        unanswered = [
            index + 1
            for index, item in enumerate(self.activities)
            if not self.answers.get(str(item["activity_id"]), "").strip()
        ]
        if unanswered:
            QMessageBox.information(
                self,
                "Answer Every Question",
                "Complete all eight questions before submitting. Missing: "
                + ", ".join(str(value) for value in unanswered),
            )
            self._show_question(unanswered[0] - 1)
            return
        result = weekly_checks.record_attempt(self.conn, self.week, self.answers)
        self.review_button.setEnabled(True)
        if result.passed:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.setWindowTitle("Knowledge Check Passed")
            dialog.setText(f"Passed — {result.score} of {result.total} correct")
            dialog.setInformativeText(
                f"Week {self.week} is complete. The next week's skill-dependent work is now eligible to unlock."
            )
            dialog.exec()
            if self.passed_callback is not None:
                task_id = weekly_checks.task_id_for_week(self.conn, self.week)
                self.passed_callback(self.week, int(task_id or 0))
            self.accept()
            return

        missed = [item for item in result.review if not item["passed"]]
        summary = [
            f"Not passed — {result.score} of {result.total} correct.",
            "",
            "Review these topics before retaking:",
        ]
        summary.extend(f"• {item['title']}: {item['recommendation']}" for item in missed)
        self._show_review_dialog(result.review, "\n".join(summary), passed=False)
        first_missed = missed[0]["number"] if missed else 1
        self._show_question(int(first_missed) - 1)

    def _review_last_attempt(self) -> None:
        attempt = weekly_checks.latest_attempt(self.conn, self.week)
        if attempt is None:
            QMessageBox.information(self, "No Attempt Yet", "Submit the knowledge check first.")
            return
        self._show_review_dialog(
            tuple(attempt.get("review") or []),
            f"Attempt {attempt['attempt_number']} • {attempt['score']} of {attempt['total']} correct",
            passed=bool(attempt["passed"]),
        )

    def _show_review_dialog(self, review, heading: str, *, passed: bool) -> None:
        lines: list[str] = []
        for item in review:
            lines.extend(
                [
                    f"{item['number']}. {item['title']}",
                    f"Question: {item['prompt']}",
                    f"Your answer: {item['selected']}",
                    f"Correct answer: {item['correct']}",
                    "Result: Correct" if item["passed"] else "Result: Review Needed",
                ]
            )
            if not item["passed"]:
                lines.append(f"Recommended review: {item['recommendation']}")
            lines.append("")
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information if passed else QMessageBox.Icon.Warning)
        dialog.setWindowTitle(f"{weekly_checks.title(self.week)} — Attempt Review")
        dialog.setText(heading)
        dialog.setInformativeText(
            "Open the details to review every selected answer, the correct answer, and the recommended topic to revisit."
        )
        dialog.setDetailedText("\n".join(lines))
        dialog.exec()
