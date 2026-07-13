from __future__ import annotations

import os
import re
import subprocess
import sys
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROGRESS_CONFIG = ROOT / "progress-data.yml"
APP_CONFIG = ROOT / "app-config.yml"

PROJECTS = {
    1: ROOT / "projects" / "project-01-vfx-production-intelligence",
    2: ROOT / "projects" / "project-02-retail-operations",
    3: ROOT / "projects" / "project-03-movie-industry-financial-analytics",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def current_week_file(config: dict) -> Path:
    week = int(config["program"]["current_week"])
    return ROOT / "weeks" / f"week-{week:02d}" / "README.md"


def current_retro_file(config: dict) -> Path:
    week = int(config["program"]["current_week"])
    return ROOT / "weeks" / f"week-{week:02d}" / "RETROSPECTIVE.md"


def parse_checkboxes(text: str) -> list[tuple[int, bool, str]]:
    tasks = []
    for line_no, line in enumerate(text.splitlines()):
        match = re.match(r"^(\s*)- \[([ xX])\] (.+)$", line)
        if match:
            tasks.append((line_no, match.group(2).lower() == "x", match.group(3)))
    return tasks


def parse_daily_log(text: str) -> list[list[str]]:
    match = re.search(r"<!-- DAILY_LOG_START -->(.*?)<!-- DAILY_LOG_END -->", text, re.S)
    if not match:
        return []
    rows = []
    for line in match.group(1).splitlines():
        if not line.startswith("|") or "---" in line or "| Date |" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 6:
            rows.append(cells[:6])
    return rows


def run_progress_update() -> tuple[bool, str]:
    script = ROOT / "scripts" / "update_progress.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, result.stderr or result.stdout or "Unknown progress update error."
    return True, result.stdout.strip() or "Progress updated."


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


class ScrollableFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)

        self.inner.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class CareerAcceleratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.progress = load_yaml(PROGRESS_CONFIG)
        self.app_config = load_yaml(APP_CONFIG)
        self.title(f"{self.app_config['app']['title']} v{self.app_config['app']['version']}")
        self.geometry("1180x780")
        self.minsize(980, 680)

        self.style = ttk.Style(self)
        available = self.style.theme_names()
        if "vista" in available:
            self.style.theme_use("vista")
        elif "clam" in available:
            self.style.theme_use("clam")

        self.style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        self.style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
        self.style.configure("Metric.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("Subtle.TLabel", foreground="#666666")
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

        self.task_vars: list[tuple[int, tk.BooleanVar, str]] = []
        self.project_vars: list[tuple[int, tk.BooleanVar, str]] = []

        self._build_shell()
        self.refresh_all()

    def _build_shell(self):
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")

        ttk.Label(header, text="Career Accelerator", style="Title.TLabel").pack(side="left")

        self.header_status = ttk.Label(header, text="", style="Subtle.TLabel")
        self.header_status.pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.dashboard_tab = ttk.Frame(self.notebook, padding=14)
        self.today_tab = ttk.Frame(self.notebook, padding=14)
        self.session_tab = ttk.Frame(self.notebook, padding=14)
        self.learning_tab = ttk.Frame(self.notebook, padding=14)
        self.portfolio_tab = ttk.Frame(self.notebook, padding=14)
        self.sql_tab = ttk.Frame(self.notebook, padding=14)
        self.review_tab = ttk.Frame(self.notebook, padding=14)
        self.git_tab = ttk.Frame(self.notebook, padding=14)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.today_tab, text="Today's Tasks")
        self.notebook.add(self.session_tab, text="Study Session")
        self.notebook.add(self.learning_tab, text="Learning")
        self.notebook.add(self.portfolio_tab, text="Portfolio")
        self.notebook.add(self.sql_tab, text="SQL Practice")
        self.notebook.add(self.review_tab, text="Weekly Review")
        self.notebook.add(self.git_tab, text="Git")

        self._build_dashboard()
        self._build_today()
        self._build_session()
        self._build_learning()
        self._build_portfolio()
        self._build_sql()
        self._build_review()
        self._build_git()

        footer = ttk.Frame(self, padding=(14, 0, 14, 12))
        footer.pack(fill="x")

        ttk.Button(
            footer, text="Refresh", command=self.refresh_all
        ).pack(side="left")

        ttk.Button(
            footer, text="Open Repository", command=lambda: open_path(ROOT)
        ).pack(side="left", padx=8)

        ttk.Button(
            footer, text="Open Current Week",
            command=lambda: open_path(current_week_file(self.progress))
        ).pack(side="left")

        ttk.Button(
            footer, text="Exit", command=self.destroy
        ).pack(side="right")

    def _metric_card(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=12)
        value = ttk.Label(frame, text="—", style="Metric.TLabel")
        value.pack(anchor="w")
        detail = ttk.Label(frame, text="", style="Subtle.TLabel")
        detail.pack(anchor="w", pady=(4, 0))
        return frame, value, detail

    def _build_dashboard(self):
        self.dashboard_tab.columnconfigure((0, 1, 2), weight=1)

        cards = [
            ("Current Sprint", "sprint"),
            ("Weekly Completion", "week"),
            ("Hours This Week", "hours"),
            ("Google Certificate", "google"),
            ("SQL Practice", "sql"),
            ("Portfolio", "portfolio"),
        ]

        self.metric_widgets = {}
        for idx, (title, key) in enumerate(cards):
            frame, value, detail = self._metric_card(self.dashboard_tab, title)
            frame.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=6, pady=6)
            self.metric_widgets[key] = (value, detail)

        current = ttk.LabelFrame(self.dashboard_tab, text="Current Focus", padding=14)
        current.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=6, pady=(14, 6))
        self.current_focus = ttk.Label(current, text="", wraplength=980, justify="left")
        self.current_focus.pack(anchor="w")

        actions = ttk.Frame(self.dashboard_tab)
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=12)

        ttk.Button(
            actions, text="Start Study Session",
            style="Accent.TButton",
            command=lambda: self.notebook.select(self.session_tab),
        ).pack(side="left")

        ttk.Button(
            actions, text="View Today's Tasks",
            command=lambda: self.notebook.select(self.today_tab),
        ).pack(side="left", padx=8)

        ttk.Button(
            actions, text="Refresh Dashboards",
            command=self.refresh_dashboards,
        ).pack(side="left")

    def _build_today(self):
        top = ttk.Frame(self.today_tab)
        top.pack(fill="x")
        self.today_title = ttk.Label(top, text="", style="Section.TLabel")
        self.today_title.pack(side="left")

        ttk.Button(
            top, text="Save Task Changes", command=self.save_tasks
        ).pack(side="right")

        self.today_scroll = ScrollableFrame(self.today_tab)
        self.today_scroll.pack(fill="both", expand=True, pady=(10, 0))

    def _build_session(self):
        ttk.Label(
            self.session_tab,
            text="Log Study Session",
            style="Section.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        fields = [
            ("Date", "date"),
            ("Hours Studied", "hours"),
            ("Google Progress", "google"),
            ("DataCamp Progress", "datacamp"),
            ("SQL Problems Completed", "sql"),
            ("Portfolio Progress", "portfolio"),
        ]

        self.session_entries = {}
        for row, (label, key) in enumerate(fields, start=1):
            ttk.Label(self.session_tab, text=label).grid(row=row, column=0, sticky="w", pady=7)
            entry = ttk.Entry(self.session_tab, width=76)
            entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=7)
            self.session_entries[key] = entry

        self.session_tab.columnconfigure(1, weight=1)

        self.session_entries["date"].insert(0, date.today().isoformat())
        self.session_entries["hours"].insert(
            0, str(self.app_config["preferences"]["default_session_hours"])
        )
        self.session_entries["sql"].insert(0, "0")

        ttk.Button(
            self.session_tab,
            text="Finish Session and Update Progress",
            style="Accent.TButton",
            command=self.finish_session,
        ).grid(row=len(fields) + 1, column=1, sticky="e", pady=18)

        recent_frame = ttk.LabelFrame(self.session_tab, text="Recent Sessions", padding=8)
        recent_frame.grid(
            row=len(fields) + 2, column=0, columnspan=2,
            sticky="nsew", pady=(10, 0)
        )
        self.session_tab.rowconfigure(len(fields) + 2, weight=1)

        self.recent_tree = ttk.Treeview(
            recent_frame,
            columns=("date", "hours", "google", "datacamp", "sql", "portfolio"),
            show="headings",
            height=8,
        )
        widths = [100, 75, 200, 180, 70, 260]
        labels = ["Date", "Hours", "Google", "DataCamp", "SQL", "Portfolio"]
        for col, width, label in zip(self.recent_tree["columns"], widths, labels):
            self.recent_tree.heading(col, text=label)
            self.recent_tree.column(col, width=width, anchor="w")
        self.recent_tree.pack(fill="both", expand=True)

    def _build_learning(self):
        self.learning_tab.columnconfigure(1, weight=1)

        ttk.Label(
            self.learning_tab, text="Google Data Analytics",
            style="Section.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.learning_entries = {}
        fields = [
            ("Current Course", "course"),
            ("Current Module", "module"),
            ("Weekly Target Hours", "hours"),
        ]
        for row, (label, key) in enumerate(fields, start=1):
            ttk.Label(self.learning_tab, text=label).grid(row=row, column=0, sticky="w", pady=7)
            entry = ttk.Entry(self.learning_tab, width=20)
            entry.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=7)
            self.learning_entries[key] = entry

        ttk.Button(
            self.learning_tab, text="Save Learning Progress",
            command=self.save_learning_progress
        ).grid(row=4, column=1, sticky="w", pady=14)

        guidance = ttk.LabelFrame(self.learning_tab, text="Current Learning Plan", padding=12)
        guidance.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        self.learning_guidance = ttk.Label(guidance, text="", wraplength=900, justify="left")
        self.learning_guidance.pack(anchor="w")

    def _build_portfolio(self):
        top = ttk.Frame(self.portfolio_tab)
        top.pack(fill="x")

        ttk.Label(top, text="Portfolio Project", style="Section.TLabel").pack(side="left")

        self.project_selector = ttk.Combobox(
            top,
            state="readonly",
            values=[
                "1 — VFX Production Intelligence",
                "2 — Retail Operations Performance",
                "3 — Movie Industry Financial Analytics",
            ],
            width=42,
        )
        self.project_selector.pack(side="left", padx=12)
        self.project_selector.bind("<<ComboboxSelected>>", lambda _: self.load_project_tasks())

        ttk.Button(
            top, text="Set Active Project", command=self.set_active_project
        ).pack(side="left")

        ttk.Button(
            top, text="Save Project Tasks", command=self.save_project_tasks
        ).pack(side="right")

        self.portfolio_scroll = ScrollableFrame(self.portfolio_tab)
        self.portfolio_scroll.pack(fill="both", expand=True, pady=(10, 0))

    def _build_sql(self):
        ttk.Label(
            self.sql_tab, text="Add SQL Practice Problem",
            style="Section.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        fields = [
            ("Problem Title", "title"),
            ("Difficulty", "difficulty"),
            ("Concepts", "concepts"),
        ]
        self.sql_entries = {}
        for row, (label, key) in enumerate(fields, start=1):
            ttk.Label(self.sql_tab, text=label).grid(row=row, column=0, sticky="w", pady=7)
            entry = ttk.Entry(self.sql_tab, width=70)
            entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=7)
            self.sql_entries[key] = entry

        self.sql_tab.columnconfigure(1, weight=1)
        self.sql_entries["difficulty"].insert(0, "Easy")

        buttons = ttk.Frame(self.sql_tab)
        buttons.grid(row=4, column=1, sticky="e", pady=14)

        ttk.Button(
            buttons, text="Create Solution File",
            command=self.create_sql_solution
        ).pack(side="left")

        ttk.Button(
            buttons, text="Open SQL Folder",
            command=lambda: open_path(ROOT / "resources" / "sql" / "datalemur")
        ).pack(side="left", padx=8)

        list_frame = ttk.LabelFrame(self.sql_tab, text="Completed SQL Files", padding=8)
        list_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        self.sql_tab.rowconfigure(5, weight=1)

        self.sql_list = tk.Listbox(list_frame)
        self.sql_list.pack(fill="both", expand=True)

    def _build_review(self):
        ttk.Label(
            self.review_tab, text="Weekly Review",
            style="Section.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.review_fields = {}
        labels = [
            ("Biggest Win", "Wins"),
            ("Primary Blocker", "Blockers"),
            ("SQL Topic to Review", "SQL Topics to Review"),
            ("Next Week Adjustment", "Week 2 Adjustments"),
        ]

        for row, (label, section) in enumerate(labels, start=1):
            ttk.Label(self.review_tab, text=label).grid(row=row, column=0, sticky="nw", pady=7)
            text = tk.Text(self.review_tab, height=4, width=78)
            text.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=7)
            self.review_fields[section] = text

        self.review_tab.columnconfigure(1, weight=1)

        ttk.Button(
            self.review_tab,
            text="Save Weekly Review",
            style="Accent.TButton",
            command=self.save_weekly_review,
        ).grid(row=5, column=1, sticky="e", pady=16)

    def _build_git(self):
        ttk.Label(
            self.git_tab, text="Git Changes",
            style="Section.TLabel"
        ).pack(anchor="w")

        self.git_status_text = tk.Text(self.git_tab, height=22)
        self.git_status_text.pack(fill="both", expand=True, pady=10)

        options = ttk.Frame(self.git_tab)
        options.pack(fill="x")

        self.commit_message = ttk.Entry(options, width=70)
        self.commit_message.insert(0, "progress: update current sprint")
        self.commit_message.pack(side="left", fill="x", expand=True)

        ttk.Button(
            options, text="Refresh Status", command=self.refresh_git_status
        ).pack(side="left", padx=8)

        ttk.Button(
            options, text="Commit Changes", command=self.commit_changes
        ).pack(side="left")

        ttk.Button(
            options, text="Push", command=self.push_changes
        ).pack(side="left", padx=(8, 0))

    def refresh_all(self):
        self.progress = load_yaml(PROGRESS_CONFIG)
        week = int(self.progress["program"]["current_week"])
        course = int(self.progress["google"]["current_course"])
        self.header_status.config(text=f"Week {week} • Google Course {course}")

        self.refresh_dashboard_metrics()
        self.load_today_tasks()
        self.load_recent_sessions()
        self.load_learning()
        self.load_project_selector()
        self.load_project_tasks()
        self.load_sql_files()
        self.refresh_git_status()

    def refresh_dashboard_metrics(self):
        week_file = current_week_file(self.progress)
        text = week_file.read_text(encoding="utf-8")
        tasks = parse_checkboxes(text)
        completed = sum(1 for _, done, _ in tasks if done)
        total = len(tasks)
        pct = round(completed / total * 100) if total else 0

        sessions = parse_daily_log(text)
        hours = 0.0
        for row in sessions:
            try:
                hours += float(row[1])
            except ValueError:
                pass

        sql_files = list((ROOT / "resources" / "sql" / "datalemur").glob("*.sql"))
        target_sql = int(self.progress["sql"]["target_problems"])
        target_hours = float(self.progress["weekly_hours"]["target"])
        current_project = int(self.progress["portfolio"]["current_project"])
        total_projects = int(self.progress["portfolio"]["total_projects"])

        project_names = self.progress["portfolio"]["project_names"]
        project_name = project_names.get(current_project) or project_names.get(str(current_project), "")

        values = {
            "sprint": (f"Week {self.progress['program']['current_week']}", "of 12 weeks"),
            "week": (f"{pct}%", f"{completed} of {total} tasks"),
            "hours": (f"{hours:g}", f"of {target_hours:g} hours"),
            "google": (
                f"Course {self.progress['google']['current_course']}",
                f"of {self.progress['google']['total_courses']}",
            ),
            "sql": (f"{len(sql_files)}", f"of {target_sql} problems"),
            "portfolio": (f"Project {current_project}", f"of {total_projects} projects"),
        }

        for key, (value, detail) in values.items():
            self.metric_widgets[key][0].config(text=value)
            self.metric_widgets[key][1].config(text=detail)

        remaining = [label for _, done, label in tasks if not done][:5]
        focus = f"Active project: {project_name}\n"
        if remaining:
            focus += "Next priorities:\n• " + "\n• ".join(remaining)
        else:
            focus += "All sprint tasks are complete. Finish the weekly review."
        self.current_focus.config(text=focus)

    def load_today_tasks(self):
        frame = self.today_scroll.inner
        for child in frame.winfo_children():
            child.destroy()

        text = current_week_file(self.progress).read_text(encoding="utf-8")
        tasks = parse_checkboxes(text)
        self.task_vars = []

        week = self.progress["program"]["current_week"]
        self.today_title.config(text=f"Week {week} Sprint Checklist")

        for index, (line_no, done, label) in enumerate(tasks, start=1):
            var = tk.BooleanVar(value=done)
            ttk.Checkbutton(
                frame,
                text=f"{index}. {label}",
                variable=var,
            ).pack(anchor="w", fill="x", pady=4)
            self.task_vars.append((line_no, var, label))

    def save_tasks(self):
        path = current_week_file(self.progress)
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, var, _ in self.task_vars:
            marker = "x" if var.get() else " "
            lines[line_no] = re.sub(
                r"^(\s*)- \[[ xX]\] ",
                rf"\1- [{marker}] ",
                lines[line_no],
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.refresh_dashboards()
        messagebox.showinfo("Saved", "Sprint tasks updated.")

    def finish_session(self):
        values = {key: entry.get().strip() for key, entry in self.session_entries.items()}
        try:
            float(values["hours"])
            int(values["sql"])
        except ValueError:
            messagebox.showerror(
                "Invalid Session",
                "Hours must be numeric and SQL problems must be a whole number.",
            )
            return

        path = current_week_file(self.progress)
        text = path.read_text(encoding="utf-8")
        marker = "<!-- DAILY_LOG_END -->"
        if marker not in text:
            messagebox.showerror("Missing Log", "The current sprint does not contain a daily log.")
            return

        row = (
            f"| {values['date']} | {values['hours']} | "
            f"{values['google'] or '-'} | {values['datacamp'] or '-'} | "
            f"{values['sql']} | {values['portfolio'] or '-'} |"
        )
        text = text.replace(marker, row + "\n" + marker, 1)
        path.write_text(text, encoding="utf-8")

        self.session_entries["google"].delete(0, tk.END)
        self.session_entries["datacamp"].delete(0, tk.END)
        self.session_entries["portfolio"].delete(0, tk.END)
        self.session_entries["sql"].delete(0, tk.END)
        self.session_entries["sql"].insert(0, "0")
        self.session_entries["date"].delete(0, tk.END)
        self.session_entries["date"].insert(0, date.today().isoformat())

        self.refresh_dashboards()
        messagebox.showinfo("Session Saved", "Your study session was logged.")

    def load_recent_sessions(self):
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        text = current_week_file(self.progress).read_text(encoding="utf-8")
        for row in reversed(parse_daily_log(text)[-10:]):
            self.recent_tree.insert("", "end", values=row)

    def load_learning(self):
        mapping = {
            "course": self.progress["google"]["current_course"],
            "module": self.progress["google"]["current_module"],
            "hours": self.progress["weekly_hours"]["target"],
        }
        for key, value in mapping.items():
            self.learning_entries[key].delete(0, tk.END)
            self.learning_entries[key].insert(0, str(value))

        week = int(self.progress["program"]["current_week"])
        guidance_map = {
            1: "Continue Google Course 5. Complete DataCamp Introduction to SQL and begin Intermediate SQL.",
            2: "Finish Course 5, begin Course 6, finish Intermediate SQL, and begin Joining Data in SQL.",
            3: "Continue Course 6. Finish Joining Data in SQL and begin Data Manipulation in SQL.",
            4: "Finish or substantially progress through Course 6 and begin Introduction to Power BI.",
            5: "Begin Course 7 and continue Power BI dashboard development.",
            6: "Continue Course 7 and finish the flagship VFX project.",
            7: "Begin Course 8 and start Python and Pandas.",
            8: "Continue Course 8 and study data cleaning and exploratory analysis.",
            9: "Finish Course 8 and strengthen statistics.",
            10: "Begin Course 9 or capstone work and start Project 3.",
            11: "Complete capstone requirements and prepare project walkthroughs.",
            12: "Polish projects and begin targeted applications and interview preparation.",
        }
        self.learning_guidance.config(text=guidance_map.get(week, ""))

    def save_learning_progress(self):
        try:
            self.progress["google"]["current_course"] = int(self.learning_entries["course"].get())
            self.progress["google"]["current_module"] = int(self.learning_entries["module"].get())
            self.progress["weekly_hours"]["target"] = float(self.learning_entries["hours"].get())
        except ValueError:
            messagebox.showerror("Invalid Entry", "Course, module, and target hours must be numeric.")
            return

        save_yaml(PROGRESS_CONFIG, self.progress)
        self.refresh_dashboards()
        messagebox.showinfo("Saved", "Learning progress updated.")

    def load_project_selector(self):
        current = int(self.progress["portfolio"]["current_project"])
        self.project_selector.current(current - 1)

    def selected_project_number(self) -> int:
        selected = self.project_selector.current()
        return selected + 1 if selected >= 0 else int(self.progress["portfolio"]["current_project"])

    def load_project_tasks(self):
        frame = self.portfolio_scroll.inner
        for child in frame.winfo_children():
            child.destroy()

        project_num = self.selected_project_number()
        tasks_path = PROJECTS[project_num] / "TASKS.md"
        if not tasks_path.exists():
            ttk.Label(frame, text="No TASKS.md file found for this project.").pack(anchor="w")
            return

        text = tasks_path.read_text(encoding="utf-8")
        tasks = parse_checkboxes(text)
        self.project_vars = []

        for index, (line_no, done, label) in enumerate(tasks, start=1):
            var = tk.BooleanVar(value=done)
            ttk.Checkbutton(
                frame,
                text=f"{index}. {label}",
                variable=var,
            ).pack(anchor="w", fill="x", pady=4)
            self.project_vars.append((line_no, var, label))

    def set_active_project(self):
        project_num = self.selected_project_number()
        self.progress["portfolio"]["current_project"] = project_num
        save_yaml(PROGRESS_CONFIG, self.progress)
        self.refresh_dashboards()
        messagebox.showinfo("Updated", f"Project {project_num} is now active.")

    def save_project_tasks(self):
        project_num = self.selected_project_number()
        path = PROJECTS[project_num] / "TASKS.md"
        lines = path.read_text(encoding="utf-8").splitlines()

        for line_no, var, _ in self.project_vars:
            marker = "x" if var.get() else " "
            lines[line_no] = re.sub(
                r"^(\s*)- \[[ xX]\] ",
                rf"\1- [{marker}] ",
                lines[line_no],
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.refresh_dashboards()
        messagebox.showinfo("Saved", "Project tasks updated.")

    def create_sql_solution(self):
        title = self.sql_entries["title"].get().strip()
        difficulty = self.sql_entries["difficulty"].get().strip() or "Easy"
        concepts = self.sql_entries["concepts"].get().strip() or "To be completed"

        if not title:
            messagebox.showerror("Missing Title", "Enter the SQL problem title.")
            return

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        path = ROOT / "resources" / "sql" / "datalemur" / f"{slug}.sql"
        if path.exists():
            messagebox.showwarning("Already Exists", f"{path.name} already exists.")
            return

        content = f"""-- Problem: {title}
-- Difficulty: {difficulty}
-- Concepts: {concepts}
-- Completed: {date.today().isoformat()}

-- Write your solution below.


-- Reflection
-- Business question:
-- What was difficult:
-- Alternative approach:
"""
        path.write_text(content, encoding="utf-8")
        self.sql_entries["title"].delete(0, tk.END)
        self.sql_entries["concepts"].delete(0, tk.END)
        self.refresh_dashboards()
        messagebox.showinfo("Created", f"Created {path.name}")

    def load_sql_files(self):
        self.sql_list.delete(0, tk.END)
        sql_dir = ROOT / "resources" / "sql" / "datalemur"
        files = sorted(sql_dir.glob("*.sql"))
        for path in files:
            self.sql_list.insert(tk.END, path.name)

    def save_weekly_review(self):
        path = current_retro_file(self.progress)
        text = path.read_text(encoding="utf-8")

        for section, widget in self.review_fields.items():
            note = widget.get("1.0", tk.END).strip()
            if not note:
                continue

            pattern = re.compile(rf"(^## {re.escape(section)}\s*$)", re.M)
            match = pattern.search(text)
            if match:
                insert_at = match.end()
                text = text[:insert_at] + f"\n- {note}" + text[insert_at:]

        path.write_text(text, encoding="utf-8")
        for widget in self.review_fields.values():
            widget.delete("1.0", tk.END)

        self.refresh_dashboards()
        messagebox.showinfo("Saved", "Weekly review saved.")

    def refresh_dashboards(self):
        ok, output = run_progress_update()
        if not ok:
            messagebox.showerror("Update Failed", output)
            return
        self.refresh_all()

    def refresh_git_status(self):
        self.git_status_text.delete("1.0", tk.END)
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.git_status_text.insert("1.0", result.stderr or "Git status failed.")
        else:
            self.git_status_text.insert("1.0", result.stdout or "Working tree clean.")

    def commit_changes(self):
        message = self.commit_message.get().strip()
        if not message:
            messagebox.showerror("Missing Message", "Enter a commit message.")
            return

        add = subprocess.run(["git", "add", "."], cwd=ROOT, capture_output=True, text=True)
        if add.returncode != 0:
            messagebox.showerror("Git Error", add.stderr)
            return

        commit = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if commit.returncode != 0:
            messagebox.showwarning("Commit Result", commit.stderr or commit.stdout)
        else:
            messagebox.showinfo("Committed", commit.stdout)
        self.refresh_git_status()

    def push_changes(self):
        confirm = messagebox.askyesno(
            "Push Changes",
            "Push committed changes to the configured remote?",
        )
        if not confirm:
            return

        result = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            messagebox.showerror("Push Failed", result.stderr or result.stdout)
        else:
            messagebox.showinfo("Pushed", result.stdout or "Changes pushed successfully.")
        self.refresh_git_status()


if __name__ == "__main__":
    app = CareerAcceleratorApp()
    app.mainloop()
