"""Persistence and workflow tests for the WorkPulse review modules."""

import os
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date, timedelta

from services.workpulse_service import (
    create_employee,
    delete_period,
    get_areas,
    get_assessments,
    get_dashboard_summary,
    get_employees,
    get_notifications,
    get_pending_reviews,
    get_periods,
    get_settings,
    initialize_database,
    mark_notifications_read,
    save_areas,
    save_assessment,
    save_period,
    save_settings,
    update_employee_profile,
    delete_employee,
)


class WorkPulseServiceTests(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(handle)
        initialize_database(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_initializes_real_zero_counts_and_default_review_areas(self):
        summary = get_dashboard_summary(self.db_path)
        self.assertEqual(summary["total_employees"], 0)
        self.assertEqual(summary["active_periods"], 0)
        self.assertEqual(summary["completed_assessments"], 0)
        self.assertEqual(summary["performance_areas"], 5)
        self.assertTrue(get_employees(self.db_path).empty)

    def test_employee_create_persists_and_uses_validation(self):
        employee_id = create_employee(
            "WP-101", "Avery Chen", "Engineering", "Analyst",
            date.today(), "Active", 2.5, self.db_path,
        )
        record = get_employees(self.db_path).iloc[0]
        self.assertEqual(int(record["employee_id"]), employee_id)
        self.assertEqual(record["designation"], "Analyst")
        self.assertTrue(_is_missing(record["performance_category"]))
        with self.assertRaises(ValueError):
            create_employee(
                "", " ", "Engineering", "", date.today(), "Active", 2, self.db_path
            )

    def test_employee_profile_can_be_updated_and_deleted(self):
        employee_id = create_employee(
            "WP-106", "Morgan Lee", "Finance", "Analyst",
            date.today(), "Active", 1, self.db_path,
        )
        update_employee_profile(
            employee_id, "WP-106", "Morgan Lee", "Finance",
            "Senior Analyst", date.today(), "On leave", 2, self.db_path,
        )
        employees = get_employees(self.db_path)
        self.assertEqual(employees.iloc[0]["designation"], "Senior Analyst")
        self.assertEqual(employees.iloc[0]["status"], "On leave")
        delete_employee(employee_id, self.db_path)
        self.assertTrue(get_employees(self.db_path).empty)

    def test_period_and_assessment_workflow_calculates_weighted_score(self):
        employee_id = create_employee(
            "WP-102", "Jordan Rivera", "Product Management", "Lead",
            date.today(), "Active", 4, self.db_path,
        )
        start = date.today()
        period_id = save_period(
            "FY 2026", start, start + timedelta(days=90), "Active",
            db_path=self.db_path,
        )
        self.assertEqual(len(get_pending_reviews(self.db_path)), 1)
        scores = {
            "Attendance": 100,
            "Task completion": 80,
            "Productivity": 80,
            "Teamwork": 60,
            "Learning and development": 40,
        }
        assessment_id = save_assessment(
            employee_id, period_id, start, "Reviewer One", scores,
            "Reviewed against agreed goals.", self.db_path,
        )
        assessments = get_assessments(self.db_path)
        self.assertEqual(int(assessments.iloc[0]["assessment_id"]), assessment_id)
        self.assertEqual(float(assessments.iloc[0]["overall_score"]), 75.0)
        self.assertTrue(get_pending_reviews(self.db_path).empty)
        self.assertEqual(get_dashboard_summary(self.db_path)["completed_assessments"], 1)
        self.assertGreaterEqual(len(get_notifications(self.db_path)), 3)

    def test_assessments_require_active_period_and_valid_scores(self):
        employee_id = create_employee(
            "WP-103", "Sam Lee", "Finance", "Analyst",
            date.today(), "Active", 1, self.db_path,
        )
        period_id = save_period(
            "Draft review", date.today(), date.today(), "Draft", db_path=self.db_path
        )
        with self.assertRaisesRegex(ValueError, "active review period"):
            save_assessment(
                employee_id, period_id, date.today(), "Reviewer", {}, "", self.db_path
            )
        with self.assertRaisesRegex(ValueError, "end date"):
            save_period(
                "Invalid dates", date.today(), date.today() - timedelta(days=1),
                "Active", db_path=self.db_path,
            )
        self.assertTrue(get_assessments(self.db_path).empty)

    def test_indicator_weights_must_total_one_hundred(self):
        areas = get_areas(self.db_path).to_dict(orient="records")
        areas[0]["weight"] = 1
        with self.assertRaisesRegex(ValueError, "total 100"):
            save_areas(areas, self.db_path)
        self.assertEqual(float(get_areas(self.db_path)["weight"].sum()), 100.0)
        areas[0]["weight"] = 20
        areas[0]["description"] = "Reliability"
        save_areas(areas, self.db_path)
        self.assertEqual(
            get_areas(self.db_path).iloc[0]["description"], "Reliability"
        )

    def test_existing_indicator_weights_are_normalized_for_weighted_scoring(self):
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("UPDATE performance_areas SET weight = weight * 1.15")
            connection.commit()
        initialize_database.cache_clear()
        areas = get_areas(self.db_path)
        active_areas = areas[areas["active"].astype(bool)]
        self.assertAlmostEqual(float(active_areas["weight"].sum()), 100.0)

    def test_period_with_assessments_cannot_be_deleted(self):
        employee_id = create_employee(
            "WP-104", "Taylor Morgan", "Operations", "Coordinator",
            date.today(), "Active", 3, self.db_path,
        )
        period_id = save_period(
            "Review", date.today(), date.today(), "Active", db_path=self.db_path
        )
        save_assessment(
            employee_id,
            period_id,
            date.today(),
            "Reviewer",
            {
                "Attendance": 80,
                "Task completion": 80,
                "Productivity": 80,
                "Teamwork": 80,
                "Learning and development": 80,
            },
            "",
            self.db_path,
        )
        with self.assertRaises(Exception):
            delete_period(period_id, self.db_path)
        self.assertEqual(len(get_periods(self.db_path)), 1)

    def test_notifications_can_be_marked_read(self):
        create_employee(
            "WP-105", "Casey Park", "Sales", "Associate",
            date.today(), "Active", 1, self.db_path,
        )
        notifications = get_notifications(self.db_path)
        notification_id = int(notifications.iloc[0]["notification_id"])
        mark_notifications_read([notification_id], self.db_path)
        updated = get_notifications(self.db_path)
        self.assertFalse(_is_missing(updated.iloc[0]["read_at"]))

    def test_workspace_preferences_persist(self):
        save_settings(
            {"admin_name": "Review Lead", "workspace_name": "People Operations"},
            self.db_path,
        )
        self.assertEqual(
            get_settings(self.db_path),
            {"admin_name": "Review Lead", "workspace_name": "People Operations"},
        )

    def test_existing_one_to_five_schema_is_migrated_without_losing_reviews(self):
        handle, legacy_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(handle)
        try:
            with closing(sqlite3.connect(legacy_path)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE employees (
                        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_code TEXT NOT NULL UNIQUE,
                        employee_name TEXT NOT NULL,
                        department TEXT NOT NULL,
                        experience_years REAL NOT NULL
                    );
                    INSERT INTO employees
                        (employee_id, employee_code, employee_name, department, experience_years)
                    VALUES (1, 'OLD-1', 'Legacy Employee', 'Engineering', 3);
                    CREATE TABLE performance_periods (
                        period_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'Planned'
                            CHECK(status IN ('Planned', 'Active', 'Completed')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO performance_periods
                        (period_id, title, start_date, end_date, status)
                    VALUES (1, 'Legacy period', '2025-01-01', '2025-12-31', 'Planned');
                    CREATE TABLE performance_areas (
                        area_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT NOT NULL DEFAULT '',
                        weight REAL NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1
                    );
                    INSERT INTO performance_areas (name, description, weight)
                    VALUES ('Attendance', 'Existing criterion', 100);
                    CREATE TABLE assessments (
                        assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id INTEGER NOT NULL,
                        period_id INTEGER,
                        reviewer TEXT NOT NULL,
                        assessment_date TEXT NOT NULL,
                        scores_json TEXT NOT NULL,
                        overall_score REAL NOT NULL CHECK(overall_score BETWEEN 1 AND 5),
                        category TEXT NOT NULL,
                        comments TEXT NOT NULL DEFAULT '',
                        status TEXT NOT NULL DEFAULT 'Completed',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
                        FOREIGN KEY(period_id) REFERENCES performance_periods(period_id)
                    );
                    INSERT INTO assessments
                        (employee_id, period_id, reviewer, assessment_date, scores_json,
                         overall_score, category, comments)
                    VALUES
                        (1, 1, 'Reviewer', '2025-06-30', '{"Attendance": 3.5}',
                         3.5, 'Moderate', 'Legacy review notes');
                    CREATE TABLE notifications (
                        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        notification_type TEXT NOT NULL DEFAULT 'info',
                        is_read INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
            initialize_database.cache_clear()
            migrated_areas = get_areas(legacy_path)
            migrated_periods = get_periods(legacy_path)
            migrated_assessments = get_assessments(legacy_path)
            self.assertEqual(len(migrated_areas), 1)
            self.assertTrue(bool(migrated_areas.iloc[0]["active"]))
            self.assertEqual(migrated_periods.iloc[0]["name"], "Legacy period")
            self.assertEqual(migrated_periods.iloc[0]["status"], "Draft")
            self.assertEqual(float(migrated_assessments.iloc[0]["overall_score"]), 70.0)
            self.assertEqual(
                json.loads(migrated_assessments.iloc[0]["scores_json"])["Attendance"],
                70,
            )
            self.assertEqual(
                migrated_assessments.iloc[0]["comments"], "Legacy review notes"
            )
        finally:
            initialize_database.cache_clear()
            if os.path.exists(legacy_path):
                os.remove(legacy_path)

    def test_demo_review_cycle_seeding_and_clearing(self):
        from services.workpulse_service import seed_demo_review_cycle, clear_demo_assessments
        # Create a sample employee first
        create_employee(
            "WP-DEMO-1", "Jordan Demo", "Engineering", "Developer",
            date.today(), "Active", 3.0, self.db_path
        )
        count = seed_demo_review_cycle(self.db_path)
        self.assertGreater(count, 0)
        assessments = get_assessments(self.db_path)
        self.assertFalse(assessments.empty)
        
        # Now clear
        deleted = clear_demo_assessments(self.db_path)
        self.assertGreater(deleted, 0)
        self.assertTrue(get_assessments(self.db_path).empty)



def _is_missing(value):
    return value is None or str(value) == "nan"


if __name__ == "__main__":
    unittest.main()