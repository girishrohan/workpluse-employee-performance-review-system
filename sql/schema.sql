-- Employee Performance Analytics - SQL Database Schema
-- Compatible with SQLite and MySQL 8.0

-- 1. Employees Table
CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    department VARCHAR(100),
    experience_years DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Historical Performance Records Table
CREATE TABLE IF NOT EXISTS performance_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_rate DECIMAL(5,2),
    task_completion_rate DECIMAL(5,2),
    training_hours DECIMAL(7,2),
    previous_performance VARCHAR(30),
    performance_category VARCHAR(20) NOT NULL,
    recorded_at DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);

-- 3. Machine Learning Model Metadata Table
CREATE TABLE IF NOT EXISTS ml_models (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(30) NOT NULL,
    algorithm VARCHAR(50) NOT NULL,
    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluation_metrics TEXT,
    model_file_path VARCHAR(255),
    model_status VARCHAR(20) DEFAULT 'Active',
    UNIQUE (model_name, model_version)
);

-- 4. Prediction Records Table
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NULL,
    model_id INTEGER NOT NULL,
    predicted_category VARCHAR(20) NOT NULL,
    feature_snapshot TEXT NOT NULL,
    prediction_probability DECIMAL(7,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES ml_models(model_id) ON DELETE CASCADE
);

-- 5. Prediction Explanations Table
CREATE TABLE IF NOT EXISTS prediction_explanations (
    explanation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    contribution_value DECIMAL(12,6),
    explanation_text TEXT,
    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id) ON DELETE CASCADE
);
