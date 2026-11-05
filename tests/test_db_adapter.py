"""
Tests for the Database Adapter module.
Verifies that both SQLite and Supabase (mock) backends work correctly.
"""

import os
import unittest
from unittest.mock import MagicMock, patch


class TestDatabaseAdapter(unittest.TestCase):
    """Test the database adapter functionality."""

    def setUp(self):
        """Set up test environment."""
        # Ensure we're using SQLite for these tests
        os.environ['DATABASE_PROVIDER'] = 'sqlite'

    def tearDown(self):
        """Clean up after tests."""
        from database.db_adapter import reset_adapter
        reset_adapter()

    def test_get_database_provider(self):
        """Test that database provider is returned correctly."""
        from database.db_adapter import get_database_provider

        provider = get_database_provider()
        self.assertEqual(provider, 'sqlite')

    def test_get_db_returns_adapter(self):
        """Test that get_db returns a DatabaseAdapter instance."""
        from database.db_adapter import get_db, DatabaseAdapter

        adapter = get_db()
        self.assertIsInstance(adapter, DatabaseAdapter)

    def test_is_supabase_disabled_by_default(self):
        """Test that Supabase is disabled by default."""
        from database.db_adapter import is_supabase_enabled

        self.assertFalse(is_supabase_enabled())

    def test_adapter_is_supabase_false(self):
        """Test that adapter correctly reports not using Supabase."""
        from database.db_adapter import get_db

        adapter = get_db()
        self.assertFalse(adapter.is_supabase())

    @patch.dict(os.environ, {'DATABASE_PROVIDER': 'supabase'})
    def test_supabase_provider_detection(self):
        """Test that Supabase provider is detected when set."""
        # Need to reload the module to pick up new env var
        import importlib
        import database.db_adapter as db_adapter_module
        importlib.reload(db_adapter_module)

        provider = db_adapter_module.get_database_provider()
        self.assertEqual(provider, 'supabase')


class TestDatabaseAdapterSQLiteOperations(unittest.TestCase):
    """Test SQLite operations via the adapter."""

    def setUp(self):
        """Set up test environment."""
        os.environ['DATABASE_PROVIDER'] = 'sqlite'
        from database.db_adapter import get_db, reset_adapter
        reset_adapter()
        self.adapter = get_db()

    def tearDown(self):
        """Clean up after tests."""
        from database.db_adapter import reset_adapter
        reset_adapter()

    def test_get_employees_returns_dataframe(self):
        """Test that get_employees returns a pandas DataFrame."""
        import pandas as pd

        result = self.adapter.get_employees()
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_periods_returns_dataframe(self):
        """Test that get_periods returns a pandas DataFrame."""
        import pandas as pd

        result = self.adapter.get_periods()
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_areas_returns_dataframe(self):
        """Test that get_areas returns a pandas DataFrame."""
        import pandas as pd

        result = self.adapter.get_areas()
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_assessments_returns_dataframe(self):
        """Test that get_assessments returns a pandas DataFrame."""
        import pandas as pd

        result = self.adapter.get_assessments()
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_dashboard_summary_returns_dict(self):
        """Test that get_dashboard_summary returns a dictionary."""
        result = self.adapter.get_dashboard_summary()
        self.assertIsInstance(result, dict)
        self.assertIn('total_employees', result)

    def test_get_notifications_returns_dataframe(self):
        """Test that get_notifications returns a pandas DataFrame."""
        import pandas as pd

        result = self.adapter.get_notifications()
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_pending_reviews_returns_dataframe(self):
        """Test that get_pending_reviews returns a pandas DataFrame."""
        import pandas as pd

        result = self.adapter.get_pending_reviews()
        self.assertIsInstance(result, pd.DataFrame)

    def test_get_settings_returns_dict(self):
        """Test that get_settings returns a dictionary."""
        result = self.adapter.get_settings()
        self.assertIsInstance(result, dict)


class TestDatabaseAdapterLogging(unittest.TestCase):
    """Test logging operations."""

    def setUp(self):
        """Set up test environment."""
        os.environ['DATABASE_PROVIDER'] = 'sqlite'
        from database.db_adapter import get_db, reset_adapter
        reset_adapter()
        self.adapter = get_db()

    def tearDown(self):
        """Clean up after tests."""
        from database.db_adapter import reset_adapter
        reset_adapter()

    def test_log_prediction_returns_int(self):
        """Test that log_prediction returns an integer (or 0 for SQLite)."""
        result = self.adapter.log_prediction(
            predicted_category="Moderate",
            feature_snapshot={"test": 0.5},
            explanation_summary="Test explanation",
            model_id=1,
            employee_id=1
        )
        self.assertIsInstance(result, int)

    def test_get_predictions_history_returns_dataframe(self):
        """Test that get_predictions_history returns a DataFrame."""
        import pandas as pd

        result = self.adapter.get_predictions_history()
        self.assertIsInstance(result, pd.DataFrame)

    def test_log_model_run_returns_int(self):
        """Test that log_model_run returns an integer."""
        result = self.adapter.log_model_run(
            model_name="Test Model",
            model_version="1.0.0",
            metrics_dict={"accuracy": 0.85},
            status="Active"
        )
        self.assertIsInstance(result, int)

    def test_get_model_runs_returns_dataframe(self):
        """Test that get_model_runs returns a DataFrame."""
        import pandas as pd

        result = self.adapter.get_model_runs()
        self.assertIsInstance(result, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()