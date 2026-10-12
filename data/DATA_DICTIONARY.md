# Data Dictionary - Employee Performance Dataset

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
