"""
WorkPulse Database Adapter
Provides a unified interface that can switch between SQLite and Supabase backends.

Usage:
    # For local/development (SQLite):
    from database.db_adapter import get_db

    # For production (Supabase):
    os.environ['DATABASE_PROVIDER'] = 'supabase'
    from database.db_adapter import get_db
"""

import json
import os
import sqlite3
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Check if we're using Supabase
DATABASE_PROVIDER = os.environ.get("DATABASE_PROVIDER", "sqlite").lower()

# Try to import Supabase client
try:
    if DATABASE_PROVIDER == "supabase":
        from database.supabase_client import (
            get_supabase_client,
            get_all_employees as supabase_get_all_employees,
            get_employees as supabase_get_employees,
            create_employee as supabase_create_employee,
            update_employee_profile as supabase_update_employee_profile,
            delete_employee as supabase_delete_employee,
            get_periods as supabase_get_periods,
            save_period as supabase_save_period,
            delete_period as supabase_delete_period,
            get_areas as supabase_get_areas,
            save_areas as supabase_save_areas,
            get_assessments as supabase_get_assessments,
            save_assessment as supabase_save_assessment,
            get_dashboard_summary as supabase_get_dashboard_summary,
            get_notifications as supabase_get_notifications,
            mark_notifications_read as supabase_mark_notifications_read,
            get_pending_reviews as supabase_get_pending_reviews,
            get_settings as supabase_get_settings,
            save_settings as supabase_save_settings,
            seed_demo_review_cycle as supabase_seed_demo_review_cycle,
            clear_demo_assessments as supabase_clear_demo_assessments,
            get_all_employees_supabase,
            get_employees_with_latest_performance,
            log_prediction_supabase,
            get_predictions_history_supabase,
            compute_kpis_supabase,
            log_model_run as supabase_log_model_run,
            get_model_runs as supabase_get_model_runs,
            get_latest_model as supabase_get_latest_model,
        )
        SUPABASE_AVAILABLE = True
    else:
        SUPABASE_AVAILABLE = False
except ImportError:
    SUPABASE_AVAILABLE = False


