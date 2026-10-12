# Technical Requirements Document (TRD)

## Employee Performance Analytics and Explainable Prediction System

**Version**: 1.0 | September 2026  
**Project**: Employee Performance Analytics and Explainable Prediction System  
**Department**: Computer Science and Engineering  
**Architecture**: Python-based web application with a machine learning pipeline  
**Platform**: Local computer / web browser  

---

## 1. Purpose

This Technical Requirements Document defines the software architecture, hardware and software requirements, data specifications, machine learning requirements, interfaces, security measures, and testing criteria for the Employee Performance Analytics and Explainable Prediction System.

The application will analyse employee-related work data, display analytical visualisations, and generate experimental predictions of performance categories using machine learning.

---

## 2. System Architecture

The application follows a modular architecture in which the user interface communicates with data-processing, analytics, and machine-learning components.

```
+-------------------------------------------------------------+
|                      User Interface                         |
|           Presentation Layer (Streamlit Dashboard)          |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                    Application Layer                        |
|        Data Validation, Preprocessing & Workflow            |
+-------------------------------------------------------------+
               |                               |
               v                               v
+------------------------------+ +----------------------------+
|         Data Module          | |         ML Module          |
|    (Pandas / NumPy / CSV)    | |  (Decision Tree / Forest)  |
+------------------------------+ +----------------------------+
               |                               |
               +---------------+---------------+
                               |
                               v
+-------------------------------------------------------------+
|                        Output Layer                         |
|   Predictions, Explanations, Charts & Evaluation Metrics    |
+-------------------------------------------------------------+
```

---

## 3. Hardware Requirements

| Component | Minimum Requirement | Recommended Specification |
| --- | --- | --- |
| **Processor** | Dual-core CPU | Quad-core CPU |
| **RAM** | 4 GB | 8 GB or more |
| **Storage** | 2 GB free space | 5 GB or more |
| **Display** | 1366 × 768 | Full HD (1920 × 1080) |
| **Internet** | Initial setup only | Stable connection |
| **GPU** | Not required | Not required |

---

## 4. Software Requirements

| Software | Purpose | Status |
| --- | --- | --- |
| **Windows / Linux / macOS** | Operating system | Compatible ✅ |
| **Python 3.10+** | Language runtime | Python 3.14 installed ✅ |
| **Streamlit 1.30+** | Interactive web dashboard | Installed ✅ |
| **Pandas 2.0+** | Dataset processing | Installed ✅ |
| **NumPy 1.24+** | Numerical operations & linear algebra | Installed ✅ |
| **Plotly 5.15+** | Interactive charts | Installed ✅ |
| **Joblib 1.3+** | Model persistence | Installed ✅ |

---

## 5. Functional Technical Requirements Audit

| ID | Technical Requirement | Implementation Status |
| --- | --- | --- |
| **TR-01** | Accept CSV files through user interface | Completed ✅ (`app.py` sidebar uploader) |
| **TR-02** | Validate file type, required columns, and data types | Completed ✅ (`app.py` & `src/dataset_generator.py`) |
| **TR-03** | Identify missing values and duplicate records | Completed ✅ (`src/ml_model.py`) |
| **TR-04** | Preprocess numerical and categorical features | Completed ✅ (`CustomPreprocessor` in `src/ml_model.py`) |
| **TR-05** | Split data into training and testing sets | Completed ✅ (80/20 Stratified Train/Test Split) |
| **TR-06** | Train at least one classification model | Completed ✅ (Decision Tree & Random Forest) |
| **TR-07** | Generate predictions for valid input records | Completed ✅ (Tab 3 Single Employee Prediction) |
| **TR-08** | Calculate classification evaluation metrics | Completed ✅ (Accuracy, Precision, Recall, F1, Confusion Matrix) |
| **TR-09** | Display analytical charts and summary statistics | Completed ✅ (Tab 1 Plotly Analytics Dashboard) |
| **TR-10** | Show feature importance and factor contributions | Completed ✅ (Tab 2 Global & Tab 3 Local Explainability) |
| **TR-11** | Support a what-if prediction interface | Completed ✅ (Tab 4 What-If Support Simulator) |
| **TR-12** | Allow results to be exported as a CSV file | Completed ✅ (Tab 5 Dataset CSV Export) |

---

## 6. Automated Testing Suite Summary (`tests/test_application.py`)

All 9 Technical Requirement Test Cases (TC-01 to TC-09) were executed and passed with 100% success rate:

```
Ran 9 tests in 2.992s
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
