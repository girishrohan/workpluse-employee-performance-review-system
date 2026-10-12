"""
WorkPulse - Input & Dataset Validation Utilities
Validates user inputs, numerical bounds, required fields, and CSV dataset consistency.
"""

import re
import pandas as pd
import numpy as np

VALID_DEPARTMENTS = [
    'Engineering', 'Sales', 'Marketing', 'Human Resources',
    'Customer Support', 'Finance', 'Operations', 'Product Management'
]

VALID_CATEGORIES = ['Needs Support', 'Moderate', 'High', 'Low', 'Medium']
NORM_CATEGORY_MAP = {
    'low': 'Needs Support',
    'needs support': 'Needs Support',
    'medium': 'Moderate',
    'moderate': 'Moderate',
    'high': 'High'
}


def validate_employee_input(employee_code, employee_name, department, experience_years,
                            attendance_rate, task_completion_rate, training_hours,
                            previous_performance, performance_category=None):
    """
    Validates form fields for employee creation/editing.
    Returns (is_valid: bool, errors: list of str).
    """
    errors = []

    if not str(employee_code).strip():
        errors.append("Employee code cannot be empty.")
    elif not re.match(r'^[A-Za-z0-9\-_]+$', str(employee_code).strip()):
        errors.append("Employee code must contain only letters, numbers, hyphens, and underscores.")

    if not str(employee_name).strip():
        errors.append("Employee name cannot be empty.")

    if department not in VALID_DEPARTMENTS and str(department).strip() == "":
        errors.append("Please specify a valid department.")

    try:
        exp = float(experience_years)
        if exp < 0 or exp > 50:
            errors.append("Experience must be between 0 and 50 years.")
    except (ValueError, TypeError):
        errors.append("Experience must be a valid numerical value.")

    try:
        att = float(attendance_rate)
        if att < 0.0 or att > 100.0:
            errors.append("Attendance rate must be between 0.0% and 100.0%.")
    except (ValueError, TypeError):
        errors.append("Attendance rate must be a valid numerical percentage.")

    try:
        tc = float(task_completion_rate)
        if tc < 0.0 or tc > 100.0:
            errors.append("Task completion rate must be between 0.0% and 100.0%.")
    except (ValueError, TypeError):
        errors.append("Task completion rate must be a valid numerical percentage.")

    try:
        th = float(training_hours)
        if th < 0.0:
            errors.append("Training hours cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Training hours must be a valid numerical value.")

    try:
        prev = float(previous_performance)
        if prev < 1.0 or prev > 5.0:
            errors.append("Previous performance rating must be between 1.0 and 5.0.")
    except (ValueError, TypeError):
        errors.append("Previous performance must be a valid rating (1.0 to 5.0).")

    if performance_category:
        clean_cat = str(performance_category).strip().lower()
        if clean_cat not in NORM_CATEGORY_MAP:
            errors.append(f"Performance category must be one of: Needs Support, Moderate, High.")

    return len(errors) == 0, errors


def validate_csv_dataset(df):
    """
    Validates an uploaded CSV dataset.
    Returns:
    - is_valid (bool)
    - cleaned_df (pd.DataFrame or None)
    - issues (list of str)
    - stats (dict)
    """
    issues = []
    stats = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_values': int(df.isnull().sum().sum()),
        'duplicate_codes': 0,
        'valid_rows': 0
    }

    # Normalize column names (strip whitespace and lowercase)
    col_mapping = {}
    for col in df.columns:
        norm_col = str(col).strip().lower().replace(' ', '_')
        col_mapping[col] = norm_col

    df_norm = df.rename(columns=col_mapping)

    # Check for legacy employee_id mapping
    if 'employee_id' in df_norm.columns and 'employee_code' not in df_norm.columns:
        df_norm['employee_code'] = df_norm['employee_id']

    # Required columns
    required_cols = ['employee_code', 'department', 'attendance_rate', 'task_completion_rate', 'performance_category']
    missing_cols = [c for c in required_cols if c not in df_norm.columns]

    if missing_cols:
        issues.append(f"Missing mandatory column(s): {', '.join(missing_cols)}")
        return False, None, issues, stats

    # Duplicate employee_code check within the uploaded CSV
    duplicate_mask = df_norm['employee_code'].duplicated()
    dup_count = int(duplicate_mask.sum())
    stats['duplicate_codes'] = dup_count
    if dup_count > 0:
        issues.append(f"Found {dup_count} duplicate employee code(s) within the file. Duplicates will be consolidated.")
        df_norm = df_norm.drop_duplicates(subset=['employee_code'], keep='first')

    # Drop rows missing crucial identifiers
    before_len = len(df_norm)
    df_norm = df_norm.dropna(subset=['employee_code', 'performance_category'])
    dropped_nulls = before_len - len(df_norm)
    if dropped_nulls > 0:
        issues.append(f"Dropped {dropped_nulls} row(s) missing mandatory employee_code or performance_category.")

    # Fill defaults for optional fields
    if 'employee_name' not in df_norm.columns:
        df_norm['employee_name'] = df_norm['employee_code'].apply(lambda x: f"Employee {x}")
    else:
        df_norm['employee_name'] = df_norm['employee_name'].fillna(df_norm['employee_code'].apply(lambda x: f"Employee {x}"))

    if 'experience_years' not in df_norm.columns:
        df_norm['experience_years'] = 2.0
    else:
        df_norm['experience_years'] = pd.to_numeric(df_norm['experience_years'], errors='coerce').fillna(2.0)

    if 'training_hours' not in df_norm.columns:
        df_norm['training_hours'] = 15.0
    else:
        df_norm['training_hours'] = pd.to_numeric(df_norm['training_hours'], errors='coerce').fillna(15.0)

    if 'previous_performance' not in df_norm.columns:
        df_norm['previous_performance'] = 3.5
    else:
        df_norm['previous_performance'] = pd.to_numeric(df_norm['previous_performance'], errors='coerce').fillna(3.5)

    if 'review_date' not in df_norm.columns:
        df_norm['review_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    else:
        df_norm['review_date'] = df_norm['review_date'].fillna(pd.Timestamp.now().strftime('%Y-%m-%d'))

    # Coerce numerical bounds
    df_norm['attendance_rate'] = pd.to_numeric(df_norm['attendance_rate'], errors='coerce')
    df_norm['task_completion_rate'] = pd.to_numeric(df_norm['task_completion_rate'], errors='coerce')
    
    # Drop rows where critical rates could not be parsed
    df_norm = df_norm.dropna(subset=['attendance_rate', 'task_completion_rate'])
    df_norm['attendance_rate'] = np.clip(df_norm['attendance_rate'], 0.0, 100.0).round(1)
    df_norm['task_completion_rate'] = np.clip(df_norm['task_completion_rate'], 0.0, 100.0).round(1)
    df_norm['training_hours'] = np.maximum(df_norm['training_hours'], 0.0).round(1)
    df_norm['experience_years'] = np.maximum(df_norm['experience_years'], 0.0).round(1)
    df_norm['previous_performance'] = np.clip(df_norm['previous_performance'], 1.0, 5.0).round(1)

    # Standardize category labels
    def map_category(val):
        key = str(val).strip().lower()
        return NORM_CATEGORY_MAP.get(key, 'Moderate')

    df_norm['performance_category'] = df_norm['performance_category'].apply(map_category)

    stats['valid_rows'] = len(df_norm)
    is_valid = len(df_norm) > 0

    return is_valid, df_norm, issues, stats
