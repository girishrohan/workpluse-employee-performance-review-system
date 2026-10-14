-- WorkPulse SQLite schema.
-- Runtime migrations and default performance-area seeding live in
-- services/workpulse_service.py and database/db_manager.py.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code TEXT NOT NULL UNIQUE,
    employee_name TEXT NOT NULL,
    department TEXT NOT NULL,
    experience_years REAL NOT NULL,
    designation TEXT NOT NULL DEFAULT '',
    joining_date TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'On leave', 'Inactive')),
    data_origin TEXT NOT NULL DEFAULT 'user'
        CHECK (data_origin IN ('user', 'demo')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_rate REAL NOT NULL,
    task_completion_rate REAL NOT NULL,
    training_hours REAL NOT NULL,
    previous_performance REAL NOT NULL,
    performance_category TEXT NOT NULL,
    review_date TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_runs (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    training_date TEXT DEFAULT CURRENT_TIMESTAMP,
    evaluation_metrics TEXT,
    model_status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    model_id INTEGER NOT NULL,
    predicted_category TEXT NOT NULL,
    prediction_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    feature_snapshot TEXT,
    explanation_summary TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES model_runs(model_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS performance_periods (
    period_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft'
        CHECK (status IN ('Draft', 'Active', 'Completed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_areas (
    area_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    weight REAL NOT NULL CHECK (weight >= 0 AND weight <= 100),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    assessment_date TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    overall_score REAL NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    comments TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    FOREIGN KEY (period_id) REFERENCES performance_periods(period_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_assessments_employee_date
    ON assessments(employee_id, assessment_date DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_period
    ON assessments(period_id);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);

INSERT OR IGNORE INTO performance_areas (name, description, weight) VALUES
    ('Attendance', 'Reliability and attendance over the review period.', 20),
    ('Task completion', 'Delivery of agreed work and responsibilities.', 25),
    ('Productivity', 'Quality and consistency of work output.', 25),
    ('Teamwork', 'Collaboration and communication with colleagues.', 15),
    ('Learning and development', 'Engagement with training and skill development.', 15);
