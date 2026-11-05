"""
WorkPulse - Supabase Database Client
Provides unified database access with Supabase PostgreSQL backend.
"""

import os
import json
from typing import Any, Dict, List, Optional

import pandas as pd
from supabase import create_client, Client

# Global client instance
_supabase_client: Optional[Client] = None

# Environment variable names
SUPABASE_URL_KEY = "SUPABASE_URL"
SUPABASE_KEY_KEY = "SUPABASE_SERVICE_KEY"
SUPABASE_ANON_KEY_KEY = "SUPABASE_ANON_KEY"


def get_supabase_url() -> str:
    """Get Supabase URL from environment."""
    url = os.environ.get(SUPABASE_URL_KEY, "")
    if not url:
        raise ValueError(f"SUPABASE_URL is not configured. Set the {SUPABASE_URL_KEY} environment variable.")
    return url.rstrip("/")


def get_supabase_service_key() -> str:
    """Get Supabase service key from environment."""
    key = os.environ.get(SUPABASE_KEY_KEY, "")
    if not key:
        raise ValueError(f"SUPABASE_SERVICE_KEY is not configured. Set the {SUPABASE_KEY_KEY} environment variable.")
    return key


def get_supabase_anon_key() -> str:
    """Get Supabase anon key from environment."""
    key = os.environ.get(SUPABASE_ANON_KEY_KEY, "")
    if not key:
        raise ValueError(f"SUPABASE_ANON_KEY is not configured. Set the {SUPABASE_ANON_KEY_KEY} environment variable.")
    return key


def get_supabase_client(use_service_key: bool = False) -> Client:
    """
    Get or create a Supabase client instance.

    Args:
        use_service_key: If True, use service key (for admin operations).
                        If False, use anon key (for client-side operations).

    Returns:
        Supabase Client instance
    """
    global _supabase_client

    url = get_supabase_url()

    if use_service_key:
        key = get_supabase_service_key()
    else:
        key = get_supabase_anon_key()

    if _supabase_client is None:
        _supabase_client = create_client(url, key)

    return _supabase_client


def reset_client():
    """Reset the client instance (useful for testing)."""
    global _supabase_client
    _supabase_client = None


# -----------------------------------------------------------------------------
# Employee Operations
# -----------------------------------------------------------------------------

def get_all_employees_supabase() -> pd.DataFrame:
    """Fetch all employees from Supabase."""
    client = get_supabase_client(use_service_key=True)
    response = client.table('employees').select('*').order('employee_id', desc=False).execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)

    # Get latest performance records
    if 'employee_id' in df.columns and not df.empty:
        # Subquery for latest performance record per employee
        perf_df = get_employees_with_latest_performance()
        if not perf_df.empty:
            perf_cols = ['employee_id', 'attendance_rate', 'task_completion_rate',
                        'training_hours', 'previous_performance', 'performance_category', 'review_date']
            perf_cols_exist = [c for c in perf_cols if c in perf_df.columns]
            if perf_cols_exist:
                df = df.merge(
                    perf_df[['employee_id'] + perf_cols_exist],
                    on='employee_id',
                    how='left',
                    suffixes=('', '_perf')
                )
                # Handle column name conflicts
                for col in perf_cols_exist:
                    if col != 'employee_id' and f'{col}_perf' in df.columns:
                        df[col] = df[f'{col}_perf']
                        df = df.drop(columns=[f'{col}_perf'])

    return df


def get_employees_with_latest_performance() -> pd.DataFrame:
    """Fetch employees with their latest performance records."""
    client = get_supabase_client(use_service_key=True)

    # Get all performance records ordered by employee and review date
    response = client.table('performance_records').select('*').order('employee_id').order('review_date', desc=True).execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)

    # Get latest record per employee
    latest = df.drop_duplicates(subset=['employee_id'], keep='first')

    return latest


