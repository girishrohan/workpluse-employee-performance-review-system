# System Architecture & Technical Design

## WorkPulse – Employee Performance Review System

This document outlines the software architecture, relational database schema, Entity Relationship (ER) model, and data flow diagrams for **WorkPulse**.

---

### 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Presentation_Layer [Presentation Layer - Streamlit Web UI]
        UI1[Home & Overview Page]
        UI2[Dashboard & KPIs]
        UI3[Employee Management CRUD]
        UI4[Dataset Management & Upload]
        UI5[Performance Analytics Charts]
        UI6[ML Prediction & Explainability]
        UI7[Model Evaluation Comparison]
        UI8[Reports & Export Center]
    end

    subgraph Service_Layer [Service Layer - Python Business Logic]
        S1[Employee Service]
        S2[Analytics Service]
        S3[Prediction Service]
        S4[Report & Export Service]
        S5[Validation Engine]
    end

    subgraph Machine_Learning_Layer [Machine Learning Engine]
        ML1[Data Preprocessing & Scaling]
        ML2[Decision Tree Classifier]
        ML3[Random Forest Classifier]
        ML4[Explainability & Feature Importance]
    end

    subgraph Persistence_Layer [Persistence Layer - SQLite Database]
        DB[(workpulse.db)]
        T1[employees Table]
        T2[performance_records Table]
        T3[model_runs Table]
        T4[predictions Table]
    end

    UI1 --> Service_Layer
    UI2 --> S2
    UI3 --> S1
    UI4 --> S5
    UI5 --> S2
    UI6 --> S3
    UI7 --> Machine_Learning_Layer
    UI8 --> S4

    S1 --> DB
    S2 --> DB
    S3 --> Machine_Learning_Layer
    S3 --> DB
    S4 --> DB
    S5 --> S1

    DB --- T1
    DB --- T2
    DB --- T3
    DB --- T4
```

---

### 2. Entity Relationship (ER) Diagram

```mermaid
erDiagram
    EMPLOYEES ||--o{ PERFORMANCE_RECORDS : "tracks history"
    EMPLOYEES ||--o{ PREDICTIONS : "receives"
    MODEL_RUNS ||--o{ PREDICTIONS : "generates"

    EMPLOYEES {
        int employee_id PK
        string employee_code UK
        string employee_name
        string department
        real experience_years
        datetime created_at
    }

    PERFORMANCE_RECORDS {
        int record_id PK
        int employee_id FK
        real attendance_rate
        real task_completion_rate
        real training_hours
        real previous_performance
        string performance_category
        date review_date
    }

    MODEL_RUNS {
        int model_id PK
        string model_name
        string model_version
        datetime training_date
        text evaluation_metrics
        string model_status
    }

    PREDICTIONS {
        int prediction_id PK
        int employee_id FK
        int model_id FK
        string predicted_category
        datetime prediction_timestamp
        text feature_snapshot
        text explanation_summary
    }
```

---

### 3. Data Flow Diagrams (DFD)

#### DFD Level 0 (Context Diagram)
```mermaid
flowchart LR
    Manager[HR Manager / Evaluator] -->|1. Upload CSV / Enter Employee Record| WorkPulse[WorkPulse System]
    Manager -->|2. Request Performance Prediction| WorkPulse
    WorkPulse -->|3. Dashboard Analytics & Plots| Manager
    WorkPulse -->|4. Prediction & Local Factor Explanations| Manager
    WorkPulse -->|5. Executive Evaluation Reports| Manager
```

#### DFD Level 1 (Functional Decomposition)
```mermaid
flowchart TD
    User([User / Manager]) -->|Upload File| P1[1.0 Dataset Validation]
    P1 -->|Cleaned DataFrame| P2[2.0 Employee Management & Persistence]
    P2 -->|Write Records| DB[(SQLite Database)]
    DB -->|Read Historical Data| P3[3.0 Model Training & Pipeline Fit]
    P3 -->|Save Model Artifact| Models[(Model Binaries)]
    User -->|Enter Indicators| P4[4.0 Real-Time Prediction Service]
    Models -->|Pipeline Inference| P4
    P4 -->|Predicted Category & Explanations| User
    P4 -->|Log Prediction Result| DB
    DB -->|Aggregated Data| P5[5.0 Analytics & Dashboard Rendering]
    P5 -->|Interactive Charts & KPIs| User
```

---

### 4. Machine Learning Pipeline Architecture
1. **Feature Separation**: Numerical features (`attendance_rate`, `task_completion_rate`, `training_hours`, `experience_years`, `previous_performance`) are separated from categorical features (`department`).
2. **Preprocessing**:
   - Numerical columns are standardized using zero-mean unit-variance z-score normalization ($z = \frac{x - \mu}{\sigma}$).
   - Categorical columns are one-hot encoded into binary indicator vectors.
3. **Training & Evaluation**:
   - Stratified train-test split (80% training, 20% held-out test).
   - Training fits Decision Tree and Random Forest classifiers.
   - Evaluates test accuracy, precision, recall, F1-score, and confusion matrix.
4. **Explainability**:
   - Global: Gini importance reduction across tree nodes.
   - Local: Quantifies deviation of employee metrics from population averages weighted by model importance.
