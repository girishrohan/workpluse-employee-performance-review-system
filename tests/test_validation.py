"""
WorkPulse - Automated Validation Unit Tests
Verifies input parameter checks, bounds enforcement, and CSV dataset schema validation.
"""

import unittest
import pandas as pd
from utils.validation import validate_employee_input, validate_csv_dataset


class TestValidationUtils(unittest.TestCase):

    def test_valid_employee_input(self):
        """Verifies valid input passes validation."""
        is_valid, errors = validate_employee_input(
            employee_code="WP-101",
            employee_name="John Doe",
            department="Engineering",
            experience_years=4.5,
            attendance_rate=92.0,
            task_completion_rate=88.0,
            training_hours=30.0,
            previous_performance=4.0,
            performance_category="High"
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_invalid_ranges(self):
        """Verifies out-of-range inputs are caught with errors."""
        is_valid, errors = validate_employee_input(
            employee_code="WP-ERR",
            employee_name="Bad Input",
            department="Engineering",
            experience_years=-2.0,  # Negative
            attendance_rate=150.0,  # Exceeds 100%
            task_completion_rate=-10.0,  # Negative
            training_hours=-5.0,  # Negative
            previous_performance=7.5  # Exceeds 5.0
        )
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(errors), 4)

    def test_empty_identifiers(self):
        """Verifies empty name or code is rejected."""
        is_valid, errors = validate_employee_input(
            employee_code="",
            employee_name="",
            department="Engineering",
            experience_years=2.0,
            attendance_rate=80.0,
            task_completion_rate=80.0,
            training_hours=10.0,
            previous_performance=3.0
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("code" in e.lower() for e in errors))
        self.assertTrue(any("name" in e.lower() for e in errors))

    def test_csv_validation_success(self):
        """Verifies valid CSV dataframe passes and cleans records."""
        sample_data = {
            'employee_code': ['WP-01', 'WP-02'],
            'department': ['Sales', 'Engineering'],
            'attendance_rate': [90.0, 85.0],
            'task_completion_rate': [88.0, 80.0],
            'performance_category': ['High', 'Moderate']
        }
        df = pd.DataFrame(sample_data)
        is_valid, clean_df, issues, stats = validate_csv_dataset(df)
        self.assertTrue(is_valid)
        self.assertEqual(stats['valid_rows'], 2)
        self.assertIn('employee_name', clean_df.columns)

    def test_csv_validation_missing_columns(self):
        """Verifies CSV missing required columns is rejected."""
        broken_data = {
            'department': ['Sales'],
            'attendance_rate': [90.0]
        }
        df = pd.DataFrame(broken_data)
        is_valid, clean_df, issues, stats = validate_csv_dataset(df)
        self.assertFalse(is_valid)
        self.assertTrue(any("missing mandatory" in i.lower() for i in issues))


if __name__ == '__main__':
    unittest.main()
