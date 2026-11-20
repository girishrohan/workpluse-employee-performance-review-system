-- ============================================================================
-- WorkPulse Dashboard Data Restore Script
-- Restores sample employees, review cycles, and assessments for admin view
-- Idempotent: safe to run multiple times without duplicating rows
-- ============================================================================

-- 1. Ensure the admin user exists in the Supabase 'users' table
-- This is critical for RLS policies to allow access to all data
-- NOTE: The trigger on auth.users should auto-create this on first login
-- But if the user already exists in auth.users without a users table row,
-- run this manually after getting the UUID from Supabase Dashboard > Authentication > Users
--
-- To find the UUID: Go to Supabase Dashboard > Authentication > Users
-- Find admin@workpulse.local and copy the UUID
-- Then uncomment and run:
-- INSERT INTO users (id, role, full_name) VALUES ('PASTE-UUID-HERE', 'admin', 'Admin')
-- ON CONFLICT (id) DO UPDATE SET role = 'admin', full_name = 'Admin', updated_at = NOW();

-- 2. Ensure default performance areas exist (idempotent) - name is UNIQUE
INSERT INTO performance_areas (name, description, weight) VALUES
    ('Attendance', 'Reliability and attendance over the review period.', 20),
    ('Task completion', 'Delivery of agreed work and responsibilities.', 25),
    ('Productivity', 'Quality and consistency of work output.', 25),
    ('Teamwork', 'Collaboration and communication with colleagues.', 15),
    ('Learning and development', 'Engagement with training and skill development.', 15)
ON CONFLICT (name) DO NOTHING;

-- 3. Ensure app settings exist (idempotent) - setting_key is PRIMARY KEY
INSERT INTO app_settings (setting_key, setting_value) VALUES
    ('default_review_period_days', '90'),
    ('notification_days_before_deadline', '7'),
    ('kpi_threshold_high', '80'),
    ('kpi_threshold_moderate', '60'),
    ('max_training_hours_per_period', '40')
ON CONFLICT (setting_key) DO NOTHING;

-- 4. Insert demo employees into demo_employees table (idempotent - only if table is empty)
-- employee_code is UNIQUE in demo_employees
INSERT INTO demo_employees (employee_code, employee_name, department, designation, joining_date, experience_years, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category)
SELECT * FROM (VALUES
    ('EMP001', 'John Smith', 'Engineering', 'Senior Developer', '2020-01-15'::date, 4.5, 95, 92, 35, 3.8, 'High'),
    ('EMP002', 'Sarah Johnson', 'Marketing', 'Marketing Specialist', '2021-03-10'::date, 2.8, 88, 85, 28, 3.2, 'Moderate'),
    ('EMP003', 'Michael Chen', 'Sales', 'Sales Executive', '2019-06-01'::date, 5.2, 92, 89, 42, 3.5, 'High'),
    ('EMP004', 'Emily Davis', 'HR', 'HR Coordinator', '2022-01-20'::date, 1.5, 82, 78, 15, 2.8, 'Moderate'),
    ('EMP005', 'David Wilson', 'Engineering', 'QA Engineer', '2020-08-12'::date, 3.8, 78, 85, 30, 3.1, 'Moderate'),
    ('EMP006', 'Lisa Anderson', 'Product', 'Product Manager', '2018-11-05'::date, 6.0, 90, 88, 50, 3.7, 'High'),
    ('EMP007', 'Robert Martinez', 'Finance', 'Accountant', '2021-09-15'::date, 3.0, 85, 82, 22, 3.0, 'Moderate'),
    ('EMP008', 'Jennifer Lee', 'Customer Success', 'Support Specialist', '2022-04-01'::date, 1.8, 80, 85, 18, 2.5, 'Moderate'),
    ('EMP009', 'Chris Thompson', 'Engineering', 'DevOps Engineer', '2019-04-20'::date, 5.0, 94, 90, 40, 3.9, 'High'),
    ('EMP010', 'Amanda White', 'Operations', 'Operations Analyst', '2020-12-01'::date, 3.2, 87, 88, 25, 3.3, 'Moderate')
) AS v(employee_code, employee_name, department, designation, joining_date, experience_years, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category)
WHERE NOT EXISTS (SELECT 1 FROM demo_employees);

-- 5. Migrate demo employees to the main 'employees' table with proper RLS visibility
-- employee_code is UNIQUE in employees
INSERT INTO employees (employee_code, employee_name, department, designation, joining_date, experience_years, status, data_origin)
SELECT employee_code, employee_name, department, designation, joining_date, experience_years, 'Active', 'demo'
FROM demo_employees
ON CONFLICT (employee_code) DO UPDATE SET
    employee_name = EXCLUDED.employee_name,
    department = EXCLUDED.department,
    experience_years = EXCLUDED.experience_years,
    status = 'Active',
    data_origin = 'demo',
    updated_at = NOW();

-- 6. Create sample review cycles/periods (idempotent) - name is UNIQUE
INSERT INTO performance_periods (name, start_date, end_date, status)
SELECT * FROM (VALUES
    ('Q4 2024 Review', '2024-10-01'::date, '2024-12-31'::date, 'Active'),
    ('Q3 2024 Review', '2024-07-01'::date, '2024-09-30'::date, 'Completed'),
    ('Q2 2024 Review', '2024-04-01'::date, '2024-06-30'::date, 'Completed'),
    ('Q1 2024 Review', '2024-01-01'::date, '2024-03-31'::date, 'Completed')
) AS v(name, start_date, end_date, status)
WHERE NOT EXISTS (SELECT 1 FROM performance_periods);

