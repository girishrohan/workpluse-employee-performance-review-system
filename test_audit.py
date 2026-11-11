#!/usr/bin/env python
"""
Comprehensive functionality audit for WorkPulse Employee Performance Review System.
Tests: Authentication, Employee Management, HR Functions, Performance Management,
Machine Learning, Dashboard, Database, Reports, Navigation, Security.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import pandas as pd
import bcrypt
import json

# Test results storage
test_results = {
    "passed": [],
    "failed": [],
    "errors": []
}

def test(name, func):
    """Run a test and record results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)
    try:
        result = func()
        if result:
            test_results["passed"].append(name)
            print("PASSED")
            return True
        else:
            test_results["failed"].append(name)
            print("FAILED")
            return False
    except Exception as e:
        test_results["errors"].append((name, str(e)))
        print(f"ERROR: {e}")
        return False

# ============================================================================
# 1. DATABASE CONNECTIVITY & BASIC OPERATIONS
# ============================================================================

def test_database_connection():
    """Test database connection and basic queries."""
    from database.db_manager import get_db_connection, resolve_db_path

    db_path = resolve_db_path()
    conn = get_db_connection(db_path)

    # Test basic query
    cursor = conn.execute("SELECT COUNT(*) as cnt FROM employees")
    count = cursor.fetchone()["cnt"]
    conn.close()

    assert count > 0, f"Expected employees to exist, found {count}"
    print(f"  Database connected, {count} employees found")
    return True

def test_database_tables():
    """Test all required tables exist."""
    conn = sqlite3.connect('data/workpulse.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    required = ['employees', 'assessments', 'users', 'performance_periods',
                'performance_areas', 'notifications', 'app_settings', 'login_attempts']

    missing = [t for t in required if t not in tables]
    if missing:
        print(f"  Missing tables: {missing}")
        return False

    print(f"  All {len(required)} required tables present")
    return True

# ============================================================================
# 2. AUTHENTICATION TESTS
# ============================================================================

def test_user_credentials_exist():
    """Test that default users exist with valid credentials."""
    from auth.auth_service import get_user_by_email

    users = [
        ('admin@workpulse.local', 'admin'),
        ('hr@workpulse.local', 'hr'),
        ('employee@workpulse.local', 'employee'),
    ]

    for email, expected_role in users:
        user = get_user_by_email(email)
        if not user:
            print(f"  User {email} not found")
            return False
        if user.get('role') != expected_role:
            print(f"  User {email} has wrong role: {user.get('role')}")
            return False
        print(f"  User {email} exists with role {expected_role}")

    return True

def test_authenticate_admin():
    """Test admin login with valid credentials."""
    from auth.auth_service import authenticate_user

    user = authenticate_user('admin@workpulse.local', 'Admin@WorkPulse2024')

    if not user:
        print("  Admin authentication failed")
        return False

    if user.get('role') != 'admin':
        print(f"  Wrong role: {user.get('role')}")
        return False

    print(f"  Admin authenticated: {user.get('email')}")
    return True

def test_authenticate_hr():
    """Test HR login with valid credentials."""
    from auth.auth_service import authenticate_user

    user = authenticate_user('hr@workpulse.local', 'Hr@WorkPulse2024')

    if not user:
        print("  HR authentication failed")
        return False

    if user.get('role') != 'hr':
        print(f"  Wrong role: {user.get('role')}")
        return False

    print(f"  HR authenticated: {user.get('email')}")
    return True

def test_authenticate_employee():
    """Test employee login with valid credentials."""
    from auth.auth_service import authenticate_user

    user = authenticate_user('employee@workpulse.local', 'Emp@WorkPulse2024')

    if not user:
        print("  Employee authentication failed")
        return False

    if user.get('role') != 'employee':
        print(f"  Wrong role: {user.get('role')}")
        return False

    print(f"  Employee authenticated: {user.get('email')}")
    return True

def test_invalid_credentials():
    """Test login with invalid credentials."""
    from auth.auth_service import authenticate_user

    # Wrong password
    user = authenticate_user('admin@workpulse.local', 'wrongpassword')
    if user is not None:
        print("  Wrong password should fail")
        return False
    print("  Wrong password correctly rejected")

    # Non-existent user
    user = authenticate_user('nonexistent@workpulse.local', 'anypassword')
    if user is not None:
        print("  Non-existent user should fail")
        return False
    print("  Non-existent user correctly rejected")

    return True

