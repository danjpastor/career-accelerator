from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLayout,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.academy import AcademyService, ProgressState
from career_app.academy.models import (
    ActivityDefinition,
    AssessmentDefinition,
    LessonDefinition,
    SkillsLabDefinition,
)
from career_app.theme import COLORS
from career_app.ui.course_ui import CoursePageWidget, SqlCodeEditor
from career_app.ui.exercise_packs import FeedbackLabel
from career_app.ui.widgets import Card, make_card_scrollable


_SECTION_NAMES = (
    "Learning Paths",
    "Courses",
    "Practice",
    "Skills Lab",
    "Assessments",
    "Demonstrated Evidence",
)

_STATE_ICONS = {
    ProgressState.NOT_STARTED.value: "○",
    ProgressState.LEARNING.value: "◔",
    ProgressState.PRACTICED.value: "◐",
    ProgressState.MASTERED.value: "✓",
}

_ACTIVITY_ICONS = {
    "Not Started": "○",
    "In Progress": "◔",
    "Needs Review": "△",
    "Passed": "✓",
}


class AcceleratorAcademyWidget(QWidget):
    """Polished, program-neutral Academy workspace backed by external content."""

    def __init__(self, conn, repository_root: str | Path, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.repository_root = Path(repository_root)
        self.service = AcademyService(conn, self.repository_root)
        self.catalog = self.service.catalog
        self.settings = QSettings("DanjPastor", "Career Accelerator")

        self._practice_lesson: LessonDefinition | None = None
        self._practice_activity: ActivityDefinition | None = None
        self._assessment: AssessmentDefinition | None = None
        self._assessment_activity: ActivityDefinition | None = None
        self._assessment_answers: dict[str, str] = {}
        self._active_section = 0
        self._responsive_mode: str | None = None
        self._building_lists = False

        self._build_ui()
        self.refresh_all()
        self.open_recommendation()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 16)
        outer.setSpacing(10)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(16)
        heading_text = QVBoxLayout()
        heading_text.setSpacing(3)
        system_name = self.service.labels.get("system_name", "Accelerator Academy")
        title = QLabel(system_name)
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Build durable, job-ready capability through comprehensive instruction, original practice, "
            "independent assessment, and applied evidence."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        heading_text.addWidget(title)
        heading_text.addWidget(subtitle)
        heading_row.addLayout(heading_text, 1)

        recommendation_card = QFrame()
        recommendation_card.setObjectName("AcademyRecommendation")
        recommendation_card.setStyleSheet(
            "QFrame#AcademyRecommendation {background:#171D31;border:1px solid #4B3F76;"
            "border-radius:11px;}"
        )
        recommendation_layout = QVBoxLayout(recommendation_card)
        recommendation_layout.setContentsMargins(12, 8, 12, 8)
        recommendation_layout.setSpacing(2)
        recommendation_caption = QLabel("RECOMMENDED NEXT")
        recommendation_caption.setStyleSheet(
            "color:#BFA7F5;font-size:8pt;font-weight:700;"
        )
        self.recommendation_label = QLabel("Preparing your next step…")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet(
            "color:#FFFFFF;font-size:9.5pt;font-weight:650;"
        )
        recommendation_layout.addWidget(recommendation_caption)
        recommendation_layout.addWidget(self.recommendation_label)
        recommendation_card.setMaximumWidth(430)
        heading_row.addWidget(recommendation_card)
        outer.addLayout(heading_row)

        progress_host = QFrame()
        progress_host.setObjectName("AcademyProgressHost")
        progress_host.setStyleSheet(
            "QFrame#AcademyProgressHost {background:#11192A;border:1px solid #263754;border-radius:9px;}"
        )
        progress_layout = QHBoxLayout(progress_host)
        progress_layout.setContentsMargins(12, 7, 12, 7)
        progress_layout.setSpacing(10)
        self.progress_summary = QLabel("0 of 0 lessons mastered")
        self.progress_summary.setObjectName("Muted")
        progress_layout.addWidget(self.progress_summary)
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setTextVisible(False)
        self.overall_progress.setMaximumHeight(8)
        progress_layout.addWidget(self.overall_progress, 1)
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("font-weight:700;color:#FFFFFF;")
        progress_layout.addWidget(self.progress_percent)
        outer.addWidget(progress_host)

        self.section_nav = QWidget()
        self.section_nav.setObjectName("AcademySectionNav")
        self.section_nav_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.section_nav)
        self.section_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.section_nav_layout.setSpacing(8)
        self.section_group = QButtonGroup(self.section_nav)
        self.section_group.setExclusive(True)
        self.section_buttons: list[QPushButton] = []
        for index, label in enumerate(_SECTION_NAMES):
            button = QPushButton(label)
            button.setObjectName("AcademySectionButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, target=index: self._set_section(target) if checked else None
            )
            self.section_group.addButton(button, index)
            self.section_buttons.append(button)
            self.section_nav_layout.addWidget(button)
        self.section_nav_layout.addStretch(1)
        self.section_buttons[0].setChecked(True)
        self.section_nav.setStyleSheet(
            f"""
            QWidget#AcademySectionNav {{background:transparent;border:none;}}
            QPushButton#AcademySectionButton {{
                background:{COLORS['panel']};color:{COLORS['muted']};
                border:1px solid {COLORS['border']};border-radius:10px;
                padding:8px 13px;min-height:20px;font-weight:600;
            }}
            QPushButton#AcademySectionButton:hover {{
                background:{COLORS['panel_hover']};color:white;border-color:{COLORS['purple_soft']};
            }}
            QPushButton#AcademySectionButton:checked {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['magenta']},stop:1 {COLORS['purple']});
                color:white;border-color:#C07BFF;font-weight:700;
            }}
            """
        )
        outer.addWidget(self.section_nav)

        self.section_stack = QStackedWidget()
        self.section_stack.setMinimumWidth(0)
        self.section_stack.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.section_stack.addWidget(self._build_paths_page())
        self.section_stack.addWidget(self._build_courses_page())
        self.section_stack.addWidget(self._build_practice_page())
        self.section_stack.addWidget(self._build_lab_page())
        self.section_stack.addWidget(self._build_assessment_page())
        self.section_stack.addWidget(self._build_evidence_page())
        outer.addWidget(self.section_stack, 1)
        QTimer.singleShot(0, self._restore_splitters)

    def _build_paths_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        path = self.catalog.program.paths[0]
        summary = Card(path.title, path.description)
        summary.layout.setContentsMargins(16, 14, 16, 14)
        self.path_status = QLabel()
        self.path_status.setWordWrap(True)
        self.path_status.setStyleSheet(
            "background:#151E31;border:1px solid #33435F;border-radius:8px;padding:8px;color:#DCE4F3;"
        )
        summary.layout.addWidget(self.path_status)
        layout.addWidget(summary)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.path_splitter = splitter

        sequence = Card("Learning Path", "Complete lessons in prerequisite order. Mastery unlocks the next step.")
        self.path_lesson_list = QListWidget()
        self._style_learning_list(self.path_lesson_list)
        self.path_lesson_list.currentItemChanged.connect(self._show_path_lesson)
        sequence.layout.addWidget(self.path_lesson_list, 1)
        splitter.addWidget(sequence)

        detail = Card("Path Detail")
        self.path_lesson_view = CoursePageWidget()
        self.path_lesson_view.set_navigation(next_title=None, show_back=False)
        detail.layout.setContentsMargins(8, 8, 8, 8)
        detail.layout.addWidget(self.path_lesson_view, 1)
        self.path_open_button = QPushButton("Open Lesson in Practice")
        self.path_open_button.setObjectName("Primary")
        self.path_open_button.clicked.connect(self._open_selected_path_lesson)
        detail.layout.addWidget(self.path_open_button)
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)
        return page

    def _build_courses_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 8)
        content_layout.setSpacing(10)

        for course in self.catalog.courses():
            card = Card(course.title, course.description)
            card.layout.setContentsMargins(18, 16, 18, 16)
            metrics = QHBoxLayout()
            lesson_count = sum(len(module.lessons) for module in course.modules)
            activity_count = sum(len(lesson.activities) for module in course.modules for lesson in module.lessons)
            for text in (
                f"{lesson_count} lessons",
                f"{activity_count} practice activities",
                f"{course.estimated_minutes} minutes",
                f"{len(course.assessments)} checkpoint",
                f"{len(course.skills_labs)} Skills Lab",
            ):
                pill = QLabel(text)
                pill.setStyleSheet(
                    "background:#1A2440;border:1px solid #3A4970;border-radius:10px;"
                    "padding:4px 9px;color:#DCE4F3;font-size:9pt;font-weight:600;"
                )
                metrics.addWidget(pill)
            metrics.addStretch()
            card.layout.addLayout(metrics)

            if course.outcomes:
                outcomes = QLabel("COURSE OUTCOMES")
                outcomes.setStyleSheet("color:#A8B4C8;font-size:8.5pt;font-weight:700;")
                card.layout.addWidget(outcomes)
                outcome_text = QLabel("\n".join(f"✓  {item}" for item in course.outcomes))
                outcome_text.setWordWrap(True)
                outcome_text.setStyleSheet("color:#D8E1F0;line-height:1.35;")
                card.layout.addWidget(outcome_text)

            for module in course.modules:
                module_frame = QFrame()
                module_frame.setStyleSheet(
                    "QFrame {background:#111D31;border:1px solid #263754;border-radius:9px;}"
                )
                module_layout = QVBoxLayout(module_frame)
                module_layout.setContentsMargins(12, 10, 12, 10)
                module_title = QLabel(module.title)
                module_title.setObjectName("SectionTitle")
                module_layout.addWidget(module_title)
                if module.description:
                    description = QLabel(module.description)
                    description.setObjectName("Muted")
                    description.setWordWrap(True)
                    module_layout.addWidget(description)
                for lesson in module.lessons:
                    row = QFrame()
                    row.setStyleSheet("QFrame {background:transparent;border:none;}")
                    row_layout = QHBoxLayout(row)
                    row_layout.setContentsMargins(4, 5, 4, 5)
                    state = self.service.progress.lesson_state(lesson.lesson_id).value
                    icon = QLabel(_STATE_ICONS.get(state, "○"))
                    icon.setStyleSheet("color:#B679FF;font-size:13pt;font-weight:700;")
                    row_layout.addWidget(icon)
                    text = QLabel(f"{lesson.order}. {lesson.title}")
                    text.setWordWrap(True)
                    text.setStyleSheet("font-weight:650;color:#FFFFFF;")
                    row_layout.addWidget(text, 1)
                    meta = QLabel(f"{len(lesson.activities)} activities • {lesson.estimated_minutes} min • {state}")
                    meta.setObjectName("Muted")
                    row_layout.addWidget(meta)
                    open_button = QPushButton("Open")
                    open_button.setObjectName("Secondary")
                    open_button.clicked.connect(
                        lambda checked=False, lesson_id=lesson.lesson_id: self.open_lesson(lesson_id)
                    )
                    row_layout.addWidget(open_button)
                    module_layout.addWidget(row)
                card.layout.addWidget(module_frame)
            content_layout.addWidget(card)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _build_practice_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        toolbar = Card()
        toolbar.layout.setContentsMargins(10, 7, 10, 7)
        row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.practice_toolbar_row = row
        row.setSpacing(8)
        self.practice_breadcrumb = QLabel("Accelerator Academy  ›  Query Foundations")
        self.practice_breadcrumb.setStyleSheet("color:#B8C4D8;font-size:9.5pt;")
        row.addWidget(self.practice_breadcrumb, 1)
        lesson_label = QLabel("Lesson")
        lesson_label.setObjectName("Muted")
        row.addWidget(lesson_label)
        self.practice_lesson_combo = QComboBox()
        self.practice_lesson_combo.setMinimumWidth(210)
        for lesson in self.catalog.lessons():
            self.practice_lesson_combo.addItem(lesson.title, lesson.lesson_id)
        self.practice_lesson_combo.currentIndexChanged.connect(self._practice_lesson_changed)
        row.addWidget(self.practice_lesson_combo)
        toolbar.layout.addLayout(row)
        root.addWidget(toolbar)

        outer_splitter = QSplitter(Qt.Horizontal)
        outer_splitter.setChildrenCollapsible(False)
        outer_splitter.setHandleWidth(5)
        self.practice_outer_splitter = outer_splitter

        library = Card("Course Progress", "Use the lesson sequence and activity states to choose your next step.")
        library.setMinimumWidth(270)
        library.setMaximumWidth(410)
        self.lesson_progress_text = QLabel("0%")
        self.lesson_progress_text.setStyleSheet("font-size:20pt;font-weight:700;color:#FFFFFF;")
        library.layout.addWidget(self.lesson_progress_text)
        self.lesson_progress_bar = QProgressBar()
        self.lesson_progress_bar.setRange(0, 100)
        self.lesson_progress_bar.setTextVisible(False)
        self.lesson_progress_bar.setMaximumHeight(8)
        library.layout.addWidget(self.lesson_progress_bar)
        lesson_caption = QLabel("LESSONS")
        lesson_caption.setStyleSheet("color:#A8B4C8;font-size:8.5pt;font-weight:700;")
        library.layout.addWidget(lesson_caption)
        self.practice_lesson_list = QListWidget()
        self._style_learning_list(self.practice_lesson_list)
        self.practice_lesson_list.currentItemChanged.connect(self._practice_lesson_list_changed)
        library.layout.addWidget(self.practice_lesson_list, 2)
        activity_caption = QLabel("PRACTICE ACTIVITIES")
        activity_caption.setStyleSheet("color:#A8B4C8;font-size:8.5pt;font-weight:700;")
        library.layout.addWidget(activity_caption)
        self.practice_activity_list = QListWidget()
        self._style_learning_list(self.practice_activity_list)
        self.practice_activity_list.currentItemChanged.connect(self._practice_activity_list_changed)
        library.layout.addWidget(self.practice_activity_list, 3)
        outer_splitter.addWidget(library)

        workspace = QSplitter(Qt.Horizontal)
        workspace.setChildrenCollapsible(False)
        workspace.setHandleWidth(5)
        self.practice_workspace_splitter = workspace

        learn_card = Card("Learn")
        learn_card.layout.setContentsMargins(8, 8, 8, 8)
        self.practice_learn_view = CoursePageWidget()
        self.practice_learn_view.set_navigation(next_title=None, show_back=False)
        learn_card.layout.addWidget(self.practice_learn_view, 1)
        workspace.addWidget(learn_card)

        practice_card = Card("Practice")
        practice_card.layout.setContentsMargins(8, 8, 8, 8)
        practice_body = QWidget()
        practice_body_layout = QVBoxLayout(practice_body)
        practice_body_layout.setContentsMargins(4, 4, 4, 4)
        practice_body_layout.setSpacing(8)

        selector_row = QHBoxLayout()
        selector_label = QLabel("Practice question")
        selector_label.setObjectName("Muted")
        selector_row.addWidget(selector_label)
        self.practice_activity_combo = QComboBox()
        self.practice_activity_combo.currentIndexChanged.connect(self._practice_activity_changed)
        selector_row.addWidget(self.practice_activity_combo, 1)
        practice_body_layout.addLayout(selector_row)

        self.practice_lock = QLabel()
        self.practice_lock.setWordWrap(True)
        self.practice_lock.setStyleSheet(
            "background:#111D31;border:1px solid #263754;border-radius:8px;padding:7px;color:#C7D1E2;"
        )
        practice_body_layout.addWidget(self.practice_lock)

        self.practice_brief = CoursePageWidget()
        self.practice_brief.set_navigation(next_title=None, show_back=False)
        self.practice_brief.setMinimumHeight(240)
        self.practice_brief.setMaximumHeight(330)
        practice_body_layout.addWidget(self.practice_brief)

        self.practice_input_stack = QStackedWidget()
        self.practice_sql = SqlCodeEditor()
        self.practice_sql.setMinimumHeight(210)
        self.practice_sql.setPlaceholderText("Write your SQL here…")
        self.practice_choice_host = QWidget()
        choice_layout = QVBoxLayout(self.practice_choice_host)
        choice_layout.setContentsMargins(0, 4, 0, 4)
        choice_layout.addWidget(QLabel("Choose the best answer"))
        self.practice_choice = QComboBox()
        self.practice_choice.setMinimumHeight(38)
        choice_layout.addWidget(self.practice_choice)
        choice_layout.addStretch(1)
        self.practice_input_stack.addWidget(self.practice_sql)
        self.practice_input_stack.addWidget(self.practice_choice_host)
        practice_body_layout.addWidget(self.practice_input_stack, 1)

        action_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.practice_action_row = action_row
        self.practice_run = QPushButton("▶ Run Query")
        self.practice_run.setObjectName("Secondary")
        self.practice_run.clicked.connect(self._run_practice)
        self.practice_check = QPushButton("✓ Submit Solution")
        self.practice_check.setObjectName("Primary")
        self.practice_check.clicked.connect(self._check_practice)
        self.practice_hint = QPushButton("💡 Show Hint")
        self.practice_hint.setObjectName("Secondary")
        self.practice_hint.clicked.connect(self._show_practice_hint)
        self.practice_solution = QPushButton("View Solution")
        self.practice_solution.setObjectName("Secondary")
        self.practice_solution.clicked.connect(self._show_practice_solution)
        for button in (self.practice_run, self.practice_check, self.practice_hint, self.practice_solution):
            action_row.addWidget(button)
        action_row.addStretch(1)
        practice_body_layout.addLayout(action_row)

        self.practice_feedback = FeedbackLabel()
        practice_body_layout.addWidget(self.practice_feedback)
        self.practice_explanation = QLabel()
        self.practice_explanation.setWordWrap(True)
        self.practice_explanation.setStyleSheet(
            "background:#14233B;border:1px solid #52627F;border-radius:8px;padding:9px;color:#E7ECF8;"
        )
        self.practice_explanation.hide()
        practice_body_layout.addWidget(self.practice_explanation)

        self.practice_results = self._result_table()
        self.practice_results.setMinimumHeight(135)
        practice_body_layout.addWidget(self.practice_results, 1)

        practice_scroll = QScrollArea()
        practice_scroll.setWidgetResizable(True)
        practice_scroll.setFrameShape(QFrame.Shape.NoFrame)
        practice_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        practice_scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        practice_scroll.setWidget(practice_body)
        practice_card.layout.addWidget(practice_scroll, 1)
        workspace.addWidget(practice_card)
        workspace.setStretchFactor(0, 47)
        workspace.setStretchFactor(1, 53)
        outer_splitter.addWidget(workspace)
        outer_splitter.setStretchFactor(0, 1)
        outer_splitter.setStretchFactor(1, 3)
        root.addWidget(outer_splitter, 1)
        return page

    def _build_lab_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        toolbar = Card()
        toolbar.layout.setContentsMargins(10, 7, 10, 7)
        row = QHBoxLayout()
        row.addWidget(QLabel("Accelerator Academy  ›  Skills Lab"), 1)
        self.lab_status_combo = QComboBox()
        self.lab_status_combo.addItems(("Not Started", "In Progress", "Completed"))
        self.lab_status_combo.setMinimumWidth(130)
        toolbar.layout.addLayout(row)
        outer.addWidget(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)
        self.lab_splitter = splitter

        library = Card("Skills Lab", "Apply the course concepts in a stakeholder-facing assignment.")
        library.setMinimumWidth(270)
        library.setMaximumWidth(420)
        self.lab_list = QListWidget()
        self._style_learning_list(self.lab_list)
        for lab in self.catalog.skills_labs():
            item = QListWidgetItem(f"◆  {lab.title}\n{lab.estimated_minutes} minutes • Applied challenge")
            item.setData(Qt.ItemDataRole.UserRole, lab.lab_id)
            self.lab_list.addItem(item)
        self.lab_list.currentItemChanged.connect(self._lab_selected)
        library.layout.addWidget(self.lab_list, 1)
        self.lab_lock = QLabel()
        self.lab_lock.setWordWrap(True)
        self.lab_lock.setStyleSheet(
            "background:#111D31;border:1px solid #263754;border-radius:8px;padding:8px;color:#D4DCEC;"
        )
        library.layout.addWidget(self.lab_lock)
        splitter.addWidget(library)

        workspace = Card("Learn")
        workspace.layout.setContentsMargins(8, 8, 8, 8)
        self.lab_learn_view = CoursePageWidget()
        # The Skills Lab embeds editors and result tables beneath substantial
        # course material. Enforce the course page's natural minimum height so
        # the internal scroll area expands instead of compressing headings.
        self.lab_learn_view.page_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.lab_practice_panel = QWidget()
        lab_practice_layout = QVBoxLayout(self.lab_practice_panel)
        lab_practice_layout.setContentsMargins(0, 4, 0, 0)
        lab_practice_layout.setSpacing(9)

        sql_frame = QFrame()
        sql_frame.setStyleSheet("QFrame {background:#111D31;border:1px solid #263754;border-radius:9px;}")
        sql_layout = QVBoxLayout(sql_frame)
        sql_layout.setContentsMargins(12, 10, 12, 10)
        sql_title = QLabel("SQL Submission")
        sql_title.setObjectName("SectionTitle")
        sql_layout.addWidget(sql_title)
        self.lab_sql = SqlCodeEditor()
        self.lab_sql.setMinimumHeight(220)
        sql_layout.addWidget(self.lab_sql)
        lab_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.lab_action_row = lab_actions
        self.lab_run = QPushButton("▶ Run SQL")
        self.lab_run.setObjectName("Secondary")
        self.lab_run.clicked.connect(self._run_lab)
        self.lab_submit = QPushButton("✓ Validate Lab")
        self.lab_submit.setObjectName("Primary")
        self.lab_submit.clicked.connect(self._submit_lab)
        lab_actions.addWidget(self.lab_run)
        lab_actions.addWidget(self.lab_submit)
        lab_actions.addStretch(1)
        sql_layout.addLayout(lab_actions)
        self.lab_feedback = FeedbackLabel()
        sql_layout.addWidget(self.lab_feedback)
        self.lab_results = self._result_table()
        self.lab_results.setMinimumHeight(140)
        sql_layout.addWidget(self.lab_results)
        lab_practice_layout.addWidget(sql_frame)

        evidence_frame = QFrame()
        evidence_frame.setStyleSheet("QFrame {background:#111D31;border:1px solid #263754;border-radius:9px;}")
        evidence_layout = QVBoxLayout(evidence_frame)
        evidence_layout.setContentsMargins(12, 10, 12, 10)
        findings_title = QLabel("Findings and Evidence Notes")
        findings_title.setObjectName("SectionTitle")
        evidence_layout.addWidget(findings_title)
        findings_help = QLabel(
            "Write at least three concise findings. State the observation, cite what the result shows, and explain why it matters."
        )
        findings_help.setObjectName("Muted")
        findings_help.setWordWrap(True)
        evidence_layout.addWidget(findings_help)
        self.lab_notes = QTextEdit()
        self.lab_notes.setMinimumHeight(130)
        self.lab_notes.setPlaceholderText(
            "1. Observation and evidence…\n2. Observation and evidence…\n3. Observation and evidence…"
        )
        evidence_layout.addWidget(self.lab_notes)
        lab_practice_layout.addWidget(evidence_frame)

        self.lab_learn_view.set_embedded_widget(self.lab_practice_panel)
        self.lab_learn_view.set_header_controls(self.lab_status_combo)
        self.lab_learn_view.header_actions_host.setStyleSheet("background:transparent;border:none;")
        self.lab_learn_view.header_actions_host.setMaximumHeight(42)
        self.lab_learn_view.header_actions_host.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        self.lab_save = QPushButton("Save Progress")
        self.lab_save.setObjectName("Secondary")
        self.lab_save.clicked.connect(self._save_lab_progress)
        self.lab_complete = QPushButton("Mark Complete")
        self.lab_complete.setObjectName("Primary")
        self.lab_complete.clicked.connect(self._submit_lab)
        self.lab_learn_view.set_footer_controls(self.lab_save, self.lab_complete)
        self.lab_learn_view.set_navigation(next_title=None, show_back=False)
        workspace.layout.addWidget(self.lab_learn_view, 1)
        splitter.addWidget(workspace)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)
        return page

    def _build_assessment_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        assessment = self.catalog.assessments()[0]
        self._assessment = assessment
        intro = Card(assessment.title, assessment.description)
        intro.layout.setContentsMargins(16, 12, 16, 12)
        intro_row = QHBoxLayout()
        self.assessment_lock = QLabel()
        self.assessment_lock.setWordWrap(True)
        intro_row.addWidget(self.assessment_lock, 1)
        pass_pill = QLabel(f"Pass: {round(assessment.passing_score * 100)}%")
        pass_pill.setStyleSheet(
            "background:#1A2440;border:1px solid #3A4970;border-radius:10px;padding:4px 9px;font-weight:700;"
        )
        intro_row.addWidget(pass_pill)
        time_pill = QLabel(f"{assessment.estimated_minutes} minutes")
        time_pill.setStyleSheet(
            "background:#1A2440;border:1px solid #3A4970;border-radius:10px;padding:4px 9px;font-weight:700;"
        )
        intro_row.addWidget(time_pill)
        intro.layout.addLayout(intro_row)
        outer.addWidget(intro)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.assessment_splitter = splitter
        question_card = Card("Checkpoint Questions")
        self.assessment_question_list = QListWidget()
        self._style_learning_list(self.assessment_question_list)
        for index, activity in enumerate(assessment.activities, start=1):
            item = QListWidgetItem(f"{index}. {activity.title}")
            item.setData(Qt.ItemDataRole.UserRole, activity.activity_id)
            self.assessment_question_list.addItem(item)
        self.assessment_question_list.currentItemChanged.connect(self._assessment_question_selected)
        question_card.layout.addWidget(self.assessment_question_list, 1)
        self.assessment_progress = QProgressBar()
        self.assessment_progress.setRange(0, len(assessment.activities))
        self.assessment_progress.setFormat("%v of %m answered")
        question_card.layout.addWidget(self.assessment_progress)
        splitter.addWidget(question_card)

        work_card = Card("Assessment")
        work_card.layout.setContentsMargins(8, 8, 8, 8)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(4, 4, 4, 4)
        body_layout.setSpacing(8)
        self.assessment_brief = CoursePageWidget()
        self.assessment_brief.page_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.assessment_brief.set_navigation(next_title=None, show_back=False)
        self.assessment_brief.setMinimumHeight(220)
        self.assessment_brief.setMaximumHeight(300)
        body_layout.addWidget(self.assessment_brief)
        self.assessment_sql = SqlCodeEditor()
        self.assessment_sql.setMinimumHeight(230)
        body_layout.addWidget(self.assessment_sql, 1)
        assessment_actions = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.assessment_action_row = assessment_actions
        self.assessment_save = QPushButton("Save Answer")
        self.assessment_save.setObjectName("Secondary")
        self.assessment_save.clicked.connect(self._save_assessment_answer)
        self.assessment_next = QPushButton("Next Question  →")
        self.assessment_next.setObjectName("Secondary")
        self.assessment_next.clicked.connect(self._next_assessment_question)
        self.assessment_submit = QPushButton("Submit Checkpoint")
        self.assessment_submit.setObjectName("Primary")
        self.assessment_submit.clicked.connect(self._submit_assessment)
        assessment_actions.addWidget(self.assessment_save)
        assessment_actions.addWidget(self.assessment_next)
        assessment_actions.addStretch(1)
        assessment_actions.addWidget(self.assessment_submit)
        body_layout.addLayout(assessment_actions)
        self.assessment_feedback = FeedbackLabel()
        body_layout.addWidget(self.assessment_feedback)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        scroll.setWidget(body)
        work_card.layout.addWidget(scroll, 1)
        splitter.addWidget(work_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)
        return page

    def _build_evidence_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)
        summary = Card(
            self.service.labels.get("evidence_label", "Demonstrated Evidence"),
            "Validated independent work and Skills Lab artifacts appear here as proof of job-relevant capability.",
        )
        self.evidence_summary = QLabel()
        self.evidence_summary.setWordWrap(True)
        self.evidence_summary.setStyleSheet("font-size:16pt;font-weight:700;color:#FFFFFF;")
        summary.layout.addWidget(self.evidence_summary)
        outer.addWidget(summary)
        card = Card("Validated Academy Evidence")
        self.evidence_table = QTableWidget()
        self.evidence_table.setColumnCount(7)
        self.evidence_table.setHorizontalHeaderLabels(
            ["Skill", "Source", "Difficulty", "Dataset", "Competency", "Artifact", "Completed"]
        )
        self.evidence_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.evidence_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.evidence_table.setAlternatingRowColors(True)
        self.evidence_table.setShowGrid(False)
        self.evidence_table.verticalHeader().setVisible(False)
        self.evidence_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.evidence_table.horizontalHeader().setStretchLastSection(True)
        self.evidence_table.setStyleSheet(self._table_style())
        card.layout.addWidget(self.evidence_table, 1)
        outer.addWidget(card, 1)
        return page

    # --------------------------------------------------------------- helpers
    def _set_section(self, index: int) -> None:
        index = max(0, min(self.section_stack.count() - 1, int(index)))
        self._active_section = index
        self.section_stack.setCurrentIndex(index)
        button = self.section_group.button(index)
        if button is not None:
            button.setChecked(True)
        if index == 2 and self._practice_lesson is None and self.catalog.lessons():
            self.open_lesson(self.catalog.lessons()[0].lesson_id)
        if index == 3 and self.lab_list.count() and self.lab_list.currentRow() < 0:
            self.lab_list.setCurrentRow(0)
        if index == 4 and self.assessment_question_list.count() and self.assessment_question_list.currentRow() < 0:
            self.assessment_question_list.setCurrentRow(0)
        if index == 5:
            self._refresh_evidence()

    @staticmethod
    def _style_learning_list(widget: QListWidget) -> None:
        widget.setWordWrap(True)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        widget.setSpacing(3)
        widget.setAlternatingRowColors(False)

    @staticmethod
    def _table_style() -> str:
        return (
            f"QTableWidget {{background:{COLORS.get('surface_alt', '#111A2C')};"
            "alternate-background-color:#121F34;color:#FFFFFF;"
            f"border:1px solid {COLORS.get('border', '#2B3656')};border-radius:8px;}}"
            "QHeaderView::section {background:#1B2540;color:#FFFFFF;padding:7px;"
            "border:none;border-right:1px solid #3a3d5e;font-weight:600;}"
        )

    def _result_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(self._table_style())
        return table

    def _restore_splitters(self) -> None:
        self.practice_outer_splitter.setSizes([330, 1040])
        self.practice_workspace_splitter.setSizes([470, 530])
        self.path_splitter.setSizes([360, 760])
        self.lab_splitter.setSizes([350, 760])
        self.assessment_splitter.setSizes([330, 780])

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        width = max(0, event.size().width())
        mode = "compact" if width < 900 else "medium" if width < 1220 else "wide"
        if mode == self._responsive_mode:
            return
        self._responsive_mode = mode
        self.section_nav_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if mode == "compact" else QBoxLayout.Direction.LeftToRight
        )
        self.practice_toolbar_row.setDirection(
            QBoxLayout.Direction.TopToBottom if width < 760 else QBoxLayout.Direction.LeftToRight
        )
        for layout in (self.practice_action_row, self.lab_action_row, self.assessment_action_row):
            layout.setDirection(
                QBoxLayout.Direction.TopToBottom if width < 700 else QBoxLayout.Direction.LeftToRight
            )
        if mode == "compact":
            self.practice_outer_splitter.setOrientation(Qt.Orientation.Vertical)
            self.practice_workspace_splitter.setOrientation(Qt.Orientation.Vertical)
            self.path_splitter.setOrientation(Qt.Orientation.Vertical)
            self.lab_splitter.setOrientation(Qt.Orientation.Vertical)
            self.assessment_splitter.setOrientation(Qt.Orientation.Vertical)
        else:
            self.practice_outer_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.practice_workspace_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.path_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.lab_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.assessment_splitter.setOrientation(Qt.Orientation.Horizontal)
            QTimer.singleShot(0, self._restore_splitters)

    # --------------------------------------------------------------- refresh
    def refresh_all(self) -> None:
        summary = self.service.completion_summary()
        total = max(1, summary["total"])
        percent = round(100 * summary["mastered"] / total)
        self.overall_progress.setValue(percent)
        self.progress_percent.setText(f"{percent}%")
        self.progress_summary.setText(
            f"{summary['mastered']} of {summary['total']} lessons mastered • "
            f"{summary['practiced']} practiced • {summary['learning']} learning"
        )
        self.path_status.setText(
            f"Progress: {summary['mastered']}/{summary['total']} mastered. "
            "Lessons unlock only after required skills are demonstrated through validated independent work."
        )
        recommendation = self.service.next_recommendation()
        self.recommendation_label.setText(
            recommendation.title if recommendation else "Path complete — review your evidence and continue applied work."
        )
        self._refresh_path_list()
        self._refresh_practice_lists()
        self._refresh_locks()
        self._refresh_evidence()

    def _refresh_path_list(self) -> None:
        selected = self.path_lesson_list.currentItem()
        selected_id = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        self.path_lesson_list.blockSignals(True)
        self.path_lesson_list.clear()
        for lesson in self.catalog.lessons():
            state = self.service.progress.lesson_state(lesson.lesson_id).value
            unlocked, _missing = self.service.lesson_unlocked(lesson.lesson_id)
            icon = _STATE_ICONS.get(state, "○") if unlocked else "🔒"
            item = QListWidgetItem(
                f"{icon}  Lesson {lesson.order}: {lesson.title}\n"
                f"{state} • {len(lesson.activities)} activities • {lesson.estimated_minutes} min"
            )
            item.setData(Qt.ItemDataRole.UserRole, lesson.lesson_id)
            self.path_lesson_list.addItem(item)
            if lesson.lesson_id == selected_id:
                self.path_lesson_list.setCurrentItem(item)
        self.path_lesson_list.blockSignals(False)
        if self.path_lesson_list.currentRow() < 0 and self.path_lesson_list.count():
            self.path_lesson_list.setCurrentRow(0)

    def _refresh_practice_lists(self) -> None:
        self._building_lists = True
        try:
            selected_lesson = self._practice_lesson.lesson_id if self._practice_lesson else None
            self.practice_lesson_list.blockSignals(True)
            self.practice_lesson_list.clear()
            for lesson in self.catalog.lessons():
                state = self.service.progress.lesson_state(lesson.lesson_id).value
                unlocked, _missing = self.service.lesson_unlocked(lesson.lesson_id)
                icon = _STATE_ICONS.get(state, "○") if unlocked else "🔒"
                item = QListWidgetItem(f"{icon}  {lesson.order}. {lesson.title}\n{state}")
                item.setData(Qt.ItemDataRole.UserRole, lesson.lesson_id)
                self.practice_lesson_list.addItem(item)
                if lesson.lesson_id == selected_lesson:
                    self.practice_lesson_list.setCurrentItem(item)
            self.practice_lesson_list.blockSignals(False)
            if self._practice_lesson:
                self._populate_activity_list(self._practice_lesson)
                state = self.service.progress.lesson_state(self._practice_lesson.lesson_id).value
                rank = ProgressState(state).rank
                lesson_percent = round(100 * rank / 3)
                self.lesson_progress_bar.setValue(lesson_percent)
                self.lesson_progress_text.setText(f"{lesson_percent}% • {state}")
        finally:
            self._building_lists = False

    def _populate_activity_list(self, lesson: LessonDefinition) -> None:
        selected_activity = self._practice_activity.activity_id if self._practice_activity else None
        self.practice_activity_list.blockSignals(True)
        self.practice_activity_list.clear()
        self.practice_activity_combo.blockSignals(True)
        self.practice_activity_combo.clear()
        for index, activity in enumerate(lesson.activities, start=1):
            row = self.service.activity_progress(lesson.lesson_id, activity.activity_id)
            state = row["state"] if row else "Not Started"
            icon = _ACTIVITY_ICONS.get(state, "○")
            item = QListWidgetItem(
                f"{icon}  {index}. {activity.title}\n"
                f"{activity.activity_type.value.title()} • {activity.estimated_minutes} min • {state}"
            )
            item.setData(Qt.ItemDataRole.UserRole, activity.activity_id)
            self.practice_activity_list.addItem(item)
            self.practice_activity_combo.addItem(activity.title, activity.activity_id)
            if activity.activity_id == selected_activity:
                self.practice_activity_list.setCurrentItem(item)
                self.practice_activity_combo.setCurrentIndex(index - 1)
        self.practice_activity_combo.blockSignals(False)
        self.practice_activity_list.blockSignals(False)

    # --------------------------------------------------------------- routing
    def open_recommendation(self) -> None:
        recommendation = self.service.next_recommendation()
        if recommendation is None:
            return
        parts = recommendation.target_key.split(":")
        if len(parts) >= 3 and parts[1] == "lesson":
            self.open_lesson(parts[2])
        elif len(parts) >= 4 and parts[1] == "activity":
            self.open_lesson(parts[2], parts[3])
        elif len(parts) >= 3 and parts[1] == "assessment":
            self._set_section(4)
        elif len(parts) >= 3 and parts[1] == "skills_lab":
            self._set_section(3)

    def open_lesson(self, lesson_id: str, activity_id: str | None = None) -> None:
        unlocked, missing = self.service.lesson_unlocked(lesson_id)
        if not unlocked:
            QMessageBox.information(
                self,
                "Lesson Locked",
                "Master these skills first:\n\n" + "\n".join(f"• {item}" for item in missing),
            )
            return
        self.service.open_lesson(lesson_id)
        lesson = self.catalog.lesson(lesson_id)
        self._practice_lesson = lesson
        lesson_index = self.practice_lesson_combo.findData(lesson_id)
        if lesson_index >= 0:
            self.practice_lesson_combo.blockSignals(True)
            self.practice_lesson_combo.setCurrentIndex(lesson_index)
            self.practice_lesson_combo.blockSignals(False)
        self._render_lesson(lesson)
        self._populate_activity_list(lesson)
        target_activity = activity_id or (lesson.activities[0].activity_id if lesson.activities else None)
        if target_activity:
            self._select_activity(target_activity)
        self._set_section(2)
        self.refresh_all()

    def _practice_lesson_changed(self) -> None:
        if self._building_lists:
            return
        lesson_id = self.practice_lesson_combo.currentData()
        if lesson_id:
            self.open_lesson(str(lesson_id))

    def _practice_lesson_list_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if self._building_lists or current is None:
            return
        lesson_id = current.data(Qt.ItemDataRole.UserRole)
        if lesson_id and (self._practice_lesson is None or lesson_id != self._practice_lesson.lesson_id):
            self.open_lesson(str(lesson_id))

    def _practice_activity_list_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if self._building_lists or current is None:
            return
        activity_id = current.data(Qt.ItemDataRole.UserRole)
        if activity_id:
            self._select_activity(str(activity_id))

    def _practice_activity_changed(self) -> None:
        if self._building_lists:
            return
        activity_id = self.practice_activity_combo.currentData()
        if activity_id:
            self._select_activity(str(activity_id))

    def _select_activity(self, activity_id: str) -> None:
        self._save_current_practice()
        if self._practice_lesson is None:
            return
        activity = next(
            (item for item in self._practice_lesson.activities if item.activity_id == activity_id),
            None,
        )
        if activity is None:
            return
        self._practice_activity = activity
        combo_index = self.practice_activity_combo.findData(activity_id)
        if combo_index >= 0 and combo_index != self.practice_activity_combo.currentIndex():
            self.practice_activity_combo.blockSignals(True)
            self.practice_activity_combo.setCurrentIndex(combo_index)
            self.practice_activity_combo.blockSignals(False)
        for index in range(self.practice_activity_list.count()):
            item = self.practice_activity_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == activity_id:
                self.practice_activity_list.blockSignals(True)
                self.practice_activity_list.setCurrentItem(item)
                self.practice_activity_list.blockSignals(False)
                break
        self._render_activity(activity)

    # --------------------------------------------------------------- render
    def _render_lesson(self, lesson: LessonDefinition) -> None:
        objectives = "\n".join(f"- {item}" for item in lesson.objectives)
        takeaways = "\n".join(f"- {item}" for item in lesson.key_takeaways)
        markdown = lesson.content_markdown
        if objectives and "## Learning objectives" not in markdown:
            markdown = markdown.replace(
                "\n## ", f"\n## Learning objectives\n{objectives}\n\n## ", 1
            )
        if takeaways:
            markdown += f"\n\n## Key takeaways\n{takeaways}\n"
        subtitle = f"Beginner • {lesson.estimated_minutes} minutes • {len(lesson.activities)} practice activities"
        self.practice_learn_view.set_markdown(
            markdown,
            eyebrow="QUERY FOUNDATIONS",
            subtitle=subtitle,
            bookmarked=False,
        )
        self.practice_learn_view.set_navigation(next_title=None, show_back=False)
        self.practice_breadcrumb.setText(f"Accelerator Academy  ›  Query Foundations  ›  {lesson.title}")

    def _activity_markdown(self, activity: ActivityDefinition) -> str:
        p = dict(activity.presentation)
        scenario = str(p.get("scenario") or "Practice scenario")
        introduction = str(p.get("introduction") or "Apply the lesson concept to the following task.")
        task = str(p.get("task") or activity.prompt)
        table = str(p.get("table") or activity.validator.get("dataset_id") or "Provided dataset")
        requirements = p.get("requirements") or []
        expected_output = str(p.get("expected_output") or "Return the requested result.")
        skills = p.get("skills_practiced") or []
        common_errors = p.get("common_errors") or []
        requirement_text = "\n".join(f"- {item}" for item in requirements) or "- Follow the task exactly."
        skill_text = ", ".join(f"`{item}`" for item in skills) or activity.activity_type.value.title()
        error_text = ""
        if common_errors:
            error_text = "\n\n## Common mistakes to avoid\n" + "\n".join(f"- {item}" for item in common_errors)
        return (
            f"# {activity.title}\n\n"
            f"> **Scenario:** {scenario}\n\n"
            f"{introduction}\n\n"
            f"## Available data\n`{table}`\n\n"
            f"## Your task\n> {task}\n\n"
            f"## Requirements\n{requirement_text}\n\n"
            f"### Expected output\n{expected_output}\n\n"
            f"### Skills practiced\n{skill_text}"
            f"{error_text}\n"
        )

    def _render_activity(self, activity: ActivityDefinition) -> None:
        self.practice_brief.set_markdown(
            self._activity_markdown(activity),
            eyebrow=activity.activity_type.value.upper(),
            subtitle=f"{activity.difficulty.title()} • About {activity.estimated_minutes} minutes",
            bookmarked=False,
        )
        self.practice_brief.set_navigation(next_title=None, show_back=False)
        row = self.service.activity_progress(self._practice_lesson.lesson_id, activity.activity_id)
        answer = str(row["answer_text"] or "") if row else ""
        if not answer:
            answer = activity.starter
        recognition = activity.runtime == "recognition"
        self.practice_input_stack.setCurrentIndex(1 if recognition else 0)
        self.practice_choice.blockSignals(True)
        self.practice_choice.clear()
        if recognition:
            self.practice_choice.addItem("Select an answer…")
            self.practice_choice.addItems(activity.answer_options)
            if answer:
                index = self.practice_choice.findText(answer)
                if index >= 0:
                    self.practice_choice.setCurrentIndex(index)
        self.practice_choice.blockSignals(False)
        if not recognition:
            self.practice_sql.blockSignals(True)
            self.practice_sql.setPlainText(answer)
            self.practice_sql.blockSignals(False)
        unlocked, missing = self.service.lesson_unlocked(self._practice_lesson.lesson_id)
        self.practice_lock.setText(
            "✓ Prerequisites satisfied • Your answer is saved when you switch activities."
            if unlocked
            else "🔒 Locked • Master first: " + ", ".join(missing)
        )
        self.practice_run.setVisible(not recognition)
        self.practice_run.setEnabled(unlocked and not recognition)
        for button in (self.practice_check, self.practice_hint, self.practice_solution):
            button.setEnabled(unlocked)
        state = row["state"] if row else "Not Started"
        self.practice_feedback.setText(f"Current status: {state}")
        self.practice_explanation.hide()
        self._show_result(self.practice_results, (), ())

    # --------------------------------------------------------------- practice
    def _practice_answer(self) -> str:
        if self._practice_activity and self._practice_activity.runtime == "recognition":
            text = self.practice_choice.currentText()
            return "" if text == "Select an answer…" else text
        return self.practice_sql.toPlainText()

    def _save_current_practice(self) -> None:
        if self._practice_lesson is None or self._practice_activity is None:
            return
        answer = self._practice_answer()
        if answer.strip():
            self.service.progress.save_answer(
                self._practice_lesson.lesson_id,
                self._practice_activity,
                answer,
            )

    def _run_practice(self) -> None:
        if self._practice_activity is None:
            return
        result = self.service.run_activity(self._practice_activity, self._practice_answer())
        prefix = "✅ " if result.passed else "❌ "
        self.practice_feedback.setText(prefix + result.feedback)
        self._show_result(self.practice_results, result.columns, result.rows)
        if not result.passed:
            self.practice_sql.navigate_to_error(result.feedback)

    def _check_practice(self) -> None:
        if self._practice_lesson is None or self._practice_activity is None:
            return
        result = self.service.validate_activity(
            self._practice_lesson,
            self._practice_activity,
            self._practice_answer(),
        )
        prefix = "✅ " if result.passed else "❌ "
        self.practice_feedback.setText(prefix + result.feedback)
        self._show_result(self.practice_results, result.columns, result.rows)
        if result.passed:
            explanation = str(self._practice_activity.presentation.get("after_correct") or "")
            if explanation:
                self.practice_explanation.setText("Why this works\n\n" + explanation)
                self.practice_explanation.show()
        else:
            self.practice_sql.navigate_to_error(result.feedback)
        self.refresh_all()
        self._render_activity(self._practice_activity)
        if result.passed:
            explanation = str(self._practice_activity.presentation.get("after_correct") or "")
            if explanation:
                self.practice_explanation.setText("Why this works\n\n" + explanation)
                self.practice_explanation.show()
            self.practice_feedback.setText("✅ " + result.feedback)
            self._show_result(self.practice_results, result.columns, result.rows)

    def _show_practice_hint(self) -> None:
        if self._practice_lesson is None or self._practice_activity is None:
            return
        level, hint = self.service.reveal_hint(
            self._practice_lesson.lesson_id,
            self._practice_activity,
        )
        self.practice_feedback.setText(f"💡 Hint {level}: {hint}")

    def _show_practice_solution(self) -> None:
        if self._practice_lesson is None or self._practice_activity is None:
            return
        solution = self.service.reveal_solution(
            self._practice_lesson.lesson_id,
            self._practice_activity,
        )
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Official Solution")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText(
            "The full solution is shown below. Your editor has not been overwritten. "
            "This attempt cannot grant mastery after the solution is viewed."
        )
        dialog.setDetailedText(solution)
        dialog.exec()
        self.practice_feedback.setText(
            "💡 Solution viewed. Study the structure, close the solution, and rebuild the query independently."
        )
        self.refresh_all()

    # ---------------------------------------------------------------- paths
    def _show_path_lesson(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        lesson_id = current.data(Qt.ItemDataRole.UserRole)
        lesson = self.catalog.lesson(str(lesson_id))
        state = self.service.progress.lesson_state(lesson.lesson_id).value
        unlocked, missing = self.service.lesson_unlocked(lesson.lesson_id)
        objectives = "\n".join(f"- {item}" for item in lesson.objectives)
        markdown = (
            f"# {lesson.title}\n\n"
            f"> **Current state:** {state}\n\n"
            f"{lesson.description}\n\n"
            f"## Learning objectives\n{objectives}\n\n"
            f"## Practice structure\n"
            f"This lesson contains {len(lesson.activities)} activities across recognition, guided, independent, "
            f"debugging, transfer, or mastery formats.\n\n"
            f"## Unlock status\n"
            + ("Ready to begin." if unlocked else "Master first: " + ", ".join(missing))
        )
        self.path_lesson_view.set_markdown(
            markdown,
            eyebrow="LEARNING PATH",
            subtitle=f"Lesson {lesson.order} • {lesson.estimated_minutes} minutes",
            bookmarked=False,
        )
        self.path_lesson_view.set_navigation(next_title=None, show_back=False)
        self.path_open_button.setEnabled(unlocked)

    def _open_selected_path_lesson(self) -> None:
        item = self.path_lesson_list.currentItem()
        if item is not None:
            self.open_lesson(str(item.data(Qt.ItemDataRole.UserRole)))

    # ------------------------------------------------------------------ lab
    def _lab_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        lab = self.catalog.skills_lab(str(current.data(Qt.ItemDataRole.UserRole)))
        self._render_lab(lab)

    def _render_lab(self, lab: SkillsLabDefinition) -> None:
        markdown = lab.brief_markdown or f"# {lab.title}\n\n{lab.description}\n\n## Your task\n{lab.prompt}"
        if lab.deliverables:
            markdown += "\n\n## Required deliverables\n" + "\n".join(f"- {item}" for item in lab.deliverables)
        if lab.acceptance_criteria:
            markdown += "\n\n## Acceptance criteria\n" + "\n".join(f"- {item}" for item in lab.acceptance_criteria)
        if lab.rubric:
            markdown += "\n\n## Evaluation rubric\n" + "\n".join(
                f"- **{key.replace('_', ' ').title()}:** {value}" for key, value in lab.rubric.items()
            )
        if lab.reflection_questions:
            markdown += "\n\n## Reflection questions\n" + "\n".join(f"- {item}" for item in lab.reflection_questions)
        self.lab_learn_view.set_markdown(
            markdown,
            eyebrow="SKILLS LAB",
            subtitle=f"Applied challenge • About {lab.estimated_minutes} minutes",
            bookmarked=False,
        )
        self.lab_learn_view.set_navigation(next_title=None, show_back=False)
        row = self.conn.execute(
            "SELECT answer_text,notes,validation_status FROM academy_submissions WHERE item_type='skills_lab' AND item_id=? ORDER BY submission_id DESC LIMIT 1",
            (lab.lab_id,),
        ).fetchone()
        self.lab_sql.setPlainText(str(row["answer_text"] or lab.activity.starter) if row else lab.activity.starter)
        self.lab_notes.setPlainText(str(row["notes"] or "") if row else "")
        if row and row["validation_status"] == "Passed":
            self.lab_status_combo.setCurrentText("Completed")
        elif row:
            self.lab_status_combo.setCurrentText("In Progress")
        else:
            self.lab_status_combo.setCurrentText("Not Started")
        self._refresh_locks()

    def _run_lab(self) -> None:
        lab = self.catalog.skills_labs()[0]
        result = self.service.run_activity(lab.activity, self.lab_sql.toPlainText())
        self.lab_feedback.setText(("✅ " if result.passed else "❌ ") + result.feedback)
        self._show_result(self.lab_results, result.columns, result.rows)

    def _save_lab_progress(self) -> None:
        lab = self.catalog.skills_labs()[0]
        self.service.save_skills_lab_progress(
            lab,
            self.lab_sql.toPlainText(),
            self.lab_notes.toPlainText(),
        )
        self.lab_status_combo.setCurrentText("In Progress")
        self.lab_feedback.setText("Progress saved. Validate the lab when the SQL and findings are ready.")

    def _submit_lab(self) -> None:
        lab = self.catalog.skills_labs()[0]
        result = self.service.validate_skills_lab(
            lab,
            self.lab_sql.toPlainText(),
            self.lab_notes.toPlainText(),
        )
        self.lab_feedback.setText(("✅ " if result.passed else "❌ ") + result.feedback)
        if result.passed:
            self.lab_status_combo.setCurrentText("Completed")
            QMessageBox.information(
                self,
                "Skills Lab Complete",
                "The validated SQL and written findings were saved and added to Demonstrated Evidence.",
            )
        else:
            self.lab_status_combo.setCurrentText("In Progress")
        self.refresh_all()

    # ------------------------------------------------------------- assessment
    def _assessment_question_selected(self, current: QListWidgetItem | None, _previous) -> None:
        self._save_assessment_answer(silent=True)
        if current is None or self._assessment is None:
            return
        activity_id = str(current.data(Qt.ItemDataRole.UserRole))
        activity = next((item for item in self._assessment.activities if item.activity_id == activity_id), None)
        if activity is None:
            return
        self._assessment_activity = activity
        self.assessment_brief.set_markdown(
            self._activity_markdown(activity),
            eyebrow="CHECKPOINT",
            subtitle=f"Question {self.assessment_question_list.currentRow() + 1} of {len(self._assessment.activities)}",
            bookmarked=False,
        )
        self.assessment_brief.set_navigation(next_title=None, show_back=False)
        self.assessment_sql.setPlainText(self._assessment_answers.get(activity.activity_id, activity.starter))
        self.assessment_feedback.setText("")

    def _save_assessment_answer(self, silent: bool = False) -> None:
        if self._assessment_activity is None:
            return
        self._assessment_answers[self._assessment_activity.activity_id] = self.assessment_sql.toPlainText()
        self.assessment_progress.setValue(sum(bool(value.strip()) for value in self._assessment_answers.values()))
        self._refresh_assessment_question_labels()
        if not silent:
            self.assessment_feedback.setText("Answer saved for this checkpoint attempt.")

    def _refresh_assessment_question_labels(self) -> None:
        if self._assessment is None:
            return
        for index, activity in enumerate(self._assessment.activities):
            answered = bool(self._assessment_answers.get(activity.activity_id, "").strip())
            self.assessment_question_list.item(index).setText(
                f"{'✓' if answered else '○'}  {index + 1}. {activity.title}"
            )

    def _next_assessment_question(self) -> None:
        self._save_assessment_answer(silent=True)
        current = self.assessment_question_list.currentRow()
        if current < self.assessment_question_list.count() - 1:
            self.assessment_question_list.setCurrentRow(current + 1)

    def _submit_assessment(self) -> None:
        if self._assessment is None:
            return
        self._save_assessment_answer(silent=True)
        result = self.service.validate_assessment(self._assessment, self._assessment_answers)
        percent = round(100 * result["score"])
        if result.get("feedback"):
            text = "❌ " + str(result["feedback"])
        elif result["passed"]:
            text = f"✅ Checkpoint passed • Score: {percent}%. The Skills Lab is now available."
        else:
            failed = [
                activity.title
                for activity in self._assessment.activities
                if not result["results"].get(activity.activity_id, {}).get("passed")
            ]
            text = f"❌ Checkpoint needs review • Score: {percent}%. Review: " + ", ".join(failed)
        self.assessment_feedback.setText(text)
        self.service.sync_planner_task()
        self.refresh_all()

    # --------------------------------------------------------------- evidence
    def _refresh_evidence(self) -> None:
        rows = self.service.evidence_rows()
        self.evidence_summary.setText(f"{len(rows)} validated Academy evidence record(s)")
        self.evidence_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["skill_key"],
                row["source_type"],
                row["difficulty"] or "",
                row["dataset"] or "",
                row["job_competency"] or "",
                row["submission_path"] or "",
                row["demonstrated_at"] or "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.evidence_table.setItem(row_index, column, item)

    def _refresh_locks(self) -> None:
        mastered = self.service.progress.mastered_skills()
        if self._assessment is not None:
            missing = [skill for skill in self._assessment.requires if skill not in mastered]
            ready = not missing
            self.assessment_submit.setEnabled(ready)
            self.assessment_sql.setEnabled(ready)
            self.assessment_lock.setText(
                "✓ Checkpoint unlocked. Complete all questions independently."
                if ready
                else "🔒 Locked • Master first: " + ", ".join(missing)
            )
        if self.catalog.skills_labs():
            lab = self.catalog.skills_labs()[0]
            missing = [skill for skill in lab.requires if skill not in mastered]
            ready = not missing
            for widget in (self.lab_sql, self.lab_notes, self.lab_run, self.lab_submit, self.lab_complete):
                widget.setEnabled(ready)
            self.lab_lock.setText(
                "✓ Skills Lab unlocked. Validate the query and submit at least three findings."
                if ready
                else "🔒 Locked • Master first: " + ", ".join(missing)
            )

    @staticmethod
    def _show_result(table: QTableWidget, columns, rows) -> None:
        table.clear()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([str(item) for item in columns])
        preview = list(rows)[:200]
        table.setRowCount(len(preview))
        for row_index, row in enumerate(preview):
            for column, value in enumerate(row):
                table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem("NULL" if value is None else str(value)),
                )
        table.resizeColumnsToContents()
