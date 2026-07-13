from __future__ import annotations

from pathlib import Path
from datetime import date
import re
import subprocess
import sys
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


def show_tasks() -> None:
    config = load_config()
    path = current_week_path(config)
    text = path.read_text(encoding="utf-8")
    tasks = parse_tasks(text)

    print(f"\nCurrent sprint: Week {config['program']['current_week']}")
    if not tasks:
        print("No checklist tasks found.")
        return

    for index, (_, done, label) in enumerate(tasks, start=1):
        marker = "x" if done else " "
        print(f"{index:>2}. [{marker}] {label}")


def mark_tasks() -> None:
    config = load_config()
    path = current_week_path(config)
    lines = path.read_text(encoding="utf-8").splitlines()
    tasks = parse_tasks("\n".join(lines))

    if not tasks:
        print("No checklist tasks found.")
        return

    show_tasks()
    raw = input(
        "\nEnter task numbers to toggle, separated by commas "
        "(example: 1,3,5), or press Enter to cancel: "
    ).strip()

    if not raw:
        return

    try:
        selected = {int(value.strip()) for value in raw.split(",")}
    except ValueError:
        print("Please enter only task numbers separated by commas.")
        return

    for index in selected:
        if index < 1 or index > len(tasks):
            print(f"Skipping invalid task number: {index}")
            continue

        line_num, done, label = tasks[index - 1]
        replacement = " " if done else "x"
        lines[line_num] = re.sub(
            r"^(\s*)- \[[ xX]\] ",
            rf"\1- [{replacement}] ",
            lines[line_num],
        )
        print(f"{'Reopened' if done else 'Completed'}: {label}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_dashboard_update()


def add_daily_log() -> None:
    config = load_config()
    path = current_week_path(config)
    text = path.read_text(encoding="utf-8")

    if "<!-- DAILY_LOG_START -->" not in text:
        print("The current sprint does not contain a daily log.")
        return

    log_date = input(f"Date [{date.today().isoformat()}]: ").strip() or date.today().isoformat()
    hours = input("Hours studied: ").strip()
    google = input("Google progress: ").strip() or "-"
    datacamp = input("DataCamp progress: ").strip() or "-"
    sql_problems = input("Number of SQL problems completed: ").strip() or "0"
    portfolio = input("Portfolio progress: ").strip() or "-"

    try:
        float(hours)
        int(sql_problems)
    except ValueError:
        print("Hours must be numeric and SQL problems must be a whole number.")
        return

    row = f"| {log_date} | {hours} | {google} | {datacamp} | {sql_problems} | {portfolio} |"
    marker = "<!-- DAILY_LOG_END -->"
    text = text.replace(marker, row + "\n" + marker, 1)
    path.write_text(text, encoding="utf-8")
    print("Daily log added.")
    run_dashboard_update()


def create_sql_solution() -> None:
    title = input("DataLemur problem title: ").strip()
    if not title:
        return

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    path = ROOT / "resources" / "sql" / "datalemur" / f"{slug}.sql"

    if path.exists():
        print(f"File already exists: {path.relative_to(ROOT)}")
        return

    difficulty = input("Difficulty [Easy]: ").strip() or "Easy"
    concepts = input("Concepts used: ").strip() or "To be completed"

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
    print(f"Created: {path.relative_to(ROOT)}")
    run_dashboard_update()


def update_metadata() -> None:
    config = load_config()

    print("\nLeave any field blank to keep its current value.")

    week = input(f"Current week [{config['program']['current_week']}]: ").strip()
    course = input(f"Google course [{config['google']['current_course']}]: ").strip()
    module = input(f"Google module [{config['google']['current_module']}]: ").strip()
    project = input(f"Current portfolio project [{config['portfolio']['current_project']}]: ").strip()
    target_hours = input(f"Weekly target hours [{config['weekly_hours']['target']}]: ").strip()

    try:
        if week:
            config["program"]["current_week"] = int(week)
        if course:
            config["google"]["current_course"] = int(course)
        if module:
            config["google"]["current_module"] = int(module)
        if project:
            config["portfolio"]["current_project"] = int(project)
        if target_hours:
            config["weekly_hours"]["target"] = float(target_hours)
    except ValueError:
        print("Week, course, module, project, and hours must be numeric.")
        return

    save_config(config)
    print("Metadata updated.")
    run_dashboard_update()


def add_retrospective_note() -> None:
    config = load_config()
    week = int(config["program"]["current_week"])
    path = ROOT / "weeks" / f"week-{week:02d}" / "RETROSPECTIVE.md"

    if not path.exists():
        print("Retrospective file not found.")
        return

    section = input("Section (Wins, Blockers, Topics to Review, Next Sprint Adjustments): ").strip()
    note = input("Note: ").strip()

    if not section or not note:
        return

    text = path.read_text(encoding="utf-8")
    heading_pattern = re.compile(rf"(^## {re.escape(section)}\s*$)", re.M)

    match = heading_pattern.search(text)
    if not match:
        print("Section not found. Use the exact section name shown in the file.")
        return

    insert_pos = match.end()
    text = text[:insert_pos] + f"\n- {note}" + text[insert_pos:]
    path.write_text(text, encoding="utf-8")
    print("Retrospective note added.")


def run_dashboard_update() -> None:
    script = ROOT / "scripts" / "update_progress.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    if result.returncode != 0:
        print("Dashboard update failed.")
    else:
        print("Dashboards refreshed.")


def main() -> None:
    while True:
        config = load_config()
        print("\n" + "=" * 52)
        print("Career Accelerator Progress Tracker")
        print(f"Current week: {config['program']['current_week']}")
        print("=" * 52)
        print("1. View current checklist")
        print("2. Mark or reopen checklist tasks")
        print("3. Add daily study log")
        print("4. Create DataLemur solution file")
        print("5. Update week/course/project metadata")
        print("6. Add retrospective note")
        print("7. Refresh dashboards")
        print("8. Exit")

        choice = input("\nChoose an option: ").strip()

        actions = {
            "1": show_tasks,
            "2": mark_tasks,
            "3": add_daily_log,
            "4": create_sql_solution,
            "5": update_metadata,
            "6": add_retrospective_note,
            "7": run_dashboard_update,
        }

        if choice == "8":
            print("Progress saved. Keep going.")
            break

        action = actions.get(choice)
        if action:
            action()
        else:
            print("Choose a number from 1 to 8.")


if __name__ == "__main__":
    main()