-- 7. Create sample assessments linking employees to cycles
-- NO unique constraint on (employee_id, period_id), so use WHERE NOT EXISTS
INSERT INTO assessments (employee_id, period_id, assessment_date, reviewer, scores_json, overall_score, category, status)
SELECT
    e.employee_id,
    p.period_id,
    CURRENT_DATE - INTERVAL '15 days' AS assessment_date,
    'Admin' AS reviewer,
    '{"Attendance": 85, "Task completion": 90, "Productivity": 78, "Teamwork": 80, "Learning and development": 75}'::JSONB,
    CASE
        WHEN e.employee_code = 'EMP001' THEN 88
        WHEN e.employee_code = 'EMP002' THEN 75
        WHEN e.employee_code = 'EMP003' THEN 92
        WHEN e.employee_code = 'EMP004' THEN 70
        WHEN e.employee_code = 'EMP005' THEN 72
        WHEN e.employee_code = 'EMP006' THEN 85
        WHEN e.employee_code = 'EMP007' THEN 78
        WHEN e.employee_code = 'EMP008' THEN 73
        WHEN e.employee_code = 'EMP009' THEN 84
        WHEN e.employee_code = 'EMP010' THEN 77
    END AS overall_score,
    CASE
        WHEN e.employee_code IN ('EMP001', 'EMP003', 'EMP006', 'EMP009') THEN 'High'
        ELSE 'Moderate'
    END AS category,
    'Completed' AS status
FROM employees e
CROSS JOIN performance_periods p
WHERE p.status = 'Active'
AND NOT EXISTS (
    SELECT 1 FROM assessments a
    WHERE a.employee_id = e.employee_id
    AND a.period_id = p.period_id
);

-- 8. Create performance records for each employee (idempotent)
-- NO unique constraint on employee_id, so use WHERE NOT EXISTS + UPDATE separately
-- First, insert new records
INSERT INTO performance_records (employee_id, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category, review_date)
SELECT
    e.employee_id,
    85 + (e.employee_id % 10)::NUMERIC,  -- attendance 85-94
    80 + (e.employee_id % 7 + 1)::NUMERIC,  -- task completion 81-87
    20 + (e.employee_id % 5 + 1)::NUMERIC,  -- training hours 21-25
    3.0 + (e.employee_id % 3)::NUMERIC * 0.3,  -- previous performance 3.0-3.3
    CASE WHEN e.employee_id % 3 = 0 THEN 'High' WHEN e.employee_id % 3 = 1 THEN 'Moderate' ELSE 'Needs Support' END,
    CURRENT_DATE - INTERVAL '30 days'
FROM employees e
WHERE NOT EXISTS (
    SELECT 1 FROM performance_records pr WHERE pr.employee_id = e.employee_id
);

-- Then update existing records
UPDATE performance_records pr
SET
    attendance_rate = 85 + (pr.employee_id % 10)::NUMERIC,
    task_completion_rate = 80 + (pr.employee_id % 7 + 1)::NUMERIC,
    training_hours = 20 + (pr.employee_id % 5 + 1)::NUMERIC,
    previous_performance = 3.0 + (pr.employee_id % 3)::NUMERIC * 0.3,
    performance_category = CASE WHEN pr.employee_id % 3 = 0 THEN 'High' WHEN pr.employee_id % 3 = 1 THEN 'Moderate' ELSE 'Needs Support' END,
    review_date = CURRENT_DATE - INTERVAL '30 days'
WHERE EXISTS (
    SELECT 1 FROM employees e WHERE e.employee_id = pr.employee_id
);

-- 9. Create notifications for admin (idempotent)
-- NO unique constraint, so check manually
INSERT INTO notifications (title, message, employee_id)
SELECT DISTINCT ON (e.employee_id)
    'Welcome back, Admin!',
    'You have ' || (SELECT COUNT(*) FROM employees WHERE data_origin = 'demo') || ' employees in your workspace and ' || (SELECT COUNT(*) FROM performance_periods WHERE status = 'Active') || ' active review cycles.',
    e.employee_id
FROM employees e
CROSS JOIN performance_periods p
WHERE p.status = 'Active'
AND NOT EXISTS (
    SELECT 1 FROM notifications n
    WHERE n.title = 'Welcome back, Admin!'
    AND n.employee_id = e.employee_id
);

-- 10. Verify the data is accessible (diagnostic)
SELECT '--- Employee Count ---' AS info;
SELECT COUNT(*) AS total_employees FROM employees WHERE data_origin = 'demo';

SELECT '--- Active Periods ---' AS info;
SELECT COUNT(*) AS active_periods FROM performance_periods WHERE status = 'Active';

SELECT '--- Assessments Count ---' AS info;
SELECT COUNT(*) AS total_assessments FROM assessments;

SELECT '--- Sample Employees ---' AS info;
SELECT employee_id, employee_name, employee_code, department, data_origin, status FROM employees LIMIT 5;

-- Done
SELECT 'Restore complete!' AS status;