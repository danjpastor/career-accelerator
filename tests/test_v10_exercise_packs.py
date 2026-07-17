from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import unittest

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


if __name__ == "__main__":
    unittest.main()
