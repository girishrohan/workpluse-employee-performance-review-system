# Product Requirements Document (PRD)

## Employee Performance Analytics and Explainable Prediction System

**Project Title**: Employee Performance Analytics and Explainable Prediction System  
**Prepared by**: Girish S  
**Department**: Computer Science and Engineering  
**Project Type**: Academic Mini-Project (CSE 3rd Year)  
**Proposed Duration**: 10 Days  
**Technology Stack**: Python, Streamlit, Pandas, Scikit-learn / NumPy, Plotly  

---

## 1. Introduction

The **Employee Performance Analytics and Explainable Prediction System** is a machine-learning-based application designed to analyse employee-related work data and identify patterns associated with performance.

The system allows users to upload employee data, view interactive dashboards, and generate experimental performance-category predictions using a trained machine learning model. It also provides explanations of the factors that influenced each prediction.

The application is intended for academic demonstration and decision support. Its predictions must not be treated as definitive assessments of an employee's ability or used as the sole basis for employment decisions.

---

## 2. Problem Statement

Organisations may collect employee data such as attendance, task completion, training hours, and work experience. Analysing these records manually can make it difficult to identify patterns across a large dataset.

The proposed system provides a centralised platform to analyse employee data, visualise performance-related trends, and demonstrate how machine learning can estimate performance categories from historical examples.

---

## 3. Product Vision

To build a simple, interactive, and explainable analytics dashboard that demonstrates how employee work-related data can be analysed using machine learning while maintaining transparency, privacy, and responsible use.

---

## 4. Goals and Objectives

* Develop a web-based employee analytics dashboard.
* Allow users to upload and validate employee datasets.
* Clean and preprocess the uploaded data.
* Train a machine learning model to predict performance categories.
* Display interactive charts and statistical summaries.
* Explain the factors contributing to a model's predictions.
* Evaluate the model using appropriate performance metrics.
* Include a what-if simulator to explore how changing input values affects a prediction.
* Use synthetic or appropriately authorised data and minimise sensitive information.

---

## 5. Target Users

| User | Purpose |
| --- | --- |
| **Students** | Demonstrate machine learning and data analytics concepts |
| **Project Evaluators** | Review the workflow, interface, and model evaluation |
| **Data Analysts** | Explore employee-related data and trends |
| **HR Professionals (Demonstration Only)** | Understand the potential use and limitations of workforce analytics |

---

## 6. Scope of the Product

### In Scope — First Version (MVP)
- CSV dataset upload & validation
- Dataset preview and missing value handling
- Data cleaning and preprocessing pipeline
- Descriptive analytics (correlation heatmaps, distributions, scatter plots)
- Machine learning model training (Decision Tree & Random Forest)
- Performance-category prediction (`Needs Support`, `Moderate`, `High`)
- Local & global prediction explanation
- Model evaluation (Accuracy, Precision, Recall, F1, Confusion Matrix)
- Interactive What-If prediction simulator
- Report and results export (CSV & documentation)

### Out of Scope
- Automatic hiring, firing, promotion, or salary decisions
- Live integration with company HR systems (e.g. Workday / SAP)
- Employee surveillance or continuous monitoring
- Facial expression, emotion, or personality analysis
- Predicting employee behaviour using private communications

---

## 7. Functional Requirements

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| **FR-01** | Upload employee data in CSV format | Must Have | Completed ✅ |
| **FR-02** | Display uploaded data in a table | Must Have | Completed ✅ |
| **FR-03** | Detect missing values and invalid records | Must Have | Completed ✅ |
| **FR-04** | Preprocess data for machine learning | Must Have | Completed ✅ |
| **FR-05** | Train a Decision Tree or Random Forest model | Must Have | Completed ✅ |
| **FR-06** | Predict an employee performance category | Must Have | Completed ✅ |
| **FR-07** | Display charts and performance statistics | Must Have | Completed ✅ |
| **FR-08** | Show factors influencing predictions | Must Have | Completed ✅ |
| **FR-09** | Display model evaluation metrics | Must Have | Completed ✅ |
| **FR-10** | Provide a what-if prediction simulator | Should Have | Completed ✅ |
| **FR-11** | Export results or a summary report | Should Have | Completed ✅ |

---

## 8. Non-Functional Requirements

| Requirement | Description | Status |
| --- | --- | --- |
| **Usability** | The interface should be simple, styled with glassmorphism cards, and easy to navigate. | Passed ✅ |
| **Performance** | Application processes synthetic 600-record dataset in under 1 second. | Passed ✅ |
| **Reliability** | Invalid files produce clear user-friendly error messages. | Passed ✅ |
| **Security** | Data processed locally in session memory without external exposure. | Passed ✅ |
| **Privacy** | Synthetic data excludes sensitive attributes (age, gender, ethnicity). | Passed ✅ |
| **Maintainability** | Code divided into modular packages (`src/dataset_generator`, `src/ml_model`, `src/explainability`, `src/simulator`, `src/fairness`). | Passed ✅ |
| **Explainability** | Predictions display relative impact waterfall breakdown and plain-English insights. | Passed ✅ |
| **Compatibility** | Streamlit web application compatible with all modern browsers. | Passed ✅ |

---

## 9. Dataset Requirements

| Attribute | Data Type | Description | Range / Values |
| --- | --- | --- | --- |
| `employee_id` | String | Unique record identifier | EMP-1001 to EMP-1600 |
| `department` | Categorical | Department/Team placement | Engineering, Sales, Marketing, HR, Support, Finance |
| `attendance_rate` | Numeric | Attendance percentage | 60.0% - 100.0% |
| `task_completion_rate` | Numeric | Percentage of assigned tasks completed | 45.0% - 100.0% |
| `training_hours` | Numeric | Training hours completed | 0.0 - 120.0 hrs |
| `experience_years` | Numeric | Years of work experience | 0.5 - 15.0 yrs |
| `previous_performance` | Numeric | Historical performance rating | 1.0 - 5.0 rating |
| `projects_delivered` | Numeric | Projects completed | 1 - 25 projects |
| `overtime_hours` | Numeric | Monthly overtime hours | 0.0 - 50.0 hrs |
| `peer_review_score` | Numeric | Peer rating | 1.0 - 5.0 rating |
| `communication_score` | Numeric | Communication rating | 1.0 - 5.0 rating |
| `performance_category` | Categorical | Target label for training | `Needs Support`, `Moderate`, `High` |

---

## 10. Acceptance Criteria Checklist

- [x] Application starts and opens in web browser (`streamlit run app.py`).
- [x] Valid CSV file can be uploaded and previewed.
- [x] Invalid files and missing required columns produce clear messages.
- [x] Data preprocessing pipeline runs successfully.
- [x] Classification models (Decision Tree & Random Forest) can be trained and evaluated.
- [x] Application displays predictions for valid sample inputs.
- [x] Dashboard displays relevant charts and summary statistics.
- [x] System provides an understandable explanation of model output.
- [x] Evaluation metrics and confusion matrix are displayed.
- [x] Project includes README, sample dataset, and usage instructions.
