"""
WorkPulse - System Output Inspector
Runs the system and displays live database analytics, ML metrics, and sample predictions.
"""

import sys
import io
import os
import pandas as pd

# Enforce UTF-8 for Windows PowerShell output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from database.db_manager import get_all_employees
from services.analytics_service import compute_kpis, get_department_summary
from models.train_model import train_and_evaluate_all_models
from services.prediction_service import run_employee_prediction

# 1. Fetch data
df = get_all_employees("data/workpulse.db")
kpis = compute_kpis(df)
dept_summary = get_department_summary(df)

# 2. Evaluate ML models
eval_results, pipelines, splits = train_and_evaluate_all_models(df, "models")

# 3. Test prediction on sample record
sample_emp = df.iloc[0].to_dict()
rf_pipeline = pipelines["Random Forest"]
pred = run_employee_prediction(rf_pipeline, sample_emp, model_id=1, population_df=df)

print("=" * 65)
print("       WORKPULSE: EMPLOYEE PERFORMANCE REVIEW SYSTEM")
print("               LIVE RUNTIME RESULTS & METRICS")
print("=" * 65)

print("\n[1] ACTIVE WORKFORCE KPI METRICS (DATABASE)")
print(f" * Total Active Employees:               {kpis['total_employees']}")
print(f" * Average Attendance Rate:              {kpis['avg_attendance']}%")
print(f" * Average Task Completion Rate:         {kpis['avg_task_completion']}%")
print(f" * Average Performance Rating:           {kpis['avg_performance_score']} / 5.0")
print(f" * High Performance Category:            {kpis['high_count']} employees ({kpis['high_pct']}%)")
print(f" * Moderate Performance Category:        {kpis['moderate_count']} employees ({kpis['moderate_pct']}%)")
print(f" * Needs Support Category:               {kpis['needs_support_count']} employees ({kpis['needs_support_pct']}%)")

print("\n[2] MACHINE LEARNING MODEL EVALUATION (HELD-OUT TEST SET)")
for name, m in eval_results.items():
    print(f" * [{name:13}] Accuracy: {m['accuracy']*100:.2f}% | F1-Score: {m['f1_score']:.4f} | Precision: {m['precision']:.4f} | Recall: {m['recall']:.4f}")

print("\n[3] REAL-TIME MODEL PREDICTION & EXPLAINABILITY DEMONSTRATION")
print(f" * Employee Profile:                     {sample_emp.get('employee_name')} ({sample_emp.get('employee_code')})")
print(f" * Department:                           {sample_emp.get('department')}")
print(f" * Work Indicators:                      Attendance: {sample_emp.get('attendance_rate')}%, Task Completion: {sample_emp.get('task_completion_rate')}%, Training: {sample_emp.get('training_hours')} hrs")
print(f" * Predicted Performance Category:       {pred['predicted_category']}")
print(f" * Model Class Probabilities:            {pred['probabilities']}")
print(f" * Factor Explainability Drivers:        {pred['summary']}")

print("\n[4] DEPARTMENT-WISE PERFORMANCE SUMMARY")
print(dept_summary[['department', 'Total_Employees', 'Avg_Attendance', 'Avg_Task_Completion', 'High_Performers_Pct']].to_string(index=False))
print("=" * 65)
