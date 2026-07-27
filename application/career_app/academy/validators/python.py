from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ..models import DatasetDefinition
from .base import ValidationResult


_WORKER = r'''
import contextlib
import io
import json
import traceback
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd

payload = json.loads(Path(__import__('sys').argv[1]).read_text(encoding='utf-8'))
namespace = {'pd': pd, 'np': np}
for table in payload.get('tables', []):
    namespace[table['name']] = pd.read_csv(table['path'])
stdout = io.StringIO()
try:
    with contextlib.redirect_stdout(stdout):
        exec(compile(payload.get('code', ''), '<academy-python>', 'exec'), namespace, namespace)
    failures = []
    for item in payload.get('checks', []):
        expression = str(item.get('expression') or '')
        try:
            passed = bool(eval(expression, namespace, namespace))
        except Exception as exc:
            passed = False
            failures.append(str(item.get('feedback') or f"The check {expression!r} could not run: {exc}"))
            continue
        if not passed:
            failures.append(str(item.get('feedback') or 'Your code ran, but the result does not match the task yet.'))
    rows = []
    columns = []
    display = str(payload.get('display_variable') or '')
    if display and display in namespace:
        value = namespace[display]
        if isinstance(value, pd.DataFrame):
            preview = value.head(20)
            columns = [str(c) for c in preview.columns]
            rows = [[None if pd.isna(v) else v for v in row] for row in preview.itertuples(index=False, name=None)]
        elif isinstance(value, pd.Series):
            preview = value.head(20)
            columns = [str(value.name or display)]
            rows = [[None if pd.isna(v) else v] for v in preview.tolist()]
        else:
            columns = [display]
            rows = [[value]]
    print(json.dumps({
        'ok': not failures,
        'stdout': stdout.getvalue(),
        'failures': failures,
        'columns': columns,
        'rows': rows,
    }, default=str))
except Exception:
    print(json.dumps({'ok': False, 'error': traceback.format_exc(), 'stdout': stdout.getvalue()}))
'''


class PythonValidator:
    def __init__(self, dataset: DatasetDefinition | None = None, timeout_seconds: int = 8):
        self.dataset = dataset
        self.timeout_seconds = max(2, int(timeout_seconds))

    def _payload(self, code: str, spec: dict[str, Any]) -> dict[str, Any]:
        tables = []
        if self.dataset is not None:
            tables = [{"name": item.name, "path": str(item.csv_path)} for item in self.dataset.tables]
        checks = spec.get("checks") or []
        if not isinstance(checks, list):
            checks = []
        return {
            "code": code,
            "tables": tables,
            "checks": checks,
            "display_variable": str(spec.get("display_variable") or ""),
        }

    def _run(self, code: str, spec: dict[str, Any]) -> ValidationResult:
        if not str(code or "").strip():
            return ValidationResult(False, "Write some Python before running or checking the exercise.")
        with tempfile.TemporaryDirectory(prefix="dca-python-") as temp:
            temp_path = Path(temp)
            worker = temp_path / "worker.py"
            payload = temp_path / "payload.json"
            worker.write_text(_WORKER, encoding="utf-8")
            payload.write_text(json.dumps(self._payload(code, spec)), encoding="utf-8")
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", str(worker), str(payload)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return ValidationResult(False, "Your code took too long to finish. Check for a loop that never ends, then try again.")
        output = (completed.stdout or "").strip().splitlines()
        if not output:
            detail = (completed.stderr or "").strip()
            return ValidationResult(False, "Python could not return a result." + (f"\n\n{detail}" if detail else ""))
        try:
            result = json.loads(output[-1])
        except json.JSONDecodeError:
            return ValidationResult(False, "Python returned an unreadable result. Review the code and try again.")
        if result.get("error"):
            trace = str(result["error"])
            last = next((line.strip() for line in reversed(trace.splitlines()) if line.strip()), "Python error")
            return ValidationResult(False, f"Your code did not run yet: {last}")
        columns = tuple(str(item) for item in result.get("columns", []))
        rows = tuple(tuple(row) for row in result.get("rows", []))
        if result.get("ok"):
            feedback = str(spec.get("success_feedback") or "Your Python code runs and produces the result the exercise asks for.")
            stdout = str(result.get("stdout") or "").strip()
            if stdout:
                feedback += f"\n\nOutput:\n{stdout}"
            return ValidationResult(True, feedback, columns=columns, rows=rows)
        failures = [str(item) for item in result.get("failures", []) if str(item).strip()]
        return ValidationResult(False, failures[0] if failures else str(spec.get("failure_feedback") or "Your code ran, but the result does not match the task yet."), columns=columns, rows=rows)

    def execute(self, code: str) -> ValidationResult:
        return self._run(code, {"checks": [], "success_feedback": "Your code ran successfully."})

    def validate(self, code: str, spec: dict[str, Any]) -> ValidationResult:
        return self._run(code, spec)