class DatabaseAdapter:
    """Unified database adapter that routes to SQLite or Supabase based on configuration."""

    def __init__(self):
        self.provider = DATABASE_PROVIDER
        self._supabase_client = None

    def is_supabase(self) -> bool:
        return self.provider == "supabase" and SUPABASE_AVAILABLE

    # Employee operations
    def get_employees(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_employees()
        from services.workpulse_service import get_employees as sqlite_get_employees
        return sqlite_get_employees()

    def get_all_employees(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_all_employees()
        from database.db_manager import get_all_employees as sqlite_get_all
        return sqlite_get_all()

    def create_employee(self, **kwargs) -> int:
        if self.is_supabase():
            return supabase_create_employee(**kwargs)
        from services.workpulse_service import create_employee as sqlite_create
        return sqlite_create(**kwargs)

    def update_employee_profile(self, employee_id: int, **kwargs) -> None:
        if self.is_supabase():
            return supabase_update_employee_profile(employee_id, **kwargs)
        from services.workpulse_service import update_employee_profile as sqlite_update
        return sqlite_update(employee_id, **kwargs)

    def delete_employee(self, employee_id: int) -> None:
        if self.is_supabase():
            return supabase_delete_employee(employee_id)
        from services.workpulse_service import delete_employee as sqlite_delete
        return sqlite_delete(employee_id)

    # Period operations
    def get_periods(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_periods()
        from services.workpulse_service import get_periods as sqlite_get_periods
        return sqlite_get_periods()

    def save_period(self, **kwargs) -> int:
        if self.is_supabase():
            return supabase_save_period(**kwargs)
        from services.workpulse_service import save_period as sqlite_save_period
        return sqlite_save_period(**kwargs)

    def delete_period(self, period_id: int) -> None:
        if self.is_supabase():
            return supabase_delete_period(period_id)
        from services.workpulse_service import delete_period as sqlite_delete_period
        return sqlite_delete_period(period_id)

    # Area operations
    def get_areas(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_areas()
        from services.workpulse_service import get_areas as sqlite_get_areas
        return sqlite_get_areas()

    def save_areas(self, areas: List[Dict[str, Any]]) -> None:
        if self.is_supabase():
            return supabase_save_areas(areas)
        from services.workpulse_service import save_areas as sqlite_save_areas
        return sqlite_save_areas(areas)

    # Assessment operations
    def get_assessments(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_assessments()
        from services.workpulse_service import get_assessments as sqlite_get_assessments
        return sqlite_get_assessments()

    def save_assessment(self, **kwargs) -> int:
        if self.is_supabase():
            return supabase_save_assessment(**kwargs)
        from services.workpulse_service import save_assessment as sqlite_save_assessment
        return sqlite_save_assessment(**kwargs)

    # Dashboard and analytics
    def get_dashboard_summary(self) -> Dict[str, int]:
        if self.is_supabase():
            return supabase_get_dashboard_summary()
        from services.workpulse_service import get_dashboard_summary as sqlite_get_summary
        return sqlite_get_summary()

    def compute_kpis(self, employees_df: pd.DataFrame = None) -> Dict[str, Any]:
        if self.is_supabase():
            return compute_kpis_supabase(employees_df)
        from services.analytics_service import compute_kpis as sqlite_compute_kpis
        import sqlite3
        from database.db_manager import get_db_connection, resolve_db_path
        db_path = resolve_db_path()
        conn = get_db_connection(db_path)
        try:
            df = employees_df if employees_df is not None else pd.read_sql_query("SELECT * FROM employees", conn)
            return sqlite_compute_kpis(df)
        finally:
            conn.close()

    # Notifications
    def get_notifications(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_notifications()
        from services.workpulse_service import get_notifications as sqlite_get_notifications
        return sqlite_get_notifications()

    def mark_notifications_read(self, notification_ids: List[int] = None) -> None:
        if self.is_supabase():
            return supabase_mark_notifications_read(notification_ids)
        from services.workpulse_service import mark_notifications_read as sqlite_mark
        return sqlite_mark(notification_ids)

    def get_pending_reviews(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_pending_reviews()
        from services.workpulse_service import get_pending_reviews as sqlite_get_pending
        return sqlite_get_pending()

    # Settings
    def get_settings(self) -> Dict[str, str]:
        if self.is_supabase():
            return supabase_get_settings()
        from services.workpulse_service import get_settings as sqlite_get_settings
        return sqlite_get_settings()

    def save_settings(self, values: Dict[str, str]) -> None:
        if self.is_supabase():
            return supabase_save_settings(values)
        from services.workpulse_service import save_settings as sqlite_save_settings
        return sqlite_save_settings(values)

    # Demo data management
    def seed_demo_review_cycle(self) -> int:
        if self.is_supabase():
            return supabase_seed_demo_review_cycle()
        from services.workpulse_service import seed_demo_review_cycle as sqlite_seed
        return sqlite_seed()

    def clear_demo_assessments(self) -> int:
        if self.is_supabase():
            return supabase_clear_demo_assessments()
        from services.workpulse_service import clear_demo_assessments as sqlite_clear
        return sqlite_clear()

    # Prediction logging
    def log_prediction(self, **kwargs) -> int:
        if self.is_supabase():
            return log_prediction_supabase(**kwargs)
        return 0  # No-op for SQLite in this version

    def get_predictions_history(self) -> pd.DataFrame:
        if self.is_supabase():
            return get_predictions_history_supabase()
        return pd.DataFrame()

    # Model runs logging (ML training operations)
    def log_model_run(self, **kwargs) -> int:
        if self.is_supabase():
            return supabase_log_model_run(**kwargs)
        # For SQLite, use db_manager's log_model_run
        from database.db_manager import log_model_run as sqlite_log_model_run
        # Extract required args
        return sqlite_log_model_run(
            model_name=kwargs.get("model_name", "Unknown"),
            model_version=kwargs.get("model_version", "1.0.0"),
            metrics_dict=kwargs.get("metrics_dict", {}),
            status=kwargs.get("status", "Active")
        )

    def get_model_runs(self) -> pd.DataFrame:
        if self.is_supabase():
            return supabase_get_model_runs()
        # For SQLite, query directly
        import sqlite3
        from database.db_manager import get_db_connection, resolve_db_path
        db_path = resolve_db_path()
        conn = get_db_connection(db_path)
        try:
            return pd.read_sql_query("SELECT * FROM model_runs ORDER BY training_date DESC", conn)
        finally:
            conn.close()

    def get_latest_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        if self.is_supabase():
            return supabase_get_latest_model(model_name)
        # For SQLite, query directly
        import sqlite3
        from database.db_manager import get_db_connection, resolve_db_path
        db_path = resolve_db_path()
        conn = get_db_connection(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM model_runs WHERE model_name = ? AND model_status = 'Active' ORDER BY training_date DESC LIMIT 1",
                (model_name,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # Utility methods for backward compatibility
    def get_db_connection(self):
        """For SQLite backend, returns connection object."""
        if self.is_supabase():
            raise NotImplementedError("Supabase doesn't use direct connections")
        from database.db_manager import get_db_connection, resolve_db_path
        return get_db_connection(resolve_db_path())

    def initialize_database(self) -> None:
        """Initialize the database schema."""
        if self.is_supabase():
            # Supabase schema should already be deployed via migrations
            return
        from services.workpulse_service import initialize_database
        import os
        db_path = os.path.join("data", "workpulse.db")
        return initialize_database(db_path)


# Global adapter instance
_adapter: Optional[DatabaseAdapter] = None


def get_db(adapter_class=None) -> DatabaseAdapter:
    """
    Get the database adapter instance.

    Args:
        adapter_class: Optional custom adapter class for testing.

    Returns:
        DatabaseAdapter instance configured for the current environment.
    """
    global _adapter
    if _adapter is None:
        _adapter = adapter_class() if adapter_class else DatabaseAdapter()
    return _adapter


def reset_adapter():
    """Reset the adapter instance (useful for testing)."""
    global _adapter
    _adapter = None


def get_database_provider() -> str:
    """Return the current database provider name."""
    return DATABASE_PROVIDER


def is_supabase_enabled() -> bool:
    """Check if Supabase is configured and available."""
    return DATABASE_PROVIDER == "supabase" and SUPABASE_AVAILABLE


def require_supabase(func):
    """Decorator to ensure function only runs with Supabase provider."""
    def wrapper(*args, **kwargs):
        if not is_supabase_enabled():
            raise RuntimeError(
                f"Supabase is not enabled. Set DATABASE_PROVIDER='supabase' "
                f"and configure SUPABASE_URL/SUPABASE_SERVICE_KEY environment variables."
            )
        return func(*args, **kwargs)
    return wrapper