from __future__ import annotations

import unittest

from career_app.main import CareerAccelerator
from career_app.services import sql_workspace


class InterviewSubmissionV10Tests(unittest.TestCase):
    def test_untouched_template_is_not_original_work(self) -> None:
        template = sql_workspace.starter_template(
            title="Example Problem",
            difficulty="Easy",
            topic="Aggregation",
            concepts="COUNT, GROUP BY",
        )
        self.assertFalse(CareerAccelerator._sql_submission_has_original_query(template))

    def test_completed_select_is_recognized_as_original_work(self) -> None:
        query = "SELECT customer_id, COUNT(*) AS order_count FROM orders GROUP BY customer_id;"
        self.assertTrue(CareerAccelerator._sql_submission_has_original_query(query))

    def test_non_query_text_is_rejected(self) -> None:
        self.assertFalse(CareerAccelerator._sql_submission_has_original_query("I would group the rows."))


if __name__ == "__main__":
    unittest.main()
