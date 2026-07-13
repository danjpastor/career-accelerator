from __future__ import annotations

import re
import subprocess
import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "progress-data.yml"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def current_week_path(config: dict) -> Path:
    week = int(config["program"]["current_week"])
    return ROOT / "weeks" / f"week-{week:02d}" / "README.md"


def parse_tasks(text: str) -> list[tuple[int, bool, str]]:
    tasks = []
    for line_num, line in enumerate(text.splitlines()):
        match = re.match(r"^(\s*)- \[([ xX])\] (.+)$", line)
        if match:
            tasks.append((line_num, match.group(2).lower() == "x", match.group(3)))
    return tasks


def run_dashboard_update() -> tuple[bool, str]:
    script = ROOT / "scripts" / "update_progress.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, result.stderr or result.stdout or "Unknown update error."
    return True, result.stdout.strip() or "Dashboards refreshed."


class TrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Career Accelerator Tracker")
        self.geometry("980x720")
        self.minsize(860, 620)

        self.config_data = load_config()
        self.task_vars: list[tuple[int, tk.BooleanVar, str]] = []

        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")

        self.title_label = ttk.Label(
            header,
            text="Career Accelerator Progress Tracker",
            font=("Segoe UI", 16, "bold"),
        )
        self.title_label.pack(side="left")

        self.status_label = ttk.Label(header, text="")
        self.status_label.pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tasks_tab = ttk.Frame(notebook, padding=10)
        self.log_tab = ttk.Frame(notebook, padding=10)
        self.meta_tab = ttk.Frame(notebook, padding=10)
        self.sql_tab = ttk.Frame(notebook, padding=10)
        self.retro_tab = ttk.Frame(notebook, padding=10)

        notebook.add(self.tasks_tab, text="Sprint Tasks")
        notebook.add(self.log_tab, text="Daily Log")
        notebook.add(self.meta_tab, text="Metadata")
        notebook.add(self.sql_tab, text="SQL Practice")
        notebook.add(self.retro_tab, text="Retrospective")

        self._build_tasks_tab()
        self._build_log_tab()
        self._build_meta_tab()
        self._build_sql_tab()
        self._build_retro_tab()

        footer = ttk.Frame(self, padding=10)
        footer.pack(fill="x")

        ttk.Button(
            footer,
            text="Refresh Dashboards",
            command=self.refresh_dashboards,
        ).pack(side="left")

        ttk.Button(
            footer,
            text="Open Repository Folder",
            command=self.open_repo_folder,
        ).pack(side="left", padx=8)

        ttk.Button(
            footer,
            text="Reload",
            command=self.refresh_all,
        ).pack(side="right")

    def _build_tasks_tab(self):
        top = ttk.Frame(self.tasks_tab)
        top.pack(fill="x")

        self.week_label = ttk.Label(top, text="", font=("Segoe UI", 12, "bold"))
        self.week_label.pack(side="left")

        ttk.Button(top, text="Save Task Changes", command=self.save_tasks).pack(side="right")

        canvas = tk.Canvas(self.tasks_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tasks_tab, orient="vertical", command=canvas.yview)
        self.tasks_frame = ttk.Frame(canvas)

        self.tasks_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

    def _build_log_tab(self):
        fields = [
            ("Date", "date"),
            ("Hours", "hours"),
            ("Google Progress", "google"),
            ("DataCamp Progress", "datacamp"),
            ("SQL Problems Completed", "sql"),
            ("Portfolio Progress", "portfolio"),
        ]

        self.log_entries = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(self.log_tab, text=label).grid(row=row, column=0, sticky="w", pady=6)
            entry = ttk.Entry(self.log_tab, width=70)
            entry.grid(row=row, column=1, sticky="ew", pady=6, padx=(10, 0))
            self.log_entries[key] = entry

        self.log_tab.columnconfigure(1, weight=1)
        self.log_entries["date"].insert(0, date.today().isoformat())
        self.log_entries["sql"].insert(0, "0")

        ttk.Button(
            self.log_tab,
            text="Add Daily Log",
            command=self.add_daily_log,
        ).grid(row=len(fields), column=1, sticky="e", pady=16)

    def _build_meta_tab(self):
        labels = [
            ("Current Week", "week"),
            ("Google Course", "course"),
            ("Google Module", "module"),
            ("Current Portfolio Project", "project"),
            ("Weekly Target Hours", "hours"),
        ]

        self.meta_entries = {}
        for row, (label, key) in enumerate(labels):
            ttk.Label(self.meta_tab, text=label).grid(row=row, column=0, sticky="w", pady=6)
            entry = ttk.Entry(self.meta_tab, width=24)
            entry.grid(row=row, column=1, sticky="w", pady=6, padx=(10, 0))
            self.meta_entries[key] = entry

        ttk.Button(
            self.meta_tab,
            text="Save Metadata",
            command=self.save_metadata,
        ).grid(row=len(labels), column=1, sticky="w", pady=16)

    def _build_sql_tab(self):
        fields = [
            ("Problem Title", "title"),
            ("Difficulty", "difficulty"),
            ("Concepts", "concepts"),
        ]

        self.sql_entries = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(self.sql_tab, text=label).grid(row=row, column=0, sticky="w", pady=6)
            entry = ttk.Entry(self.sql_tab, width=60)
            entry.grid(row=row, column=1, sticky="ew", pady=6, padx=(10, 0))
            self.sql_entries[key] = entry

        self.sql_tab.columnconfigure(1, weight=1)
        self.sql_entries["difficulty"].insert(0, "Easy")

        ttk.Button(
            self.sql_tab,
            text="Create SQL Solution File",
            command=self.create_sql_solution,
        ).grid(row=len(fields), column=1, sticky="e", pady=16)

    def _build_retro_tab(self):
        ttk.Label(self.retro_tab, text="Section").grid(row=0, column=0, sticky="w", pady=6)
        self.retro_section = ttk.Combobox(
            self.retro_tab,
            values=["Wins", "Blockers", "SQL Topics to Review", "Week 2 Adjustments"],
            state="readonly",
            width=32,
        )
        self.retro_section.grid(row=0, column=1, sticky="w", pady=6, padx=(10, 0))
        self.retro_section.current(0)

        ttk.Label(self.retro_tab, text="Note").grid(row=1, column=0, sticky="nw", pady=6)
        self.retro_note = tk.Text(self.retro_tab, height=8, width=70)
        self.retro_note.grid(row=1, column=1, sticky="nsew", pady=6, padx=(10, 0))

        self.retro_tab.columnconfigure(1, weight=1)
        self.retro_tab.rowconfigure(1, weight=1)

        ttk.Button(
            self.retro_tab,
            text="Add Retrospective Note",
            command=self.add_retro_note,
        ).grid(row=2, column=1, sticky="e", pady=16)

    def refresh_all(self):
        self.config_data = load_config()
        week = int(self.config_data["program"]["current_week"])
        self.status_label.config(
            text=f"Week {week} | Google Course {self.config_data['google']['current_course']}"
        )
        self.week_label.config(text=f"Week {week} Checklist")
        self.load_tasks()
        self.load_metadata()

    def load_tasks(self):
        for child in self.tasks_frame.winfo_children():
            child.destroy()

        path = current_week_path(self.config_data)
        text = path.read_text(encoding="utf-8")
        tasks = parse_tasks(text)
        self.task_vars.clear()

        if not tasks:
            ttk.Label(self.tasks_frame, text="No checklist tasks found.").pack(anchor="w")
            return

        for index, (line_num, done, label) in enumerate(tasks, start=1):
            var = tk.BooleanVar(value=done)
            cb = ttk.Checkbutton(
                self.tasks_frame,
                text=f"{index}. {label}",
                variable=var,
            )
            cb.pack(anchor="w", fill="x", pady=3)
            self.task_vars.append((line_num, var, label))

    def save_tasks(self):
        path = current_week_path(self.config_data)
        lines = path.read_text(encoding="utf-8").splitlines()

        for line_num, var, _ in self.task_vars:
            value = "x" if var.get() else " "
            lines[line_num] = re.sub(
                r"^(\s*)- \[[ xX]\] ",
                rf"\1- [{value}] ",
                lines[line_num],
            )

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.refresh_dashboards()
        messagebox.showinfo("Saved", "Checklist changes saved.")

    def add_daily_log(self):
        values = {key: entry.get().strip() for key, entry in self.log_entries.items()}

        try:
            float(values["hours"])
            int(values["sql"])
        except ValueError:
            messagebox.showerror(
                "Invalid Entry",
                "Hours must be numeric and SQL problems must be a whole number.",
            )
            return

        path = current_week_path(self.config_data)
        text = path.read_text(encoding="utf-8")

        marker = "<!-- DAILY_LOG_END -->"
        if marker not in text:
            messagebox.showerror("Missing Log", "The current sprint has no daily-log section.")
            return

        row = (
            f"| {values['date']} | {values['hours']} | "
            f"{values['google'] or '-'} | {values['datacamp'] or '-'} | "
            f"{values['sql']} | {values['portfolio'] or '-'} |"
        )

        text = text.replace(marker, row + "\n" + marker, 1)
        path.write_text(text, encoding="utf-8")
        self.refresh_dashboards()
        messagebox.showinfo("Saved", "Daily study log added.")

    def load_metadata(self):
        mapping = {
            "week": self.config_data["program"]["current_week"],
            "course": self.config_data["google"]["current_course"],
            "module": self.config_data["google"]["current_module"],
            "project": self.config_data["portfolio"]["current_project"],
            "hours": self.config_data["weekly_hours"]["target"],
        }

        for key, value in mapping.items():
            self.meta_entries[key].delete(0, tk.END)
            self.meta_entries[key].insert(0, str(value))

    def save_metadata(self):
        try:
            self.config_data["program"]["current_week"] = int(self.meta_entries["week"].get())
            self.config_data["google"]["current_course"] = int(self.meta_entries["course"].get())
            self.config_data["google"]["current_module"] = int(self.meta_entries["module"].get())
            self.config_data["portfolio"]["current_project"] = int(self.meta_entries["project"].get())
            self.config_data["weekly_hours"]["target"] = float(self.meta_entries["hours"].get())
        except ValueError:
            messagebox.showerror("Invalid Entry", "Metadata fields must be numeric.")
            return

        save_config(self.config_data)
        self.refresh_dashboards()
        self.refresh_all()
        messagebox.showinfo("Saved", "Metadata updated.")

    def create_sql_solution(self):
        title = self.sql_entries["title"].get().strip()
        difficulty = self.sql_entries["difficulty"].get().strip() or "Easy"
        concepts = self.sql_entries["concepts"].get().strip() or "To be completed"

        if not title:
            messagebox.showerror("Missing Title", "Enter the DataLemur problem title.")
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
        self.refresh_dashboards()
        messagebox.showinfo("Created", f"Created {path.name}")

    def add_retro_note(self):
        section = self.retro_section.get().strip()
        note = self.retro_note.get("1.0", tk.END).strip()

        if not note:
            messagebox.showerror("Missing Note", "Enter a retrospective note.")
            return

        week = int(self.config_data["program"]["current_week"])
        path = ROOT / "weeks" / f"week-{week:02d}" / "RETROSPECTIVE.md"

        if not path.exists():
            messagebox.showerror("Missing File", "Retrospective file not found.")
            return

        text = path.read_text(encoding="utf-8")
        heading = re.compile(rf"(^## {re.escape(section)}\s*$)", re.M)
        match = heading.search(text)

        if not match:
            messagebox.showerror(
                "Missing Section",
                f"The section '{section}' was not found in the retrospective.",
            )
            return

        insert_pos = match.end()
        text = text[:insert_pos] + f"\n- {note}" + text[insert_pos:]
        path.write_text(text, encoding="utf-8")
        self.retro_note.delete("1.0", tk.END)
        messagebox.showinfo("Saved", "Retrospective note added.")

    def refresh_dashboards(self):
        ok, output = run_dashboard_update()
        if not ok:
            messagebox.showerror("Update Failed", output)
        else:
            self.refresh_all()

    def open_repo_folder(self):
        try:
            if sys.platform.startswith("win"):
                subprocess.run(["explorer", str(ROOT)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(ROOT)])
            else:
                subprocess.run(["xdg-open", str(ROOT)])
        except Exception as exc:
            messagebox.showerror("Open Folder Failed", str(exc))


if __name__ == "__main__":
    app = TrackerGUI()
    app.mainloop()