def test_password_verification():
    """Test bcrypt password hashing."""
    from auth.auth_service import hash_password, verify_password

    password = "TestPassword123!"
    hashed = hash_password(password)

    if not hashed.startswith('$2b$'):
        print("  Hash should start with $2b$")
        return False

    if not verify_password(password, hashed):
        print("  Correct password should verify")
        return False

    if verify_password("wrongpassword", hashed):
        print("  Wrong password should not verify")
        return False

    print("  Password hashing and verification working correctly")
    return True

# ============================================================================
# 3. EMPLOYEE MANAGEMENT TESTS
# ============================================================================

def test_get_employees():
    """Test fetching employees."""
    from services.workpulse_service import get_employees

    df = get_employees()
    if df.empty:
        print("  No employees found")
        return True  # Not necessarily an error, just empty DB

    required_cols = ['employee_code', 'employee_name', 'department', 'status']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"  Missing columns: {missing}")
        return False

    print(f"  {len(df)} employees fetched with correct columns")
    return True

def test_create_employee():
    """Test creating a new employee."""
    from services.workpulse_service import create_employee

    # Try to create an employee
    try:
        emp_id = create_employee(
            employee_code='TEST-EMP-001',
            employee_name='Test Employee Name',
            department='Engineering',
            designation='Test Engineer',
            joining_date='2024-01-01',
            status='Active',
            experience_years=2.0
        )
        print(f"  Created employee with ID: {emp_id}")
        return True
    except Exception as e:
        # Employee might already exist
        if 'UNIQUE constraint' in str(e) or 'duplicate' in str(e).lower():
            print("  Employee already exists (expected on re-run)")
            return True
        print(f"  Error creating employee: {e}")
        return False

def test_update_employee():
    """Test updating employee details."""
    from services.workpulse_service import get_employees, update_employee_profile

    df = get_employees()
    if df.empty:
        print("  No employees to update")
        return True

    emp = df.iloc[0]
    emp_id = emp['employee_id']

    # Get joining_date safely
    joining_date = emp.get('joining_date', '2024-01-01')
    if joining_date is None or pd.isna(joining_date):
        joining_date = '2024-01-01'
    else:
        joining_date = str(joining_date)[:10]  # Extract date part

    try:
        update_employee_profile(
            employee_id=emp_id,
            employee_code=str(emp['employee_code']),
            employee_name=f"{emp['employee_name']} Updated",
            department=str(emp['department']),
            designation=str(emp.get('designation', 'Engineer')),
            joining_date=joining_date,
            status=str(emp.get('status', 'Active')),
            experience_years=float(emp.get('experience_years', 1.0))
        )
        print(f"  Updated employee {emp_id}")
        return True
    except Exception as e:
        print(f"  Error updating employee: {e}")
        return False

# ============================================================================
# 4. PERFORMANCE MANAGEMENT TESTS
# ============================================================================

def test_performance_periods():
    """Test performance period operations."""
    from services.workpulse_service import get_periods, save_period, delete_period

    periods = get_periods()
    print(f"  Found {len(periods)} performance periods")

    # Check that periods have active status
    if not periods.empty:
        if 'status' not in periods.columns:
            print("  Missing 'status' column in periods")
            return False
        print(f"  Period statuses: {periods['status'].unique().tolist()}")

    return True

def test_assessments():
    """Test assessment operations."""
    from services.workpulse_service import get_assessments, get_dashboard_summary

    assessments = get_assessments()
    summary = get_dashboard_summary()

    print(f"  {len(assessments)} assessments found")
    print(f"  Summary: {summary}")

    if not assessments.empty:
        required_cols = ['employee_id', 'overall_score', 'reviewer', 'period_id']
        missing = [c for c in required_cols if c not in assessments.columns]
        if missing:
            print(f"  Missing columns: {missing}")
            return False

        # Check score range
        scores = assessments['overall_score']
        if scores.min() < 0 or scores.max() > 100:
            print(f"  Scores out of range: {scores.min()} to {scores.max()}")
            return False

    return True

def test_score_calculation():
    """Test weighted score calculation."""
    from services.workpulse_service import get_areas, save_assessment, get_assessments

    areas = get_areas()
    if areas.empty:
        print("  No performance areas configured")
        return True

    # Check weights sum to 100
    active_areas = areas[areas['active'] == 1]
    if not active_areas.empty:
        weight_sum = active_areas['weight'].sum()
        if abs(weight_sum - 100) > 0.01:
            print(f"  Weights don't sum to 100: {weight_sum}")
            return False
        print(f"  Active weights sum to: {weight_sum}")

    return True