def create_employee_supabase(
    employee_code: str,
    employee_name: str,
    department: str,
    designation: str = "Staff Member",
    joining_date: str = None,
    status: str = "Active",
    experience_years: float = 0.0,
    attendance_rate: float = 85.0,
    task_completion_rate: float = 80.0,
    training_hours: float = 20.0,
    previous_performance: float = 3.0,
    performance_category: str = "Moderate",
    review_date: str = None
) -> int:
    """Create a new employee with initial performance record."""
    from datetime import date

    if joining_date is None:
        joining_date = date.today().isoformat()
    if review_date is None:
        review_date = date.today().isoformat()

    client = get_supabase_client(use_service_key=True)

    # Insert employee
    employee_data = {
        'employee_code': employee_code.strip(),
        'employee_name': employee_name.strip(),
        'department': department.strip(),
        'designation': designation.strip(),
        'joining_date': joining_date,
        'status': status,
        'experience_years': float(experience_years),
        'data_origin': 'user'
    }

    response = client.table('employees').insert(employee_data).execute()

    if not response.data:
        raise ValueError("Failed to create employee")

    employee_id = response.data[0]['employee_id']

    # Insert initial performance record
    perf_data = {
        'employee_id': employee_id,
        'attendance_rate': float(attendance_rate),
        'task_completion_rate': float(task_completion_rate),
        'training_hours': float(training_hours),
        'previous_performance': float(previous_performance),
        'performance_category': performance_category,
        'review_date': review_date
    }

    client.table('performance_records').insert(perf_data).execute()

    return employee_id


def update_employee_profile_supabase(
    employee_id: int,
    employee_name: str,
    department: str,
    designation: str,
    joining_date: str,
    status: str,
    experience_years: float,
    attendance_rate: float = 85.0,
    task_completion_rate: float = 80.0,
    training_hours: float = 20.0,
    previous_performance: float = 3.0,
    performance_category: str = "Moderate",
    review_date: str = None
) -> None:
    """Update employee profile and latest performance record."""
    if review_date is None:
        from datetime import date
        review_date = date.today().isoformat()

    client = get_supabase_client(use_service_key=True)

    # Update employee
    employee_data = {
        'employee_name': employee_name.strip(),
        'department': department.strip(),
        'designation': designation.strip(),
        'joining_date': joining_date.strip(),
        'status': status,
        'experience_years': float(experience_years)
    }

    response = client.table('employees').update(employee_data).eq('employee_id', employee_id).execute()

    if not response.data:
        raise ValueError("Employee not found")

    # Insert new performance record (keep history)
    perf_data = {
        'employee_id': employee_id,
        'attendance_rate': float(attendance_rate),
        'task_completion_rate': float(task_completion_rate),
        'training_hours': float(training_hours),
        'previous_performance': float(previous_performance),
        'performance_category': performance_category,
        'review_date': review_date
    }

    client.table('performance_records').insert(perf_data).execute()


def delete_employee_supabase(employee_id: int) -> None:
    """Delete an employee (cascades to performance_records due to FK)."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('employees').delete().eq('employee_id', employee_id).execute()

    if not response.data:
        raise ValueError("Employee not found or already deleted")


# -----------------------------------------------------------------------------
# Review Cycles / Periods
# -----------------------------------------------------------------------------

def get_periods_supabase() -> pd.DataFrame:
    """Fetch all performance review periods."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('performance_periods').select('*').order('start_date', desc=True).execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)

    # Add assessment count
    counts_response = client.table('assessments').select('period_id, count').execute()

    if counts_response.data:
        counts_df = pd.DataFrame(counts_response.data)
        # Group by period_id and count
        assessments_by_period = counts_df.groupby('period_id').size().reset_index(name='assessment_count')
        df = df.merge(assessments_by_period, left_on='period_id', right_on='period_id', how='left')
        df['assessment_count'] = df['assessment_count'].fillna(0)

    return df


def save_period_supabase(
    name: str,
    start_date: str,
    end_date: str,
    status: str = "Draft",
    period_id: int = None
) -> int:
    """Create or update a review period."""
    client = get_supabase_client(use_service_key=True)

    period_data = {
        'name': name.strip(),
        'start_date': start_date.strip(),
        'end_date': end_date.strip(),
        'status': status
    }

    if period_id is None:
        response = client.table('performance_periods').insert(period_data).execute()
    else:
        response = client.table('performance_periods').update(period_data).eq('period_id', period_id).execute()

    if not response.data:
        raise ValueError("Failed to save period")

    return response.data[0]['period_id']


def delete_period_supabase(period_id: int) -> None:
    """Delete a review period (restricts if has assessments)."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('performance_periods').delete().eq('period_id', period_id).execute()

    if not response.data:
        raise ValueError("Period not found or cannot be deleted (has assessments)")


# -----------------------------------------------------------------------------
# Performance Areas / KPI Framework
# -----------------------------------------------------------------------------

def get_areas_supabase() -> pd.DataFrame:
    """Fetch performance areas."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('performance_areas').select('*').order('area_id').execute()

    if not response.data:
        return pd.DataFrame()

    return pd.DataFrame(response.data)


