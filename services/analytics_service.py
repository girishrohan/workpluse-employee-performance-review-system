"""
WorkPulse - Analytics Service
Calculates real KPIs, departmental statistics, correlations, and time-series trends.
Never hardcodes dashboard values.
"""

import pandas as pd
import numpy as np


def compute_kpis(df):
    """Computes headline KPIs from real loaded employee records."""
    if df is None or len(df) == 0:
        return {
            'total_employees': 0,
            'avg_attendance': 0.0,
            'avg_task_completion': 0.0,
            'avg_performance_score': 0.0,
            'high_count': 0,
            'moderate_count': 0,
            'needs_support_count': 0,
            'high_pct': 0.0,
            'moderate_pct': 0.0,
            'needs_support_pct': 0.0
        }

    total = len(df)
    avg_att = float(df['attendance_rate'].mean()) if 'attendance_rate' in df.columns else 0.0
    avg_tc = float(df['task_completion_rate'].mean()) if 'task_completion_rate' in df.columns else 0.0
    avg_score = float(df['previous_performance'].mean()) if 'previous_performance' in df.columns else 0.0

    cat_counts = df['performance_category'].value_counts() if 'performance_category' in df.columns else pd.Series()
    high_c = int(cat_counts.get('High', 0))
    mod_c = int(cat_counts.get('Moderate', 0))
    supp_c = int(cat_counts.get('Needs Support', 0))

    return {
        'total_employees': total,
        'avg_attendance': round(avg_att, 1),
        'avg_task_completion': round(avg_tc, 1),
        'avg_performance_score': round(avg_score, 2),
        'high_count': high_c,
        'moderate_count': mod_c,
        'needs_support_count': supp_c,
        'high_pct': round((high_c / total * 100), 1) if total > 0 else 0.0,
        'moderate_pct': round((mod_c / total * 100), 1) if total > 0 else 0.0,
        'needs_support_pct': round((supp_c / total * 100), 1) if total > 0 else 0.0
    }


def get_department_summary(df):
    """Computes aggregation metrics grouped by department."""
    if df is None or len(df) == 0 or 'department' not in df.columns:
        return pd.DataFrame()

    dept_grp = df.groupby('department')
    summary = dept_grp.agg(
        Total_Employees=('employee_code', 'count'),
        Avg_Attendance=('attendance_rate', lambda x: round(x.mean(), 1)),
        Avg_Task_Completion=('task_completion_rate', lambda x: round(x.mean(), 1)),
        Avg_Training_Hours=('training_hours', lambda x: round(x.mean(), 1)),
        Avg_Previous_Rating=('previous_performance', lambda x: round(x.mean(), 2))
    ).reset_index()

    # Calculate percentage of high performers per department
    high_pcts = []
    for dept in summary['department']:
        dept_rows = df[df['department'] == dept]
        high_cnt = (dept_rows['performance_category'] == 'High').sum()
        pct = round(high_cnt / len(dept_rows) * 100, 1) if len(dept_rows) > 0 else 0.0
        high_pcts.append(pct)

    summary['High_Performers_Pct'] = high_pcts
    return summary.sort_values(by='Total_Employees', ascending=False)


def get_time_series_trends(df):
    """Computes monthly aggregated trends when dated records are available."""
    if df is None or len(df) == 0 or 'review_date' not in df.columns:
        return pd.DataFrame()

    df_dated = df.copy()
    df_dated['review_date'] = pd.to_datetime(df_dated['review_date'], errors='coerce')
    df_dated = df_dated.dropna(subset=['review_date'])

    if len(df_dated) == 0:
        return pd.DataFrame()

    df_dated['month_year'] = df_dated['review_date'].dt.to_period('M').astype(str)
    trends = df_dated.groupby('month_year').agg(
        Review_Count=('employee_code', 'count'),
        Avg_Attendance=('attendance_rate', 'mean'),
        Avg_Task_Completion=('task_completion_rate', 'mean')
    ).reset_index().sort_values(by='month_year')

    trends['Avg_Attendance'] = trends['Avg_Attendance'].round(1)
    trends['Avg_Task_Completion'] = trends['Avg_Task_Completion'].round(1)
    return trends
