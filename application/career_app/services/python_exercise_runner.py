"""Run and validate learner Python submissions in the local application environment."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

from career_app.data.python_exercises import PYTHON_EXERCISES
from career_app.services import python_workspace

DEFAULT_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class ValidationItem:
    label: str
    passed: bool
    detail: str


def instructions_markdown(root: Path, number: int) -> str:
    path = python_workspace.paths(root, number)["instructions"]
    if not path.is_file():
        raise FileNotFoundError(f"Python exercise guide was not found: {path}")
    return path.read_text(encoding="utf-8")


def starter_code(root: Path, number: int) -> str:
    path = python_workspace.paths(root, number)["starter"]
    if not path.is_file():
        raise FileNotFoundError(f"Python starter file was not found: {path}")
    return path.read_text(encoding="utf-8")


def _sitecustomize_text() -> str:
    return r'''
import os
try:
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    _output_dir = os.environ.get("CA_PYTHON_OUTPUT_DIR", "")
    _counter = {"value": 0}
    def _career_accelerator_show(*args, **kwargs):
        if not _output_dir:
            return
        os.makedirs(_output_dir, exist_ok=True)
        figures = list(map(plt.figure, plt.get_fignums()))
        for figure in figures:
            _counter["value"] += 1
            figure.savefig(
                os.path.join(_output_dir, f"figure_{_counter['value']:02d}.png"),
                bbox_inches="tight",
                dpi=130,
            )
        plt.close("all")
    plt.show = _career_accelerator_show
except Exception:
    pass
'''


def _error_line(stderr: str) -> int | None:
    matches = re.findall(r'File "[^"]+", line (\d+)', str(stderr or ""))
    return int(matches[-1]) if matches else None


def run_code(root: Path, number: int, code: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    number = int(number)
    paths = python_workspace.paths(root, number)
    submission = python_workspace.save_code(root, number, code)
    output_dir = paths["outputs"]
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("figure_*.png"):
        old.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="career_accelerator_python_") as temp_dir:
        temp = Path(temp_dir)
        (temp / "sitecustomize.py").write_text(_sitecustomize_text(), encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"
        env["MPLBACKEND"] = "Agg"
        env["CA_PYTHON_OUTPUT_DIR"] = str(output_dir)
        env["PYTHONPATH"] = str(temp) + os.pathsep + env.get("PYTHONPATH", "")
        started = time.perf_counter()
        try:
            result = subprocess.run(
                [sys.executable, str(submission)],
                cwd=str(paths["exercise_dir"]),
                env=env,
                capture_output=True,
                text=True,
                timeout=max(2, int(timeout)),
            )
            duration = time.perf_counter() - started
            stderr = str(result.stderr or "")
            stdout = str(result.stdout or "")
            return {
                "ok": result.returncode == 0,
                "returncode": int(result.returncode),
                "stdout": stdout,
                "stderr": stderr,
                "duration_seconds": duration,
                "error_line": _error_line(stderr),
                "images": [str(path) for path in sorted(output_dir.glob("figure_*.png"))],
            }
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - started
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            return {
                "ok": False,
                "returncode": -1,
                "stdout": stdout,
                "stderr": (stderr + f"\nExecution stopped after {int(timeout)} seconds. Check for an infinite loop.").strip(),
                "duration_seconds": duration,
                "error_line": None,
                "images": [],
                "timed_out": True,
            }


def _call_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            parts = [func.attr]
            value = func.value
            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name):
                parts.append(value.id)
            names.add(".".join(reversed(parts)))
            names.add(func.attr)
    return names


def _import_names(tree: ast.AST) -> set[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                values.add(alias.name)
                values.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                values.add(node.module)
            for alias in node.names:
                values.add(alias.name)
                values.add(alias.asname or alias.name)
    return values


def _custom_comment_count(code: str) -> int:
    ignored = re.compile(r"^#\s*(Task\s+\d+|Evidence:|Python Exercise|Read README)", re.I)
    return sum(
        1
        for line in str(code or "").splitlines()
        if line.strip().startswith("#") and not ignored.match(line.strip())
    )


def _has_dataframe_filter(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and any(isinstance(child, (ast.Compare, ast.BoolOp)) for child in ast.walk(node.slice)):
            return True
    return False


def _feature_checks(number: int, tree: ast.AST, code: str) -> list[ValidationItem]:
    calls = _call_names(tree)
    imports = _import_names(tree)
    nodes = list(ast.walk(tree))
    assignments = sum(isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) for node in nodes)
    has_output = "print" in calls or any(isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) for node in tree.body)

    def call_any(*values: str) -> bool:
        return any(value in calls or any(name.endswith("." + value) for name in calls) for value in values)

    checks: list[ValidationItem] = []
    if number == 1:
        checks += [
            ValidationItem("Create reusable variables", assignments >= 3, "Use separate variables for the requested analyst values."),
            ValidationItem("Inspect value types", call_any("type"), "Use Python to inspect at least one value type."),
            ValidationItem("Calculate from variables", any(isinstance(n, ast.BinOp) for n in nodes), "Use arithmetic between variables rather than typing the final result."),
            ValidationItem("Build a readable sentence", any(isinstance(n, ast.JoinedStr) for n in nodes) or call_any("format"), "Combine text and calculated values in a readable output."),
        ]
    elif number == 2:
        checks += [
            ValidationItem("Create or load a list", any(isinstance(n, (ast.List, ast.ListComp)) for n in nodes) or call_any("list"), "Use a Python list for the requested values."),
            ValidationItem("Subset the list", any(isinstance(n, ast.Subscript) for n in nodes), "Use indexing or slicing to retrieve part of the list."),
            ValidationItem("Update the list", call_any("append", "extend", "insert", "remove", "pop") or any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) for t in n.targets) for n in nodes), "Modify the list with a method or indexed assignment."),
        ]
    elif number == 3:
        checks += [
            ValidationItem("Define a function", any(isinstance(n, ast.FunctionDef) for n in nodes), "Create a named function for repeated logic."),
            ValidationItem("Return a result", any(isinstance(n, ast.Return) for n in nodes), "Return the calculated value from the function."),
            ValidationItem("Use a package", bool(imports), "Import and use an appropriate standard or installed package."),
        ]
    elif number == 4:
        checks += [
            ValidationItem("Import NumPy", "numpy" in imports or "np" in imports, "Import NumPy using a clear alias."),
            ValidationItem("Create a NumPy array", call_any("array"), "Convert the numeric values into a NumPy array."),
            ValidationItem("Use vectorized arithmetic", any(isinstance(n, ast.BinOp) for n in nodes), "Apply a calculation to the array without manually editing each value."),
            ValidationItem("Summarize the array", call_any("mean", "median", "sum", "min", "max", "std"), "Calculate at least one summary statistic."),
        ]
    elif number == 5:
        checks += [
            ValidationItem("Import Matplotlib", any(name.startswith("matplotlib") for name in imports) or "plt" in imports, "Import Matplotlib for chart creation."),
            ValidationItem("Create a comparison chart", call_any("plot", "bar"), "Create a line or bar-style comparison chart."),
            ValidationItem("Create a histogram", call_any("hist"), "Create a histogram for a numeric field."),
            ValidationItem("Label the charts", call_any("title") and call_any("xlabel") and call_any("ylabel"), "Add a title and axis labels so the charts are understandable."),
        ]
    elif number == 6:
        checks += [
            ValidationItem("Use a dictionary", any(isinstance(n, (ast.Dict, ast.DictComp)) for n in nodes), "Create or work with a dictionary."),
            ValidationItem("Create or load a DataFrame", call_any("DataFrame", "read_csv"), "Use pandas to create or load a DataFrame."),
            ValidationItem("Select DataFrame columns", any(isinstance(n, ast.Subscript) for n in nodes), "Select one or more columns for inspection."),
        ]
    elif number == 7:
        checks += [
            ValidationItem("Use comparisons", any(isinstance(n, ast.Compare) for n in nodes), "Compare values using an appropriate comparison operator."),
            ValidationItem("Use Boolean logic", any(isinstance(n, ast.BoolOp) for n in nodes), "Combine conditions with Boolean logic."),
            ValidationItem("Use conditional control flow", any(isinstance(n, ast.If) for n in nodes), "Use if/elif/else to make a decision."),
            ValidationItem("Filter a DataFrame", _has_dataframe_filter(tree) or call_any("query", "loc"), "Filter rows based on one or more conditions."),
        ]
    elif number == 8:
        checks += [
            ValidationItem("Use a loop", any(isinstance(n, (ast.For, ast.While)) for n in nodes), "Use a for or while loop for repeated work."),
            ValidationItem("Work with a collection", any(isinstance(n, (ast.List, ast.Dict, ast.Set, ast.Tuple)) for n in nodes) or call_any("iterrows", "items"), "Iterate through a collection or DataFrame."),
            ValidationItem("Produce a collected result", assignments >= 2 or call_any("append", "update"), "Store or summarize the results of the repeated work."),
        ]
    elif number == 9:
        checks += [
            ValidationItem("Use random values", any(name.startswith("random") or name.startswith("np.random") for name in calls | imports), "Use a random-number tool for the simulation."),
            ValidationItem("Repeat the trial", any(isinstance(n, (ast.For, ast.While)) for n in nodes), "Run the simulated trial repeatedly."),
            ValidationItem("Summarize the outcomes", call_any("mean", "sum", "count") or any(isinstance(n, ast.BinOp) for n in nodes), "Calculate a probability or distribution summary from the outcomes."),
        ]
    elif number == 10:
        checks += [
            ValidationItem("Load the operations data", call_any("read_csv"), "Load the supplied CSV into a DataFrame."),
            ValidationItem("Create a calculated column", any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) for t in n.targets) for n in nodes) or call_any("assign"), "Add a new calculated field without overwriting a source column."),
            ValidationItem("Clean a label", call_any("rename", "replace"), "Rename a field or replace an inconsistent category value."),
            ValidationItem("Sort the result", call_any("sort_values", "sort_index"), "Sort the transformed DataFrame for review."),
        ]
    elif number == 11:
        checks += [
            ValidationItem("Load the operations data", call_any("read_csv"), "Load the supplied CSV into a DataFrame."),
            ValidationItem("Group the data", call_any("groupby"), "Group rows by an appropriate business category."),
            ValidationItem("Aggregate measures", call_any("agg", "sum", "mean", "count", "nunique"), "Calculate one or more grouped summary measures."),
        ]
    elif number == 12:
        checks += [
            ValidationItem("Load the operations data", call_any("read_csv"), "Load the supplied CSV into a DataFrame."),
            ValidationItem("Use label-based selection", call_any("loc") or ".loc" in code, "Use loc for a label-based selection."),
            ValidationItem("Use position-based selection", call_any("iloc") or ".iloc" in code, "Use iloc for a position-based selection."),
            ValidationItem("Work with an index", call_any("set_index", "reset_index", "sort_index") or ".index" in code, "Create, inspect, or use a meaningful index."),
        ]
    elif number == 13:
        checks += [
            ValidationItem("Create or load a DataFrame", call_any("DataFrame", "read_csv"), "Create or load the analysis DataFrame."),
            ValidationItem("Reshape the data", call_any("pivot", "pivot_table", "melt", "stack", "unstack"), "Reshape the data for comparison."),
            ValidationItem("Visualize the result", call_any("plot", "bar", "hist"), "Create a chart from the DataFrame result."),
            ValidationItem("Interpret the output", has_output, "Print a short result or interpretation from the analysis."),
        ]
    checks.append(ValidationItem("Add decision and validation comments", _custom_comment_count(code) >= 2, "Add at least two original comments: one decision and one validation check."))
    checks.append(ValidationItem("Produce reviewable output", has_output or number in {5, 13}, "Print the requested values or create the required charts."))
    return checks


def check_code(root: Path, number: int, code: str) -> dict[str, Any]:
    code = str(code or "")
    checklist: list[ValidationItem] = []
    try:
        tree = ast.parse(code)
        checklist.append(ValidationItem("Python syntax", True, "The editor content parses as valid Python."))
    except SyntaxError as exc:
        return {
            "passed": False,
            "checklist": [ValidationItem("Python syntax", False, str(exc))],
            "run": {
                "ok": False,
                "stdout": "",
                "stderr": str(exc),
                "error_line": int(exc.lineno or 1),
                "images": [],
            },
            "summary": f"Fix the syntax error on line {int(exc.lineno or 1)} before checking the exercise.",
        }

    starter = starter_code(root, number).strip()
    changed = code.strip() != starter
    checklist.append(ValidationItem("Starter completed", changed, "Replace the blank task sections with your own code."))
    checklist.extend(_feature_checks(int(number), tree, code))
    run = run_code(root, number, code)
    checklist.append(
        ValidationItem(
            "Runs from top to bottom",
            bool(run["ok"]),
            "The file completed without an exception." if run["ok"] else (str(run.get("stderr") or "Python returned an error.").splitlines()[-1]),
        )
    )
    output_present = bool(str(run.get("stdout") or "").strip() or run.get("images"))
    checklist.append(
        ValidationItem(
            "Output can be reviewed",
            output_present,
            "The run produced text or a chart." if output_present else "Print the requested result or display the requested chart.",
        )
    )
    passed = all(item.passed for item in checklist)
    failed = [item.label for item in checklist if not item.passed]
    summary = (
        "All validation checkpoints passed. You can mark the exercise complete."
        if passed
        else "Review: " + "; ".join(failed[:4]) + ("." if failed else "")
    )
    return {"passed": passed, "checklist": checklist, "run": run, "summary": summary}
