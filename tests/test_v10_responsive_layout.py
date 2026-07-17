from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel

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
        self.assertEqual(self.window.dashboard_layout_mode, "fit")
        self.assertEqual(self.window.dashboard_density, "ultra")
        self.assertEqual(self.window.sidebar.width(), 180)
        self.assertEqual(self.window.dashboard_scroll.verticalScrollBar().maximum(), 0)

        self.resize_window(1280, 800)
        self.window.navigate(0)
        self._flush()
        self.assertEqual(self.window.dashboard_layout_mode, "fit")
        self.assertEqual(self.window.dashboard_density, "compact")
        self.assertEqual(self.window.sidebar.width(), 224)
        self.assertEqual(self.window.dashboard_scroll.verticalScrollBar().maximum(), 0)

        self.resize_window(1536, 1020)
        self.window.navigate(0)
        self._flush()
        self.assertEqual(self.window.dashboard_layout_mode, "wide")
        self.assertEqual(self.window.dashboard_density, "comfortable")
        self.assertEqual(self.window.sidebar.width(), 266)
        self.assertEqual(self.window.dashboard_scroll.verticalScrollBar().maximum(), 0)

    def test_dashboard_stays_fully_visible_at_supported_desktop_sizes(self) -> None:
        for size in (
            (900, 620),
            (1024, 768),
            (1280, 800),
            (1366, 768),
            (1536, 1020),
        ):
            with self.subTest(size=size):
                self.resize_window(*size)
                self.window.navigate(0)
                self._flush()
                page = self.window.dashboard_scroll
                self.assertEqual(page.verticalScrollBar().maximum(), 0)
                self.assertEqual(page.horizontalScrollBar().maximum(), 0)
                for card in self.window.dashboard_metric_cards:
                    ring = card.layout.itemAt(0).widget()
                    self.assertLessEqual(ring.height(), card.contentsRect().height())

    def test_front_page_sidebar_and_dashboard_fit_without_scrolling(self) -> None:
        for size in (
            (900, 620),
            (1024, 768),
            (1280, 800),
            (1366, 768),
            (1536, 1020),
        ):
            with self.subTest(size=size):
                self.resize_window(*size)
                self.window.navigate(0)
                self._flush()
                self.assertEqual(
                    self.window.sidebar_scroll.verticalScrollBar().maximum(),
                    0,
                )
                viewport = self.window.sidebar_scroll.viewport()
                for widget in (
                    self.window.sidebar_streak_card,
                    self.window.sidebar_time_card,
                    self.window.sidebar_footer,
                ):
                    top_left = widget.mapTo(viewport, widget.rect().topLeft())
                    self.assertGreaterEqual(top_left.y(), 0)
                    self.assertLessEqual(
                        top_left.y() + widget.height(),
                        viewport.height(),
                    )

    def test_dashboard_rows_do_not_expand_into_large_blank_bands(self) -> None:
        for size in (
            (900, 620),
            (1024, 768),
            (1280, 800),
            (1366, 768),
            (1536, 1020),
        ):
            with self.subTest(size=size):
                self.resize_window(*size)
                self.window.navigate(0)
                self._flush()
                sections = (
                    self.window.dashboard_header_section,
                    self.window.dashboard_metrics_section,
                    self.window.dashboard_primary_section,
                    self.window.dashboard_secondary_section,
                    self.window.dashboard_footer_section,
                )
                expected_gap = self.window.dashboard_root_layout.spacing()
                for previous, current in zip(sections, sections[1:]):
                    actual_gap = current.y() - (
                        previous.y() + previous.height()
                    )
                    self.assertEqual(actual_gap, expected_gap)

                self.assertEqual(
                    self.window.dashboard_primary_section.height(),
                    self.window.dashboard_focus_card.height(),
                )
                self.assertEqual(
                    self.window.dashboard_secondary_section.height(),
                    self.window.dashboard_growth_card.height(),
                )
                self.assertEqual(
                    self.window.dashboard_footer_section.height(),
                    self.window.encouragement_card.height(),
                )


    def test_dashboard_action_labels_have_full_scaled_height(self) -> None:
        for size in (
            (900, 620),
            (1024, 768),
            (1280, 800),
            (1680, 944),
            (1536, 1020),
        ):
            with self.subTest(size=size):
                self.resize_window(*size)
                self.window.navigate(0)
                self._flush()
                buttons = [
                    self.window.dashboard_start_button,
                    *(
                        self.window.dashboard_timer_controls.itemAt(index).widget()
                        for index in range(
                            self.window.dashboard_timer_controls.count()
                        )
                    ),
                    self.window.dashboard_summary_button,
                    self.window.dashboard_highest_impact_button,
                    self.window.dashboard_view_readiness_button,
                ]
                for button in buttons:
                    self.assertGreaterEqual(
                        button.height(),
                        button.sizeHint().height(),
                        f"button text clipped for {button.text()} at {size}",
                    )

                for button in buttons[:4]:
                    bottom = button.mapTo(
                        self.window.dashboard_timer_card,
                        button.rect().bottomLeft(),
                    ).y()
                    self.assertLessEqual(
                        bottom,
                        self.window.dashboard_timer_card.contentsRect().bottom(),
                        f"Study Session control overflowed at {size}",
                    )

    def test_sidebar_links_expand_into_the_available_navigation_region(self) -> None:
        for size in ((900, 620), (1280, 800), (1680, 944), (1536, 1020)):
            with self.subTest(size=size):
                self.resize_window(*size)
                self.window.navigate(0)
                self._flush()
                content = self.window.sidebar_scroll.widget()
                last_button = self.window.nav_buttons[-1]
                last_bottom = last_button.mapTo(
                    content,
                    last_button.rect().bottomLeft(),
                ).y()
                gap = self.window.sidebar_streak_card.y() - last_bottom - 1
                self.assertLessEqual(
                    gap,
                    max(8, self.window.sidebar_content_layout.spacing() + 4),
                    f"sidebar left an unused band at {size}",
                )
                heights = [button.height() for button in self.window.nav_buttons]
                self.assertLessEqual(max(heights) - min(heights), 1)

    def test_settings_exposes_rebuild_today_snapshot_action(self) -> None:
        self.resize_window(1024, 768)
        self.window.navigate(10)
        self._flush()
        button = self.window.rebuild_today_snapshot_button
        self.assertIn("Rebuild Today's Snapshot", button.text())
        self.assertTrue(button.isEnabled())

    def test_dashboard_matches_display_scaled_window_without_scroll_or_timer_overlap(self) -> None:
        # Mirrors the logical client size shown by a 1680-wide Windows desktop
        # using display scaling. This was the remaining real-world regression.
        self.resize_window(1680, 944)
        self.window.navigate(0)
        self._flush()
        page = self.window.dashboard_scroll
        self.assertEqual(
            page.verticalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertEqual(page.verticalScrollBar().maximum(), 0)
        self.assertLessEqual(
            self.window.dashboard_content.sizeHint().height(),
            page.viewport().height(),
        )

        timer_bottom = (
            self.window.dashboard_timer_stage.y()
            + self.window.circular_timer.y()
            + self.window.circular_timer.height()
        )
        self.assertLessEqual(
            timer_bottom,
            self.window.dashboard_start_button.y(),
        )

    def test_page_header_dates_stay_on_one_line(self) -> None:
        for size in ((900, 620), (1680, 944)):
            with self.subTest(size=size):
                self.resize_window(*size)
                for index in range(1, self.window.stack.count()):
                    self.window.navigate(index)
                    self._flush(2)
                    page = self.window.stack.currentWidget()
                    date_label = getattr(page, "date_label", None)
                    if date_label is None:
                        continue
                    self.assertFalse(date_label.wordWrap())
                    self.assertGreaterEqual(
                        date_label.width(),
                        date_label.sizeHint().width(),
                        f"date clipped on page {index} at {size}",
                    )
                    self.assertLessEqual(
                        date_label.height(),
                        max(40, date_label.sizeHint().height() * 2),
                        f"date unexpectedly stacked on page {index} at {size}",
                    )

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

    def test_course_extension_host_does_not_float_behind_title_pill(self) -> None:
        page = CoursePageWidget()
        embedded = QFrame()
        embedded.setMinimumHeight(80)
        page.set_embedded_widget(embedded)
        page.resize(620, 500)
        page.show()
        page.set_markdown(
            "# Lesson title\n\nBody",
            eyebrow="Applied Lab",
            subtitle="Power BI • Week 7 • 45 minutes",
        )
        self._flush()
        self.assertIs(embedded.parentWidget(), page.embedded_host)
        self.assertIs(page.embedded_host.parentWidget(), page.page)
        self.assertGreater(page.embedded_host.y(), 100)
        page.close()

    def test_rounded_course_subtitle_uses_its_required_wrapped_height(self) -> None:
        page = CoursePageWidget()
        page.resize(520, 420)
        page.show()
        subtitle = (
            "Week 6 • 45 minutes • 7 questions • 3 datasets • "
            "INNER JOIN, LEFT JOIN, multi-table joins"
        )
        page.set_markdown(
            "# Join customers, orders, and payments\n\nBody",
            eyebrow="DuckDB Exercise",
            subtitle=subtitle,
        )
        self._flush()
        labels = [label for label in page.page.findChildren(QLabel) if label.text() == subtitle]
        self.assertEqual(len(labels), 1)
        label = labels[0]
        self.assertGreater(label.heightForWidth(label.width()), 0)
        self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
        page.close()


if __name__ == "__main__":
    unittest.main()
