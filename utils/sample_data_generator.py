"""
WorkPulse - Sample Dataset Generator
Generates realistic employee records for demonstration and creates sample CSV template.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

FIRST_NAMES = [
    'Aarav', 'Ananya', 'Rahul', 'Priya', 'Aditya', 'Sneha', 'Vikram', 'Rhea',
    'Rohan', 'Tanvi', 'Karan', 'Pooja', 'Nikhil', 'Divya', 'Arjun', 'Meera',
    'Sameer', 'Isha', 'Varun', 'Kavya', 'Gaurav', 'Neha', 'Kabir', 'Simran'
]
LAST_NAMES = [
    'Sharma', 'Verma', 'Patel', 'Reddy', 'Nair', 'Iyer', 'Gupta', 'Singh',
    'Kumar', 'Joshi', 'Mehta', 'Rao', 'Das', 'Chatterjee', 'Bose', 'Menon'
]
DEPARTMENTS = [
    'Engineering', 'Sales', 'Marketing', 'Human Resources',
    'Customer Support', 'Finance', 'Operations', 'Product Management'
]
DEPT_WEIGHTS = [0.25, 0.20, 0.15, 0.10, 0.12, 0.08, 0.05, 0.05]


def generate_sample_employees(n_samples=600, random_seed=42):
    """Generates synthetic employee performance records."""
    np.random.seed(random_seed)

    emp_codes = [f"WP-{1000 + i}" for i in range(1, n_samples + 1)]
    names = [
        f"{np.random.choice(FIRST_NAMES)} {np.random.choice(LAST_NAMES)}"
        for _ in range(n_samples)
    ]
    departments = np.random.choice(DEPARTMENTS, size=n_samples, p=DEPT_WEIGHTS)
    experience = np.clip(np.random.exponential(3.5, n_samples) + 0.5, 0.5, 20.0).round(1)

    attendance = np.clip(np.random.normal(87, 8, n_samples), 55, 100).round(1)
    task_comp = np.clip(np.random.normal(83, 11, n_samples), 45, 100).round(1)
    training = np.clip(np.random.gamma(2.5, 12, n_samples), 0, 120).round(1)
    prev_perf = np.clip(np.random.normal(3.5, 0.8, n_samples), 1.0, 5.0).round(1)

    # Review dates between Jan 2024 and Aug 2026
    base_date = datetime(2024, 1, 15)
    days_range = (datetime(2026, 8, 30) - base_date).days
    random_days = np.random.randint(0, days_range, size=n_samples)
    review_dates = [(base_date + timedelta(days=int(d))).strftime('%Y-%m-%d') for d in random_days]

    # Ground truth latent score for target classification with noise
    latent_score = (
        0.32 * task_comp +
        0.26 * attendance +
        0.20 * (prev_perf / 5.0 * 100) +
        0.12 * (np.minimum(training, 60) / 60.0 * 100) +
        0.10 * (np.minimum(experience, 10) / 10.0 * 100) +
        np.random.normal(0, 4.0, n_samples)
    )

    categories = []
    for sc in latent_score:
        if sc < 70.0:
            categories.append('Needs Support')
        elif sc < 84.0:
            categories.append('Moderate')
        else:
            categories.append('High')

    df = pd.DataFrame({
        'employee_code': emp_codes,
        'employee_name': names,
        'department': departments,
        'experience_years': experience,
        'attendance_rate': attendance,
        'task_completion_rate': task_comp,
        'training_hours': training,
        'previous_performance': prev_perf,
        'performance_category': categories,
        'review_date': review_dates
    })

    return df


def create_sample_files(data_dir="data"):
    """Generates sample_employees.csv and sample_template.csv."""
    os.makedirs(data_dir, exist_ok=True)
    df = generate_sample_employees(n_samples=600)
    sample_path = os.path.join(data_dir, "sample_employees.csv")
    df.to_csv(sample_path, index=False)

    template_df = pd.DataFrame([
        {
            'employee_code': 'WP-2001',
            'employee_name': 'Jane Doe',
            'department': 'Engineering',
            'experience_years': 4.5,
            'attendance_rate': 94.0,
            'task_completion_rate': 89.5,
            'training_hours': 35.0,
            'previous_performance': 4.2,
            'performance_category': 'High',
            'review_date': '2026-06-15'
        },
        {
            'employee_code': 'WP-2002',
            'employee_name': 'John Smith',
            'department': 'Marketing',
            'experience_years': 2.0,
            'attendance_rate': 81.0,
            'task_completion_rate': 74.0,
            'training_hours': 18.0,
            'previous_performance': 3.1,
            'performance_category': 'Moderate',
            'review_date': '2026-06-20'
        }
    ])
    template_path = os.path.join(data_dir, "sample_template.csv")
    template_df.to_csv(template_path, index=False)

    return sample_path, template_path


if __name__ == '__main__':
    s_path, t_path = create_sample_files()
    print(f"Generated sample dataset: {s_path}")
    print(f"Generated sample template: {t_path}")
