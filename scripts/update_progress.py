from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "progress-data.yml").read_text(encoding="utf-8"))

def replace_block(text: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    block = f"{start}\n{replacement.rstrip()}\n{end}"
    if pattern.search(text):
        return pattern.sub(block, text)
    return text.rstrip() + "\n\n" + block + "\n"

def count_checkboxes(text: str):
    checked = len(re.findall(r"^- \[[xX]\] ", text, re.M))
    unchecked = len(re.findall(r"^- \[ \] ", text, re.M))
    return checked, unchecked

def parse_daily_hours(text: str) -> float:
    match = re.search(r"<!-- DAILY_LOG_START -->(.*?)<!-- DAILY_LOG_END -->", text, re.S)
    if not match:
        return 0.0
    total = 0.0
    for line in match.group(1).splitlines():
        if not line.startswith("|") or "---" in line or "| Date |" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        try:
            total += float(cells[1])
        except ValueError:
            pass
    return total

week = int(CONFIG["program"]["current_week"])
week_file = ROOT / "weeks" / f"week-{week:02d}" / "README.md"
week_text = week_file.read_text(encoding="utf-8")

checked, unchecked = count_checkboxes(week_text)
total_tasks = checked + unchecked
completion = round((checked / total_tasks) * 100) if total_tasks else 0
hours = parse_daily_hours(week_text)
target_hours = float(CONFIG["weekly_hours"]["target"])

if completion == 0:
    state = "Not Started"
elif completion >= 100:
    state = "Complete"
else:
    state = "In Progress"

sprint_status = f"""## Sprint Status

| Metric | Status |
|---|---:|
| Sprint | Week {week} |
| State | {state} |
| Completion | {completion}% |
| Hours | {hours:g} / {target_hours:g} |
| Completed Tasks | {checked} |
| Remaining Tasks | {unchecked} |"""

week_text = replace_block(
    week_text,
    "<!-- AUTO_SPRINT_STATUS_START -->",
    "<!-- AUTO_SPRINT_STATUS_END -->",
    sprint_status
)
week_file.write_text(week_text, encoding="utf-8")

sql_dir = ROOT / "resources" / "sql" / "datalemur"
sql_count = len([p for p in sql_dir.glob("*.sql") if p.is_file()])
sql_target = int(CONFIG["sql"]["target_problems"])

project_root = ROOT / "projects"
project_dirs = sorted([p for p in project_root.iterdir() if p.is_dir()])
completed_projects = 0
for project in project_dirs:
    tasks = project / "TASKS.md"
    if not tasks.exists():
        continue
    text = tasks.read_text(encoding="utf-8")
    c, u = count_checkboxes(text)
    if c > 0 and u == 0:
        completed_projects += 1

current_project_num = int(CONFIG["portfolio"]["current_project"])
project_names = CONFIG["portfolio"]["project_names"]
current_project = project_names.get(current_project_num) or project_names.get(str(current_project_num), "Unknown")

google_course = int(CONFIG["google"]["current_course"])
google_total = int(CONFIG["google"]["total_courses"])

dashboard = f"""## Current Progress

| Metric | Progress |
|---|---:|
| Current Sprint | Week {week} |
| Week Completion | {completion}% |
| Hours Completed | {hours:g} / {target_hours:g} |
| Google Certificate | Course {google_course} of {google_total} |
| SQL Problems | {sql_count} / {sql_target} |
| Portfolio Projects | {completed_projects} / {len(project_dirs)} |
| Current Project | {current_project} |"""

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = replace_block(
    readme,
    "<!-- AUTO_PROGRESS_START -->",
    "<!-- AUTO_PROGRESS_END -->",
    dashboard
)
readme_path.write_text(readme, encoding="utf-8")

progress_path = ROOT / "PROGRESS.md"
progress = progress_path.read_text(encoding="utf-8")
summary = f"""## Automated Summary

| Metric | Current |
|---|---:|
| Current week | {week} / {CONFIG['program']['total_weeks']} |
| Week completion | {completion}% |
| Hours this week | {hours:g} / {target_hours:g} |
| Google course | {google_course} / {google_total} |
| SQL problems | {sql_count} / {sql_target} |
| Completed projects | {completed_projects} / {len(project_dirs)} |"""
progress = replace_block(
    progress,
    "<!-- AUTO_SUMMARY_START -->",
    "<!-- AUTO_SUMMARY_END -->",
    summary
)
progress_path.write_text(progress, encoding="utf-8")

print("Progress dashboards updated.")
