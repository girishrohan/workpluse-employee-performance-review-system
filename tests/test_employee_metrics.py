"""Tests for operational metrics storage and honest missing-data handling."""

import os
import tempfile
import unittest
from datetime import date

from services.workpulse_service import (
    create_employee,
    get_employees,
    initialize_database,
    update_employee_metrics,
)


class EmployeeMetricsTests(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(handle)
        initialize_database(self.db_path)
        self.employee_id = create_employee(
            "WP-7001", "Metrics Tester", "Engineering", "Engineer",
            date.today(), "Active", 4.0, self.db_path,
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_new_employee_has_no_fabricated_metrics(self):
        record = get_employees(self.db_path).iloc[0]
        self.assertTrue(_is_missing(record["attendance_rate"]))
        self.assertTrue(_is_missing(record["task_completion_rate"]))
        self.assertTrue(_is_missing(record["training_hours"]))
        self.assertTrue(_is_missing(record["previous_performance"]))

    def test_metrics_round_trip_and_validation(self):
        update_employee_metrics(
            self.employee_id, 93.5, 88.0, 42.0, 4.2, self.db_path
        )
        record = get_employees(self.db_path).iloc[0]
        self.assertAlmostEqual(float(record["attendance_rate"]), 93.5)
        self.assertAlmostEqual(float(record["task_completion_rate"]), 88.0)
        self.assertAlmostEqual(float(record["training_hours"]), 42.0)
        self.assertAlmostEqual(float(record["previous_performance"]), 4.2)

        with self.assertRaises(ValueError):
            update_employee_metrics(self.employee_id, 140.0, 80.0, 10.0, 3.0, self.db_path)
        with self.assertRaises(ValueError):
            update_employee_metrics(self.employee_id, 80.0, 80.0, 10.0, 6.0, self.db_path)

    def test_updating_metrics_overwrites_previous_snapshot(self):
        update_employee_metrics(self.employee_id, 90.0, 80.0, 20.0, 3.5, self.db_path)
        update_employee_metrics(self.employee_id, 95.0, 85.0, 30.0, 4.0, self.db_path)
        record = get_employees(self.db_path).iloc[0]
        self.assertAlmostEqual(float(record["attendance_rate"]), 95.0)
        self.assertAlmostEqual(float(record["training_hours"]), 30.0)


def _is_missing(value):
    try:
        return value is None or value != value
    except Exception:
        return True


if __name__ == "__main__":
    unittest.main()
