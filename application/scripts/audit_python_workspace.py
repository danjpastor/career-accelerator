from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "application"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from career_app.data.python_exercises import PYTHON_EXERCISES, exercise_number_for_label
from career_app.services import python_exercise_runner


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    issues: list[str] = []

    expected = list(range(1, 14))
    if sorted(PYTHON_EXERCISES) != expected:
        issues.append(f"Python exercise numbers are {sorted(PYTHON_EXERCISES)}; expected {expected}.")
    for number in expected:
        item = PYTHON_EXERCISES[number]
        if exercise_number_for_label(item["label"]) != number:
            issues.append(f"Python Exercise {number:02d} label does not route to its exercise.")
        folder = root / "practice" / "python" / "exercises" / item["slug"]
        for filename in ("README.md", "starter.py"):
            if not (folder / filename).is_file():
                issues.append(f"Missing {folder.relative_to(root) / filename}.")

    dataset = root / "practice" / "python" / "datasets" / "operations.csv"
    if not dataset.is_file():
        issues.append("Shared Python dataset is missing.")

    database_source = (root / "application" / "career_app" / "database.py").read_text(encoding="utf-8")
    if "CREATE TABLE IF NOT EXISTS python_exercise_progress" not in database_source:
        issues.append("Python progress table is missing from the application schema.")
    main_source = (root / "application" / "career_app" / "main.py").read_text(encoding="utf-8")
    for token in ("PythonExercisesWidget", 'addTab(self.python_exercises_widget, "Python Exercises")', "python_exercise_number_for_label"):
        if token not in main_source:
            issues.append(f"Main Learning integration is missing {token}.")
    ui_path = root / "application" / "career_app" / "ui" / "python_exercises.py"
    if not ui_path.is_file():
        issues.append("Integrated Python exercise UI is missing.")
    else:
        ui_source = ui_path.read_text(encoding="utf-8")
        for token in ("AssistedPlainTextEdit", "Run", "Check Exercise", "Save Draft", "Submit Exercise", "chart_label"):
            if token not in ui_source:
                issues.append(f"Integrated Python UI is missing {token}.")

    if not issues:
        with tempfile.TemporaryDirectory(prefix="career_accelerator_python_audit_") as temp_dir:
            temp_root = Path(temp_dir)
            shutil.copytree(root / "practice" / "python", temp_root / "practice" / "python")
            code = '''from pathlib import Path
DATA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "operations.csv"
analyst = "Taylor"
hours = 10
rate = 0.20
print(type(hours))
projected = hours * (1 + rate)
print(f"{analyst}: {projected}; dataset={DATA_PATH.exists()}")
# Decision: keep the percentage in its own variable.
# Validation: confirm the shared dataset path exists.
'''
            result = python_exercise_runner.check_code(temp_root, 1, code)
            if not result.get("passed"):
                issues.append("Integrated Python runner did not pass the known Exercise 01 validation case.")
            output = str((result.get("run") or {}).get("stdout") or "")
            if "dataset=True" not in output:
                issues.append("Saved Python submissions do not resolve the shared dataset correctly.")

    if issues:
        print("Python exercise workspace audit FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Python exercise workspace audit PASSED")
    print("- 13 exercises are numbered in roadmap order")
    print("- integrated editor, local runner, validation, output, and chart capture are present")
    print("- submission-relative dataset path resolves correctly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
