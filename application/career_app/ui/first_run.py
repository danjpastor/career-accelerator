from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from career_app.onboarding.catalog import (
    PathwayCatalog,
    PathwayCatalogError,
    PathwayDefinition,
    load_pathway_catalog,
)
from career_app.onboarding.portfolio_catalog import apply_runtime_catalog
from career_app.onboarding.paths import load_reset_layout
from career_app.onboarding.portfolio_package import (
    PortfolioImportError,
    import_portfolio_package,
)
from career_app.onboarding.setup_file import write_setup_file
from career_app.services import completion_contract
from career_app.onboarding.state import (
    KEY_COMPLETED,
    KEY_DISPLAY_NAME,
    KEY_ORIGIN,
    KEY_PATHWAY,
    KEY_PORTFOLIO_STATUS,
    KEY_TOUR_COMPLETED,
    clear_seeded_portfolio_for_new_profile,
    display_name as stored_display_name,
    get_setting,
    mark_portfolio_status,
    mark_tour_completed,
    migrate_existing_profile_if_needed,
    onboarding_required,
    recompute_completion,
    reset_to_first_run,
    restart_tour,
    select_pathway,
    set_display_name,
)


TOUR_STEPS = (
    (
        0,
        "Dashboard",
        "Your daily command center. Today’s Focus shows the most important prerequisite-ready work, while Next Tasks, study time, achievements, and progress cards update from your activity.",
    ),
    (
        1,
        "Adaptive Planner",
        "The planner coordinates independent learning and portfolio tracks. It prioritizes the certificate pathway, respects prerequisites, and adjusts pacing to the available study time.",
    ),
    (
        2,
        "Learning",
        "Use Learning to update pathway progress, open guided lessons, practice concepts, and work through applied exercises without losing track of the broader plan.",
    ),
    (
        12,
        "Accelerator Academy",
        "Accelerator Academy contains program-neutral learning paths, courses, practice, Skills Lab work, assessments, and demonstrated evidence. The selected pathway supplies the curriculum.",
    ),
    (
        3,
        "Portfolio Workspace",
        "Your imported projects appear here. Complete milestones, inspect project data, open real files, document findings, and build evidence that can be discussed in interviews.",
    ),
    (
        4,
        "SQL Companion",
        "SQL Companion organizes interview problems and local DuckDB practice. Save learner-written solutions, request hints, validate work, and keep completed evidence connected to the plan.",
    ),
    (
        5,
        "Study Session",
        "Start or log focused work sessions, attach notes to the task you worked on, and use the history to understand consistency and workload.",
    ),
    (
        6,
        "Job Readiness",
        "This page turns completed learning and project work into evidence. It helps identify gaps before applications and interviews.",
    ),
    (
        7,
        "Applications",
        "Track roles, companies, status, follow-up dates, contacts, and notes in one place once the application phase begins.",
    ),
    (
        8,
        "Weekly Summary",
        "Review completed work, study time, lessons learned, blockers, and the next week’s priorities. Retrospectives keep the plan realistic.",
    ),
    (
        9,
        "Publish & Git",
        "Use publishing tools to check repository status and prepare portfolio progress for Git without mixing application state into public work.",
    ),
    (
        11,
        "Task Workspaces",
        "Task Workspaces preserve notes, starter artifacts, and the exact files associated with individual assignments.",
    ),
    (
        10,
        "Settings and Setup",
        "Settings controls pacing and technical preferences. The Setup menu can reopen portfolio import, restart this tour, or perform an explicit full first-run reset.",
    ),
)


