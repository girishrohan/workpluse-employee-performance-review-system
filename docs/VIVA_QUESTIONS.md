# Viva Voce Examination Guide

## WorkPulse – Employee Performance Review System

**Academic Degree**: Computer Science & Engineering (3rd Year Mini-Project)  
**Product**: WorkPulse (“Understand Performance. Empower Growth.”)  

---

### Category 1: Project Overview & System Design

#### Q1: What is the core problem that WorkPulse solves?
**Answer**: Traditional performance appraisals are often subjective, intermittent, and dispersed across spreadsheets. WorkPulse provides a centralized, data-driven decision-support platform that standardizes workforce records, visualizes team performance patterns, and predicts performance categories using machine learning while clearly explaining the contributing factors.

#### Q2: What are the primary technologies utilized in WorkPulse?
**Answer**:
- **Presentation Layer**: Streamlit (Python web framework) with custom CSS and Plotly.
- **Backend & Logic**: Python 3.10+ modular services (`employee_service`, `analytics_service`, `prediction_service`).
- **Database**: SQLite 3 relational database (`workpulse.db`) with normalized schema.
- **Machine Learning**: Decision Tree and Random Forest classifiers with Scikit-learn architecture.

#### Q3: Why is WorkPulse designated as a "decision-support" tool rather than an automated decision-maker?
**Answer**: In accordance with ethical AI guidelines and employment regulations (e.g. EU AI Act), automated systems must never make unilateral hiring, firing, or promotion decisions. Historical performance data can contain human bias. WorkPulse provides decision-support estimates with transparent confidence scores to assist managers in identifying training and development needs.

---

### Category 2: Machine Learning & Preprocessing

#### Q4: Why did you implement both Decision Tree and Random Forest classifiers?
**Answer**:
- **Decision Tree**: Simple, highly interpretable, and visualizes logical decision boundaries based on hierarchical splits. However, single trees are prone to high variance and overfitting.
- **Random Forest**: An ensemble method using bagging (bootstrap aggregating) of multiple trees. By averaging predictions and subsampling features at each split, it significantly reduces variance and yields superior generalization on tabular data (~80% vs ~68% accuracy).

#### Q5: How do you prevent data leakage during preprocessing and model evaluation?
**Answer**: Data preprocessing parameters (such as the mean and standard deviation for numerical scaling, and category encodings) are calculated strictly on the training dataset (80%). The held-out test dataset (20%) is transformed using only the parameters learned from the training data, preventing information from leaking from test data into model training.

#### Q6: Why is Accuracy alone not sufficient for evaluating employee performance classification?
**Answer**: Employee performance categories are naturally imbalanced (e.g. fewer employees in `Needs Support` compared to `Moderate`). A naive model could predict `Moderate` for all instances and achieve moderate accuracy. Therefore, we evaluate:
- **Precision**: How many of the predicted positives were truly positive.
- **Recall**: How many of the actual positive cases were correctly captured.
- **F1-Score**: Harmonic mean of Precision and Recall ($2 \cdot \frac{P \cdot R}{P + R}$).
- **Confusion Matrix**: Full breakdown of true vs predicted classes.

#### Q7: How does local prediction explainability work in WorkPulse?
**Answer**: For any single prediction, the system measures the normalized deviation of the employee's indicators (e.g. task completion, attendance) against population averages, weighted by the model's global feature importances. This derives a relative impact score indicating which specific indicators positively or negatively drove the prediction.

---

### Category 3: Database & Software Engineering

#### Q8: What database schema did you design for WorkPulse?
**Answer**: A normalized SQLite relational database containing four tables:
1. `employees`: Stores unique identifiers (`employee_code`), name, department, experience, and creation timestamp.
2. `performance_records`: Stores time-stamped metrics (`attendance_rate`, `task_completion_rate`, `training_hours`, `previous_performance`, `performance_category`, `review_date`) linked via foreign key to `employees`.
3. `model_runs`: Logs training metadata, algorithm name, version, and evaluation metrics in JSON format.
4. `predictions`: Stores prediction logs, feature snapshots, and explanation summaries linked to the model and employee.

#### Q9: How does WorkPulse handle data validation during CSV uploads?
**Answer**: The validation engine checks:
1. Presence of mandatory columns (`employee_code`, `department`, `attendance_rate`, `task_completion_rate`, `performance_category`).
2. Numerical range constraints (attendance and task completion clamped between 0% and 100%).
3. Duplicate employee codes are flagged and consolidated.
4. Missing values in non-critical columns are imputed with documented statistical defaults.

#### Q10: What automated tests have you implemented?
**Answer**: We built an automated unit testing suite (`tests/`) covering:
- `test_database.py`: Tests SQLite initialization, employee insertion, editing, deletion, duplicate code rejection, and cascade deletion.
- `test_validation.py`: Tests input boundary checks, range enforcement, and CSV schema validation.
- `test_predictions.py`: Tests model fitting, inference, feature importance extraction, and probability distributions.
All 21 automated unit tests execute with a 100% pass rate.
