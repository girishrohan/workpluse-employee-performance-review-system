# WorkPulse — Employee Performance Review System

**Understand Performance. Empower Growth.**

WorkPulse is a professional, enterprise-grade employee performance management and people analytics platform developed as a Computer Science Engineering mini-project. It combines structured review workflows, competency framework management, quantitative analytics, and interpretable machine learning decision support.

Designed with an executive SaaS visual identity inspired by modern HR technology platforms (such as OkrsTool and Lattice), WorkPulse adheres to high-tier product design principles: elegant typography, restrained color hierarchy, balanced whitespace, and authentic data visualizations.

---

## 1. Visual Identity & Design System

WorkPulse departs from typical generic dashboard templates through an art-directed enterprise design language:

* **Deep Navy (`#102A43`):** Anchor brand color communicating institutional trust, structure, and enterprise stability.
* **Muted Teal Accent (`#168C83` / `#0E7C7B`):** Action and growth indicator used for primary CTAs, active review cycles, and positive performance momentum.
* **Light Canvas (`#F8FAFC` & `#FFFFFF`):** Clean, distraction-free surfaces with 1px subtle borders (`#E2E8F0`) and micro-shadows.
* **Semantic Performance Tiers:**
  * **High Performance (Score ≥ 80):** Teal/Emerald (`#0D9488`, surface `#F0FDFA`)
  * **Moderate / Solid (60 ≤ Score < 80):** Warm Amber (`#D97706`, surface `#FFFBEB`)
  * **Needs Support / Coaching (Score < 60):** Crimson Rose (`#E11D48`, surface `#FFF1F2`)
* **Vector Icon System:** Replaced all emojis and Unicode symbols with crisp, handcrafted SVG icons (Lucide-inspired) across navigation and component cards.

---

## 2. Core Functional Modules

### A. Executive Dashboard
* **Active Review Cycle Banner:** Real-time completion progress meter (`% completed`, days remaining, pending review counts).
* **Workforce KPI Cards:** Workforce Mean Score (with benchmark delta), Registered Headcount, Active Cycles, and Completed Assessments.
* **Performance Distribution:** Donut chart breakdown with center metric.
* **Department Benchmark:** Horizontal bar chart comparing mean scores across departments with a 75.0 reference target.
* **Quarterly Trajectory:** Historical trend line tracking score progression over time.
* **Attention Queue:** Real-time roster of employees requiring coaching or awaiting evaluation.
* **Recent Evaluations Roster:** Tabulated audit of the latest completed reviews with reviewer stamps.

### B. Employee Directory & Performance Dossier
* **Search & Filters:** Real-time query by name, ID, or title, with department and status filters.
* **Employee Roster:** Structured table showing ID, Full Name, Department, Designation, Tenure, Status, and Outcome.
* **Dedicated Employee Profile Dossier:** Comprehensive talent card detailing avatar initials, tenure, and interactive KPI progress gauges (Attendance, Task Completion, Training Hours, Previous Rating).
* **Individual Review History:** Full historical audit trail of past reviews, reviewer comments, and per-competency scores.
* **CRUD Management:** Add Employee with input validation, profile updates, and safe deletion.

### C. Performance Review Cycles
* **Cadence Management:** Define review periods (e.g., *FY2026 Q3 Review Cycle*) with start/end dates.
* **Status Controls:** Lifecycle transitions across `Draft`, `Active`, and `Completed`.
* **Integrity Guard:** Deletion of review cycles with existing assessments is blocked to preserve organizational history.

### D. KPI Framework & Performance Areas
* **Weighted Indicator Configuration:** Five core default competencies (Attendance, Task Completion, Productivity, Teamwork, Learning & Development).
* **Mathematical Weight Validation:** Enforces active weights sum to exactly 100.0%.
* **Interactive Weight Tuning:** Dynamic editor with live status feedback.

### E. Structured Assessments
* **Review Composer:**
  * Employee selection with dynamic tenure and department summary.
  * Active review cycle linkage.
  * Reviewer credentials and date.
  * Per-indicator score sliders (0–100) displaying assigned mathematical weights.
  * **Live Score Preview Gauge:** Dynamic calculation of overall weighted score and real-time tier classification.
  * Qualitative feedback and developmental recommendations.
* **Assessment History:** Searchable, filterable audit registry with one-click CSV export.

### F. Workforce Analytics
* **Department Comparisons:** Mean performance across organizational units.
* **Tier Mix Analytics:** Proportional distribution of workforce standing.
* **Score Dispersion:** Box-plot distribution by department showing variance and outliers.
* **Monthly Trajectory:** Multi-month score progression.

### G. Machine Learning Decision Support
* **Model Benchmark:** Side-by-side evaluation of Scikit-learn **Decision Tree** vs. **Random Forest** Classifiers on held-out test splits.
* **Metrics:** Accuracy, Precision, Recall, F1-Score, and test sample counts.
* **Confusion Matrix:** Heatmap visualization of true vs. predicted performance tiers.
* **Single-Employee Inference & What-If Simulator:**
  * Select an existing employee or enter custom operational parameters (Attendance, Task Completion, Training Hours, Experience, Prior Rating).
  * Outputs predicted tier, probability distribution chart, and local feature contributions (identifying primary positive and negative drivers).
  * **What-If Sensitivity Analysis:** Test scenarios (e.g., increasing training hours or task completion) to observe projected classification shifts.
* **Ethical AI Disclaimer:** Prominently labels predictions as experimental decision-support estimates that must not replace human review.

### H. Executive Reports
* **Multi-Dimensional Filtering:** Slice by department, review cycle, and employee.
* **Executive Memo View:** Formatted summary scorecard for leadership presentation.
* **Tabulated Roster:** Complete audit log including reviewer comments.
* **Export:** One-click CSV export.