class FullResetConfirmationDialog(QDialog):
    CONFIRMATION_PHRASE = "RESET CAREER ACCELERATOR"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Full First-Run Reset")
        self.setModal(True)
        self.resize(760, 650)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        title = QLabel("Prepare Career Accelerator for a new learner")
        title.setObjectName("DialogTitle")
        title.setStyleSheet("font-size: 21px; font-weight: 700;")
        outer.addWidget(title)

        intro = QLabel(
            "This is the destructive reset. It is different from resetting learning "
            "progress and cannot be undone inside the application."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(12)

        removed = QFrame()
        removed.setObjectName("ResetRemovedCard")
        removed.setStyleSheet(
            "QFrame#ResetRemovedCard { border: 1px solid #d97706; border-radius: 10px; padding: 4px; }"
        )
        removed_layout = QVBoxLayout(removed)
        removed_title = QLabel("REMOVED")
        removed_title.setStyleSheet("font-weight: 800; color: #b45309;")
        removed_layout.addWidget(removed_title)
        removed_text = QLabel(
            "• Selected pathway and onboarding status<br>"
            "• Portfolio projects, milestones, notes, and generated project folders<br>"
            "• DuckDB exercise progress, learner databases, SQL solutions, and submissions<br>"
            "• Demonstrated evidence, achievements, skills, concepts, and tracked completion<br>"
            "• Study sessions, applications, task workspaces, career materials, and reflections<br>"
            "• Preferences, snapshots, installed optional packs, local backups, and archives"
        )
        removed_text.setWordWrap(True)
        removed_layout.addWidget(removed_text)
        content_layout.addWidget(removed)

        preserved = QFrame()
        preserved.setObjectName("ResetPreservedCard")
        preserved.setStyleSheet(
            "QFrame#ResetPreservedCard { border: 1px solid #3b82f6; border-radius: 10px; padding: 4px; }"
        )
        preserved_layout = QVBoxLayout(preserved)
        preserved_title = QLabel("PRESERVED")
        preserved_title.setStyleSheet("font-weight: 800; color: #2563eb;")
        preserved_layout.addWidget(preserved_title)
        preserved_text = QLabel(
            "• Application source code and required folder structure<br>"
            "• Pathway definitions, approved logos, and onboarding files<br>"
            "• Accelerator Academy curricula and bundled exercise packs<br>"
            "• Starter templates, static datasets, exercises, and validation guides<br>"
            "• Repository documentation, setup scripts, and build files"
        )
        preserved_text.setWordWrap(True)
        preserved_layout.addWidget(preserved_text)
        content_layout.addWidget(preserved)

        backup = QFrame()
        backup.setStyleSheet("QFrame { border: 1px solid #6b7280; border-radius: 10px; padding: 4px; }")
        backup_layout = QVBoxLayout(backup)
        backup_title = QLabel("SAFETY BACKUP")
        backup_title.setStyleSheet("font-weight: 800;")
        backup_layout.addWidget(backup_title)
        backup_text = QLabel(
            "Before cleanup begins, Career Accelerator creates a ZIP beside the application "
            "folder. The backup is outside the reset boundary so it cannot delete itself."
        )
        backup_text.setWordWrap(True)
        backup_layout.addWidget(backup_text)
        content_layout.addWidget(backup)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        phrase_label = QLabel(
            "Type <b>RESET CAREER ACCELERATOR</b> to enable the reset button:"
        )
        phrase_label.setWordWrap(True)
        outer.addWidget(phrase_label)
        self.phrase = QLineEdit()
        self.phrase.setPlaceholderText(self.CONFIRMATION_PHRASE)
        self.phrase.setClearButtonEnabled(True)
        outer.addWidget(self.phrase)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.reset_button = QPushButton("Erase Learner Data and Reset")
        self.reset_button.setEnabled(False)
        self.reset_button.setStyleSheet(
            "QPushButton { font-weight: 700; padding: 9px 14px; }"
            "QPushButton:enabled { background: #b91c1c; color: white; }"
        )
        self.reset_button.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.reset_button)
        outer.addLayout(buttons)

        self.phrase.textChanged.connect(self._update_confirmation)

    def _update_confirmation(self, text: str) -> None:
        self.reset_button.setEnabled(text.strip() == self.CONFIRMATION_PHRASE)


