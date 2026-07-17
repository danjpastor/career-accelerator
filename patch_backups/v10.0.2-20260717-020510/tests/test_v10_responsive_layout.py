from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication, QLabel

from career_app.main import CareerAccelerator, NAV
from career_app.ui.course_ui import CoursePageWidget


class ResponsiveLayoutV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.window = CareerAccelerator()
        cls.window.show()
        cls._flush()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls._flush()

    @classmethod
    def _flush(cls, passes: int = 8) -> None:
        for _ in range(passes):
            cls.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        cls.app.processEvents()

    def resize_window(self, width: int, height: int) -> None:
        self.window.resize(width, height)
        self.window._apply_responsive_shell()
        self._flush()

    def test_supported_window_sizes_and_dashboard_breakpoints(self) -> None:
        self.assertLessEqual(self.window.minimumWidth(), 900)
        self.assertLessEqual(self.window.minimumHeight(), 620)

        self.resize_window(900, 620)
        self.window.navigate(0)
        self._flush()
        self.assertEqual(self.window.dashboard_layout_mode, "compact")
        self.assertEqual(self.window.sidebar.width(), 180)

        self.resize_window(1280, 800)
        self.window.navigate(0)
        self._flush()
        self.assertEqual(self.window.dashboard_layout_mode, "medium")
        self.assertEqual(self.window.sidebar.width(), 224)

        self.resize_window(1536, 1020)
        self.window.navigate(0)
        self._flush()
        self.assertEqual(self.window.dashboard_layout_mode, "wide")
        self.assertEqual(self.window.sidebar.width(), 266)

    def test_every_main_page_avoids_horizontal_overflow_after_resize_cycles(self) -> None:
        # Start wide, collapse to the supported minimum, then expand again. This
        # catches stale QGridLayout stretch factors left behind by reflowing.
        for size in ((1536, 1020), (900, 620), (1280, 800), (1536, 1020)):
            self.resize_window(*size)
            for _label, index in NAV:
                self.window.navigate(index)
                self._flush(3)
                page = self.window.stack.currentWidget()
                self.assertEqual(
                    page.horizontalScrollBar().maximum(),
                    0,
                    f"page {index} overflowed horizontally at {size}",
                )

    def test_compact_single_column_cards_use_the_full_page_width(self) -> None:
        self.resize_window(900, 620)

        self.window.navigate(10)
        self._flush()
        settings_page = self.window.stack.currentWidget()
        available = settings_page.viewport().width()
        self.assertGreater(self.window.settings_cards[0].width(), available * 0.88)

        self.window.navigate(5)
        self._flush()
        study_page = self.window.stack.currentWidget()
        available = study_page.viewport().width()
        self.assertGreater(self.window.study_timer_card.width(), available * 0.88)
        self.assertGreater(self.window.study_log_card.width(), available * 0.88)

    def test_guided_sql_workspaces_receive_usable_compact_heights(self) -> None:
        self.resize_window(900, 620)

        self.window.navigate(2)
        self.window.learning_tabs.setCurrentWidget(self.window.exercise_packs_widget)
        self._flush()
        packs = self.window.exercise_packs_widget
        self.assertEqual(packs._responsive_mode, "compact")
        self.assertEqual(packs.exercise_splitter.orientation(), Qt.Orientation.Vertical)
        self.assertEqual(packs.workspace_splitter.orientation(), Qt.Orientation.Vertical)
        self.assertGreaterEqual(packs.minimumHeight(), 1400)
        self.assertGreaterEqual(self.window.learning_tabs.minimumHeight(), 1500)

        self.window.navigate(4)
        self.window.sql_tabs.setCurrentWidget(self.window.duckdb_exercises_widget)
        self._flush()
        duckdb = self.window.duckdb_exercises_widget
        self.assertEqual(duckdb._responsive_mode, "compact")
        self.assertEqual(duckdb.main_splitter.orientation(), Qt.Orientation.Vertical)
        self.assertEqual(duckdb.workspace_splitter.orientation(), Qt.Orientation.Vertical)
        self.assertGreaterEqual(duckdb.minimumHeight(), 1400)
        self.assertGreaterEqual(self.window.sql_tabs.minimumHeight(), 1500)

    def test_rebuilding_course_content_does_not_leave_overlapping_titles(self) -> None:
        page = CoursePageWidget()
        page.resize(620, 500)
        page.show()
        page.set_markdown("# First title\n\nBody", eyebrow="Lesson")
        page.set_markdown("# Final title\n\nBody", eyebrow="Lesson")
        self._flush()
        final_labels = [
            label for label in page.findChildren(QLabel)
            if label.text() == "Final title" and label.isVisible()
        ]
        first_labels = [
            label for label in page.findChildren(QLabel)
            if label.text() == "First title" and label.isVisible()
        ]
        self.assertEqual(len(final_labels), 1)
        self.assertEqual(len(first_labels), 0)
        page.close()


if __name__ == "__main__":
    unittest.main()
