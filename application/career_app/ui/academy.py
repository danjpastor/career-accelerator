from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer, QRectF, QSize, Signal
from PySide6.QtGui import QColor, QBrush, QPainter, QPen, QFontMetrics
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from career_app.academy import AcademyService
from career_app.academy.models import (
    ActivityDefinition,
    AssessmentDefinition,
    LessonDefinition,
    SkillsLabDefinition,
)
from career_app.services import completion_contract
from career_app.theme import COLORS
from career_app.ui.course_ui import CoursePageWidget, SqlCodeEditor
from career_app.ui.exercise_packs import FeedbackLabel
from career_app.ui.widgets import Card


@dataclass(frozen=True)
class JourneyNode:
    target_key: str
    kind: str
    title: str
    subtitle: str
    lesson_id: str | None = None
    activity_id: str | None = None
    assessment_id: str | None = None
    lab_id: str | None = None
    track_id: str | None = None
    track_title: str = ""
    course_id: str | None = None
    course_title: str = ""
    course_order: int = 0
    module_id: str | None = None
    module_title: str = ""
    module_order: int = 0


@dataclass(frozen=True)
class Milestone:
    key: str
    short_label: str
    title: str
    kind: str
    state: str


class AcademyMilestoneBar(QWidget):
    """Scrollable course/lesson milestone line used above the Academy player."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._milestones: tuple[Milestone, ...] = ()
        self.setMinimumHeight(72)
        self.setMaximumHeight(82)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_milestones(self, milestones: tuple[Milestone, ...]) -> None:
        self._milestones = milestones
        self.setMinimumWidth(max(620, 126 * max(1, len(milestones))))
        self.updateGeometry()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().paintEvent(event)
        if not self._milestones:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        count = len(self._milestones)
        left = 34.0
        right = max(left, float(self.width()) - 34.0)
        y = 22.0
        spacing = 0.0 if count <= 1 else (right - left) / (count - 1)
        positions = [left + spacing * index for index in range(count)]

        # Draw each connector as a real progress segment between milestone
        # circles.  The muted rail always remains visible while completed and
        # current segments receive the same Academy accent treatment as the
        # associated markers.
        for index in range(max(0, count - 1)):
            current = self._milestones[index]
            following = self._milestones[index + 1]
            current_radius = 10.0 if current.kind == "course" else 8.0
            following_radius = 10.0 if following.kind == "course" else 8.0
            segment_left = positions[index] + current_radius + 3.0
            segment_right = positions[index + 1] - following_radius - 3.0
            if segment_right <= segment_left:
                continue

            rail_pen = QPen(QColor("#31415F"), 5)
            rail_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(rail_pen)
            painter.drawLine(int(segment_left), int(y), int(segment_right), int(y))

            progress = 0.0
            progress_color = QColor("#7652D6")
            # Once a course has been opened, the rail from its course marker
            # to Lesson 1 should read as entered rather than half-finished.
            # This makes the visual path match the learner's actual position:
            # the course introduction has been read and Lesson 1 is underway.
            if (
                current.kind == "course"
                and following.kind == "lesson"
                and current.state in {"complete", "current", "in_progress"}
                and following.state != "locked"
            ):
                progress = 1.0
                progress_color = QColor(
                    "#7652D6" if current.state == "complete" else "#E044D5"
                )
            elif current.state == "complete" and following.state in {
                "complete",
                "current",
                "in_progress",
            }:
                progress = 1.0
            elif current.state in {"current", "in_progress"}:
                progress = 0.5
                progress_color = QColor("#E044D5")
            if progress:
                progress_pen = QPen(progress_color, 5)
                progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(progress_pen)
                progress_right = segment_left + (segment_right - segment_left) * progress
                painter.drawLine(int(segment_left), int(y), int(progress_right), int(y))

        metrics = QFontMetrics(painter.font())
        for index, milestone in enumerate(self._milestones):
            x = positions[index]
            radius = 10.0 if milestone.kind == "course" else 8.0
            fill = {
                "complete": QColor("#7652D6"),
                "current": QColor("#E044D5"),
                "in_progress": QColor("#3D6CA8"),
                "locked": QColor("#11192A"),
                "ready": QColor("#1A2440"),
            }.get(milestone.state, QColor("#1A2440"))
            border = QColor("#DFA8FF") if milestone.state == "current" else QColor("#8E73C7")
            if milestone.state == "complete":
                border = QColor("#BCE7CA")
            if milestone.state == "locked":
                border = QColor("#43506A")
            painter.setPen(QPen(border, 2))
            painter.setBrush(fill)
            painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
            if milestone.state == "complete":
                painter.setPen(QColor("#FFFFFF"))
                painter.drawText(QRectF(x - radius, y - radius - 1, radius * 2, radius * 2), Qt.AlignmentFlag.AlignCenter, "✓")
            else:
                painter.setPen(QColor("#FFFFFF" if milestone.state != "locked" else "#78859A"))
                painter.drawText(QRectF(x - radius, y - radius - 1, radius * 2, radius * 2), Qt.AlignmentFlag.AlignCenter, milestone.short_label)
            label_width = max(82, int(spacing) - 10) if count > 1 else self.width() - 20
            title = metrics.elidedText(milestone.title, Qt.TextElideMode.ElideRight, label_width)
            painter.setPen(QColor("#DCE4F3" if milestone.state != "locked" else "#78859A"))
            painter.drawText(
                QRectF(x - label_width / 2, 38, label_width, 28),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                title,
            )
        painter.end()


class AcceleratorAcademyWidget(QWidget):
    progressChanged = Signal()

    """Unified, sequential Academy experience.

    Domain concepts such as courses, practice, assessments, Skills Labs, and
    evidence remain available to the engine, but the learner sees one ordered
    journey.  Every lesson screen pairs a concise instructional block with an
    action that must be attempted and passed before Continue unlocks.
    """

    OVERVIEW_PAGE = 0
    LESSON_PAGE = 1
    ASSESSMENT_PAGE = 2
    LAB_PAGE = 3
    COMPLETE_PAGE = 4

    def __init__(self, conn, repository_root: str | Path, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.repository_root = Path(repository_root)
        self.service = AcademyService(conn, self.repository_root)
        completion_contract.register_academy_catalog(
            self.conn, self.service.catalog
        )
        self.catalog = self.service.catalog

        self._nodes: list[JourneyNode] = []
        self._current_target: str | None = None
        self._current_lesson: LessonDefinition | None = None
        self._current_activity: ActivityDefinition | None = None
        self._assessment: AssessmentDefinition | None = None
        self._assessment_activity: ActivityDefinition | None = None
        self._assessment_answers: dict[str, str] = {}
        self._lab: SkillsLabDefinition | None = None
        self._building_roadmap = False
        self._responsive_mode: str | None = None
        self._node_state_cache: dict[str, tuple[str, bool, str | None]] = {}
        self._course_collapsed: set[str] = set()
        self._course_collapse_initialized = False
        self._course_header_buttons: dict[str, QPushButton] = {}

        # Journey structure is immutable for the lifetime of the widget. Build
        # it once rather than recreating more than one hundred node objects on
        # every answer, hint, resize, and navigation action.
        self._nodes = self._build_nodes()
        self._build_ui()
        self.refresh_all()
        QTimer.singleShot(0, self.open_recommendation)

    # ------------------------------------------------------------------ shell
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 16)
        outer.setSpacing(10)

        heading = QHBoxLayout()
        heading.setSpacing(14)
        heading_text = QVBoxLayout()
        heading_text.setSpacing(2)
        title = QLabel(self.service.labels.get("system_name", "Accelerator Academy"))
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Learn a little, try it right away, and keep moving through one guided path."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        heading_text.addWidget(title)
        heading_text.addWidget(subtitle)
        heading.addLayout(heading_text, 1)

        self.overview_button = QPushButton("Path Overview")
        self.overview_button.setObjectName("Secondary")
        self.overview_button.clicked.connect(self.show_overview)
        heading.addWidget(self.overview_button)
        self.resume_button = QPushButton("Resume Learning  →")
        self.resume_button.setObjectName("Primary")
        self.resume_button.clicked.connect(self.open_recommendation)
        heading.addWidget(self.resume_button)
        outer.addLayout(heading)

        progress_host = QFrame()
        progress_host.setObjectName("AcademyProgressHost")
        progress_host.setStyleSheet(
            "QFrame#AcademyProgressHost {background:#11192A;border:1px solid #263754;border-radius:9px;}"
        )
        progress_layout = QVBoxLayout(progress_host)
        progress_layout.setContentsMargins(12, 8, 12, 6)
        progress_layout.setSpacing(4)
        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        self.progress_summary = QLabel("Getting your path ready…")
        self.progress_summary.setObjectName("Muted")
        progress_row.addWidget(self.progress_summary)
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setTextVisible(False)
        self.overall_progress.setMaximumHeight(8)
        progress_row.addWidget(self.overall_progress, 1)
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("font-weight:700;color:#FFFFFF;")
        progress_row.addWidget(self.progress_percent)
        progress_layout.addLayout(progress_row)

        milestone_scroll = QScrollArea()
        milestone_scroll.setWidgetResizable(True)
        milestone_scroll.setFrameShape(QFrame.Shape.NoFrame)
        milestone_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        milestone_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        milestone_scroll.setMaximumHeight(78)
        milestone_scroll.setStyleSheet(
            "QScrollArea {background:transparent;border:none;}"
            "QScrollBar:horizontal {height:5px;background:transparent;}"
            "QScrollBar::handle:horizontal {background:#31415F;border-radius:2px;min-width:40px;}"
        )
        self.milestone_bar = AcademyMilestoneBar()
        milestone_scroll.setWidget(self.milestone_bar)
        progress_layout.addWidget(milestone_scroll)
        outer.addWidget(progress_host)

        self.body_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.body_splitter.setChildrenCollapsible(False)
        self.body_splitter.setHandleWidth(5)
        self.body_splitter.addWidget(self._build_roadmap())
        self.content_stack = QStackedWidget()
        self.content_stack.setMinimumWidth(0)
        self.content_stack.addWidget(self._build_overview_page())
        self.content_stack.addWidget(self._build_lesson_page())
        self.content_stack.addWidget(self._build_assessment_page())
        self.content_stack.addWidget(self._build_lab_page())
        self.content_stack.addWidget(self._build_complete_page())
        self.body_splitter.addWidget(self.content_stack)
        self.body_splitter.setStretchFactor(0, 1)
        self.body_splitter.setStretchFactor(1, 3)
        outer.addWidget(self.body_splitter, 1)
        QTimer.singleShot(0, self._restore_splitters)

    def _build_roadmap(self) -> QWidget:
        card = Card("Your Learning Path", "Everything you need appears in one clear sequence.")
        card.setMinimumWidth(275)
        card.setMaximumWidth(420)
        path = self.catalog.program.paths[0]
        self.path_name = QLabel(path.title)
        self.path_name.setStyleSheet("font-size:13pt;font-weight:700;color:#FFFFFF;")
        self.path_name.setWordWrap(True)
        card.layout.addWidget(self.path_name)
        self.roadmap_progress = QProgressBar()
        self.roadmap_progress.setRange(0, 100)
        self.roadmap_progress.setTextVisible(False)
        self.roadmap_progress.setMaximumHeight(8)
        card.layout.addWidget(self.roadmap_progress)
        self.roadmap_list = QListWidget()
        self.roadmap_list.setWordWrap(True)
        self.roadmap_list.setSpacing(5)
        self.roadmap_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.roadmap_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.roadmap_list.currentItemChanged.connect(self._roadmap_selected)
        self.roadmap_list.setStyleSheet(
            f"""
            QListWidget {{background:{COLORS.get('surface_alt', '#111D31')};
                border:1px solid {COLORS.get('border', '#263754')};border-radius:9px;padding:5px;}}
            QListWidget::item {{padding:8px 8px;border-radius:7px;color:#D7E0EF;}}
            QListWidget::item:hover {{background:#182640;color:#FFFFFF;}}
            QListWidget::item:selected {{background:#30234C;color:#FFFFFF;border:1px solid #7652B5;}}
            """
        )
        card.layout.addWidget(self.roadmap_list, 1)
        self.roadmap_status = QLabel()
        self.roadmap_status.setWordWrap(True)
        self.roadmap_status.setObjectName("Muted")
        card.layout.addWidget(self.roadmap_status)
        return card

    # --------------------------------------------------------------- overview
    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(10)

        path = self.catalog.program.paths[0]
        courses = self.catalog.courses()
        assessments = self.catalog.assessments()
        skills_labs = self.catalog.skills_labs()
        hero = Card(path.title, path.description)
        hero.layout.setContentsMargins(20, 18, 20, 18)
        metrics = QHBoxLayout()
        total_steps = sum(len(lesson.activities) for lesson in self.catalog.lessons())
        for text in (
            f"{len(courses)} courses",
            f"{len(self.catalog.lessons())} lessons",
            f"{total_steps} interactive steps",
            f"{len(assessments)} checkpoint" + ("s" if len(assessments) != 1 else ""),
            f"{len(skills_labs)} applied project" + ("s" if len(skills_labs) != 1 else ""),
        ):
            pill = QLabel(text)
            pill.setStyleSheet(
                "background:#1A2440;border:1px solid #3A4970;border-radius:10px;"
                "padding:4px 9px;color:#DCE4F3;font-size:9pt;font-weight:600;"
            )
            metrics.addWidget(pill)
        metrics.addStretch(1)
        hero.layout.addLayout(metrics)
        self.overview_next_title = QLabel("Finding your next step…")
        self.overview_next_title.setStyleSheet("font-size:17pt;font-weight:750;color:#FFFFFF;")
        self.overview_next_title.setWordWrap(True)
        hero.layout.addWidget(self.overview_next_title)
        self.overview_next_reason = QLabel()
        self.overview_next_reason.setObjectName("Muted")
        self.overview_next_reason.setWordWrap(True)
        hero.layout.addWidget(self.overview_next_reason)
        start = QPushButton("Resume Learning  →")
        start.setObjectName("Primary")
        start.clicked.connect(self.open_recommendation)
        hero.layout.addWidget(start, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hero)

        sequence = Card("How the path works", "Learn, practice, and projects all stay in the same flow.")
        flow = QLabel(
            "Learn a focused concept  →  Try it immediately  →  Check your work  →  Continue  →  "
            "Complete the checkpoint  →  Finish the applied project"
        )
        flow.setWordWrap(True)
        flow.setStyleSheet(
            "background:#151E31;border:1px solid #33435F;border-radius:9px;padding:12px;"
            "color:#E8EDF8;font-size:11pt;font-weight:650;"
        )
        sequence.layout.addWidget(flow)
        rule = QLabel(
            "Every step gives you something to try. Finish the activity, check your work, and the next step will open."
        )
        rule.setWordWrap(True)
        rule.setObjectName("Muted")
        sequence.layout.addWidget(rule)
        layout.addWidget(sequence)

        outcomes = Card("What you will be able to do")
        path_outcomes = [item for course in courses for item in course.outcomes]
        outcomes_text = QLabel("\n".join(f"✓  {item}" for item in path_outcomes[:8]))
        outcomes_text.setWordWrap(True)
        outcomes_text.setStyleSheet("color:#D8E1F0;line-height:1.4;")
        outcomes.layout.addWidget(outcomes_text)
        layout.addWidget(outcomes)

        self.recent_card = Card("Recent progress")
        self.recent_progress = QLabel()
        self.recent_progress.setWordWrap(True)
        self.recent_progress.setObjectName("Muted")
        self.recent_card.layout.addWidget(self.recent_progress)
        layout.addWidget(self.recent_card)
        layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        return page

    # ------------------------------------------------------------- lesson page
    def _build_lesson_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        toolbar = Card()
        toolbar.layout.setContentsMargins(11, 7, 11, 7)
        row = QHBoxLayout()
        self.lesson_breadcrumb = QLabel()
        self.lesson_breadcrumb.setStyleSheet("color:#B8C4D8;font-size:9.5pt;")
        self.lesson_breadcrumb.setWordWrap(True)
        row.addWidget(self.lesson_breadcrumb, 1)
        self.lesson_step_pill = QLabel()
        self.lesson_step_pill.setStyleSheet(
            "background:#1A2440;border:1px solid #4A5C84;border-radius:10px;padding:4px 9px;font-weight:700;"
        )
        row.addWidget(self.lesson_step_pill)
        toolbar.layout.addLayout(row)
        root.addWidget(toolbar)

        self.lesson_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.lesson_splitter.setChildrenCollapsible(False)
        self.lesson_splitter.setHandleWidth(5)

        learn = Card("Lesson & Practice")
        learn.layout.setContentsMargins(8, 8, 8, 8)
        self.step_learn_view = CoursePageWidget()
        self.step_learn_view.set_navigation(next_title=None, show_back=False)
        learn.layout.addWidget(self.step_learn_view, 1)
        self.lesson_splitter.addWidget(learn)

        self.step_workspace_card = Card()
        self.step_workspace_card.setMinimumWidth(380)
        self.step_workspace_card.layout.setContentsMargins(8, 8, 8, 8)
        self.step_workspace_title = QLabel("SQL Editor & Output")
        self.step_workspace_title.setObjectName("CardTitle")
        self.step_workspace_title.setWordWrap(True)
        self.step_workspace_card.layout.addWidget(self.step_workspace_title)
        workspace_body = QWidget()
        workspace_layout = QVBoxLayout(workspace_body)
        workspace_layout.setContentsMargins(4, 4, 4, 4)
        workspace_layout.setSpacing(8)

        self.step_sql = SqlCodeEditor()
        self.step_sql.setMinimumHeight(230)
        self.step_sql.setPlaceholderText("Write your SQL here…")

        self.lesson_work_splitter = QSplitter(Qt.Orientation.Vertical)
        self.lesson_work_splitter.setChildrenCollapsible(False)
        self.lesson_work_splitter.setHandleWidth(5)
        self.lesson_work_splitter.addWidget(self.step_sql)

        self.step_output_host = QWidget()
        output_layout = QVBoxLayout(self.step_output_host)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(7)
        self.step_output_label = QLabel("Output")
        self.step_output_label.setStyleSheet("font-size:10pt;font-weight:700;color:#FFFFFF;")
        output_layout.addWidget(self.step_output_label)
        self.step_feedback = FeedbackLabel()
        output_layout.addWidget(self.step_feedback)
        self.step_explanation = QLabel()
        self.step_explanation.setWordWrap(True)
        self.step_explanation.setStyleSheet(
            "background:#14233B;border:1px solid #52627F;border-radius:8px;padding:9px;color:#E7ECF8;"
        )
        self.step_explanation.hide()
        output_layout.addWidget(self.step_explanation)
        self.step_results = self._result_table()
        self.step_results.setMinimumHeight(150)
        output_layout.addWidget(self.step_results, 1)
        self.lesson_work_splitter.addWidget(self.step_output_host)
        self.lesson_work_splitter.setStretchFactor(0, 5)
        self.lesson_work_splitter.setStretchFactor(1, 4)

        self.step_choice_host = QWidget()
        choice_layout = QVBoxLayout(self.step_choice_host)
        choice_layout.setContentsMargins(0, 4, 0, 4)
        choice_help = QLabel("Choose the answer that makes the most sense, then check your work.")
        choice_help.setObjectName("Muted")
        choice_help.setWordWrap(True)
        choice_layout.addWidget(choice_help)
        self.step_choice_options = QVBoxLayout()
        self.step_choice_options.setSpacing(7)
        choice_layout.addLayout(self.step_choice_options)
        self.step_choice_group = QButtonGroup(self.step_choice_host)
        self.step_choice_group.setExclusive(True)
        self.step_choice_feedback = FeedbackLabel()
        choice_layout.addWidget(self.step_choice_feedback)
        self.step_choice_explanation = QLabel()
        self.step_choice_explanation.setWordWrap(True)
        self.step_choice_explanation.setStyleSheet(
            "background:#14233B;border:1px solid #52627F;border-radius:8px;padding:9px;color:#E7ECF8;"
        )
        self.step_choice_explanation.hide()
        choice_layout.addWidget(self.step_choice_explanation)
        choice_layout.addStretch(1)

        # SQL steps use an editor/output splitter. Recognition steps use a
        # single uninterrupted answer surface so an empty editor/output divider
        # never persists when neither SQL pane is present.
        self.step_workspace_stack = QStackedWidget()
        self.step_workspace_stack.addWidget(self.lesson_work_splitter)
        self.step_workspace_stack.addWidget(self.step_choice_host)
        workspace_layout.addWidget(self.step_workspace_stack, 1)
        self.step_workspace_card.layout.addWidget(workspace_body, 1)
        self.lesson_splitter.addWidget(self.step_workspace_card)
        self.lesson_splitter.setStretchFactor(0, 55)
        self.lesson_splitter.setStretchFactor(1, 45)
        root.addWidget(self.lesson_splitter, 1)

        footer = Card()
        footer.layout.setContentsMargins(10, 7, 10, 7)
        self.lesson_footer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.lesson_footer_splitter.setChildrenCollapsible(False)
        self.lesson_footer_splitter.setHandleWidth(0)

        self.lesson_footer_left = QWidget()
        self.lesson_footer_left.setMinimumWidth(0)
        self.lesson_left_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.lesson_left_row.setContentsMargins(0, 0, 8, 0)
        self.lesson_left_row.setSpacing(8)
        self.lesson_footer_left.setLayout(self.lesson_left_row)
        self.lesson_back = QPushButton("← Back")
        self.lesson_back.setObjectName("Secondary")
        self.lesson_back.clicked.connect(self._open_previous_node)
        self.lesson_nav_status = QLabel("Complete the lesson to move on!")
        self.lesson_nav_status.setObjectName("Muted")
        self.lesson_nav_status.setStyleSheet(
            "color:#AEB9CC;background:transparent;border:none;padding:0;margin:0;"
        )
        self.lesson_nav_status.setWordWrap(True)
        self.lesson_nav_status.setMinimumWidth(0)
        self.lesson_left_row.addWidget(self.lesson_back)
        self.lesson_left_row.addWidget(self.lesson_nav_status, 1)

        self.lesson_footer_right = QWidget()
        self.lesson_footer_right.setMinimumWidth(0)
        self.lesson_action_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.lesson_action_row.setContentsMargins(8, 0, 0, 0)
        self.lesson_action_row.setSpacing(7)
        self.lesson_footer_right.setLayout(self.lesson_action_row)
        self.step_run = QPushButton("▶ Run Query")
        self.step_run.setObjectName("Secondary")
        self.step_run.clicked.connect(self._run_lesson_step)
        self.step_check = QPushButton("✓ Check Answer")
        self.step_check.setObjectName("Primary")
        self.step_check.clicked.connect(self._check_lesson_step)
        self.step_hint = QPushButton("💡 Show Hint")
        self.step_hint.setObjectName("Secondary")
        self.step_hint.clicked.connect(self._show_step_hint)
        self.step_solution = QPushButton("View Solution")
        self.step_solution.setObjectName("Secondary")
        self.step_solution.clicked.connect(self._show_step_solution)
        self.lesson_continue = QPushButton("Continue  →")
        self.lesson_continue.setObjectName("Primary")
        self.lesson_continue.clicked.connect(self._open_next_node)
        for button in (
            self.step_run,
            self.step_check,
            self.step_hint,
            self.step_solution,
            self.lesson_continue,
        ):
            button.setMinimumWidth(0)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lesson_action_spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.lesson_action_row.addItem(self.lesson_action_spacer)
        for button in (
            self.step_run,
            self.step_check,
            self.step_hint,
            self.step_solution,
        ):
            self.lesson_action_row.addWidget(button)
        self.lesson_action_row.addWidget(self.lesson_continue)

        self.lesson_footer_splitter.addWidget(self.lesson_footer_left)
        self.lesson_footer_splitter.addWidget(self.lesson_footer_right)
        self.lesson_footer_splitter.setStretchFactor(0, 55)
        self.lesson_footer_splitter.setStretchFactor(1, 45)
        footer.layout.addWidget(self.lesson_footer_splitter)
        self.lesson_splitter.splitterMoved.connect(self._sync_lesson_footer_splitter)
        root.addWidget(footer)
        return page

    # ---------------------------------------------------------- assessment page
    def _build_assessment_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        toolbar = Card()
        toolbar.layout.setContentsMargins(11, 7, 11, 7)
        row = QHBoxLayout()
        self.assessment_breadcrumb = QLabel()
        self.assessment_breadcrumb.setStyleSheet("color:#B8C4D8;font-size:9.5pt;")
        row.addWidget(self.assessment_breadcrumb, 1)
        self.assessment_step_pill = QLabel()
        self.assessment_step_pill.setStyleSheet(
            "background:#1A2440;border:1px solid #4A5C84;border-radius:10px;padding:4px 9px;font-weight:700;"
        )
        row.addWidget(self.assessment_step_pill)
        toolbar.layout.addLayout(row)
        root.addWidget(toolbar)

        self.assessment_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.assessment_splitter.setChildrenCollapsible(False)
        self.assessment_splitter.setHandleWidth(5)
        overview = Card("Checkpoint")
        overview.layout.setContentsMargins(8, 8, 8, 8)
        self.assessment_brief = CoursePageWidget()
        self.assessment_brief.set_navigation(next_title=None, show_back=False)
        overview.layout.addWidget(self.assessment_brief, 1)
        self.assessment_splitter.addWidget(overview)

        work = Card("Your Answer")
        work.layout.setContentsMargins(8, 8, 8, 8)
        work_body = QWidget()
        work_layout = QVBoxLayout(work_body)
        work_layout.setContentsMargins(4, 4, 4, 4)
        work_layout.setSpacing(8)
        self.assessment_sql = SqlCodeEditor()
        self.assessment_sql.setMinimumHeight(260)
        self.assessment_sql.setPlaceholderText("Write the checkpoint query…")
        work_layout.addWidget(self.assessment_sql, 1)
        self.assessment_action_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.assessment_run = QPushButton("▶ Run Query")
        self.assessment_run.setObjectName("Secondary")
        self.assessment_run.clicked.connect(self._run_assessment_query)
        self.assessment_save = QPushButton("Save Answer")
        self.assessment_save.setObjectName("Secondary")
        self.assessment_save.clicked.connect(self._save_assessment_answer)
        self.assessment_submit = QPushButton("Submit Checkpoint")
        self.assessment_submit.setObjectName("Primary")
        self.assessment_submit.clicked.connect(self._submit_assessment)
        self.assessment_action_row.addWidget(self.assessment_run)
        self.assessment_action_row.addWidget(self.assessment_save)
        self.assessment_action_row.addStretch(1)
        self.assessment_action_row.addWidget(self.assessment_submit)
        work_layout.addLayout(self.assessment_action_row)
        self.assessment_feedback = FeedbackLabel()
        work_layout.addWidget(self.assessment_feedback)
        self.assessment_results = self._result_table()
        self.assessment_results.setMinimumHeight(150)
        work_layout.addWidget(self.assessment_results, 1)
        work_scroll = QScrollArea()
        work_scroll.setWidgetResizable(True)
        work_scroll.setFrameShape(QFrame.Shape.NoFrame)
        work_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        work_scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        work_scroll.setWidget(work_body)
        work.layout.addWidget(work_scroll, 1)
        self.assessment_splitter.addWidget(work)
        self.assessment_splitter.setStretchFactor(0, 43)
        self.assessment_splitter.setStretchFactor(1, 57)
        root.addWidget(self.assessment_splitter, 1)

        footer = Card()
        footer.layout.setContentsMargins(10, 7, 10, 7)
        self.assessment_nav_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        back = QPushButton("← Back")
        back.setObjectName("Secondary")
        back.clicked.connect(self._open_previous_node)
        self.assessment_nav_status = QLabel()
        self.assessment_nav_status.setObjectName("Muted")
        self.assessment_nav_status.setWordWrap(True)
        self.assessment_continue = QPushButton("Save & Continue  →")
        self.assessment_continue.setObjectName("Primary")
        self.assessment_continue.clicked.connect(self._assessment_continue_clicked)
        self.assessment_nav_row.addWidget(back)
        self.assessment_nav_row.addWidget(self.assessment_nav_status, 1)
        self.assessment_nav_row.addWidget(self.assessment_continue)
        footer.layout.addLayout(self.assessment_nav_row)
        root.addWidget(footer)
        return page

    # --------------------------------------------------------------- lab page
    def _build_lab_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        toolbar = Card()
        toolbar.layout.setContentsMargins(11, 7, 11, 7)
        row = QHBoxLayout()
        self.lab_breadcrumb = QLabel("Accelerator Academy  ›  Applied Project")
        self.lab_breadcrumb.setStyleSheet("color:#B8C4D8;font-size:9.5pt;")
        row.addWidget(self.lab_breadcrumb, 1)
        self.lab_status_pill = QLabel("Not Started")
        self.lab_status_pill.setStyleSheet(
            "background:#1A2440;border:1px solid #4A5C84;border-radius:10px;padding:4px 9px;font-weight:700;"
        )
        row.addWidget(self.lab_status_pill)
        toolbar.layout.addLayout(row)
        root.addWidget(toolbar)

        self.lab_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.lab_splitter.setChildrenCollapsible(False)
        self.lab_splitter.setHandleWidth(5)
        brief_card = Card("Project Brief")
        brief_card.layout.setContentsMargins(8, 8, 8, 8)
        self.lab_brief = CoursePageWidget()
        self.lab_brief.set_navigation(next_title=None, show_back=False)
        brief_card.layout.addWidget(self.lab_brief, 1)
        self.lab_splitter.addWidget(brief_card)

        work_card = Card("Build and Submit")
        work_card.layout.setContentsMargins(8, 8, 8, 8)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(4, 4, 4, 4)
        body_layout.setSpacing(9)
        self.lab_work_title = QLabel("Analysis Submission")
        self.lab_work_title.setObjectName("SectionTitle")
        body_layout.addWidget(self.lab_work_title)
        self.lab_sql = SqlCodeEditor()
        self.lab_sql.setMinimumHeight(230)
        self.lab_sql.setPlaceholderText("Build the project query…")
        body_layout.addWidget(self.lab_sql)
        findings_title = QLabel("Findings")
        findings_title.setObjectName("SectionTitle")
        body_layout.addWidget(findings_title)
        findings_help = QLabel(
            "Write at least three concise findings. Connect each observation to the query result and its business meaning."
        )
        findings_help.setObjectName("Muted")
        findings_help.setWordWrap(True)
        body_layout.addWidget(findings_help)
        self.lab_notes = QTextEdit()
        self.lab_notes.setMinimumHeight(130)
        self.lab_notes.setPlaceholderText(
            "1. Observation, supporting result, and why it matters…\n"
            "2. Observation, supporting result, and why it matters…\n"
            "3. Observation, supporting result, and why it matters…"
        )
        body_layout.addWidget(self.lab_notes)
        self.lab_action_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.lab_run = QPushButton("▶ Run Work")
        self.lab_run.setObjectName("Secondary")
        self.lab_run.clicked.connect(self._run_lab)
        self.lab_save = QPushButton("Save Progress")
        self.lab_save.setObjectName("Secondary")
        self.lab_save.clicked.connect(self._save_lab)
        self.lab_submit = QPushButton("✓ Validate Project")
        self.lab_submit.setObjectName("Primary")
        self.lab_submit.clicked.connect(self._submit_lab)
        self.lab_action_row.addWidget(self.lab_run)
        self.lab_action_row.addWidget(self.lab_save)
        self.lab_action_row.addStretch(1)
        self.lab_action_row.addWidget(self.lab_submit)
        body_layout.addLayout(self.lab_action_row)
        self.lab_feedback = FeedbackLabel()
        body_layout.addWidget(self.lab_feedback)
        self.lab_results = self._result_table()
        self.lab_results.setMinimumHeight(140)
        body_layout.addWidget(self.lab_results)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        scroll.setWidget(body)
        work_card.layout.addWidget(scroll, 1)
        self.lab_splitter.addWidget(work_card)
        self.lab_splitter.setStretchFactor(0, 43)
        self.lab_splitter.setStretchFactor(1, 57)
        root.addWidget(self.lab_splitter, 1)

        footer = Card()
        footer.layout.setContentsMargins(10, 7, 10, 7)
        self.lab_nav_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        back = QPushButton("← Back")
        back.setObjectName("Secondary")
        back.clicked.connect(self._open_previous_node)
        self.lab_nav_status = QLabel("Finish the project to wrap up the course!")
        self.lab_nav_status.setObjectName("Muted")
        self.lab_nav_status.setWordWrap(True)
        self.lab_continue = QPushButton("Finish Course  →")
        self.lab_continue.setObjectName("Primary")
        self.lab_continue.setEnabled(False)
        self.lab_continue.clicked.connect(self._open_next_node)
        self.lab_nav_row.addWidget(back)
        self.lab_nav_row.addWidget(self.lab_nav_status, 1)
        self.lab_nav_row.addWidget(self.lab_continue)
        footer.layout.addLayout(self.lab_nav_row)
        root.addWidget(footer)
        return page

    # ---------------------------------------------------------- completion page
    def _build_complete_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        path_title = self.catalog.program.paths[0].title
        card = Card(
            f"{path_title} Complete",
            "You made it through every lesson, checkpoint, and applied project in this learning path.",
        )
        card.layout.setContentsMargins(24, 24, 24, 24)
        badge = QLabel("✓")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            "font-size:42pt;font-weight:800;color:#FFFFFF;background:#42276D;"
            "border:2px solid #A66BFF;border-radius:42px;min-width:84px;min-height:84px;max-width:84px;max-height:84px;"
        )
        card.layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignHCenter)
        message = QLabel(
            "Your strongest work is now part of Demonstrated Evidence. Review the path whenever you want to revisit a skill or inspect what you completed."
        )
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("font-size:12pt;color:#DCE4F3;")
        card.layout.addWidget(message)
        review = QPushButton("Review Learning Path")
        review.setObjectName("Secondary")
        review.clicked.connect(self.show_overview)
        card.layout.addWidget(review, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(card, 1)
        return page

    # -------------------------------------------------------------- roadmap data
    def _build_nodes(self) -> list[JourneyNode]:
        nodes: list[JourneyNode] = []
        for path in self.catalog.program.paths:
            for track in path.tracks:
                track_title = track.navigation_title or track.title
                for course in track.courses:
                    for module in course.modules:
                        for lesson in module.lessons:
                            for index, activity in enumerate(lesson.activities, start=1):
                                nodes.append(
                                    JourneyNode(
                                        target_key=f"academy:activity:{lesson.lesson_id}:{activity.activity_id}",
                                        kind="lesson_step",
                                        title=activity.title,
                                        subtitle=f"Lesson {lesson.order} • Step {index} of {len(lesson.activities)}",
                                        lesson_id=lesson.lesson_id,
                                        activity_id=activity.activity_id,
                                        track_id=track.track_id,
                                        track_title=track_title,
                                        course_id=course.course_id,
                                        course_title=course.title,
                                        course_order=course.order,
                                        module_id=module.module_id,
                                        module_title=module.title,
                                        module_order=module.order,
                                    )
                                )
                    for assessment in course.assessments:
                        for index, activity in enumerate(assessment.activities, start=1):
                            nodes.append(
                                JourneyNode(
                                    target_key=f"academy:assessment:{assessment.assessment_id}:{activity.activity_id}",
                                    kind="assessment",
                                    title=activity.title,
                                    subtitle=f"Checkpoint • Question {index} of {len(assessment.activities)}",
                                    assessment_id=assessment.assessment_id,
                                    activity_id=activity.activity_id,
                                    track_id=track.track_id,
                                    track_title=track_title,
                                    course_id=course.course_id,
                                    course_title=course.title,
                                    course_order=course.order,
                                )
                            )
                    for lab in course.skills_labs:
                        nodes.append(
                            JourneyNode(
                                target_key=f"academy:skills_lab:{lab.lab_id}",
                                kind="skills_lab",
                                title=lab.title,
                                subtitle="Applied project • Demonstrated Evidence",
                                lab_id=lab.lab_id,
                                track_id=track.track_id,
                                track_title=track_title,
                                course_id=course.course_id,
                                course_title=course.title,
                                course_order=course.order,
                            )
                        )
        return nodes

    def _prime_node_state_cache(self) -> None:
        """Load all roadmap state with a small, fixed number of queries.

        The earlier implementation asked SQLite about each roadmap node many
        times while rebuilding the list. With the expanded curriculum that
        became hundreds of synchronous queries whenever Academy was selected
        or an answer changed. This snapshot keeps navigation responsive while
        preserving the same prerequisite and mastery rules.
        """

        activity_rows = {
            (str(row["lesson_id"]), str(row["activity_id"])): row
            for row in self.conn.execute(
                "SELECT * FROM academy_activity_progress"
            ).fetchall()
        }
        mastered = self.service.progress.mastered_skills()
        passed_assessments = {
            str(row[0])
            for row in self.conn.execute(
                """SELECT DISTINCT assessment_id
                   FROM academy_assessment_attempts
                   WHERE passed=1"""
            ).fetchall()
        }
        passed_labs = {
            str(row[0])
            for row in self.conn.execute(
                """SELECT DISTINCT item_id
                   FROM academy_submissions
                   WHERE item_type='skills_lab'
                     AND validation_status='Passed'"""
            ).fetchall()
        }

        lab_course_assessments: dict[str, tuple[str, ...]] = {}
        for course in self.catalog.courses():
            assessment_ids = tuple(item.assessment_id for item in course.assessments)
            for lab in course.skills_labs:
                lab_course_assessments[lab.lab_id] = assessment_ids

        cache: dict[str, tuple[str, bool, str | None]] = {}
        for node in self._nodes:
            if node.kind == "lesson_step":
                lesson = self.catalog.lesson(str(node.lesson_id))
                activity = next(
                    item for item in lesson.activities
                    if item.activity_id == node.activity_id
                )
                row = activity_rows.get((lesson.lesson_id, activity.activity_id))
                passed = bool(row and row["state"] == "Passed")
                complete = passed and not (
                    activity.required_for_mastery
                    and bool(row["last_attempt_solution_assisted"])
                )
                missing = tuple(skill for skill in lesson.requires if skill not in mastered)
                unlocked = not missing
                reason: str | None = None
                if missing:
                    reason = "Master first: " + ", ".join(missing)
                else:
                    for earlier in lesson.activities:
                        if earlier.activity_id == activity.activity_id:
                            break
                        if not earlier.required_for_completion:
                            continue
                        earlier_row = activity_rows.get(
                            (lesson.lesson_id, earlier.activity_id)
                        )
                        if earlier_row is None or earlier_row["state"] != "Passed":
                            unlocked = False
                            reason = f"Complete the earlier step: {earlier.title}"
                            break
                cache[node.target_key] = (
                    "Passed" if complete else "Ready" if unlocked else "Locked",
                    unlocked,
                    reason,
                )
                continue

            if node.kind == "assessment":
                assessment = self.catalog.assessment(str(node.assessment_id))
                if assessment.assessment_id in passed_assessments:
                    cache[node.target_key] = ("Passed", True, None)
                    continue
                missing = tuple(skill for skill in assessment.requires if skill not in mastered)
                unlocked = not missing
                answered = bool(
                    self._assessment_answers.get(str(node.activity_id), "").strip()
                )
                cache[node.target_key] = (
                    "Answered" if answered else "Ready" if unlocked else "Locked",
                    unlocked,
                    ", ".join(missing) or None,
                )
                continue

            lab = self.catalog.skills_lab(str(node.lab_id))
            if lab.lab_id in passed_labs:
                cache[node.target_key] = ("Passed", True, None)
                continue
            missing_items = [skill for skill in lab.requires if skill not in mastered]
            for assessment_id in lab_course_assessments.get(lab.lab_id, ()):
                if assessment_id not in passed_assessments:
                    assessment = self.catalog.assessment(assessment_id)
                    missing_items.append(f"checkpoint:{assessment.title}")
            cache[node.target_key] = (
                "Ready" if not missing_items else "Locked",
                not missing_items,
                ", ".join(missing_items) or None,
            )

        self._node_state_cache = cache

    def _node_state(self, node: JourneyNode) -> tuple[str, bool, str | None]:
        cached = self._node_state_cache.get(node.target_key)
        if cached is not None:
            return cached

        # Defensive fallback for a route opened before the first full refresh.
        self._prime_node_state_cache()
        return self._node_state_cache.get(
            node.target_key,
            ("Locked", False, "This step is not available yet."),
        )

    def _add_roadmap_header(
        self,
        text: str,
        *,
        background: str,
        foreground: str,
        border: str,
        height: int,
        course_id: str | None = None,
        collapsible: bool = False,
    ) -> QListWidgetItem:
        """Add a tinted hierarchy heading, optionally as a course toggle."""

        item = QListWidgetItem("")
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setData(Qt.ItemDataRole.UserRole + 10, "course_header" if collapsible else "roadmap_header")
        item.setData(Qt.ItemDataRole.UserRole + 11, course_id)
        item.setSizeHint(QSize(1, height + 8))
        self.roadmap_list.addItem(item)

        frame = QFrame()
        frame.setMinimumHeight(height)
        frame.setMaximumHeight(height)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        frame.setStyleSheet(
            f"QFrame {{background:{background};border:1px solid {border};border-radius:7px;}}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(1)

        if collapsible and course_id:
            collapsed = course_id in self._course_collapsed
            button = QPushButton(("▸  " if collapsed else "▾  ") + text)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.setStyleSheet(
                f"QPushButton {{color:{foreground};font-weight:750;font-size:9.5pt;"
                "background:transparent;border:none;padding:0;text-align:left;}"
                "QPushButton:hover {color:#FFFFFF;}"
            )
            button.clicked.connect(
                lambda _checked=False, key=course_id: self._toggle_course(key)
            )
            layout.addWidget(button, 1)
            self._course_header_buttons[course_id] = button
        else:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet(
                f"color:{foreground};font-weight:750;font-size:9.5pt;"
                "background:transparent;border:none;padding:0;"
            )
            layout.addWidget(label, 1)

        self.roadmap_list.setItemWidget(item, frame)
        return item

    def _toggle_course(self, course_id: str) -> None:
        if course_id in self._course_collapsed:
            self._course_collapsed.remove(course_id)
        else:
            self._course_collapsed.add(course_id)
        # Rebuilding only the visible rows is inexpensive because node state is
        # already cached and collapsed courses do not create child widgets.
        self._refresh_roadmap(recompute_states=False)
        self._select_current_roadmap_item()

    def _initialize_course_collapse(self) -> None:
        if self._course_collapse_initialized:
            return
        active_course: str | None = None
        if self._current_target:
            try:
                active_course = self._node(self._current_target).course_id
            except KeyError:
                active_course = None
        if active_course is None:
            for node in self._nodes:
                state, unlocked, _reason = self._node_state(node)
                if state != "Passed" and unlocked:
                    active_course = node.course_id
                    break
        course_ids = {str(node.course_id) for node in self._nodes if node.course_id}
        self._course_collapsed = {
            course_id for course_id in course_ids if course_id != active_course
        }
        self._course_collapse_initialized = True

    def _refresh_roadmap(self, *, recompute_states: bool = True) -> None:
        current = self._current_target
        if recompute_states or not self._node_state_cache:
            self._prime_node_state_cache()
        self._initialize_course_collapse()

        lesson_nodes_by_id: dict[str, list[JourneyNode]] = {}
        for item in self._nodes:
            if item.kind == "lesson_step" and item.lesson_id:
                lesson_nodes_by_id.setdefault(str(item.lesson_id), []).append(item)

        self._building_roadmap = True
        self._course_header_buttons.clear()
        self.roadmap_list.blockSignals(True)
        self.roadmap_list.setUpdatesEnabled(False)
        self.roadmap_list.clear()
        try:
            previous_track: str | None = None
            previous_course: str | None = None
            previous_section: str | None = None
            previous_module: str | None = None
            previous_lesson: str | None = None

            for node in self._nodes:
                if node.track_id != previous_track:
                    self._add_roadmap_header(
                        node.track_title.upper(),
                        background="#2C1D48",
                        foreground="#FFFFFF",
                        border="#7652B5",
                        height=44,
                    )
                    previous_track = node.track_id
                    previous_course = None
                    previous_section = None
                    previous_module = None
                    previous_lesson = None

                if node.course_id != previous_course:
                    self._add_roadmap_header(
                        f"COURSE {node.course_order}  •  {node.course_title}",
                        background="#1B2741",
                        foreground="#E6D8FF",
                        border="#485B82",
                        height=52,
                        course_id=str(node.course_id),
                        collapsible=True,
                    )
                    previous_course = node.course_id
                    previous_section = None
                    previous_module = None
                    previous_lesson = None

                if str(node.course_id) in self._course_collapsed:
                    continue

                if node.kind == "lesson_step" and node.module_id != previous_module:
                    chapter = self._add_roadmap_header(
                        f"CHAPTER {node.module_order}  •  {node.module_title}",
                        background="#17233A",
                        foreground="#BFD0F4",
                        border="#3A4D70",
                        height=44,
                        course_id=str(node.course_id),
                    )
                    chapter.setData(Qt.ItemDataRole.UserRole + 11, str(node.course_id))
                    previous_module = node.module_id
                    previous_section = None
                    previous_lesson = None

                if node.kind == "lesson_step" and node.lesson_id != previous_lesson:
                    lesson = self.catalog.lesson(str(node.lesson_id))
                    lesson_nodes = lesson_nodes_by_id.get(lesson.lesson_id, [])
                    lesson_states = [self._node_state(item)[0] for item in lesson_nodes]
                    lesson_complete = bool(lesson_states) and all(
                        state == "Passed" for state in lesson_states
                    )
                    lesson_current = any(
                        item.target_key == current for item in lesson_nodes
                    )
                    lesson_started = any(
                        state in {"Passed", "Answered"} for state in lesson_states
                    )
                    lesson_ready = bool(
                        lesson_nodes and self._node_state(lesson_nodes[0])[1]
                    )
                    if lesson_complete:
                        lesson_background = QColor("#19302B")
                        lesson_foreground = QColor("#C7F0D3")
                    elif lesson_current:
                        lesson_background = QColor("#352454")
                        lesson_foreground = QColor("#FFFFFF")
                    elif lesson_started:
                        lesson_background = QColor("#202B49")
                        lesson_foreground = QColor("#DCE7FF")
                    elif lesson_ready:
                        lesson_background = QColor("#241C3B")
                        lesson_foreground = QColor("#DCCBFF")
                    else:
                        lesson_background = QColor("#141A29")
                        lesson_foreground = QColor("#7F8CA3")
                    header = self._add_roadmap_header(
                        f"LESSON {lesson.order}\n{lesson.title}",
                        background=lesson_background.name(),
                        foreground=lesson_foreground.name(),
                        border="#7652B5" if lesson_current else "#33435F",
                        height=68,
                        course_id=str(node.course_id),
                    )
                    header.setData(Qt.ItemDataRole.UserRole + 11, str(node.course_id))
                    previous_lesson = node.lesson_id
                    previous_section = "lesson"
                elif node.kind == "assessment" and previous_section != "assessment":
                    header = self._add_roadmap_header(
                        "COURSE CHECKPOINT",
                        background="#20213B",
                        foreground="#D9C1FF",
                        border="#594A7A",
                        height=44,
                        course_id=str(node.course_id),
                    )
                    header.setData(Qt.ItemDataRole.UserRole + 11, str(node.course_id))
                    previous_section = "assessment"
                    previous_module = None
                    previous_lesson = None
                elif node.kind == "skills_lab" and previous_section != "lab":
                    header = self._add_roadmap_header(
                        "APPLIED PROJECT",
                        background="#20213B",
                        foreground="#D9C1FF",
                        border="#594A7A",
                        height=44,
                        course_id=str(node.course_id),
                    )
                    header.setData(Qt.ItemDataRole.UserRole + 11, str(node.course_id))
                    previous_section = "lab"
                    previous_module = None
                    previous_lesson = None

                state, unlocked, _reason = self._node_state(node)
                icon = {
                    "Passed": "✓",
                    "Answered": "◐",
                    "Ready": "○",
                    "Locked": "🔒",
                }.get(state, "○")
                item = QListWidgetItem(
                    f"{icon}  {node.title}\n    {node.subtitle}"
                )
                item.setData(Qt.ItemDataRole.UserRole, node.target_key)
                item.setData(Qt.ItemDataRole.UserRole + 1, unlocked)
                item.setData(Qt.ItemDataRole.UserRole + 11, str(node.course_id))
                if state == "Passed":
                    item.setForeground(QBrush(QColor("#BCE7CA")))
                elif state == "Locked":
                    item.setForeground(QBrush(QColor("#78859A")))
                self.roadmap_list.addItem(item)
                if node.target_key == current:
                    self.roadmap_list.setCurrentItem(item)
        finally:
            self.roadmap_list.setUpdatesEnabled(True)
            self.roadmap_list.blockSignals(False)
            self._building_roadmap = False
            self.roadmap_list.viewport().update()

    def _roadmap_selected(self, current: QListWidgetItem | None, _previous) -> None:
        if self._building_roadmap or current is None:
            return
        target = current.data(Qt.ItemDataRole.UserRole)
        if not target:
            return
        if not bool(current.data(Qt.ItemDataRole.UserRole + 1)):
            node = self._node(str(target))
            _state, _unlocked, reason = self._node_state(node)
            QMessageBox.information(
                self,
                "Step Locked",
                reason or "Finish the earlier lesson steps first, then come back to this one.",
            )
            self._select_current_roadmap_item()
            return
        self.open_target(str(target))

    def _select_current_roadmap_item(self) -> None:
        if not self._current_target:
            return
        self.roadmap_list.blockSignals(True)
        for index in range(self.roadmap_list.count()):
            item = self.roadmap_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == self._current_target:
                self.roadmap_list.setCurrentItem(item)
                self.roadmap_list.scrollToItem(item)
                break
        self.roadmap_list.blockSignals(False)

    def _node(self, target_key: str) -> JourneyNode:
        for node in self._nodes or self._build_nodes():
            if node.target_key == target_key:
                return node
        raise KeyError(f"Unknown Academy target: {target_key}")

    # --------------------------------------------------------------- navigation
    def show_overview(self) -> None:
        self._save_current_work()
        self.content_stack.setCurrentIndex(self.OVERVIEW_PAGE)
        self._current_target = None
        self.roadmap_list.clearSelection()
        self.refresh_all()

    def open_recommendation(self) -> None:
        self._save_current_work()
        recommendation = self.service.next_recommendation()
        if recommendation is None:
            if self.service.path_complete():
                self.content_stack.setCurrentIndex(self.COMPLETE_PAGE)
                self._current_target = self._nodes[-1].target_key if self._nodes else None
            else:
                self.content_stack.setCurrentIndex(self.OVERVIEW_PAGE)
                QMessageBox.information(
                    self,
                    "Progress Needs Attention",
                    "Your pathway is still in progress, but Academy could not identify the next step. "
                    "Your work has been preserved. Reopen Academy to refresh the learning path.",
                )
            self.refresh_all()
            return
        target = recommendation.target_key
        if recommendation.kind == "assessment":
            assessment = self.catalog.assessment(target.split(":")[2])
            drafts = self.service.assessment_drafts(assessment.assessment_id)
            activity = next(
                (item for item in assessment.activities if not drafts.get(item.activity_id, "").strip()),
                assessment.activities[0],
            )
            target = f"academy:assessment:{assessment.assessment_id}:{activity.activity_id}"
        self.open_target(target)

    def open_target(self, target_key: str) -> None:
        self._save_current_work()
        node = self._node(target_key)
        if not self._node_state_cache:
            self._prime_node_state_cache()
        state, unlocked, reason = self._node_state(node)
        if not unlocked and state != "Passed":
            QMessageBox.information(self, "Step Locked", reason or "Finish the earlier lesson steps first, then come back to this one.")
            return
        self._current_target = node.target_key
        if node.course_id:
            self._course_collapsed.discard(str(node.course_id))
        self.service.remember_target(node.target_key)
        if node.kind == "lesson_step":
            self._open_lesson_node(node)
        elif node.kind == "assessment":
            self._open_assessment_node(node)
        else:
            self._open_lab_node(node)
        self.refresh_all()
        self._select_current_roadmap_item()

    def open_lesson(self, lesson_id: str, activity_id: str | None = None) -> None:
        """Compatibility route used by existing planner/navigation code."""
        lesson = self.catalog.lesson(lesson_id)
        activity = next(
            (item for item in lesson.activities if item.activity_id == activity_id),
            None,
        )
        if activity is None:
            activity = next(
                (item for item in lesson.activities if not self.service.activity_complete(lesson_id, item)),
                lesson.activities[0],
            )
        self.open_target(f"academy:activity:{lesson_id}:{activity.activity_id}")

    def _open_previous_node(self) -> None:
        if not self._current_target:
            self.show_overview()
            return
        self._save_current_work()
        keys = [node.target_key for node in self._nodes]
        index = keys.index(self._current_target)
        if index <= 0:
            self.show_overview()
        else:
            self.open_target(keys[index - 1])

    def _open_next_node(self) -> None:
        if not self._current_target:
            self.open_recommendation()
            return
        self._save_current_work()
        keys = [node.target_key for node in self._nodes]
        if self._current_target not in keys:
            self.refresh_all()
            self.open_recommendation()
            return
        index = keys.index(self._current_target)
        if index >= len(keys) - 1:
            if self.service.path_complete():
                self.content_stack.setCurrentIndex(self.COMPLETE_PAGE)
            else:
                self.open_recommendation()
            self.refresh_all()
            return
        next_target = keys[index + 1]
        _state, unlocked, _reason = self._node_state(self._node(next_target))
        if not unlocked:
            recommendation = self.service.next_recommendation()
            if recommendation is not None:
                self.open_target(recommendation.target_key)
            else:
                self.refresh_all()
            return
        self.open_target(next_target)

    # -------------------------------------------------------------- lesson flow
    def _open_lesson_node(self, node: JourneyNode) -> None:
        lesson = self.catalog.lesson(str(node.lesson_id))
        activity = next(item for item in lesson.activities if item.activity_id == node.activity_id)
        self.service.open_lesson(lesson.lesson_id)
        self._current_lesson = lesson
        self._current_activity = activity
        self.content_stack.setCurrentIndex(self.LESSON_PAGE)
        step_index = lesson.activities.index(activity) + 1
        self.lesson_breadcrumb.setText(
            f"Accelerator Academy  ›  {node.track_title}  ›  {node.course_title}  ›  "
            f"Chapter {node.module_order}: {node.module_title}  ›  "
            f"Lesson {lesson.order}: {lesson.title}"
        )
        self.lesson_step_pill.setText(f"Step {step_index} of {len(lesson.activities)}")
        instruction = dict(activity.instruction)
        title = str(instruction.get("title") or activity.title)
        objective = str(instruction.get("objective") or "Learn the concept, then apply it immediately.")
        body = str(instruction.get("body") or lesson.content_markdown)
        learn_markdown = (
            f"# {title}\n\n"
            f"> **Step goal:** {objective}\n\n"
            f"{body}\n\n"
            "---\n\n"
            f"{self._activity_markdown(activity, embedded=True)}"
        )
        self.step_learn_view.set_markdown(
            learn_markdown,
            eyebrow=f"LESSON {lesson.order} • {activity.activity_type.value.upper()}",
            subtitle=(
                f"About {activity.estimated_minutes} minutes • "
                f"{activity.difficulty.title()} interactive step"
            ),
            bookmarked=False,
        )
        self.step_learn_view.set_navigation(next_title=None, show_back=False)
        row = self.service.activity_progress(lesson.lesson_id, activity.activity_id)
        answer = str(row["answer_text"] or "") if row else ""
        if not answer:
            answer = activity.starter
        recognition = activity.runtime == "recognition"
        self.step_workspace_title.setText("Answer & Feedback" if recognition else "SQL Editor & Output")
        self.step_workspace_stack.setCurrentIndex(1 if recognition else 0)
        for button in self.step_choice_group.buttons():
            self.step_choice_group.removeButton(button)
            button.setParent(None)
            button.deleteLater()
        if recognition:
            for option in activity.answer_options:
                button = QRadioButton(option)
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                button.setStyleSheet(
                    "QRadioButton {background:#111D31;border:1px solid #31415F;border-radius:8px;"
                    "padding:9px 10px;color:#E4EAF5;}"
                    "QRadioButton:hover {background:#182640;border-color:#7652B5;}"
                    "QRadioButton:checked {background:#30234C;border-color:#A66BFF;color:#FFFFFF;}"
                )
                if option == answer:
                    button.setChecked(True)
                self.step_choice_group.addButton(button)
                self.step_choice_options.addWidget(button)
        if not recognition:
            self.step_sql.blockSignals(True)
            self.step_sql.setPlainText(answer)
            self.step_sql.blockSignals(False)
        self.step_run.setVisible(not recognition)
        self.step_solution.setVisible(True)
        self.step_feedback.setText("")
        self.step_choice_feedback.setText("")
        self.step_explanation.hide()
        self.step_choice_explanation.hide()
        self._show_result(self.step_results, (), ())
        self._refresh_lesson_navigation()
        QTimer.singleShot(0, self._sync_lesson_footer_splitter)

    def _lesson_answer(self) -> str:
        if self._current_activity is None:
            return ""
        if self._current_activity.runtime == "recognition":
            button = self.step_choice_group.checkedButton()
            return button.text() if button is not None else ""
        return self.step_sql.toPlainText()

    def _active_step_feedback(self) -> FeedbackLabel:
        if self._current_activity is not None and self._current_activity.runtime == "recognition":
            return self.step_choice_feedback
        return self.step_feedback

    def _active_step_explanation(self) -> QLabel:
        if self._current_activity is not None and self._current_activity.runtime == "recognition":
            return self.step_choice_explanation
        return self.step_explanation

    def _sync_lesson_footer_splitter(self, *_args) -> None:
        """Keep footer controls aligned with the lesson/editor divider."""

        if not hasattr(self, "lesson_footer_splitter"):
            return
        if self.lesson_splitter.orientation() != Qt.Orientation.Horizontal:
            return
        sizes = self.lesson_splitter.sizes()
        if len(sizes) != 2 or sum(sizes) <= 0:
            return
        available = max(1, self.lesson_footer_splitter.width())
        left = round(available * sizes[0] / sum(sizes))
        self._fit_lesson_action_buttons(max(1, available - left))
        self.lesson_footer_splitter.setSizes([left, max(1, available - left)])

    def _fit_lesson_action_buttons(self, available_width: int) -> None:
        """Use all editor-side footer space until each control reaches full size."""

        checkpoint_next = self.lesson_continue.text().startswith("Continue to Checkpoint")
        label_sets = (
            {
                self.step_run: "▶ Run Query",
                self.step_check: "✓ Check Answer",
                self.step_hint: "💡 Show Hint",
                self.step_solution: "View Solution",
                self.lesson_continue: "Continue to Checkpoint  →" if checkpoint_next else "Continue  →",
            },
            {
                self.step_run: "▶ Run",
                self.step_check: "✓ Check",
                self.step_hint: "💡 Hint",
                self.step_solution: "Solution",
                self.lesson_continue: "Checkpoint  →" if checkpoint_next else "Continue  →",
            },
            {
                self.step_run: "Run",
                self.step_check: "Check",
                self.step_hint: "Hint",
                self.step_solution: "Answer",
                self.lesson_continue: "Next  →",
            },
        )
        visible_buttons = [
            button
            for button in (
                self.step_run,
                self.step_check,
                self.step_hint,
                self.step_solution,
                self.lesson_continue,
            )
            if button.isVisible()
        ]
        if not visible_buttons:
            return

        spacing = 7 if available_width >= 560 else 5 if available_width >= 430 else 3
        self.lesson_action_row.setSpacing(spacing)
        layout_margins = 12
        budget = max(1, available_width - layout_margins - spacing * (len(visible_buttons) - 1))

        def text_width(button: QPushButton, text: str, padding: int) -> int:
            return button.fontMetrics().horizontalAdvance(text) + padding

        labels = label_sets[-1]
        for candidate in label_sets:
            required = sum(text_width(button, candidate[button], 18) for button in visible_buttons)
            if required <= budget:
                labels = candidate
                break

        minimums = {
            button: max(48, text_width(button, labels[button], 14))
            for button in visible_buttons
        }
        maximums = {
            button: max(minimums[button], text_width(button, labels[button], 34))
            for button in visible_buttons
        }
        widths = dict(minimums)
        extra = max(0, budget - sum(widths.values()))

        # Grow every visible button together. This keeps the footer balanced
        # and consumes the complete editor-side width until all controls reach
        # their comfortable full size. Any space left after that becomes the
        # right-alignment spacer.
        while extra > 0:
            growable = [button for button in visible_buttons if widths[button] < maximums[button]]
            if not growable:
                break
            share = max(1, extra // len(growable))
            used = 0
            for button in growable:
                growth = min(share, maximums[button] - widths[button], extra - used)
                widths[button] += growth
                used += growth
                if used >= extra:
                    break
            if used <= 0:
                break
            extra -= used

        self.lesson_action_spacer.changeSize(
            max(0, extra),
            0,
            QSizePolicy.Policy.Fixed if extra <= 0 else QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.lesson_action_row.invalidate()
        for button in visible_buttons:
            button.setText(labels[button])
            button.setFixedWidth(widths[button])

    def _save_current_lesson_answer(self) -> None:
        if self._current_lesson is None or self._current_activity is None:
            return
        answer = self._lesson_answer()
        if answer or self._current_activity.starter:
            self.service.progress.save_answer(
                self._current_lesson.lesson_id,
                self._current_activity,
                answer,
            )

    def _run_lesson_step(self) -> None:
        if self._current_activity is None:
            return
        result = self.service.run_activity(self._current_activity, self._lesson_answer())
        self._active_step_feedback().setText(("✅ " if result.passed else "❌ ") + result.feedback)
        self._show_result(self.step_results, result.columns, result.rows)
        if not result.passed:
            self.step_sql.navigate_to_error(result.feedback)

    def _check_lesson_step(self) -> None:
        if self._current_lesson is None or self._current_activity is None:
            return
        result = self.service.validate_activity(
            self._current_lesson,
            self._current_activity,
            self._lesson_answer(),
        )
        self._active_step_feedback().setText(("✅ " if result.passed else "❌ ") + result.feedback)
        if self._current_activity.runtime == "sql":
            self._show_result(self.step_results, result.columns, result.rows)
        if result.passed:
            explanation = str(self._current_activity.presentation.get("after_correct") or "")
            if explanation:
                active_explanation = self._active_step_explanation()
                active_explanation.setText("Why this works\n\n" + explanation)
                active_explanation.show()
        elif self._current_activity.runtime == "sql":
            self.step_sql.navigate_to_error(result.feedback)
        self.refresh_all()
        self._refresh_lesson_navigation()
        self.progressChanged.emit()

    def _show_step_hint(self) -> None:
        if self._current_lesson is None or self._current_activity is None:
            return
        level, hint = self.service.reveal_hint(self._current_lesson.lesson_id, self._current_activity)
        self._active_step_feedback().setText(f"💡 Hint {level}: {hint}")

    def _show_step_solution(self) -> None:
        if self._current_lesson is None or self._current_activity is None:
            return
        solution = self.service.reveal_solution(self._current_lesson.lesson_id, self._current_activity)
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Official Solution")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText(
            "The solution is shown for study and will not replace your work. "
            "To earn mastery, give it another try without the full solution open."
        )
        dialog.setDetailedText(solution)
        dialog.exec()
        self._active_step_feedback().setText(
            "Take a look, then rebuild the answer yourself. You’ll need a clean pass before moving on."
        )
        self.refresh_all()
        self._refresh_lesson_navigation()

    def _refresh_lesson_navigation(self) -> None:
        if self._current_lesson is None or self._current_activity is None:
            return
        complete = self.service.activity_complete(self._current_lesson.lesson_id, self._current_activity)
        self.lesson_continue.setEnabled(complete)
        self.lesson_nav_status.setText(
            "✓ Nice work! Continue when you’re ready."
            if complete
            else "Complete the lesson to move on!"
        )
        keys = [node.target_key for node in self._nodes]
        if self._current_target in keys:
            index = keys.index(self._current_target)
            self.lesson_back.setText("Path Overview" if index == 0 else "← Back")
            self.lesson_continue.setText("Continue to Checkpoint  →" if index + 1 < len(self._nodes) and self._nodes[index + 1].kind == "assessment" else "Continue  →")
        QTimer.singleShot(0, self._sync_lesson_footer_splitter)

    # ----------------------------------------------------------- assessment flow
    def _open_assessment_node(self, node: JourneyNode) -> None:
        assessment = self.catalog.assessment(str(node.assessment_id))
        activity = next(item for item in assessment.activities if item.activity_id == node.activity_id)
        self._assessment = assessment
        self._assessment_activity = activity
        self._assessment_answers = {
            **self.service.assessment_drafts(assessment.assessment_id),
            **self._assessment_answers,
        }
        self.content_stack.setCurrentIndex(self.ASSESSMENT_PAGE)
        index = assessment.activities.index(activity) + 1
        self.assessment_breadcrumb.setText(f"Accelerator Academy  ›  {assessment.title}")
        self.assessment_step_pill.setText(f"Question {index} of {len(assessment.activities)}")
        instructions = "\n".join(f"- {item}" for item in assessment.instructions)
        markdown = (
            f"# {activity.title}\n\n"
            f"> **Checkpoint question {index}:** Complete this independently. Hints and solutions are unavailable.\n\n"
            f"{assessment.description}\n\n"
            f"## Instructions\n{instructions}\n\n"
            f"## Your task\n{activity.prompt}\n\n"
            f"## Requirements\n"
            + "\n".join(f"- {item}" for item in activity.presentation.get("requirements", []))
            + f"\n\n### Expected output\n{activity.presentation.get('expected_output', 'Return the requested result.')}"
        )
        self.assessment_brief.set_markdown(
            markdown,
            eyebrow="COURSE CHECKPOINT",
            subtitle=f"Pass score: {round(assessment.passing_score * 100)}% • {assessment.estimated_minutes} minutes total",
            bookmarked=False,
        )
        self.assessment_brief.set_navigation(next_title=None, show_back=False)
        answer = self._assessment_answers.get(activity.activity_id, activity.starter)
        self.assessment_sql.setPlainText(answer)
        self.assessment_feedback.setText("")
        self._show_result(self.assessment_results, (), ())
        self._refresh_assessment_navigation()

    def _save_assessment_answer(self, silent: bool = False) -> bool:
        if self._assessment is None or self._assessment_activity is None:
            return False
        answer = self.assessment_sql.toPlainText()
        self._assessment_answers[self._assessment_activity.activity_id] = answer
        self.service.save_assessment_draft(
            self._assessment.assessment_id,
            self._assessment_activity.activity_id,
            answer,
        )
        if not silent:
            self.assessment_feedback.setText("Saved! You can come back and change this answer before you submit.")
        self.refresh_all()
        return bool(answer.strip())

    def _run_assessment_query(self) -> None:
        if self._assessment_activity is None:
            return
        result = self.service.run_activity(self._assessment_activity, self.assessment_sql.toPlainText())
        self.assessment_feedback.setText(("✅ Query ran. " if result.passed else "❌ ") + result.feedback)
        self._show_result(self.assessment_results, result.columns, result.rows)
        if not result.passed:
            self.assessment_sql.navigate_to_error(result.feedback)

    def _assessment_continue_clicked(self) -> None:
        if not self._save_assessment_answer(silent=True):
            self.assessment_feedback.setText("Add an answer before moving to the next checkpoint question.")
            return
        if self._assessment is None or self._assessment_activity is None:
            return
        index = self._assessment.activities.index(self._assessment_activity)
        if index == len(self._assessment.activities) - 1:
            self._submit_assessment()
        else:
            self._open_next_node()

    def _submit_assessment(self) -> None:
        if self._assessment is None:
            return
        self._save_assessment_answer(silent=True)
        answers = self.service.assessment_drafts(self._assessment.assessment_id)
        missing = [item.title for item in self._assessment.activities if not answers.get(item.activity_id, "").strip()]
        if missing:
            self.assessment_feedback.setText(
                "A few questions still need answers: " + ", ".join(missing)
            )
            return
        result = self.service.validate_assessment(self._assessment, answers)
        score = round(float(result.get("score", 0.0)) * 100)
        if result.get("passed"):
            self.assessment_feedback.setText(f"✅ You passed with {score}%! Your applied project is ready.")
            QMessageBox.information(
                self,
                "Checkpoint Passed",
                f"Score: {score}%\n\nGreat job—your applied project is ready.",
            )
            self.refresh_all()
            lab = self.catalog.skills_labs()[0]
            self.open_target(f"academy:skills_lab:{lab.lab_id}")
            return
        failed_ids = [key for key, value in result.get("results", {}).items() if not value.get("passed")]
        failed_titles = [
            item.title for item in self._assessment.activities if item.activity_id in failed_ids
        ]
        self.assessment_feedback.setText(
            f"You scored {score}%. Take another look at: " + ", ".join(failed_titles)
        )
        QMessageBox.information(
            self,
            "Checkpoint Needs Review",
            f"Score: {score}%\n\nReview the questions you missed, make a few changes, and try again.",
        )
        self.refresh_all()

    def _refresh_assessment_navigation(self) -> None:
        if self._assessment is None or self._assessment_activity is None:
            return
        index = self._assessment.activities.index(self._assessment_activity)
        answered = sum(
            bool(self._assessment_answers.get(item.activity_id, "").strip())
            for item in self._assessment.activities
        )
        self.assessment_nav_status.setText(
            f"{answered} of {len(self._assessment.activities)} answers saved. "
            "We’ll score everything when you submit the checkpoint."
        )
        last = index == len(self._assessment.activities) - 1
        self.assessment_continue.setText("Submit Checkpoint" if last else "Save & Continue  →")
        self.assessment_submit.setVisible(not last)

    # ---------------------------------------------------------------- lab flow
    def _open_lab_node(self, node: JourneyNode) -> None:
        lab = self.catalog.skills_lab(str(node.lab_id))
        self._lab = lab
        self.content_stack.setCurrentIndex(self.LAB_PAGE)
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
        self.lab_brief.set_markdown(
            markdown,
            eyebrow="APPLIED PROJECT",
            subtitle=f"Final course milestone • About {lab.estimated_minutes} minutes",
            bookmarked=False,
        )
        self.lab_brief.set_navigation(next_title=None, show_back=False)
        runtime_label = lab.activity.runtime.upper() if lab.activity.runtime else "WORK"
        self.lab_work_title.setText(f"{runtime_label} Submission")
        self.lab_run.setText("▶ Run Query" if lab.activity.runtime == "sql" else "▶ Run Work")
        self.lab_sql.setPlaceholderText(
            "Build the project query…" if lab.activity.runtime == "sql" else "Complete the project work…"
        )
        row = self.conn.execute(
            """SELECT answer_text,notes,validation_status FROM academy_submissions
               WHERE item_type='skills_lab' AND item_id=? ORDER BY submission_id DESC LIMIT 1""",
            (lab.lab_id,),
        ).fetchone()
        self.lab_sql.setPlainText(str(row["answer_text"] or lab.activity.starter) if row else lab.activity.starter)
        self.lab_notes.setPlainText(str(row["notes"] or "") if row else "")
        passed = bool(row and row["validation_status"] == "Passed")
        self.lab_status_pill.setText("Completed" if passed else "In Progress" if row else "Not Started")
        self.lab_feedback.setText("")
        self._show_result(self.lab_results, (), ())
        self.lab_continue.setEnabled(passed)
        self.lab_nav_status.setText(
            "✓ Project complete! Finish the course when you’re ready."
            if passed
            else "Run your work, write at least three clear findings, then check the project."
        )

    def _run_lab(self) -> None:
        if self._lab is None:
            return
        result = self.service.run_activity(self._lab.activity, self.lab_sql.toPlainText())
        self.lab_feedback.setText(("✅ " if result.passed else "❌ ") + result.feedback)
        self._show_result(self.lab_results, result.columns, result.rows)

    def _save_lab(self, silent: bool = False) -> None:
        if self._lab is None:
            return
        self.service.save_skills_lab_progress(
            self._lab,
            self.lab_sql.toPlainText(),
            self.lab_notes.toPlainText(),
        )
        self.lab_status_pill.setText("In Progress")
        if not silent:
            self.lab_feedback.setText("Project saved!")
        self.refresh_all()

    def _submit_lab(self) -> None:
        if self._lab is None:
            return
        result = self.service.validate_skills_lab(
            self._lab,
            self.lab_sql.toPlainText(),
            self.lab_notes.toPlainText(),
        )
        self.lab_feedback.setText(("✅ " if result.passed else "❌ ") + result.feedback)
        self._show_result(self.lab_results, result.columns, result.rows)
        if result.passed:
            self.lab_status_pill.setText("Completed")
            self.lab_continue.setEnabled(True)
            self.lab_nav_status.setText("✓ Project complete! Your work was added to Demonstrated Evidence.")
            QMessageBox.information(
                self,
                "Project Complete",
                "Your work and findings are saved, and the finished project is now part of Demonstrated Evidence.",
            )
        else:
            self.lab_status_pill.setText("In Progress")
        self.refresh_all()

    # -------------------------------------------------------------- common data
    def _save_current_work(self) -> None:
        if self.content_stack.currentIndex() == self.LESSON_PAGE:
            self._save_current_lesson_answer()
        elif self.content_stack.currentIndex() == self.ASSESSMENT_PAGE:
            self._save_assessment_answer(silent=True)
        elif self.content_stack.currentIndex() == self.LAB_PAGE and self._lab is not None:
            if self.lab_sql.toPlainText().strip() or self.lab_notes.toPlainText().strip():
                self._save_lab(silent=True)

    def _progress_milestones(self) -> tuple[Milestone, ...]:
        node_states = {node.target_key: self._node_state(node)[0] for node in self._nodes}
        current_node = next(
            (node for node in self._nodes if node.target_key == self._current_target),
            None,
        )
        milestones: list[Milestone] = []
        for path in self.catalog.program.paths:
            for track in path.tracks:
                for course in track.courses:
                    course_nodes = [node for node in self._nodes if node.course_id == course.course_id]
                    course_passed = bool(course_nodes) and all(
                        node_states.get(node.target_key) == "Passed" for node in course_nodes
                    )
                    course_started = any(
                        node_states.get(node.target_key) in {"Passed", "Answered"}
                        for node in course_nodes
                    )
                    course_current = bool(current_node and current_node.course_id == course.course_id)
                    course_state = (
                        "complete"
                        if course_passed
                        else "current"
                        if course_current
                        else "in_progress"
                        if course_started
                        else "ready"
                    )
                    milestones.append(
                        Milestone(
                            key=f"course:{course.course_id}",
                            short_label=f"C{course.order}",
                            title=f"Course {course.order}",
                            kind="course",
                            state=course_state,
                        )
                    )
                    for module in course.modules:
                        for lesson in module.lessons:
                            lesson_nodes = [
                                node
                                for node in course_nodes
                                if node.kind == "lesson_step" and node.lesson_id == lesson.lesson_id
                            ]
                            lesson_passed = bool(lesson_nodes) and all(
                                node_states.get(node.target_key) == "Passed" for node in lesson_nodes
                            )
                            lesson_started = any(
                                node_states.get(node.target_key) == "Passed" for node in lesson_nodes
                            )
                            lesson_current = bool(
                                current_node
                                and current_node.kind == "lesson_step"
                                and current_node.lesson_id == lesson.lesson_id
                            )
                            first_unlocked = bool(
                                lesson_nodes
                                and self._node_state(lesson_nodes[0])[1]
                            )
                            lesson_state = (
                                "complete"
                                if lesson_passed
                                else "current"
                                if lesson_current
                                else "in_progress"
                                if lesson_started
                                else "ready"
                                if first_unlocked
                                else "locked"
                            )
                            milestones.append(
                                Milestone(
                                    key=f"lesson:{lesson.lesson_id}",
                                    short_label=f"L{lesson.order}",
                                    title=f"Lesson {lesson.order}",
                                    kind="lesson",
                                    state=lesson_state,
                                )
                            )
        return tuple(milestones)

    def refresh_all(self) -> None:
        self._assessment_answers = {
            **(
                self.service.assessment_drafts(self.catalog.assessments()[0].assessment_id)
                if self.catalog.assessments()
                else {}
            ),
            **self._assessment_answers,
        }
        self._refresh_roadmap()
        completed = 0
        for node in self._nodes:
            state, _unlocked, _reason = self._node_state(node)
            completed += state == "Passed"
        total = max(1, len(self._nodes))
        percent = round(100 * completed / total)
        self.overall_progress.setValue(percent)
        self.roadmap_progress.setValue(percent)
        self.progress_percent.setText(f"{percent}%")
        self.progress_summary.setText(f"{completed} of {len(self._nodes)} steps finished")
        self.milestone_bar.set_milestones(self._progress_milestones())
        recommendation = self.service.next_recommendation()
        path_complete = self.service.path_complete()
        self.overview_next_title.setText(
            recommendation.title
            if recommendation
            else (
                f"{self.catalog.program.paths[0].title} complete"
                if path_complete
                else "Your next step is being refreshed"
            )
        )
        self.overview_next_reason.setText(
            recommendation.reason
            if recommendation
            else (
                "Take a look at what you completed, or revisit any lesson whenever you want."
                if path_complete
                else "Your work is safe. Academy will keep the pathway active until every required step is complete."
            )
        )
        evidence_count = len(self.service.evidence_rows())
        summary = self.service.completion_summary()
        self.recent_progress.setText(
            f"{summary['mastered']} lessons mastered • {summary['practiced']} lessons practiced • "
            f"{evidence_count} pieces of validated Academy evidence"
        )
        self.roadmap_status.setText(
            "Up next: "
            + (
                recommendation.title
                if recommendation
                else "Path complete" if path_complete else "Refreshing progress"
            )
        )
        if self._current_lesson and self._current_activity:
            self._refresh_lesson_navigation()
        if self._assessment and self._assessment_activity:
            self._refresh_assessment_navigation()
        self._select_current_roadmap_item()

    def _schema_markdown(self, activity: ActivityDefinition) -> str:
        schemas = self.service.activity_table_schemas(activity)
        if not schemas:
            return (
                "### Table schema\n"
                "> We couldn’t load the table details for this step. Please report the lesson so it can be fixed."
            )
        sections: list[str] = []
        for table_name, columns in schemas:
            rows = "\n".join(f"| `{name}` | `{data_type}` |" for name, data_type in columns)
            sections.append(
                f"### Table schema: `{table_name}`\n"
                "| Column | Data type |\n"
                "|---|---|\n"
                f"{rows}"
            )
        return "\n\n".join(sections)

    def _activity_markdown(self, activity: ActivityDefinition, *, embedded: bool = False) -> str:
        presentation = dict(activity.presentation)
        scenario = str(presentation.get("scenario") or "Practice scenario")
        introduction = str(presentation.get("introduction") or "Use what you just learned to work through the task below.")
        task = str(presentation.get("task") or activity.prompt)
        requirements = presentation.get("requirements") or []
        expected = str(presentation.get("expected_output") or "Your result should match the requested shape and values.")
        skills = presentation.get("skills_practiced") or []
        requirement_text = "\n".join(f"- {item}" for item in requirements) or "- Follow the task and check your result."
        skill_text = ", ".join(f"`{item}`" for item in skills) or activity.activity_type.value.title()
        heading = f"## Your turn: {activity.title}" if embedded else f"# {activity.title}"
        return (
            f"{heading}\n\n"
            f"> **Scenario:** {scenario}\n\n"
            f"{introduction}\n\n"
            f"{self._schema_markdown(activity)}\n\n"
            f"### Your turn\n> **Task:** {task}\n\n"
            f"### What to include\n{requirement_text}\n\n"
            f"### What you should see\n{expected}\n\n"
            f"### You’re practicing\n{skill_text}"
        )

    @staticmethod
    def _result_table() -> QTableWidget:
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(
            f"QTableWidget {{background:{COLORS.get('surface_alt', '#111A2C')};"
            "alternate-background-color:#121F34;color:#FFFFFF;"
            f"border:1px solid {COLORS.get('border', '#2B3656')};border-radius:8px;}}"
            "QHeaderView::section {background:#1B2540;color:#FFFFFF;padding:7px;"
            "border:none;border-right:1px solid #3a3d5e;font-weight:600;}"
        )
        return table

    @staticmethod
    def _show_result(table: QTableWidget, columns, rows) -> None:
        columns = tuple(columns or ())
        rows = tuple(rows or ())
        table.clear()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([str(item) for item in columns])
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(row_index, column_index, QTableWidgetItem("NULL" if value is None else str(value)))
        if columns:
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setStretchLastSection(True)

    def _restore_splitters(self) -> None:
        self.body_splitter.setSizes([330, 1080])
        self.lesson_splitter.setSizes([620, 500])
        self.lesson_work_splitter.setSizes([330, 270])
        self.assessment_splitter.setSizes([460, 610])
        self.lab_splitter.setSizes([460, 610])
        QTimer.singleShot(0, self._sync_lesson_footer_splitter)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        width = max(0, event.size().width())
        mode = "compact" if width < 900 else "medium" if width < 1220 else "wide"
        if mode == self._responsive_mode:
            return
        self._responsive_mode = mode
        compact = mode == "compact"
        self.body_splitter.setOrientation(
            Qt.Orientation.Vertical if compact else Qt.Orientation.Horizontal
        )
        for splitter in (self.lesson_splitter, self.assessment_splitter, self.lab_splitter):
            splitter.setOrientation(
                Qt.Orientation.Vertical if width < 1120 else Qt.Orientation.Horizontal
            )
        self.lesson_footer_splitter.setOrientation(
            Qt.Orientation.Vertical if width < 1120 else Qt.Orientation.Horizontal
        )
        for layout in (
            self.lesson_left_row,
            self.lesson_action_row,
            self.assessment_action_row,
            self.assessment_nav_row,
            self.lab_action_row,
            self.lab_nav_row,
        ):
            layout.setDirection(
                QBoxLayout.Direction.TopToBottom if width < 760 else QBoxLayout.Direction.LeftToRight
            )
        if compact:
            self.roadmap_list.parentWidget().setMaximumHeight(300)
        else:
            self.roadmap_list.parentWidget().setMaximumHeight(16777215)
            QTimer.singleShot(0, self._restore_splitters)
        QTimer.singleShot(0, self._sync_lesson_footer_splitter)