### I. Notifications & Task Queue
* **Pending Reviews Tracker:** Immediate visibility into unassessed active staff in open cycles with due dates.
* **Audit Event Feed:** Historical record of workflow actions with mark-as-read controls.

### J. Settings & Viva Demonstration Suite
* **Workspace & Admin Profile:** Customize administrator display name and organization name.
* **System Diagnostics:** Live SQLite database file path, disk size, and connection integrity.
* **1-Click "Seed Demo Review Cycle":** Populates realistic demonstration review cycles and 35+ assessments across departments so evaluators can inspect a fully populated analytics suite immediately.
* **Reset Feature:** Cleans demonstration assessments to return to a clean baseline.

---

## 3. Technology Stack

* **Frontend / UI:** Streamlit (v1.40+), Custom Modern CSS Design System, Google Fonts (Inter), SVG Icon Primitives
* **Data Visualization:** Plotly Express & Plotly Graph Objects (Custom WorkPulse White Theme)
* **Backend Logic & Data Processing:** Python 3.10+, Pandas, NumPy
* **Machine Learning:** Scikit-learn (Decision Tree Classifier, Random Forest Classifier, Preprocessing Pipelines)
* **Database & Persistence:** SQLite3 (foreign key enforcement, parameterized queries, schema migration)
* **Testing:** Python `unittest` test suite (33 automated tests)

---

## 4. Project Layout

```text
├── app.py                         # Streamlit application entry point
├── workpulse_ui.py                # Main navigation, UI components & page renderers
├── ui_components.py               # Reusable visual primitives & SVG icon registry
├── styles.css                     # Custom enterprise CSS design system
├── services/
│   ├── workpulse_service.py       # Core SQLite database CRUD & workflow service
│   ├── prediction_service.py      # Real-time ML inference & explainability engine
│   ├── employee_service.py        # Employee management operations
│   ├── analytics_service.py       # Analytics aggregation helpers
│   └── report_service.py          # Reporting export utilities
├── database/
│   └── db_manager.py              # Low-level SQLite database manager & connection pool
├── models/
│   ├── train_model.py             # Decision Tree & Random Forest training engine
│   └── *.pkl                      # Serialized model pipelines & evaluation caches
├── data/
│   ├── workpulse.db               # Primary SQLite database
│   └── employee_performance_dataset.csv # Optional reference dataset
├── sql/
│   └── schema.sql                 # Reference database schema
├── utils/
│   └── validation.py              # Input validation and business rule constraints
└── tests/
    ├── test_workpulse_service.py  # Service & workflow integration tests
    ├── test_database.py           # Database CRUD tests
    ├── test_predictions.py        # Model inference tests
    ├── test_validation.py         # Business rule validation tests
    └── test_application.py       # End-to-end data pipeline tests
```

---

## 5. Local Setup & Installation

### Windows PowerShell

```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Launch application
streamlit run app.py
```

### macOS or Linux

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Launch application
streamlit run app.py
```

The application will be accessible at: `http://localhost:8501`

---

## 6. Running Automated Tests

Run the full test suite (33 test cases):

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected output:
```text
Ran 33 tests in ~11s
OK
[PASS] TC-01: Valid CSV loaded successfully.
[PASS] TC-02: Non-CSV file produces clear error validation.
[PASS] TC-03: Missing values detected and cleaned.
[PASS] TC-04: Numerical percentage ranges validated.
[PASS] TC-05: Machine learning models trained successfully.
[PASS] TC-06: Prediction returned category 'Moderate' with probabilities.
[PASS] TC-07: Evaluation metrics and confusion matrix calculated correctly.
[PASS] TC-08: CSV export generated successfully.
[PASS] TC-09: Explainability and What-If simulation executed successfully.
```

---

## 7. College Mini-Project & Viva Demonstration Guide

When presenting WorkPulse to evaluators or professors:

1. **Launch the Application:** Start via `streamlit run app.py` and open in full-screen browser mode.
2. **Instant Demo Setup:**
   * If the review database is empty, navigate to **Settings & Demo Suite** (or use the banner on the Dashboard) and click **"⚡ Seed Demo Review Cycle"**.
   * This immediately populates realistic review cycles and assessments across Engineering, Sales, Product, HR, and Finance.
3. **Walkthrough Flow:**
   * **Dashboard:** Highlight the Active Cycle Banner with live progress, executive KPI cards, Performance Distribution Donut, and Department Benchmark.
   * **Employee Directory:** Demonstrate search filtering, then open the **Employee Performance Dossier** to inspect an employee's avatar, tenure, attendance gauge, task completion, and full historical assessment records.
   * **Assessments:** Open the Review Composer, select an employee, adjust the competency sliders, and show the **Live Weighted Overall Score Preview** calculating the score and tier in real-time.
   * **Workforce Analytics:** Demonstrate interactive slicers (by department and cycle), score dispersion box plot, and monthly trajectory.
   * **Machine Learning Decision Support:** Show the side-by-side benchmark comparison (Decision Tree vs. Random Forest), confusion matrix, feature contributions, and the **What-If Sensitivity Simulator**.
   * **Executive Reports:** Filter by department and cycle, demonstrate the executive audit scorecard, and download the verified CSV report.
4. **Code Quality & Architecture Viva Answers:**
   * *How is data persistence handled?* Normalized SQLite with foreign keys, parameterized queries, and automatic migrations.
   * *How is data leakage prevented in ML?* Target labels (`performance_category`) are strictly excluded from input feature vectors, and models are evaluated exclusively on a held-out 20% test split.
   * *How are performance scores calculated?* Weighted sum formula $\text{Overall Score} = \sum (\text{Indicator Score}_i \times \frac{\text{Weight}_i}{100})$, with validation ensuring active weights sum to 100%.
