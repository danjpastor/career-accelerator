from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication

from career_app.ui.exercise_packs import ExercisePacksWidget
from career_app.services.exercise_packs import (
    check_answer, ensure_schema, load_exercise, progress_for, save_progress, validate_pack,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_DIRS = (
    ROOT / "exercise_packs" / "bundled" / "sql-subqueries-foundations",
    ROOT / "exercise_packs" / "installed" / "sql-subqueries-foundations",
    ROOT / "exercise_packs" / "installed" / "sql-joins-foundations",
    ROOT / "exercise_packs" / "templates" / "standard-pack-template",
)


class ExercisePackV10Tests(unittest.TestCase):
    def test_every_lesson_has_ordered_practice_questions(self) -> None:
        for pack_dir in PACK_DIRS:
            with self.subTest(pack=pack_dir.name):
                pack = validate_pack(pack_dir)
                lessons = {item["id"] for item in pack.get("lessons", [])}
                mapped = {lesson_id: [] for lesson_id in lessons}
                for entry in pack["exercises"]:
                    self.assertIn("lesson_id", entry)
                    self.assertIn(entry["lesson_id"], lessons)
                    self.assertGreaterEqual(int(entry.get("question_number", 0)), 1)
                    mapped[entry["lesson_id"]].append(int(entry["question_number"]))
                for lesson_id, numbers in mapped.items():
                    self.assertTrue(numbers, f"{lesson_id} has no practice question")
                    self.assertEqual(numbers, sorted(numbers))
                    self.assertEqual(len(numbers), len(set(numbers)))

    def test_builtin_starters_are_minimal_and_answer_safe(self) -> None:
        for pack_dir in PACK_DIRS:
            pack = validate_pack(pack_dir)
            for entry in pack["exercises"]:
                with self.subTest(pack=pack["pack_id"], question=entry["id"]):
                    exercise = load_exercise(pack, entry["id"])
                    starter = exercise["starter_sql"].strip()
                    solution = (pack_dir / exercise["solution_file"]).read_text(encoding="utf-8").strip()
                    self.assertTrue(starter.startswith("-- Write your answer below."))
                    self.assertIn("-- requested columns", starter)
                    self.assertNotEqual(starter.casefold(), solution.casefold())
                    self.assertNotIn(" join ", f" {starter.casefold()} ")
                    self.assertNotIn(" where ", f" {starter.casefold()} ")
                    self.assertNotIn(" group by ", f" {starter.casefold()} ")
                    self.assertNotIn(" with ", f" {starter.casefold()} ")
                    self.assertLessEqual(starter.casefold().count("select"), 1)

    def test_all_official_solutions_pass_answer_validation(self) -> None:
        # Validate only the distributable copies, not the duplicated installed/bundled
        # copy of the same Subqueries pack.
        pack_dirs = (
            ROOT / "exercise_packs" / "bundled" / "sql-subqueries-foundations",
            ROOT / "exercise_packs" / "installed" / "sql-joins-foundations",
            ROOT / "exercise_packs" / "templates" / "standard-pack-template",
        )
        for pack_dir in pack_dirs:
            pack = validate_pack(pack_dir)
            for entry in pack["exercises"]:
                with self.subTest(pack=pack["pack_id"], question=entry["id"]):
                    exercise = load_exercise(pack, entry["id"])
                    solution = (pack_dir / exercise["solution_file"]).read_text(encoding="utf-8")
                    result = check_answer(exercise, solution)
                    self.assertTrue(result["correct"], result)

    def test_manifest_and_exercise_associations_agree(self) -> None:
        for pack_dir in PACK_DIRS:
            manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
            for entry in manifest["exercises"]:
                exercise = json.loads((pack_dir / entry["file"]).read_text(encoding="utf-8"))
                self.assertEqual(entry["lesson_id"], exercise["lesson_id"])
                self.assertEqual(entry["question_number"], exercise["question_number"])
                self.assertEqual(entry["show_starter_sql"], exercise["show_starter_sql"])

    def test_lesson_examples_do_not_reveal_the_paired_question_solution(self) -> None:
        code_block_pattern = re.compile(r"```sql\s*(.*?)```", re.IGNORECASE | re.DOTALL)
        table_pattern = re.compile(
            r"\b(?:FROM|JOIN)\s+[\"`\[]?([A-Za-z_][A-Za-z0-9_]*)",
            re.IGNORECASE,
        )

        for pack_dir in PACK_DIRS:
            pack = validate_pack(pack_dir)
            lesson_markdown = {
                lesson["id"]: (pack_dir / lesson["file"]).read_text(encoding="utf-8")
                for lesson in pack.get("lessons", [])
            }
            for entry in pack["exercises"]:
                exercise = load_exercise(pack, entry["id"])
                solution = (pack_dir / exercise["solution_file"]).read_text(encoding="utf-8")
                lesson = lesson_markdown[entry["lesson_id"]]
                normalized_solution = re.sub(r"\s+", " ", solution).strip().casefold()
                normalized_lesson = re.sub(r"\s+", " ", lesson).strip().casefold()
                with self.subTest(pack=pack["pack_id"], question=entry["id"]):
                    self.assertNotIn(normalized_solution, normalized_lesson)
                    solution_tables = {
                        name.casefold() for name in table_pattern.findall(solution)
                    }
                    for example in code_block_pattern.findall(lesson):
                        example_tables = {
                            name.casefold() for name in table_pattern.findall(example)
                        }
                        if solution_tables and example_tables:
                            self.assertNotEqual(
                                example_tables,
                                solution_tables,
                                "lesson example reuses the exact paired-question tables",
                            )

    def test_hint_progress_is_persisted_per_question(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        ensure_schema(conn)
        save_progress(
            conn, "test-pack", "question-one", status="In Progress",
            answer_sql="SELECT 1;", notes="note", hint_index=2,
        )
        saved = progress_for(conn, "test-pack", "question-one")
        self.assertEqual(saved["hint_index"], 2)
        # A normal save that omits hint_index preserves the revealed level.
        save_progress(
            conn, "test-pack", "question-one", status="In Progress",
            answer_sql="SELECT 2;", notes="updated",
        )
        self.assertEqual(progress_for(conn, "test-pack", "question-one")["hint_index"], 2)
        conn.close()

    def test_existing_progress_table_migrates_hint_column(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute(
            """CREATE TABLE exercise_pack_progress (
                pack_id TEXT NOT NULL, exercise_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not Started',
                answer_sql TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT, completed_at TEXT,
                PRIMARY KEY(pack_id, exercise_id)
            )"""
        )
        ensure_schema(conn)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(exercise_pack_progress)")}
        self.assertIn("hint_index", columns)
        conn.close()


class ExercisePackUiV1006Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.widget = ExercisePacksWidget(self.conn, ROOT)
        self.widget.resize(1000, 700)
        self.widget.show()
        self._flush()

    def tearDown(self) -> None:
        self.widget.close()
        self._flush()
        self.conn.close()

    def _flush(self, passes: int = 8) -> None:
        for _ in range(passes):
            self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def _content_rows(self) -> list[dict]:
        return [
            self.widget.content_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.widget.content_list.count())
        ]

    def test_pack_selector_and_submission_controls_match_the_v1006_flow(self) -> None:
        self.assertFalse(self.widget.pack_list.isVisible())
        self.assertEqual(self.widget.pack_list.maximumHeight(), 0)
        self.assertEqual(self.widget.pack_selector_label.text(), "Select Pack")
        self.assertIs(
            self.widget.pack_selector_label.parentWidget(),
            self.widget.pack_selector_host,
        )
        self.assertLess(
            self.widget.pack_selector_label.x(),
            self.widget.pack_selector.x(),
        )
        self.assertIn("Submit Solution", self.widget.check_button.text())
        self.assertEqual(self.widget.complete_button.text(), "Mark Complete")
        self.assertTrue(self.widget.complete_button.isEnabled())

    def test_lesson_question_pair_preserves_one_editor_state(self) -> None:
        rows = self._content_rows()
        first_lesson_row = next(
            index for index, data in enumerate(rows) if data.get("kind") == "lesson"
        )
        first_question_row = first_lesson_row + 1
        self.assertEqual(rows[first_question_row].get("kind"), "exercise")
        second_lesson_row = next(
            index
            for index in range(first_question_row + 1, len(rows))
            if rows[index].get("kind") == "lesson"
        )

        self.widget.content_list.setCurrentRow(first_lesson_row)
        self._flush()
        first_question_id = self.widget.current_exercise["id"]
        self.widget.sql_editor.setPlainText("SELECT unique_pair_one;")
        self.widget.notes.setPlainText("pair one notes")

        self.widget.content_list.setCurrentRow(first_question_row)
        self._flush()
        self.assertEqual(self.widget.current_exercise["id"], first_question_id)
        self.assertEqual(self.widget.sql_editor.toPlainText(), "SELECT unique_pair_one;")
        self.assertEqual(self.widget.notes.toPlainText(), "pair one notes")

        self.widget.content_list.setCurrentRow(first_lesson_row)
        self._flush()
        self.assertEqual(self.widget.current_exercise["id"], first_question_id)
        self.assertEqual(self.widget.sql_editor.toPlainText(), "SELECT unique_pair_one;")
        self.assertEqual(self.widget.notes.toPlainText(), "pair one notes")

        self.widget.content_list.setCurrentRow(second_lesson_row)
        self._flush()
        second_question_id = self.widget.current_exercise["id"]
        self.assertNotEqual(second_question_id, first_question_id)
        self.assertNotEqual(self.widget.sql_editor.toPlainText(), "SELECT unique_pair_one;")
        self.widget.sql_editor.setPlainText("SELECT unique_pair_two;")

        self.widget.content_list.setCurrentRow(first_lesson_row)
        self._flush()
        self.assertEqual(self.widget.current_exercise["id"], first_question_id)
        self.assertEqual(self.widget.sql_editor.toPlainText(), "SELECT unique_pair_one;")
        self.assertEqual(self.widget.notes.toPlainText(), "pair one notes")

        self.widget.content_list.setCurrentRow(second_lesson_row)
        self._flush()
        self.assertEqual(self.widget.current_exercise["id"], second_question_id)
        self.assertEqual(self.widget.sql_editor.toPlainText(), "SELECT unique_pair_two;")

    def test_mark_complete_validates_and_completes_the_current_question(self) -> None:
        exercise = dict(self.widget.current_exercise)
        solution = (
            Path(exercise["pack_path"]) / exercise["solution_file"]
        ).read_text(encoding="utf-8")
        self.widget.sql_editor.setPlainText(solution)
        self.widget.complete_current_exercise()
        self._flush()
        saved = progress_for(
            self.conn,
            exercise["pack_id"],
            exercise["id"],
        )
        self.assertEqual(saved["status"], "Completed")
        self.assertEqual(saved["answer_sql"].strip(), solution.strip())



if __name__ == "__main__":
    unittest.main()
