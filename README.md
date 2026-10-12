# WorkPulse – Employee Performance Review System

> **“Understand Performance. Empower Growth.”**

A functional, full-stack workforce analytics and explainable machine learning decision-support web application developed for **Computer Science and Engineering Mini-Projects**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B)
![Scikit--Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E)
![Plotly](https://img.shields.io/badge/Plotly-5.15+-3F4F75)
![SQLite](https://img.shields.io/badge/SQLite-3.0+-003B57)
![Tests](https://img.shields.io/badge/Tests-21%20Passed-10B981)

---

## 🌟 Overview & Core Modules

WorkPulse replaces manual, subjective spreadsheet appraisals with an interactive, data-driven platform that tracks employee indicators, predicts performance categories (`Needs Support`, `Moderate`, `High`), and transparently explains prediction factors.

### 8 Functional Web Application Pages
1. **🏠 Home / Overview**: WorkPulse branding, project introduction, available modules summary, quick action buttons, and dynamic live statistics.
2. **📊 Dashboard**: Real-time KPI cards (Total Employees, Average Rating, Attendance, Task Completion, Category breakdown) and dynamic Plotly charts (Category Donut, Department Bar, Attendance vs Tasks Scatter, Training Box Plot).
3. **👥 Employee Management**: Complete persistent CRUD operations backed by SQLite (view/search records, add new employee with validation, edit details, view chronological review history, delete with confirmation).
4. **📁 Dataset Management**: CSV dataset upload, preview table, schema validation, missing value & duplicate audit, sample template download, and database CSV export.
5. **📈 Performance Analytics**: Deep-dive analytics exploring department-wise summaries, work feature correlation heatmaps, training impacts, and dated review trends.
6. **🔮 Performance Prediction**: Live machine learning inference form with custom sliders or employee lookup, confidence probability bar chart, local feature contribution waterfall chart, and decision-support disclaimers.
7. **🤖 Model Evaluation**: Side-by-side comparison of **Decision Tree** vs **Random Forest** on held-out test data (Accuracy, Precision, Recall, F1-Score, Confusion Matrix, Classification Report, Feature Importances).
8. **📑 Reports & Export**: Formal executive performance summary report, printable academic view, and SQLite prediction audit log export.

---

## 📁 Repository Structure

```
workpulse/
├── app.py                      # Main Streamlit web application (8 pages)
├── init_workpulse.py           # Database & sample data initializer
├── styles.css                  # Custom CSS styling (Navy/Blue/Teal theme)
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── config.toml             # Streamlit visual theme configuration
├── data/
│   ├── sample_employees.csv    # 600 realistic employee review records
│   ├── sample_template.csv     # Empty CSV template with example rows
├── database/
│   └── db_manager.py           # SQLite connection and parameterized CRUD operations
├── models/
│   ├── train_model.py          # Machine learning training & evaluation pipeline
│   ├── random_forest.pkl       # Serialized Random Forest pipeline
│   └── decision_tree.pkl       # Serialized Decision Tree pipeline
├── services/
│   ├── employee_service.py     # Employee management business logic
│   ├── analytics_service.py    # KPI calculations & statistical aggregations
│   ├── prediction_service.py   # Inference, confidence scoring, & logging
│   └── report_service.py       # Formal report generation & markdown exports
├── utils/
│   ├── validation.py           # Input boundaries & CSV schema validation
│   └── sample_data_generator.py # Synthetic dataset generator
├── tests/
│   ├── test_database.py        # SQLite schema & CRUD unit tests
│   ├── test_validation.py      # Input boundary & CSV validation unit tests
│   ├── test_predictions.py     # ML training, inference, & explainability tests
│   └── test_application.py     # Technical Requirements Document unit tests
└── docs/
    ├── synopsis.md             # Formal project synopsis for college submission
    ├── architecture.md         # System architecture & Mermaid ER diagrams
    └── viva_questions.md       # Comprehensive Viva Voce preparation Q&A guide
```

The SQLite database is created locally by `init_workpulse.py`; local database files are not tracked in Git.

---

## 🚀 Quick Start Guide

### 1. Environment Setup
Ensure **Python 3.10 or higher** is installed. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database & Train Models
```bash
python init_workpulse.py
```

### 4. Run Automated Unit Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```
*(All 21 unit tests will run and report 100% pass status).*

### 5. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🛡️ Responsible AI & Ethical Design
- **Decision Support Scope**: Predictions are explicitly labeled as experimental estimates to support managerial training allocations, not automated employment actions.
- **Privacy Preservation**: Sensitive demographic attributes (age, gender, ethnicity, religion) are strictly excluded from input features.
- **Explainability**: Every prediction displays local positive and negative feature contributions relative to population benchmarks to demystify model rationale.

---

## 🎓 College Mini-Project Submission Checklist
- [x] Complete, modular, functional Python source code.
- [x] Functional 8-page Streamlit web dashboard.
- [x] SQLite database with normalized schema (`employees`, `performance_records`, `model_runs`, `predictions`).
- [x] Pre-loaded 600-record sample dataset and downloadable CSV template.
- [x] Machine learning classification pipeline (Decision Tree & Random Forest).
- [x] Automated unit test suite with 21 passing test cases.
- [x] Formal Project Synopsis ([`docs/synopsis.md`](docs/synopsis.md)).
- [x] System Architecture & ER Diagrams ([`docs/architecture.md`](docs/architecture.md)).
- [x] Viva Voce Examination Prep Guide ([`docs/viva_questions.md`](docs/viva_questions.md)).