# ============================================================================
# 5. MACHINE LEARNING TESTS
# ============================================================================

def test_ml_model_files():
    """Test that ML model files exist."""
    import os

    model_files = [
        'models/decision_tree.pkl',
        'models/random_forest.pkl'
    ]

    for f in model_files:
        if not os.path.exists(f):
            print(f"  Missing model file: {f}")
            return False
        size = os.path.getsize(f)
        print(f"  {f}: {size} bytes")

    return True

def test_ml_model_loading():
    """Test loading ML models."""
    import joblib

    try:
        dt_model = joblib.load('models/decision_tree.pkl')
        rf_model = joblib.load('models/random_forest.pkl')
        print("  Models loaded successfully")
        return True
    except Exception as e:
        print(f"  Error loading models: {e}")
        return False

def test_ml_prediction_pipeline():
    """Test prediction pipeline functionality."""
    from models.train_model import FeaturePreprocessor, TARGET_CLASSES

    try:
        preprocessor = FeaturePreprocessor()

        # Test that preprocessor has expected attributes
        assert hasattr(preprocessor, 'num_cols') or hasattr(preprocessor, 'transform'), \
            "Preprocessor missing expected methods"

        print("  Prediction pipeline structure validated")
        return True
    except Exception as e:
        print(f"  Error in prediction pipeline: {e}")
        return False

def test_ml_input_validation():
    """Test ML input validation."""
    from models.train_model import FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL

    expected_numeric = ['attendance_rate', 'task_completion_rate', 'training_hours',
                        'experience_years', 'previous_performance']
    expected_categorical = ['department']

    for col in expected_numeric:
        if col not in FEATURE_COLS_NUMERIC:
            print(f"  Missing numeric feature: {col}")
            return False

    for col in expected_categorical:
        if col not in FEATURE_COLS_CATEGORICAL:
            print(f"  Missing categorical feature: {col}")
            return False

    print(f"  Numeric features: {FEATURE_COLS_NUMERIC}")
    print(f"  Categorical features: {FEATURE_COLS_CATEGORICAL}")
    return True

# ============================================================================
# 6. DASHBOARD TESTS
# ============================================================================

def test_dashboard_summary():
    """Test dashboard summary calculation."""
    from services.workpulse_service import get_dashboard_summary

    summary = get_dashboard_summary()

    required_keys = ['total_employees', 'completed_assessments', 'active_periods',
                     'performance_areas', 'demo_employees']

    for key in required_keys:
        if key not in summary:
            print(f"  Missing summary key: {key}")
            return False
        if not isinstance(summary[key], (int, float)):
            print(f"  Summary {key} is not numeric: {type(summary[key])}")
            return False

    print(f"  Dashboard summary: {summary}")
    return True

def test_employee_data_integrity():
    """Test employee data integrity."""
    from services.workpulse_service import get_employees

    df = get_employees()
    if df.empty:
        print("  No employees to validate")
        return True

    issues = []

    # Check for unique employee codes
    duplicates = df[df.duplicated(subset=['employee_code'], keep=False)]
    if not duplicates.empty:
        issues.append(f"Duplicate employee codes: {duplicates['employee_code'].tolist()}")

    # Check for null employee codes or names
    null_codes = df['employee_code'].isna().sum()
    null_names = df['employee_name'].isna().sum()

    if null_codes > 0:
        issues.append(f"NULL employee codes: {null_codes}")
    if null_names > 0:
        issues.append(f"NULL employee names: {null_names}")

    if issues:
        for issue in issues:
            print(f"  {issue}")
        return False

    print(f"  Employee data integrity verified ({len(df)} employees)")
    return True

# ============================================================================
# 7. DATABASE RELATIONSHIPS & CONSTRAINTS
# ============================================================================

