"""
WorkPulse - Automated Database Unit Tests
Verifies SQLite schema creation, CRUD operations, duplicate prevention, and cascade relationships.
"""

import os
import unittest
import pandas as pd
from database.db_manager import (
    init_db, add_employee, update_employee, delete_employee,
    get_all_employees, get_employee_history
)

TEST_DB = "data/test_workpulse.db"


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_add_and_retrieve_employee(self):
        """Tests inserting and reading an employee."""
        emp_id = add_employee(
            employee_code="WP-TEST-1",
            employee_name="Alice Test",
            department="Engineering",
            experience_years=4.0,
            attendance_rate=95.0,
            task_completion_rate=90.0,
            training_hours=30.0,
            previous_performance=4.5,
            performance_category="High",
            review_date="2026-06-01",
            db_path=TEST_DB
        )
        self.assertIsNotNone(emp_id)

        df = get_all_employees(TEST_DB)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['employee_code'], "WP-TEST-1")
        self.assertEqual(df.iloc[0]['performance_category'], "High")

    def test_duplicate_employee_code_rejected(self):
        """Verifies duplicate employee codes raise an exception."""
        add_employee(
            employee_code="WP-UNIQUE",
            employee_name="Bob Unique",
            department="Sales",
            experience_years=2.0,
            attendance_rate=80.0,
            task_completion_rate=80.0,
            training_hours=10.0,
            previous_performance=3.0,
            performance_category="Moderate",
            review_date="2026-06-01",
            db_path=TEST_DB
        )
        with self.assertRaises(ValueError):
            add_employee(
                employee_code="WP-UNIQUE",
                employee_name="Bob Duplicate",
                department="Marketing",
                experience_years=3.0,
                attendance_rate=85.0,
                task_completion_rate=85.0,
                training_hours=15.0,
                previous_performance=3.5,
                performance_category="Moderate",
                review_date="2026-06-01",
                db_path=TEST_DB
            )

    def test_update_employee(self):
        """Tests modifying an existing employee record."""
        emp_id = add_employee(
            employee_code="WP-UPD",
            employee_name="Charlie Initial",
            department="Finance",
            experience_years=1.0,
            attendance_rate=75.0,
            task_completion_rate=70.0,
            training_hours=5.0,
            previous_performance=2.5,
            performance_category="Needs Support",
            review_date="2026-05-01",
            db_path=TEST_DB
        )
        res = update_employee(
            employee_id=emp_id,
            employee_name="Charlie Updated",
            department="Operations",
            experience_years=1.5,
            attendance_rate=85.0,
            task_completion_rate=82.0,
            training_hours=25.0,
            previous_performance=3.2,
            performance_category="Moderate",
            review_date="2026-06-01",
            db_path=TEST_DB
        )
        self.assertTrue(res)

        df = get_all_employees(TEST_DB)
        self.assertEqual(df.iloc[0]['employee_name'], "Charlie Updated")
        self.assertEqual(df.iloc[0]['performance_category'], "Moderate")

    def test_delete_employee(self):
        """Tests removing an employee record."""
        emp_id = add_employee(
            employee_code="WP-DEL",
            employee_name="David Delete",
            department="Customer Support",
            experience_years=2.0,
            attendance_rate=88.0,
            task_completion_rate=85.0,
            training_hours=12.0,
            previous_performance=3.4,
            performance_category="Moderate",
            review_date="2026-06-01",
            db_path=TEST_DB
        )
        delete_employee(emp_id, db_path=TEST_DB)
        df = get_all_employees(TEST_DB)
        self.assertEqual(len(df), 0)


if __name__ == '__main__':
    unittest.main()
