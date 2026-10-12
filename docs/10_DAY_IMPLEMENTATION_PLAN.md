# 10-Day Implementation Plan & Milestone Tracker

## Employee Performance Analytics and Explainable Prediction System

**Course**: Computer Science & Engineering (3rd Year Mini Project)  
**Author**: Girish S  
**Objective**: Develop a working web application that analyses employee-related data, generates experimental performance predictions, and displays explainable results through an interactive dashboard.  

---

## 1. Implementation Phases & Schedule

| Phase | Days | Focus & Activities | Deliverable | Status |
|---|---|---|---|---|
| **Phase 1** | **Day 1** | Requirement analysis, user roles, feature scope, and PRD/TRD definition. | Requirements Document (`PRD.md`, `TRD.md`) | Completed ✅ |
| **Phase 2** | **Day 2–3** | Database schema design (SQLite/MySQL), synthetic dataset generation, and preprocessing. | Database (`sql/schema.sql`) & Dataset (`dataset.csv`) | Completed ✅ |
| **Phase 3** | **Day 4–5** | ML model development (Decision Tree & Random Forest), evaluation metrics, explainability engine. | Trained Model & Metrics (`src/ml_model.py`) | Completed ✅ |
| **Phase 4** | **Day 6–7** | Streamlit website development, 7-page navigation, prediction UI, and What-If simulator. | Working Website (`app.py`, `styles.css`) | Completed ✅ |
| **Phase 5** | **Day 8** | Automated test suite execution (TC-01 to TC-09), validation, and ethics audit. | Testing Suite (`tests/test_application.py`) | Completed ✅ |
| **Phase 6** | **Day 9–10** | Documentation finalization, academic report, presentation slides, and Viva Voce preparation. | Submission-Ready Project & Docs | Completed ✅ |

---

## 2. Milestone Tracker (6 / 6 Completed)

- [x] **Milestone 1 (Day 1)**: Requirements and dataset definitions finalized.
- [x] **Milestone 2 (Day 3)**: Database schema created & data preprocessing pipeline built.
- [x] **Milestone 3 (Day 5)**: Machine learning models trained, evaluated, and pickled.
- [x] **Milestone 4 (Day 7)**: Website and interactive Streamlit dashboard completed.
- [x] **Milestone 5 (Day 8)**: Automated unit testing (TC-01 through TC-09) 100% passed.
- [x] **Milestone 6 (Day 10)**: Final project report, viva guide, and demonstration ready.

---

## 3. Technology Implementation Stack

| Layer | Technology | Purpose | Implementation Location |
|---|---|---|---|
| **Frontend** | Streamlit 1.30+ | User interface and dashboard navigation | [`app.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/app.py) |
| **Styling** | Custom CSS | Glassmorphism card UI & dark palette | [`styles.css`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/styles.css) |
| **Backend** | Python 3.14 | Application logic & pipeline orchestration | `src/` modular packages |
| **Database** | SQLite 3 / MySQL 8.0 | Relational storage for 5 core tables | [`src/database.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/src/database.py) & [`sql/schema.sql`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/sql/schema.sql) |
| **Data Processing** | Pandas, NumPy | Cleaning, feature scaling, one-hot encoding | [`src/ml_model.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/src/ml_model.py) |
| **Machine Learning** | Decision Tree / Random Forest | Multiclass classification & feature importances | [`src/ml_model.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/src/ml_model.py) |
| **Explainability** | Local Contribution Engine | Factor impact waterfall decomposition | [`src/explainability.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/src/explainability.py) |
| **Simulation** | What-If Engine | Intervention scenario modeling | [`src/simulator.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/src/simulator.py) |
| **Visualisation** | Plotly Express | Interactive donut charts, scatter plots, heatmaps | [`app.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/app.py) |
| **Testing** | Unittest | Automated TC-01 to TC-09 test cases | [`tests/test_application.py`](file:///c:/Users/giris/Downloads/mini%20project%20employee%20performance%20reivew%20system/tests/test_application.py) |

---

## 4. Risk Management Summary

| Risk Factor | Mitigation Applied |
|---|---|
| **Insufficient Dataset** | Synthetic generator creates 600 records with realistic statistical correlations. |
| **Poor Model Performance** | Stratified train/test split with accuracy, weighted F1, and confusion matrix validation. |
| **System DLL Blocks** | Custom pure NumPy/Pandas Decision Tree & Random Forest engine eliminates external C-DLL block failures. |
| **Data Privacy Issues** | Sensitive demographic attributes (age, gender, ethnicity) excluded; synthetic IDs used. |
| **Misleading Predictions** | Clear disclaimers stating system is for decision support, not automated HR decisions. |
