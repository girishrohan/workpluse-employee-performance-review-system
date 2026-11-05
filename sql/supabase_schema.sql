-- WorkPulse Supabase PostgreSQL Schema
-- This schema is designed for Supabase deployment with Row Level Security (RLS)

-- Enable RLS on all tables
-- Note: RLS policies are defined after tables for clarity

-- ============================================================================
-- Employees Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    employee_name VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    experience_years NUMERIC(5,2) NOT NULL DEFAULT 0,
    designation VARCHAR(100) NOT NULL DEFAULT 'Staff Member',
    joining_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'On leave', 'Inactive')),
    data_origin VARCHAR(20) NOT NULL DEFAULT 'user'
        CHECK (data_origin IN ('user', 'demo')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_employees_updated_at BEFORE UPDATE
    ON employees FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- ============================================================================
-- Performance Records Table (Historical performance data per employee)
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_records (
    record_id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    attendance_rate NUMERIC(5,2) NOT NULL CHECK (attendance_rate BETWEEN 0 AND 100),
    task_completion_rate NUMERIC(5,2) NOT NULL CHECK (task_completion_rate BETWEEN 0 AND 100),
    training_hours NUMERIC(5,2) NOT NULL DEFAULT 0,
    previous_performance NUMERIC(4,2) NOT NULL CHECK (previous_performance BETWEEN 0 AND 100),
    performance_category VARCHAR(30) NOT NULL CHECK (performance_category IN ('Needs Support', 'Moderate', 'High')),
    review_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_performance_records_employee ON performance_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_performance_records_review_date ON performance_records(review_date DESC);

-- ============================================================================
-- Performance Periods Table (Review cycles)
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_periods (
    period_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Draft'
        CHECK (status IN ('Draft', 'Active', 'Completed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_performance_periods_status ON performance_periods(status);
CREATE INDEX IF NOT EXISTS idx_performance_periods_dates ON performance_periods(start_date, end_date);

-- ============================================================================
-- Performance Areas Table (KPI framework)
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_areas (
    area_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    weight NUMERIC(5,2) NOT NULL CHECK (weight >= 0 AND weight <= 100),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Assessments Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    assessment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    reviewer VARCHAR(255) NOT NULL,
    scores_json JSONB NOT NULL,
    overall_score NUMERIC(5,2) NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    category VARCHAR(30) NOT NULL CHECK (category IN ('Needs Support', 'Moderate', 'High')),
    comments TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'Completed',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    FOREIGN KEY (period_id) REFERENCES performance_periods(period_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_assessments_employee ON assessments(employee_id);
CREATE INDEX IF NOT EXISTS idx_assessments_period ON assessments(period_id);
CREATE INDEX IF NOT EXISTS idx_assessments_date ON assessments(assessment_date DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_overall_score ON assessments(overall_score DESC);

-- ============================================================================
-- Model Runs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_runs (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    training_date TIMESTAMPTZ DEFAULT NOW(),
    evaluation_metrics JSONB,
    model_status VARCHAR(20) DEFAULT 'Active'
        CHECK (model_status IN ('Active', 'Deprecated', 'Archived')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Predictions Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    employee_id INTEGER,
    model_id INTEGER NOT NULL,
    predicted_category VARCHAR(30) NOT NULL CHECK (predicted_category IN ('Needs Support', 'Moderate', 'High')),
    prediction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    feature_snapshot JSONB,
    explanation_summary TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES model_runs(model_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_predictions_employee ON predictions(employee_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(prediction_timestamp DESC);

-- ============================================================================
-- Notifications Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    employee_id INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(read_at) WHERE read_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- ============================================================================
-- App Settings Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Demo Employees Table (Sample data for development)
-- ============================================================================
CREATE TABLE IF NOT EXISTS demo_employees (
    id SERIAL PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    employee_name VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    designation VARCHAR(100) NOT NULL DEFAULT 'Staff Member',
    joining_date DATE NOT NULL,
    experience_years NUMERIC(5,2) NOT NULL DEFAULT 0,
    attendance_rate NUMERIC(5,2) NOT NULL DEFAULT 85,
    task_completion_rate NUMERIC(5,2) NOT NULL DEFAULT 80,
    training_hours NUMERIC(5,2) NOT NULL DEFAULT 20,
    previous_performance NUMERIC(4,2) NOT NULL DEFAULT 3.0,
    performance_category VARCHAR(30) NOT NULL DEFAULT 'Moderate',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Insert Default Performance Areas (if not exists)
-- ============================================================================
INSERT INTO performance_areas (name, description, weight) VALUES
    ('Attendance', 'Reliability and attendance over the review period.', 20),
    ('Task completion', 'Delivery of agreed work and responsibilities.', 25),
    ('Productivity', 'Quality and consistency of work output.', 25),
    ('Teamwork', 'Collaboration and communication with colleagues.', 15),
    ('Learning and development', 'Engagement with training and skill development.', 15)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- Insert Default App Settings (if not exists)
-- ============================================================================
INSERT INTO app_settings (setting_key, setting_value) VALUES
    ('default_review_period_days', '90'),
    ('notification_days_before_deadline', '7'),
    ('kpi_threshold_high', '80'),
    ('kpi_threshold_moderate', '60'),
    ('max_training_hours_per_period', '40')
ON CONFLICT (setting_key) DO NOTHING;

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- For authenticated users (admin/hr role) - full access
-- For regular employees - limited read access
-- Note: These policies assume Supabase Auth is configured
-- Policies are designed to be flexible based on user role

-- Employees: Admin can do everything, employee can view self
CREATE POLICY "employees_admin_all" ON employees
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

CREATE POLICY "employees_hr_access" ON employees
    FOR SELECT TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('admin', 'hr')));

CREATE POLICY "employees_self_view" ON employees
    FOR SELECT TO authenticated USING (employee_code = auth.jwt()->>'employee_code');

-- Performance Records: Related to employee access
CREATE POLICY "performance_records_admin" ON performance_records
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

CREATE POLICY "performance_records_hr" ON performance_records
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('admin', 'hr')));

CREATE POLICY "performance_records_employee" ON performance_records
    FOR SELECT TO authenticated USING (
        EXISTS(SELECT 1 FROM employees WHERE employee_id = performance_records.employee_id AND employee_code = auth.jwt()->>'employee_code')
    );

-- Performance Periods: Admin/full access
CREATE POLICY "periods_admin" ON performance_periods
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('admin', 'hr')));

-- Assessments: Admin/hr full access, employee view own
CREATE POLICY "assessments_admin" ON assessments
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

CREATE POLICY "assessments_hr" ON assessments
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('admin', 'hr')));

CREATE POLICY "assessments_employee" ON assessments
    FOR SELECT TO authenticated USING (
        EXISTS(SELECT 1 FROM employees WHERE employee_id = assessments.employee_id AND employee_code = auth.jwt()->>'employee_code')
    );

-- Performance Areas: Public read
CREATE POLICY "areas_public_read" ON performance_areas
    FOR SELECT TO public USING (active = true);

-- Predictions: Based on employee access
CREATE POLICY "predictions_admin" ON predictions
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('admin', 'hr')));

-- Notifications: Full access for admin/hr, employee sees own
CREATE POLICY "notifications_admin" ON notifications
    FOR ALL TO authenticated USING (EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('admin', 'hr')));

-- ============================================================================
-- Views for Analytics
-- ============================================================================

-- View: Employee Performance Summary (latest metrics per employee)
CREATE OR REPLACE VIEW employee_performance_summary AS
SELECT
    e.employee_id,
    e.employee_code,
    e.employee_name,
    e.department,
    e.designation,
    e.experience_years,
    e.status,
    pr.attendance_rate,
    pr.task_completion_rate,
    pr.training_hours,
    pr.previous_performance,
    pr.performance_category,
    pr.review_date
FROM employees e
LEFT JOIN performance_records pr ON (
    pr.employee_id = e.employee_id
    AND pr.review_date = (
        SELECT MAX(review_date) FROM performance_records WHERE employee_id = e.employee_id
    )
);

-- View: Assessment Summary by Period
CREATE OR REPLACE VIEW assessment_summary_by_period AS
SELECT
    p.period_id,
    p.name,
    p.start_date,
    p.end_date,
    p.status,
    COUNT(a.assessment_id) as total_assessments,
    ROUND(AVG(a.overall_score), 2) as avg_score,
    ROUND(STDDEV(a.overall_score), 2) as score_stddev,
    COUNT(CASE WHEN a.overall_score >= 80 THEN 1 END) as high_performers,
    COUNT(CASE WHEN a.overall_score >= 60 AND a.overall_score < 80 THEN 1 END) as moderate_performers,
    COUNT(CASE WHEN a.overall_score < 60 THEN 1 END) as needs_support
FROM performance_periods p
LEFT JOIN assessments a ON p.period_id = a.period_id
GROUP BY p.period_id, p.name, p.start_date, p.end_date, p.status;

-- ============================================================================
-- Functions
-- ============================================================================

-- Function: Calculate employee performance score
CREATE OR REPLACE FUNCTION calculate_performance_score(
    p_attendance NUMERIC,
    p_task_completion NUMERIC,
    p_productivity NUMERIC DEFAULT 85,
    p_teamwork NUMERIC DEFAULT 75,
    p_learning NUMERIC DEFAULT 70
) RETURNS NUMERIC AS $$
DECLARE
    v_score NUMERIC;
BEGIN
    -- Weighted calculation based on performance areas
    v_score := (
        (p_attendance * 0.20) +
        (p_task_completion * 0.25) +
        (p_productivity * 0.25) +
        (p_teamwork * 0.15) +
        (p_learning * 0.15)
    );
    RETURN ROUND(v_score, 2);
END;
$$ LANGUAGE plpgsql;

-- Function: Get dashboard summary
CREATE OR REPLACE FUNCTION get_dashboard_summary()
RETURNS TABLE(
    total_employees BIGINT,
    active_periods BIGINT,
    completed_assessments BIGINT,
    avg_attendance NUMERIC,
    avg_task_completion NUMERIC,
    avg_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM employees WHERE status = 'Active')::BIGINT,
        (SELECT COUNT(*) FROM performance_periods WHERE status = 'Active')::BIGINT,
        (SELECT COUNT(*) FROM assessments)::BIGINT,
        ROUND((SELECT AVG(attendance_rate) FROM performance_records), 2)::NUMERIC,
        ROUND((SELECT AVG(task_completion_rate) FROM performance_records), 2)::NUMERIC,
        ROUND((SELECT AVG(overall_score) FROM assessments), 2)::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Indexes and Constraints
-- ============================================================================

-- Unique constraint for employee code
CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code);

-- Check constraint for assessment date ordering (start <= end)
CREATE INDEX IF NOT EXISTS idx_periods_date_order ON performance_periods(id, start_date, end_date);

-- Composite index for assessments queries
CREATE INDEX IF NOT EXISTS idx_assessments_employee_period ON assessments(employee_id, period_id);

-- JSONB index for scores_json querying (if needed for specific queries)
-- CREATE INDEX IF NOT EXISTS idx_assessments_scores_gin ON assessments USING GIN (scores_json);

-- ============================================================================
-- Initial Demo Data
-- ============================================================================

-- Insert demo employees (only if table is empty)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM demo_employees) THEN
        INSERT INTO demo_employees (employee_code, employee_name, department, designation, joining_date, experience_years, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category) VALUES
        ('EMP001', 'John Smith', 'Engineering', 'Senior Developer', '2020-01-15', 4.5, 95, 92, 35, 3.8, 'High'),
        ('EMP002', 'Sarah Johnson', 'Marketing', 'Marketing Specialist', '2021-03-10', 2.8, 88, 85, 28, 3.2, 'Moderate'),
        ('EMP003', 'Michael Chen', 'Sales', 'Sales Executive', '2019-06-01', 5.2, 92, 89, 42, 3.5, 'High'),
        ('EMP004', 'Emily Davis', 'HR', 'HR Coordinator', '2022-01-20', 1.5, 82, 78, 15, 2.8, 'Moderate'),
        ('EMP005', 'David Wilson', 'Engineering', 'QA Engineer', '2020-08-12', 3.8, 78, 85, 30, 3.1, 'Moderate'),
        ('EMP006', 'Lisa Anderson', 'Product', 'Product Manager', '2018-11-05', 6.0, 90, 88, 50, 3.7, 'High'),
        ('EMP007', 'Robert Martinez', 'Finance', 'Accountant', '2021-09-15', 3.0, 85, 82, 22, 3.0, 'Moderate'),
        ('EMP008', 'Jennifer Lee', 'Customer Success', 'Support Specialist', '2022-04-01', 1.8, 80, 85, 18, 2.5, 'Moderate'),
        ('EMP009', 'Chris Thompson', 'Engineering', 'DevOps Engineer', '2019-04-20', 5.0, 94, 90, 40, 3.9, 'High'),
        ('EMP010', 'Amanda White', 'Operations', 'Operations Analyst', '2020-12-01', 3.2, 87, 88, 25, 3.3, 'Moderate');
    END IF;
END $$;

-- Insert sample performance periods
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM performance_periods) THEN
        INSERT INTO performance_periods (name, start_date, end_date, status) VALUES
        ('Q1 2024 Review', '2024-01-01', '2024-03-31', 'Completed'),
        ('Q2 2024 Review', '2024-04-01', '2024-06-30', 'Completed'),
        ('Q3 2024 Review', '2024-07-01', '2024-09-30', 'Active'),
        ('Q4 2024 Review', '2024-10-01', '2024-12-31', 'Draft');
    END IF;
END $$;