class FirstRunCoordinator:
    """Bridges persistent onboarding state into the existing QMainWindow."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        repo_root: Path,
        asset_root: Path,
        version: str,
    ) -> None:
        self.conn = conn
        self.repo_root = Path(repo_root)
        self.asset_root = Path(asset_root)
        self.version = str(version)
        self.reset_layout = load_reset_layout(self.repo_root)
        self.catalog_path = self.reset_layout.configured_path("portfolio_catalog")
        self.reset_marker_path = self.reset_layout.configured_path("reset_marker")
        self.catalog: PathwayCatalog = load_pathway_catalog(
            self.reset_layout.configured_path("pathways_root")
        )
        self.host = None
        self.stack = None
        self.sidebar = None
        self.nav_buttons: list[QPushButton] = []
        self._onboarding_dialog: FirstRunWizard | None = None
        self._tour_dialog: GuidedTourDialog | None = None

    def migrate_existing_profile_if_needed(self) -> str:
        return migrate_existing_profile_if_needed(
            self.conn, reset_marker_path=self.reset_marker_path
        )

    def finalize_initialization(self) -> bool:
        return clear_seeded_portfolio_for_new_profile(
            self.conn,
            catalog_path=self.catalog_path,
        )

    def selected_pathway(self) -> PathwayDefinition | None:
        return self.catalog.get(get_setting(self.conn, KEY_PATHWAY))

    def display_name(self) -> str:
        return stored_display_name(self.conn)

    def brand_mapping(self) -> dict[str, str]:
        selected = self.selected_pathway()
        if selected is None:
            return dict(self.catalog.neutral_brand)
        return {
            "application_name": selected.application_name,
            "window_title": selected.window_title,
            "logo_path": selected.logo_path,
            "horizontal_logo_path": selected.horizontal_logo_path,
            "program_icon_path": selected.program_icon_path,
            "app_icon_path": selected.app_icon_path,
            "app_user_model_id": selected.app_user_model_id,
        }

    def apply_branding(self, host=None) -> None:
        host = host or self.host
        if host is None:
            return
        brand = self.brand_mapping()
        selected = self.selected_pathway()
        title = brand["window_title"]
        if selected is not None:
            title = f"{title} v{self.version}"
        host.setWindowTitle(title)

        icon_path = self.asset_root / brand["app_icon_path"]
        if icon_path.is_file():
            icon = QIcon(str(icon_path))
            host.setWindowIcon(icon)
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(icon)
            host.app_icon_path = icon_path

        logo_path = self.asset_root / brand["horizontal_logo_path"]
        if logo_path.is_file() and hasattr(host, "_sidebar_logo_source"):
            host._sidebar_logo_source = QPixmap(str(logo_path))
            update = getattr(host, "_update_sidebar_brand_logo", None)
            if callable(update):
                update()

        if sys.platform == "win32":
            try:
                import ctypes

                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    brand["app_user_model_id"]
                )
            except Exception:
                pass

    def attach(
        self,
        host,
        stack: QStackedWidget,
        sidebar: QWidget,
        nav_buttons: list[QPushButton],
    ) -> None:
        self.host = host
        self.stack = stack
        self.sidebar = sidebar
        self.nav_buttons = list(nav_buttons)
        self.apply_branding(host)
        self._install_setup_menu()
        if onboarding_required(self.conn):
            self._set_shell_enabled(False)
            QTimer.singleShot(0, self.show_required_onboarding)

    def _set_shell_enabled(self, enabled: bool) -> None:
        if self.stack is not None:
            self.stack.setEnabled(enabled)
        if self.sidebar is not None:
            self.sidebar.setEnabled(enabled)

    def _install_setup_menu(self) -> None:
        if self.host is None or getattr(self.host, "_career_setup_menu_installed", False):
            return
        menu = self.host.menuBar().addMenu("Setup")

        portfolio_action = QAction("Portfolio Setup and Import…", self.host)
        portfolio_action.triggered.connect(self.open_portfolio_setup)
        menu.addAction(portfolio_action)

        tour_action = QAction("Restart Guided Tour", self.host)
        tour_action.triggered.connect(self.restart_guided_tour)
        menu.addAction(tour_action)

        menu.addSeparator()
        pathway_action = QAction("Pathway Information…", self.host)
        pathway_action.triggered.connect(self.show_pathway_information)
        menu.addAction(pathway_action)

        reset_action = QAction("Full First-Run Reset…", self.host)
        reset_action.triggered.connect(self.full_first_run_reset)
        menu.addAction(reset_action)
        self.host._career_setup_menu_installed = True

    def show_required_onboarding(self) -> None:
        if self.host is None:
            return
        if (
            get_setting(self.conn, KEY_DISPLAY_NAME) is None
            or get_setting(self.conn, KEY_PATHWAY) is None
            or get_setting(self.conn, KEY_PORTFOLIO_STATUS, "pending") == "pending"
        ):
            dialog = FirstRunWizard(self, self.host)
            self._onboarding_dialog = dialog
            result = dialog.exec()
            self._onboarding_dialog = None
            if result != QDialog.DialogCode.Accepted:
                QApplication.quit()
                return
        if get_setting(self.conn, KEY_TOUR_COMPLETED, "0") != "1":
            self._run_tour(required=True)
        else:
            recompute_completion(self.conn)
            self._set_shell_enabled(True)
            self.apply_branding()

    def _run_tour(self, *, required: bool) -> None:
        if self.host is None:
            return
        dialog = GuidedTourDialog(self, self.host, required=required)
        self._tour_dialog = dialog
        dialog.exec()
        self._tour_dialog = None
        self._set_shell_enabled(True)
        self.apply_branding()
        if self.host is not None:
            refresh = getattr(self.host, "refresh_all", None)
            if callable(refresh):
                refresh()
            navigate = getattr(self.host, "navigate", None)
            if callable(navigate):
                navigate(0)

    def restart_guided_tour(self) -> None:
        restart_tour(self.conn)
        self._set_shell_enabled(False)
        self._run_tour(required=False)

    def open_portfolio_setup(self) -> None:
        if self.selected_pathway() is None:
            self._set_shell_enabled(False)
            self.show_required_onboarding()
            return
        dialog = PortfolioSetupDialog(self, self.host, allow_replace=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_portfolio_ui()

    def refresh_portfolio_ui(self) -> None:
        if self.host is None:
            return
        try:
            from career_app.database import state as read_state
            from career_app.data import roadmap
            from career_app.services import tracks
            from career_app.ui.portfolio_hub import PortfolioHubWidget

            self.host.state = read_state(self.conn)
            tracks.sync_all(self.conn, self.host.state)
            self.host.state = read_state(self.conn)

            for widget in self.host.findChildren(PortfolioHubWidget):
                combo = widget.project_combo
                current = combo.currentData()
                combo.blockSignals(True)
                combo.clear()
                for project_id, name in roadmap.PROJECT_NAMES.items():
                    combo.addItem(f"{project_id} — {name}", int(project_id))
                index = combo.findData(current)
                combo.setCurrentIndex(index if index >= 0 else 0)
                combo.blockSignals(False)
                widget.refresh_all()
        except Exception:
            pass
        refresh = getattr(self.host, "refresh_all", None)
        if callable(refresh):
            refresh()

    def show_pathway_information(self) -> None:
        selected = self.selected_pathway()
        if selected is None:
            text = "No pathway has been selected."
        else:
            tracks = "\n".join(f"• {item}" for item in selected.track_shells)
            text = (
                f"Selected pathway: {selected.display_name}\n\n"
                f"{selected.description}\n\nPlanned tracks:\n{tracks}\n\n"
                "IT Support, Cybersecurity, and Software Engineering are configuration shells in this release."
            )
        QMessageBox.information(self.host, "Career Accelerator Pathway", text)

    def reset_summary_text(self) -> str:
        return (
            "Full First-Run Reset removes all learner-specific database records and "
            "configured learner-owned files, then returns Career Accelerator to the "
            "neutral locked pathway-selection screen. Static curricula, starter "
            "datasets, exercises, templates, source code, and pathway graphics remain."
        )

    def full_first_run_reset(self) -> None:
        dialog = FullResetConfirmationDialog(self.host)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if self.host is not None:
            for timer_name in (
                "timer",
                "autosave_timer",
                "greeting_timer",
                "motivation_timer",
            ):
                timer = getattr(self.host, timer_name, None)
                if timer is not None and hasattr(timer, "stop"):
                    timer.stop()
        self.conn.commit()
        try:
            report = reset_to_first_run(
                self.conn,
                application_root=self.repo_root,
                catalog_path=self.catalog_path,
                manifest_path=self.reset_layout.manifest_path,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.host,
                "Full Reset Failed",
                "Career Accelerator could not complete the full first-run reset. "
                "The application has not recorded a successful reset.\n\n" + str(exc),
            )
            return

        backup = str(report.backup_path) if report.backup_path else "No backup requested"
        summary = QMessageBox(self.host)
        summary.setIcon(QMessageBox.Icon.Information)
        summary.setWindowTitle("Full Reset Complete")
        summary.setText("Career Accelerator is ready for a new learner.")
        summary.setInformativeText(
            "The application will close now. On the next launch it will open with the "
            "neutral Career Accelerator branding and locked Step 1 pathway selector.\n\n"
            f"Safety backup:\n{backup}"
        )
        summary.setDetailedText(
            "Database tables cleared: " + str(len(report.database_tables_cleared)) + "\n"
            "Learner paths removed: " + str(len(report.removed_paths)) + "\n"
            "Secondary databases removed: " + str(len(report.runtime_databases_removed)) + "\n"
            "Reset marker: " + str(report.reset_marker_path)
        )
        summary.exec()
        app = QApplication.instance()
        if self.host is not None:
            self.host.close()
        if app is not None:
            app.quit()


class _PathwayCard(QFrame):
    def __init__(
        self,
        definition: PathwayDefinition,
        group: QButtonGroup,
        asset_root: Path,
        parent=None,
    ):
        super().__init__(parent)
        self.definition = definition
        self.setObjectName("PathwayCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setMinimumHeight(112)
        logo_path = Path(asset_root) / definition.logo_path
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            logo.setPixmap(
                pixmap.scaled(
                    190,
                    112,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        name = QLabel(definition.display_name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("font-size:16pt;font-weight:700;")
        description = QLabel(definition.description)
        description.setWordWrap(True)
        description.setObjectName("Muted")
        status = QLabel("Available" if definition.is_available else "Coming Soon")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet(
            "font-weight:700;color:#5FE0C2;" if definition.is_available else "font-weight:700;color:#A9B4C6;"
        )
        button = QPushButton(
            "Select pathway" if definition.is_available else "Coming Soon"
        )
        button.setCheckable(definition.is_available)
        button.setEnabled(definition.is_available)
        button.setProperty("pathway_id", definition.pathway_id)
        if definition.is_available:
            button.setObjectName("Primary")
            group.addButton(button)

        layout.addWidget(logo)
        layout.addWidget(name)
        layout.addWidget(status)
        layout.addWidget(description, 1)
        layout.addWidget(button)
        self.button = button


class FirstRunWizard(QDialog):
    def __init__(self, coordinator: FirstRunCoordinator, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator
        self.selected_pathway_id = get_setting(coordinator.conn, KEY_PATHWAY)
        self.setWindowTitle("Career Accelerator Setup")
        self.setModal(True)
        self.resize(920, 680)
        self.setMinimumSize(760, 560)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 22, 24, 22)
        outer.setSpacing(14)
        self.step_label = QLabel()
        self.step_label.setStyleSheet("font-weight:700;color:#A9B4C6;")
        outer.addWidget(self.step_label)
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)
        self.stack.addWidget(self._build_pathway_page())
        self.stack.addWidget(self._build_portfolio_page())

        controls = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._back)
        self.next_button = QPushButton("Continue")
        self.next_button.setObjectName("Primary")
        self.next_button.clicked.connect(self._next)
        controls.addWidget(self.back_button)
        controls.addStretch()
        controls.addWidget(self.next_button)
        outer.addLayout(controls)
        self.stack.currentChanged.connect(self._update_controls)

        initial = (
            1
            if self.selected_pathway_id and get_setting(coordinator.conn, KEY_DISPLAY_NAME)
            else 0
        )
        self.stack.setCurrentIndex(initial)
        self._update_controls()

    def _build_pathway_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        neutral_logo = QLabel()
        neutral_logo.setScaledContents(False)
        neutral_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        neutral_logo_path = (
            self.coordinator.asset_root
            / self.coordinator.catalog.neutral_brand["logo_path"]
        )
        if neutral_logo_path.is_file():
            neutral_logo.setPixmap(
                QPixmap(str(neutral_logo_path)).scaled(
                    280,
                    170,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(neutral_logo)
        title = QLabel("Choose your Career Accelerator pathway")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22pt;font-weight:800;")
        intro = QLabel(
            "Choose your pathway to begin a fixed 90-day, zero-to-hire-ready program. "
            "The application remains locked until a pathway and greeting name are selected. "
            "Branding, learning tracks, portfolio requirements, and deadline-aware planner rules "
            "load from this choice."
        )
        intro.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(intro)

        name_row = QHBoxLayout()
        name_label = QLabel("Name for your greeting")
        name_label.setMinimumWidth(165)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your preferred name")
        self.name_input.setMaxLength(60)
        self.name_input.setText(get_setting(self.coordinator.conn, KEY_DISPLAY_NAME, "") or "")
        self.name_input.setToolTip(
            "This name appears in the greeting at the top of the Dashboard."
        )
        self.name_input.textChanged.connect(self._update_controls)
        name_row.addWidget(name_label)
        name_row.addWidget(self.name_input, 1)
        layout.addLayout(name_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(12)
        self.pathway_group = QButtonGroup(self)
        self.pathway_group.setExclusive(True)
        for index, definition in enumerate(self.coordinator.catalog.pathways):
            card = _PathwayCard(
                definition, self.pathway_group, self.coordinator.asset_root
            )
            grid.addWidget(card, index // 2, index % 2)
            card.button.clicked.connect(
                lambda checked=False, pathway_id=definition.pathway_id: self._select_pathway(pathway_id)
            )
            if definition.pathway_id == self.selected_pathway_id:
                card.button.setChecked(True)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _build_portfolio_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Create personalized portfolio projects")
        title.setStyleSheet("font-size:22pt;font-weight:800;")
        intro = QLabel(
            "Download one setup file, upload it to ChatGPT, answer the focused questions, then import "
            "the JSON file ChatGPT creates. The import can populate projects, milestones, data tables, "
            "data dictionaries, guides, and starter files."
        )
        intro.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(intro)

        instructions = QLabel(
            "1. Download the ChatGPT Setup File.\n"
            "2. Upload that file to ChatGPT.\n"
            "3. Work with ChatGPT to approve strong, personalized projects.\n"
            "4. Download the .career-portfolio.json file it returns.\n"
            "5. Import the package here."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(
            "padding:16px;border:1px solid #263750;border-radius:10px;background:#101A29;"
        )
        layout.addWidget(instructions)

        buttons = QHBoxLayout()
        download = QPushButton("Download ChatGPT Setup File")
        download.setObjectName("Primary")
        download.clicked.connect(self._download_setup)
        import_button = QPushButton("Import Portfolio Package")
        import_button.clicked.connect(self._import_package)
        buttons.addWidget(download)
        buttons.addWidget(import_button)
        layout.addLayout(buttons)

        self.portfolio_status = QLabel()
        self.portfolio_status.setWordWrap(True)
        self.portfolio_status.setObjectName("Muted")
        layout.addWidget(self.portfolio_status)
        layout.addStretch()

        skip = QPushButton("Continue with a blank portfolio for now")
        skip.clicked.connect(self._skip_portfolio)
        layout.addWidget(skip, alignment=Qt.AlignmentFlag.AlignLeft)
        return page

    def _select_pathway(self, pathway_id: str) -> None:
        try:
            select_pathway(self.coordinator.conn, self.coordinator.catalog, pathway_id)
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Select Pathway", str(exc))
            return
        self.selected_pathway_id = pathway_id
        self.coordinator.apply_branding()
        self._update_controls()

    def _download_setup(self) -> None:
        pathway = self.coordinator.selected_pathway()
        if pathway is None:
            QMessageBox.warning(self, "Select a Pathway", "Choose the Data Analytics pathway first.")
            return
        default = str(Path.home() / "Career_Accelerator_Portfolio_Setup.md")
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Save ChatGPT Portfolio Setup File",
            default,
            "Markdown files (*.md);;All files (*)",
        )
        if not destination:
            return
        try:
            path = write_setup_file(
                destination, pathway, learner_name=self.coordinator.display_name()
            )
        except Exception as exc:
            QMessageBox.warning(self, "Could Not Create Setup File", str(exc))
            return
        self.portfolio_status.setText(f"Setup file created: {path}")
        QMessageBox.information(
            self,
            "Setup File Ready",
            "Upload the saved Markdown file to ChatGPT. When ChatGPT returns the portfolio JSON, come back and choose Import Portfolio Package.",
        )

    def _import_package(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Import Career Accelerator Portfolio Package",
            str(Path.home()),
            "Career Portfolio (*.career-portfolio.json *.json);;JSON files (*.json)",
        )
        if not source:
            return
        try:
            result = import_portfolio_package(
                self.coordinator.conn,
                self.coordinator.repo_root,
                source,
                replace_existing=False,
            )
        except PortfolioImportError as exc:
            QMessageBox.warning(self, "Invalid Portfolio Package", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Portfolio Import Failed", str(exc))
            return
        self.portfolio_status.setText(
            f"Imported {result.project_count} projects, {result.milestone_count} milestones, "
            f"and {result.file_count} generated files."
        )
        self.coordinator.refresh_portfolio_ui()
        self._update_controls()

    def _skip_portfolio(self) -> None:
        response = QMessageBox.question(
            self,
            "Leave Portfolio Blank",
            "Career Accelerator will remain usable, but Portfolio Workspace will stay empty until a package is imported from Setup → Portfolio Setup and Import. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return
        mark_portfolio_status(self.coordinator.conn, "skipped")
        apply_runtime_catalog([])
        self.portfolio_status.setText("Portfolio setup skipped. The workspace will remain blank.")
        self._update_controls()

    def _back(self) -> None:
        self.stack.setCurrentIndex(max(0, self.stack.currentIndex() - 1))

    def _next(self) -> None:
        index = self.stack.currentIndex()
        if index == 0:
            if self.coordinator.selected_pathway() is None:
                QMessageBox.warning(self, "Select a Pathway", "Choose an available pathway to continue.")
                return
            try:
                set_display_name(self.coordinator.conn, self.name_input.text())
            except Exception as exc:
                QMessageBox.warning(self, "Enter Your Name", str(exc))
                self.name_input.setFocus()
                return
            completion_contract.ensure_contract(self.coordinator.conn, {
                "current_week": 1,
                "google_course": 1,
                "google_module": 1,
                "current_project": 1,
                "weekly_target_hours": completion_contract.DEFAULT_WEEKLY_HOURS,
            })
            self.stack.setCurrentIndex(1)
            return
        status = get_setting(self.coordinator.conn, KEY_PORTFOLIO_STATUS, "pending")
        if status not in {"completed", "skipped"}:
            QMessageBox.warning(
                self,
                "Portfolio Setup Required",
                "Import the ChatGPT package or deliberately continue with a blank portfolio.",
            )
            return
        self.accept()

    def _update_controls(self, *_args) -> None:
        index = self.stack.currentIndex()
        self.step_label.setText(f"STEP {index + 1} OF 3")
        self.back_button.setVisible(index > 0)
        if index == 0:
            self.next_button.setText("Continue")
            has_name = bool(getattr(self, "name_input", None) and self.name_input.text().strip())
            self.next_button.setEnabled(
                has_name and self.coordinator.selected_pathway() is not None
            )
        else:
            self.next_button.setText("Start Guided Tour")
            status = get_setting(self.coordinator.conn, KEY_PORTFOLIO_STATUS, "pending")
            self.next_button.setEnabled(status in {"completed", "skipped"})

    def reject(self) -> None:
        response = QMessageBox.question(
            self,
            "Exit Setup",
            "Career Accelerator remains locked until setup is completed. Exit the application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response == QMessageBox.StandardButton.Yes:
            super().reject()


class PortfolioSetupDialog(QDialog):
    def __init__(
        self,
        coordinator: FirstRunCoordinator,
        parent=None,
        *,
        allow_replace: bool,
    ) -> None:
        super().__init__(parent)
        self.coordinator = coordinator
        self.allow_replace = allow_replace
        self.setWindowTitle("Portfolio Setup and Import")
        self.resize(700, 430)
        layout = QVBoxLayout(self)
        title = QLabel("Personalized Portfolio Setup")
        title.setStyleSheet("font-size:20pt;font-weight:800;")
        body = QLabel(
            "Download the pathway-specific ChatGPT file or import a completed Career Accelerator portfolio package. "
            "Existing portfolio data is never replaced without a separate confirmation and an automatic backup."
        )
        body.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(body)

        download = QPushButton("Download ChatGPT Setup File")
        download.setObjectName("Primary")
        download.clicked.connect(self._download)
        import_button = QPushButton("Import Portfolio Package")
        import_button.clicked.connect(self._import)
        layout.addWidget(download)
        layout.addWidget(import_button)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

    def _download(self) -> None:
        pathway = self.coordinator.selected_pathway()
        if pathway is None:
            QMessageBox.warning(self, "No Pathway", "Select a pathway before creating portfolio projects.")
            return
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Save ChatGPT Portfolio Setup File",
            str(Path.home() / "Career_Accelerator_Portfolio_Setup.md"),
            "Markdown files (*.md)",
        )
        if destination:
            try:
                path = write_setup_file(
                    destination,
                    pathway,
                    learner_name=self.coordinator.display_name(),
                )
                self.status.setText(f"Created {path}")
            except Exception as exc:
                QMessageBox.warning(self, "Could Not Create File", str(exc))

    def _import(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Import Career Accelerator Portfolio Package",
            str(Path.home()),
            "Career Portfolio (*.career-portfolio.json *.json);;JSON files (*.json)",
        )
        if not source:
            return
        replace = False
        if self.allow_replace:
            row = self.coordinator.conn.execute("SELECT 1 FROM project_tasks LIMIT 1").fetchone()
            if row:
                response = QMessageBox.warning(
                    self,
                    "Replace Existing Portfolio",
                    "Existing portfolio database records will be backed up and replaced. Existing project folders with the same generated names will be archived. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if response != QMessageBox.StandardButton.Yes:
                    return
                replace = True
        try:
            result = import_portfolio_package(
                self.coordinator.conn,
                self.coordinator.repo_root,
                source,
                replace_existing=replace,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Import Failed", str(exc))
            return
        self.coordinator.refresh_portfolio_ui()
        backup = f" Backup: {result.backup_path}" if result.backup_path else ""
        self.status.setText(
            f"Imported {result.project_count} projects and {result.milestone_count} milestones.{backup}"
        )


class GuidedTourDialog(QDialog):
    def __init__(
        self,
        coordinator: FirstRunCoordinator,
        parent=None,
        *,
        required: bool,
    ) -> None:
        super().__init__(parent)
        self.coordinator = coordinator
        self.required = required
        self.index = 0
        self._highlighted_button: QPushButton | None = None
        self._old_button_style = ""
        self.setWindowTitle("Career Accelerator Guided Tour")
        self.setModal(True)
        self.resize(610, 360)
        self.setMinimumSize(520, 310)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        self.progress = QLabel()
        self.progress.setStyleSheet("font-weight:700;color:#A9B4C6;")
        self.title = QLabel()
        self.title.setStyleSheet("font-size:22pt;font-weight:800;")
        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.progress)
        layout.addWidget(self.title)
        layout.addWidget(self.body, 1)

        controls = QHBoxLayout()
        self.back = QPushButton("Back")
        self.back.clicked.connect(self._previous)
        skip = QPushButton("Skip Tour")
        skip.clicked.connect(self._skip)
        self.next = QPushButton("Next")
        self.next.setObjectName("Primary")
        self.next.clicked.connect(self._advance)
        controls.addWidget(self.back)
        controls.addWidget(skip)
        controls.addStretch()
        controls.addWidget(self.next)
        layout.addLayout(controls)
        self._show_step()

    def _clear_highlight(self) -> None:
        if self._highlighted_button is not None:
            self._highlighted_button.setStyleSheet(self._old_button_style)
            self._highlighted_button = None
            self._old_button_style = ""

    def _show_step(self) -> None:
        self._clear_highlight()
        stack_index, title, body = TOUR_STEPS[self.index]
        self.progress.setText(f"STEP 3 OF 3  •  TOUR {self.index + 1} OF {len(TOUR_STEPS)}")
        self.title.setText(title)
        self.body.setText(body)
        self.back.setEnabled(self.index > 0)
        self.next.setText("Finish Tour" if self.index == len(TOUR_STEPS) - 1 else "Next")

        host = self.coordinator.host
        navigate = getattr(host, "navigate", None)
        if callable(navigate):
            navigate(stack_index)
        for (label, nav_index), button in zip(getattr(host, "NAV", ()), self.coordinator.nav_buttons):
            if nav_index == stack_index:
                self._old_button_style = button.styleSheet()
                button.setStyleSheet(
                    self._old_button_style
                    + ";border:2px solid #75D5FF;background:#213656;font-weight:800;"
                )
                self._highlighted_button = button
                break
        else:
            for position, button in enumerate(self.coordinator.nav_buttons):
                # NAV order is not equal to stacked index because Academy is index 12.
                text = button.text().strip().lower()
                if title.lower() in text or (title == "Settings and Setup" and "settings" in text):
                    self._old_button_style = button.styleSheet()
                    button.setStyleSheet(
                        self._old_button_style
                        + ";border:2px solid #75D5FF;background:#213656;font-weight:800;"
                    )
                    self._highlighted_button = button
                    break

    def _previous(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._show_step()

    def _advance(self) -> None:
        if self.index < len(TOUR_STEPS) - 1:
            self.index += 1
            self._show_step()
            return
        self._complete()

    def _skip(self) -> None:
        response = QMessageBox.question(
            self,
            "Skip Guided Tour",
            "The tour can be restarted later from the Setup menu. Mark it complete now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response == QMessageBox.StandardButton.Yes:
            self._complete()

    def _complete(self) -> None:
        self._clear_highlight()
        mark_tour_completed(self.coordinator.conn)
        self.accept()

    def reject(self) -> None:
        if self.required:
            self._skip()
        else:
            self._clear_highlight()
            super().reject()
