"""
Employee Performance Analytics - Synthetic Dataset Generator
Generates realistic work-related employee performance data without sensitive demographic features.
"""

import os
import numpy as np
import pandas as pd

def generate_employee_data(n_samples=600, random_seed=42):
    """
    Generates synthetic employee performance data.
    
    Attributes generated:
    - employee_id: Unique record identifier
    - department: Department/Team (Engineering, Sales, Marketing, HR, Support, Finance)
    - attendance_rate: Attendance percentage (60% to 100%)
    - task_completion_rate: Task completion percentage (45% to 100%)
    - training_hours: Hours of training completed (0 to 120)
    - experience_years: Years of experience (0.5 to 15.0)
    - previous_performance: Historical performance rating (1.0 to 5.0)
    - projects_delivered: Number of completed projects (1 to 25)
    - overtime_hours: Overtime hours per month (0 to 50)
    - peer_review_score: Peer evaluation score (1.0 to 5.0)
    - communication_score: Teamwork & communication rating (1.0 to 5.0)
    - performance_category: Target label ('Needs Support', 'Moderate', 'High')
    """
    np.random.seed(random_seed)
    
    departments = ['Engineering', 'Sales', 'Marketing', 'Human Resources', 'Customer Support', 'Finance']
    dept_weights = [0.28, 0.22, 0.18, 0.10, 0.12, 0.10]
    
    emp_ids = [f"EMP-{1000 + i}" for i in range(1, n_samples + 1)]
    assigned_depts = np.random.choice(departments, size=n_samples, p=dept_weights)
    
    # Feature distributions
    attendance = np.clip(np.random.normal(88, 8, n_samples), 60, 100).round(1)
    task_completion = np.clip(np.random.normal(82, 12, n_samples), 45, 100).round(1)
    training_hrs = np.clip(np.random.gamma(3, 12, n_samples), 0, 120).round(1)
    experience = np.clip(np.random.exponential(4, n_samples) + 0.5, 0.5, 15.0).round(1)
    prev_perf = np.clip(np.random.normal(3.5, 0.8, n_samples), 1.0, 5.0).round(1)
    projects = np.clip(np.random.poisson(8, n_samples) + (experience * 0.5).astype(int), 1, 25)
    overtime = np.clip(np.random.gamma(2, 8, n_samples), 0, 50).round(1)
    peer_review = np.clip(np.random.normal(3.6, 0.7, n_samples), 1.0, 5.0).round(1)
    comm_score = np.clip(np.random.normal(3.7, 0.6, n_samples), 1.0, 5.0).round(1)
    
    # Calculate synthetic latent score for target classification
    # Score out of 100 with realistic weights and controlled Gaussian noise
    normalized_training = np.minimum(training_hrs, 80) / 80 * 100
    prev_perf_pct = (prev_perf / 5.0) * 100
    peer_review_pct = (peer_review / 5.0) * 100
    comm_pct = (comm_score / 5.0) * 100
    
    composite_score = (
        0.28 * task_completion +
        0.22 * attendance +
        0.18 * prev_perf_pct +
        0.14 * peer_review_pct +
        0.10 * normalized_training +
        0.08 * comm_pct +
        np.random.normal(0, 4.5, n_samples)  # Unobserved real-world variance / noise
    )
    
    # Assign categories based on composite score percentiles
    categories = []
    for score in composite_score:
        if score < 72.0:
            categories.append('Needs Support')
        elif score < 85.0:
            categories.append('Moderate')
        else:
            categories.append('High')
            
    df = pd.DataFrame({
        'employee_id': emp_ids,
        'department': assigned_depts,
        'attendance_rate': attendance,
        'task_completion_rate': task_completion,
        'training_hours': training_hrs,
        'experience_years': experience,
        'previous_performance': prev_perf,
        'projects_delivered': projects,
        'overtime_hours': overtime,
        'peer_review_score': peer_review,
        'communication_score': comm_score,
        'performance_category': categories
    })
    
    return df

def save_dataset(output_path='data/employee_performance_dataset.csv', n_samples=600):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = generate_employee_data(n_samples=n_samples)
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully saved to {output_path} ({len(df)} records)")

    # Data dictionary creation
    data_dict = """# Data Dictionary - Employee Performance Dataset

| Field Name | Data Type | Description | Range / Values |
|---|---|---|---|
| `employee_id` | String | Anonymized unique identifier | EMP-1001 to EMP-1600 |
| `department` | Categorical | Department/Team placement | Engineering, Sales, Marketing, Human Resources, Customer Support, Finance |
| `attendance_rate` | Float | Percentage of scheduled workdays attended | 60.0% - 100.0% |
| `task_completion_rate` | Float | Percentage of assigned task items completed on schedule | 45.0% - 100.0% |
| `training_hours` | Float | Cumulative professional development and training hours completed | 0.0 - 120.0 hrs |
| `experience_years` | Float | Years of work experience at company | 0.5 - 15.0 yrs |
| `previous_performance` | Float | Historical rating from previous evaluation cycle | 1.0 - 5.0 rating |
| `projects_delivered` | Integer | Total key projects completed in evaluation timeframe | 1 - 25 projects |
| `overtime_hours` | Float | Average monthly overtime hours | 0.0 - 50.0 hrs |
| `peer_review_score` | Float | Peer feedback rating | 1.0 - 5.0 rating |
| `communication_score` | Float | Collaboration & communication rating | 1.0 - 5.0 rating |
| `performance_category` | Target Class | Categorical performance label (ML target) | `Needs Support`, `Moderate`, `High` |
"""
    dict_path = os.path.join(os.path.dirname(output_path), 'DATA_DICTIONARY.md')
    with open(dict_path, 'w', encoding='utf-8') as f:
        f.write(data_dict)
    print(f"Data dictionary saved to {dict_path}")
    return df

if __name__ == '__main__':
    save_dataset()