def save_areas_supabase(areas: List[Dict[str, Any]]) -> None:
    """Save performance areas (clears and re-inserts for simplicity)."""
    client = get_supabase_client(use_service_key=True)

    # Delete existing
    client.table('performance_areas').delete().neq('area_id', 0).execute()

    # Insert new
    for area in areas:
        client.table('performance_areas').insert({
            'name': area.get('name').strip() if area.get('name') else '',
            'description': area.get('description', '').strip(),
            'weight': float(area.get('weight', 0)),
            'active': 1 if area.get('active', True) else 0
        }).execute()


# -----------------------------------------------------------------------------
# Assessments
# -----------------------------------------------------------------------------

def get_assessments_supabase() -> pd.DataFrame:
    """Fetch all assessments with employee and period info."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('assessments').select('*, employees!inner(*), performance_periods!inner(*)').execute()

    if not response.data:
        return pd.DataFrame()

    # Flatten nested data
    records = []
    for row in response.data:
        record = {
            'assessment_id': row['assessment_id'],
            'assessment_date': row['assessment_date'],
            'reviewer': row['reviewer'],
            'scores_json': row['scores_json'],
            'overall_score': row['overall_score'],
            'category': row['category'],
            'comments': row['comments'],
            'status': row['status'],
            'employee_id': row['employees']['employee_id'] if row.get('employees') else None,
            'employee_code': row['employees']['employee_code'] if row.get('employees') else None,
            'employee_name': row['employees']['employee_name'] if row.get('employees') else None,
            'department': row['employees']['department'] if row.get('employees') else None,
            'period_id': row['performance_periods']['period_id'] if row.get('performance_periods') else None,
            'period_name': row['performance_periods']['name'] if row.get('performance_periods') else None,
        }
        records.append(record)

    df = pd.DataFrame(records)

    if not df.empty and 'assessment_date' in df.columns:
        df = df.sort_values('assessment_date', ascending=False)

    return df


def save_assessment_supabase(
    employee_id: int,
    period_id: int,
    assessment_date: str,
    reviewer: str,
    scores: Dict[str, float],
    comments: str = ''
) -> int:
    """Record a new assessment."""
    client = get_supabase_client(use_service_key=True)

    # Calculate weighted overall score based on performance areas
    areas_response = client.table('performance_areas').select('name, weight').eq('active', 1).execute()

    if not areas_response.data:
        raise ValueError("No active performance areas configured")

    areas = areas_response.data
    weighted_total = sum(float(scores.get(a['name'], 0)) * float(a['weight']) / 100.0 for a in areas)

    # Determine category
    if weighted_total < 60:
        category = "Needs Support"
    elif weighted_total < 80:
        category = "Moderate"
    else:
        category = "High"

    assessment_data = {
        'employee_id': int(employee_id),
        'period_id': int(period_id),
        'assessment_date': assessment_date,
        'reviewer': reviewer.strip(),
        'scores_json': json.dumps(scores, sort_keys=True),
        'overall_score': round(weighted_total, 2),
        'category': category,
        'comments': comments.strip(),
        'status': 'Completed'
    }

    response = client.table('assessments').insert(assessment_data).execute()

    if not response.data:
        raise ValueError("Failed to save assessment")

    return response.data[0]['assessment_id']


# -----------------------------------------------------------------------------
# Analytics & Dashboard Summary
# -----------------------------------------------------------------------------

def get_dashboard_summary_supabase() -> Dict[str, int]:
    """Get dashboard summary statistics."""
    client = get_supabase_client(use_service_key=True)

    employee_count = len(client.table('employees').select('employee_id', count='exact').execute().data or [])
    period_count = len(client.table('performance_periods').select('period_id', count='exact').eq('status', 'Active').execute().data or [])
    assessment_count = len(client.table('assessments').select('assessment_id', count='exact').execute().data or [])

    return {
        'total_employees': int(employee_count),
        'active_periods': int(period_count),
        'completed_assessments': int(assessment_count),
        'performance_areas': 0,
        'demo_employees': 0,
        'unread_notifications': 0
    }


def compute_kpis_supabase(employees_df: pd.DataFrame = None) -> Dict[str, Any]:
    """Compute workforce KPIs."""
    client = get_supabase_client(use_service_key=True)

    if employees_df is None or employees_df.empty:
        employees_df = get_all_employees_supabase()

    if employees_df.empty:
        return {'workforce_mean_score': 0.0, 'avg_attendance': 0.0, 'avg_task_completion': 0.0}

    kpis = {
        'total_employees': len(employees_df),
        'avg_attendance': float(employees_df['attendance_rate'].mean()) if 'attendance_rate' in employees_df.columns else 0.0,
        'avg_task_completion': float(employees_df['task_completion_rate'].mean()) if 'task_completion_rate' in employees_df.columns else 0.0,
        'avg_training_hours': float(employees_df['training_hours'].mean()) if 'training_hours' in employees_df.columns else 0.0,
        'avg_experience': float(employees_df['experience_years'].mean()) if 'experience_years' in employees_df.columns else 0.0,
    }

    # Calculate workforce mean score from assessments
    assessments_df = get_assessments_supabase()
    if not assessments_df.empty:
        kpis['workforce_mean_score'] = float(assessments_df['overall_score'].mean())
        score_dist = assessments_df['overall_score'].value_counts()
        kpis['high_performers'] = int((score_dist >= 80).sum())
        kpis['moderate_performers'] = int(((score_dist >= 60) & (score_dist < 80)).sum())
        kpis['needs_support'] = int((score_dist < 60).sum())

    return kpis


# -----------------------------------------------------------------------------
# Model Runs Logging (for training metadata)
# -----------------------------------------------------------------------------

def log_model_run(
    model_name: str,
    model_version: str,
    metrics_dict: dict,
    status: str = "Active"
) -> int:
    """
    Log a model training run to the database.

    Args:
        model_name: Name of the model (e.g., "Random Forest", "Decision Tree")
        model_version: Version string
        metrics_dict: Dictionary of evaluation metrics
        status: Model status (Active, Deprecated, Archived)

    Returns:
        The model_id of the inserted record
    """
    client = get_supabase_client(use_service_key=True)

    model_data = {
        'model_name': model_name,
        'model_version': model_version,
        'evaluation_metrics': json.dumps(metrics_dict),
        'model_status': status
    }

    response = client.table('model_runs').insert(model_data).execute()

    if not response.data:
        raise ValueError("Failed to log model run")

    return response.data[0]['model_id']


def get_model_runs() -> pd.DataFrame:
    """Fetch all model runs ordered by training date."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('model_runs').select('*').order('training_date', desc=True).execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)
    return df