def test_foreign_key_constraints():
    """Test database foreign key constraints."""
    conn = sqlite3.connect('data/workpulse.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check that assessments reference valid employees
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM assessments a
        LEFT JOIN employees e ON a.employee_id = e.employee_id
        WHERE e.employee_id IS NULL
    """)
    orphan_assessments = cursor.fetchone()['cnt']

    conn.close()

    if orphan_assessments > 0:
        print(f"  Found {orphan_assessments} orphan assessments")
        return False

    print("  No orphan assessments found")
    return True

def test_notification_system():
    """Test notification system."""
    from services.workpulse_service import get_notifications

    notifications = get_notifications()
    print(f"  {len(notifications)} notifications found")

    # Check for read_at column
    if 'read_at' in notifications.columns:
        unread = notifications['read_at'].isna().sum()
        print(f"  Unread notifications: {unread}")

    return True

# ============================================================================
# 8. SETTINGS & CONFIGURATION
# ============================================================================

def test_settings_operations():
    """Test settings save/load."""
    from services.workpulse_service import get_settings, save_settings

    # Get current settings
    settings = get_settings()
    print(f"  Current settings: {settings}")

    # Test saving settings
    try:
        save_settings({
            'admin_name': 'Test Admin',
            'workspace_name': 'Test Workspace'
        })
        print("  Settings saved successfully")
        return True
    except Exception as e:
        print(f"  Error saving settings: {e}")
        return False

# ============================================================================
# 9. DATA CONSISTENCY TESTS
# ============================================================================

def test_assessment_department_consistency():
    """Test that assessments have valid department references."""
    conn = sqlite3.connect('data/workpulse.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check assessments that join with employees
    cursor.execute("""
        SELECT a.assessment_id, a.employee_id, e.department
        FROM assessments a
        JOIN employees e ON a.employee_id = e.employee_id
        LIMIT 10
    """)
    results = cursor.fetchall()
    conn.close()

    for row in results:
        print(f"  Assessment {row['assessment_id']}: employee {row['employee_id']} in {row['department']}")

    return len(results) > 0

def test_performance_categories():
    """Test performance category classification."""
    from services.workpulse_service import get_assessments

    assessments = get_assessments()
    if assessments.empty:
        print("  No assessments to check")
        return True

    valid_categories = {'High', 'Moderate', 'Needs Support'}

    # Handle both Series and list
    cat_column = assessments.get('category')
    if cat_column is None:
        print("  No category column found")
        return True

    if hasattr(cat_column, 'unique'):
        categories = set(cat_column.unique())
    else:
        categories = set(list(cat_column))

    invalid = categories - valid_categories
    if invalid:
        print(f"  Invalid categories found: {invalid}")
        return False

    print(f"  Valid categories: {categories}")
    return True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("WORKPULSE FUNCTIONALITY AUDIT")
    print("="*60)

    # Run all tests
    tests = [
        # Database Tests
        ("Database Connection", test_database_connection),
        ("Database Tables", test_database_tables),

        # Authentication Tests
        ("User Credentials Exist", test_user_credentials_exist),
        ("Admin Authentication", test_authenticate_admin),
        ("HR Authentication", test_authenticate_hr),
        ("Employee Authentication", test_authenticate_employee),
        ("Invalid Credentials Rejection", test_invalid_credentials),
        ("Password Verification", test_password_verification),

        # Employee Management Tests
        ("Get Employees", test_get_employees),
        ("Create Employee", test_create_employee),
        ("Update Employee", test_update_employee),

        # Performance Management Tests
        ("Performance Periods", test_performance_periods),
        ("Assessments", test_assessments),
        ("Score Calculation", test_score_calculation),

        # ML Tests
        ("ML Model Files", test_ml_model_files),
        ("ML Model Loading", test_ml_model_loading),
        ("ML Prediction Pipeline", test_ml_prediction_pipeline),
        ("ML Input Validation", test_ml_input_validation),

        # Dashboard Tests
        ("Dashboard Summary", test_dashboard_summary),
        ("Employee Data Integrity", test_employee_data_integrity),

        # Database Relationship Tests
        ("Foreign Key Constraints", test_foreign_key_constraints),
        ("Notification System", test_notification_system),

        # Settings Tests
        ("Settings Operations", test_settings_operations),

        # Data Consistency Tests
        ("Assessment Department Consistency", test_assessment_department_consistency),
        ("Performance Categories", test_performance_categories),
    ]

    passed = 0
    failed = 0
    errors = 0

    for name, func in tests:
        result = test(name, func)
        if result:
            passed += 1
        else:
            failed += 1

    # Print summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"ERRORS: {len(test_results['errors'])}")

    if test_results['errors']:
        print("\nERRORS:")
        for name, error in test_results['errors']:
            print(f"  {name}: {error}")

    if test_results['failed']:
        print("\nFAILED TESTS:")
        for name in test_results['failed']:
            print(f"  {name}")

    print("\n" + "="*60)
    sys.exit(0 if failed == 0 and len(test_results['errors']) == 0 else 1)