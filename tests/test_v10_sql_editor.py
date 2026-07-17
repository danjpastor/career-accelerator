from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from PySide6.QtWidgets import QApplication, QPushButton

from career_app.ui.course_ui import SqlCodeEditor
from career_app.ui.widgets import FocusRow


class SqlEditorV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_line_numbers_track_document(self) -> None:
        editor = SqlCodeEditor()
        editor.setPlainText("SELECT 1;\nSELECT 2;\nSELECT 3;")
        self.app.processEvents()
        self.assertEqual(editor.line_numbers.toPlainText(), "1\n2\n3")
        self.assertGreaterEqual(editor.line_numbers.width(), 42)

    def test_duckdb_error_navigates_to_reported_line_and_column(self) -> None:
        editor = SqlCodeEditor()
        editor.setPlainText("SELECT\n    customer_id\nFROM customers\nWHERE;")
        self.assertTrue(editor.navigate_to_error("Parser Error: syntax error at or near WHERE\nLINE 4: WHERE;"))
        self.app.processEvents()
        cursor = editor.editor.textCursor()
        self.assertEqual(editor._error_line, 4)
        self.assertEqual(cursor.blockNumber(), 3)

    def test_editing_clears_previous_error_highlight(self) -> None:
        editor = SqlCodeEditor()
        editor.setPlainText("SELECT 1;\nSELECT 2;")
        editor.set_error_line(2)
        self.assertEqual(editor._error_line, 2)
        editor.editor.insertPlainText(" -- fixed")
        self.app.processEvents()
        self.assertIsNone(editor._error_line)

    def test_completed_focus_action_is_disabled(self) -> None:
        row = FocusRow(
            "✅", "Completed task", "Finished today", "Done", "#22c55e",
            action_text="Open", on_action=lambda: None, completed=True,
        )
        buttons = row.findChildren(QPushButton)
        self.assertEqual(len(buttons), 1)
        self.assertFalse(buttons[0].isEnabled())


if __name__ == "__main__":
    unittest.main()