def get_latest_model(model_name: str) -> Optional[Dict[str, Any]]:
    """Get the latest active model of a given type."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('model_runs').select('*').eq('model_name', model_name).eq('model_status', 'Active').order('training_date', desc=True).limit(1).execute()

    if response.data:
        return response.data[0]
    return None


# -----------------------------------------------------------------------------
# Prediction Logging
# -----------------------------------------------------------------------------

def log_prediction_supabase(
    predicted_category: str,
    feature_snapshot: Dict[str, Any],
    explanation_summary: str,
    model_id: int = 1,
    employee_id: int = None
) -> int:
    """Log a prediction to the database."""
    client = get_supabase_client(use_service_key=True)

    prediction_data = {
        'employee_id': employee_id,
        'model_id': model_id,
        'predicted_category': predicted_category,
        'feature_snapshot': json.dumps(feature_snapshot),
        'explanation_summary': explanation_summary
    }

    response = client.table('predictions').insert(prediction_data).execute()

    if not response.data:
        raise ValueError("Failed to log prediction")

    return response.data[0]['prediction_id']


def get_predictions_history_supabase() -> pd.DataFrame:
    """Get prediction history."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('predictions').select('*, employees!left(employee_code, employee_name)').order('prediction_timestamp', desc=True).execute()

    if not response.data:
        return pd.DataFrame()

    records = []
    for row in response.data:
        record = {
            'prediction_id': row['prediction_id'],
            'predicted_category': row['predicted_category'],
            'prediction_timestamp': row['prediction_timestamp'],
            'employee_code': row['employees']['employee_code'] if row.get('employees') else None,
            'employee_name': row['employees']['employee_name'] if row.get('employees') else None,
            'explanation_summary': row['explanation_summary'],
            'feature_snapshot': row['feature_snapshot']
        }
        records.append(record)

    return pd.DataFrame(records)


# -----------------------------------------------------------------------------
# Notifications
# -----------------------------------------------------------------------------

