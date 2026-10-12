# Website Flow Document

## Employee Performance Analytics and Explainable Prediction System

**Course**: Computer Science & Engineering (3rd Year Mini Project)  
**Author**: Girish S  
**Application Type**: Interactive Streamlit Web Application  

---

## 1. Website Flow Architecture

```
[ 🏠 Page 1: Home Page ]
   └─► Project Overview, Key Features & "Launch Dashboard" Button
        │
        ├──► [ 📊 Page 2: Dashboard & Analytics ]
        │     └─► KPIs, Donut Chart, Scatter Plot, Departmental Breakdown, Heatmaps
        │
        ├──► [ 📁 Page 3: Dataset Management ]
        │     └─► CSV Upload, Data Preview, Missing Value Validation & CSV Download
        │
        ├──► [ 🔮 Page 4: Performance Prediction ]
        │     └─► Select Record/Sliders, Class Badges, Probabilities, Local Feature Waterfall
        │
        ├──► [ 🧪 Page 5: What-If Simulator ]
        │     └─► Baseline Profile vs Simulated Sliders, Deltas & Intervention Suggestions
        │
        ├──► [ 🤖 Page 6: Model Evaluation ]
        │     └─► Multi-model Metrics Table, Confusion Matrix Heatmap, Feature Importances
        │
        └──► [ 🛡️ Page 7: Fairness, Privacy & Reports ]
              └─► Departmental Parity Audit, Privacy Checklist & Report Downloads
```

---

## 2. Page-by-Page Specifications

### Page 1: 🏠 Home Page
- **Purpose**: Introduce project scope and key capabilities.
- **Components**:
  - Main header and subtitle.
  - Project synopsis & academic context.
  - Key feature highlights.
  - Quick summary metric cards (600 Records, 88.5% Accuracy, 6 Departments).
  - Primary "Launch Dashboard" button linking directly to Page 2.

### Page 2: 📊 Dashboard & Analytics
- **Purpose**: Overview of workforce data distributions and trends.
- **Components**:
  - Metric cards: Total Records, % High, % Moderate, % Needs Support, Avg Attendance.
  - Performance category distribution donut chart.
  - Attendance vs Task Completion scatter plot.
  - Departmental performance breakdown bar chart.
  - Work feature correlation matrix heatmap.

### Page 3: 📁 Dataset Management
- **Purpose**: Dataset upload, validation, and preview.
- **Components**:
  - CSV file uploader in sidebar.
  - Data summary table (rows, columns, missing values).
  - Column data type & null count validation summary.
  - Raw employee dataset viewer.
  - Download dataset CSV button.

### Page 4: 🔮 Performance Prediction & Explainability
- **Purpose**: Predict performance category and explain key drivers.
- **Components**:
  - Mode selection: Choose existing record vs custom parameter sliders.
  - Model selection: Random Forest vs Decision Tree.
  - Prediction badge (`High`, `Moderate`, `Needs Support`).
  - Class probability confidence gauge.
  - **Local Feature Contribution Waterfall Chart** (positive vs negative drivers).
  - Decision-support disclaimer box.

### Page 5: 🧪 What-If Decision Support Simulator
- **Purpose**: Simulate support intervention scenarios.
- **Components**:
  - Baseline profile selection.
  - Simulated support sliders (Training Hours, Task Completion, Attendance, Peer Review).
  - Side-by-side metric comparison cards (Baseline vs Simulated).
  - Class probability shift delta metrics (e.g. `+18.5% Shift in High`).
  - Recommended support intervention text insights.

### Page 6: 🤖 Model Evaluation & Reliability
- **Purpose**: Multi-model algorithm comparison and error analysis.
- **Components**:
  - Side-by-side performance table (Accuracy, Precision, Recall, F1-Score).
  - Interactive Confusion Matrix Heatmap.
  - Global Feature Importances bar chart.
  - Detailed classification report table per category.

### Page 7: 🛡️ Fairness, Privacy & Reports
- **Purpose**: Audit subgroup parity and export deliverables.
- **Components**:
  - Departmental parity audit table and disparity ratio.
  - 5-point Privacy Standards & Ethics Compliance checklist.
  - Downloadable project report (`PROJECT_REPORT.md`) and viva guide (`VIVA_QUESTIONS.md`).