def get_notifications_supabase() -> pd.DataFrame:
    """Get all notifications."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('notifications').select('*').order('created_at', desc=True).execute()

    if not response.data:
        return pd.DataFrame()

    return pd.DataFrame(response.data)


def mark_notifications_read_supabase(notification_ids: List[int] = None) -> int:
    """Mark notifications as read."""
    client = get_supabase_client(use_service_key=True)

    if notification_ids:
        for nid in notification_ids:
            client.table('notifications').update({'read_at': 'NOW()'}).eq('notification_id', nid).execute()
    else:
        client.table('notifications').update({'read_at': 'NOW()'}).isnull('read_at').execute()

    # Count updated
    count_response = client.table('notifications').select('notification_id').eq('read_at', None).execute()
    return len(count_response.data) if count_response.data else 0


def get_pending_reviews_supabase() -> pd.DataFrame:
    """Get employees with pending reviews in active periods."""
    client = get_supabase_client(use_service_key=True)

    # Get active periods
    periods_response = client.table('performance_periods').select('period_id').eq('status', 'Active').execute()

    if not periods_response.data:
        return pd.DataFrame()

    active_period_ids = [p['period_id'] for p in periods_response.data]

    # Get employees without assessments in active periods
    pending = []
    for emp_id in get_all_employees_supabase()['employee_id'].dropna().astype(int).tolist():
        for period_id in active_period_ids:
            check_response = client.table('assessments').select('assessment_id').eq('employee_id', emp_id).eq('period_id', period_id).execute()
            if not check_response.data:
                # Get employee details
                emp_response = client.table('employees').select('*').eq('employee_id', emp_id).execute()
                if emp_response.data:
                    emp = emp_response.data[0]
                    period_info = {
                        'employee_id': emp_id,
                        'employee_code': emp.get('employee_code'),
                        'employee_name': emp.get('employee_name'),
                        'department': emp.get('department'),
                        'period_id': period_id,
                        'end_date': None  # Would need to get from periods table
                    }
                    # Get end_date from periods
                    for p in periods_response.data:
                        if p['period_id'] == period_id:
                            period_info['end_date'] = p.get('end_date')
                            period_info['period_name'] = p.get('name')
                    pending.append(period_info)

    if pending:
        return pd.DataFrame(pending)
    return pd.DataFrame()


# -----------------------------------------------------------------------------
# Settings
# -----------------------------------------------------------------------------

def get_settings_supabase() -> Dict[str, str]:
    """Get application settings."""
    client = get_supabase_client(use_service_key=True)

    response = client.table('app_settings').select('setting_key, setting_value').execute()

    if not response.data:
        return {}

    return {row['setting_key']: row['setting_value'] for row in response.data}


def save_settings_supabase(values: Dict[str, str]) -> None:
    """Save application settings."""
    client = get_supabase_client(use_service_key=True)

    for key, value in values.items():
        client.table('app_settings').upsert({'setting_key': key, 'setting_value': value}, on_conflict='setting_key').execute()


# -----------------------------------------------------------------------------
# Utility for backward compatibility with SQLite-based code
# -----------------------------------------------------------------------------

class SupabaseDB:
    """Database abstraction layer that provides SQLite-like API using Supabase."""

    @staticmethod
    def get_all_employees():
        return get_all_employees_supabase()

    @staticmethod
    def get_employees():
        return get_all_employees_supabase()

    @staticmethod
    def create_employee(**kwargs):
        return create_employee_supabase(**kwargs)

    @staticmethod
    def update_employee_profile(**kwargs):
        return update_employee_profile_supabase(**kwargs)

    @staticmethod
    def delete_employee(employee_id):
        return delete_employee_supabase(employee_id)

    @staticmethod
    def get_periods():
        return get_periods_supabase()

    @staticmethod
    def save_period(**kwargs):
        return save_period_supabase(**kwargs)

    @staticmethod
    def delete_period(period_id):
        return delete_period_supabase(period_id)

    @staticmethod
    def get_areas():
        return get_areas_supabase()

    @staticmethod
    def save_areas(areas):
        return save_areas_supabase(areas)

    @staticmethod
    def get_assessments():
        return get_assessments_supabase()

    @staticmethod
    def save_assessment(**kwargs):
        return save_assessment_supabase(**kwargs)

    @staticmethod
    def get_dashboard_summary():
        return get_dashboard_summary_supabase()

    @staticmethod
    def get_notifications():
        return get_notifications_supabase()

    @staticmethod
    def mark_notifications_read(notification_ids=None):
        return mark_notifications_read_supabase(notification_ids)

    @staticmethod
    def get_pending_reviews():
        return get_pending_reviews_supabase()

    @staticmethod
    def get_settings():
        return get_settings_supabase()

    @staticmethod
    def save_settings(values):
        return save_settings_supabase(values)

    @staticmethod
    def log_prediction(**kwargs):
        return log_prediction_supabase(**kwargs)

    @staticmethod
    def get_predictions_history():
        return get_predictions_history_supabase()

    @staticmethod
    def compute_kpis(employees_df=None):
        return compute_kpis_supabase(employees_df)