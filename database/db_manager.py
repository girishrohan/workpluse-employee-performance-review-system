"""
WorkPulse - Database Manager (SQLite)
Handles database initialization, schema creation, and parameterized CRUD operations.
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join("data", "workpulse.db")


def get_db_connection(db_path=DB_PATH):
    """Establishes an SQLite connection with row factories and foreign keys enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    """Initializes the normalized SQLite database schema for WorkPulse."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Employees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code VARCHAR(30) UNIQUE NOT NULL,
        employee_name VARCHAR(100) NOT NULL,
        department VARCHAR(50) NOT NULL,
        experience_years REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Performance Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        attendance_rate REAL NOT NULL,
        task_completion_rate REAL NOT NULL,
        training_hours REAL NOT NULL,
        previous_performance REAL NOT NULL,
        performance_category VARCHAR(20) NOT NULL,
        review_date DATE NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
    );
    """)

    # 3. Model Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_runs (
        model_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name VARCHAR(50) NOT NULL,
        model_version VARCHAR(20) NOT NULL,
        training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        evaluation_metrics TEXT,
        model_status VARCHAR(20) DEFAULT 'Active'
    );
    """)

    # 4. Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        model_id INTEGER NOT NULL,
        predicted_category VARCHAR(20) NOT NULL,
        prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        feature_snapshot TEXT,
        explanation_summary TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
        FOREIGN KEY (model_id) REFERENCES model_runs(model_id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()


def get_all_employees(db_path=DB_PATH):
    """Returns a DataFrame containing all employees and their latest performance record."""
    conn = get_db_connection(db_path)
    query = """
    SELECT 
        e.employee_id,
        e.employee_code,
        e.employee_name,
        e.department,
        e.experience_years,
        pr.attendance_rate,
        pr.task_completion_rate,
        pr.training_hours,
        pr.previous_performance,
        pr.performance_category,
        pr.review_date,
        e.created_at
    FROM employees e
    LEFT JOIN performance_records pr ON pr.record_id = (
        SELECT record_id FROM performance_records 
        WHERE employee_id = e.employee_id 
        ORDER BY review_date DESC, record_id DESC LIMIT 1
    )
    ORDER BY e.employee_id DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def add_employee(employee_code, employee_name, department, experience_years,
                 attendance_rate, task_completion_rate, training_hours,
                 previous_performance, performance_category, review_date, db_path=DB_PATH):
    """Inserts a new employee and initial performance record. Rejects duplicate employee_code."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT employee_id FROM employees WHERE employee_code = ?", (employee_code,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"An employee with code '{employee_code}' already exists.")

    try:
        cursor.execute("""
        INSERT INTO employees (employee_code, employee_name, department, experience_years)
        VALUES (?, ?, ?, ?);
        """, (employee_code, employee_name, department, float(experience_years)))
        emp_id = cursor.lastrowid

        cursor.execute("""
        INSERT INTO performance_records 
        (employee_id, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category, review_date)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (emp_id, float(attendance_rate), float(task_completion_rate), float(training_hours),
              float(previous_performance), performance_category, str(review_date)))

        conn.commit()
        return emp_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_employee(employee_id, employee_name, department, experience_years,
                    attendance_rate, task_completion_rate, training_hours,
                    previous_performance, performance_category, review_date, db_path=DB_PATH):
    """Updates employee details and their latest performance record."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE employees 
        SET employee_name = ?, department = ?, experience_years = ?
        WHERE employee_id = ?;
        """, (employee_name, department, float(experience_years), int(employee_id)))

        cursor.execute("""
        SELECT record_id FROM performance_records 
        WHERE employee_id = ? ORDER BY review_date DESC, record_id DESC LIMIT 1;
        """, (int(employee_id),))
        row = cursor.fetchone()

        if row:
            cursor.execute("""
            UPDATE performance_records
            SET attendance_rate = ?, task_completion_rate = ?, training_hours = ?,
                previous_performance = ?, performance_category = ?, review_date = ?
            WHERE record_id = ?;
            """, (float(attendance_rate), float(task_completion_rate), float(training_hours),
                  float(previous_performance), performance_category, str(review_date), row['record_id']))
        else:
            cursor.execute("""
            INSERT INTO performance_records 
            (employee_id, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category, review_date)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (int(employee_id), float(attendance_rate), float(task_completion_rate), float(training_hours),
                  float(previous_performance), performance_category, str(review_date)))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_employee(employee_id, db_path=DB_PATH):
    """Deletes an employee and cascade deletes associated performance records."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM employees WHERE employee_id = ?;", (int(employee_id),))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_employee_history(employee_id, db_path=DB_PATH):
    """Returns chronological performance records for a specific employee."""
    conn = get_db_connection(db_path)
    query = """
    SELECT 
        pr.record_id,
        pr.review_date,
        pr.attendance_rate,
        pr.task_completion_rate,
        pr.training_hours,
        pr.previous_performance,
        pr.performance_category
    FROM performance_records pr
    WHERE pr.employee_id = ?
    ORDER BY pr.review_date ASC;
    """
    df = pd.read_sql_query(query, conn, params=(int(employee_id),))
    conn.close()
    return df


def import_records_from_df(df, db_path=DB_PATH):
    """Imports employee records from DataFrame into the database. Returns count of inserted & skipped."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    inserted_count = 0
    skipped_count = 0

    for _, row in df.iterrows():
        emp_code = str(row['employee_code']).strip()
        emp_name = str(row.get('employee_name', f"Employee {emp_code}")).strip()
        dept = str(row['department']).strip()
        exp = float(row.get('experience_years', 1.0))
        att = float(row['attendance_rate'])
        tc = float(row['task_completion_rate'])
        th = float(row.get('training_hours', 10.0))
        prev = float(row.get('previous_performance', 3.0))
        cat = str(row['performance_category']).strip()
        rdate = str(row.get('review_date', datetime.now().strftime('%Y-%m-%d'))).strip()

        cursor.execute("SELECT employee_id FROM employees WHERE employee_code = ?", (emp_code,))
        existing = cursor.fetchone()

        if existing:
            emp_id = existing['employee_id']
            cursor.execute("""
            INSERT INTO performance_records 
            (employee_id, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category, review_date)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (emp_id, att, tc, th, prev, cat, rdate))
            skipped_count += 1
        else:
            cursor.execute("""
            INSERT INTO employees (employee_code, employee_name, department, experience_years)
            VALUES (?, ?, ?, ?);
            """, (emp_code, emp_name, dept, exp))
            emp_id = cursor.lastrowid

            cursor.execute("""
            INSERT INTO performance_records 
            (employee_id, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category, review_date)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (emp_id, att, tc, th, prev, cat, rdate))
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count, skipped_count


def log_model_run(model_name, model_version, metrics_dict, status="Active", db_path=DB_PATH):
    """Logs a model training run and evaluation metrics."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO model_runs (model_name, model_version, evaluation_metrics, model_status)
    VALUES (?, ?, ?, ?);
    """, (model_name, model_version, json.dumps(metrics_dict), status))
    model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return model_id


def log_prediction(model_id, predicted_category, feature_snapshot, explanation_summary, employee_id=None, db_path=DB_PATH):
    """Logs an experimental performance prediction, ensuring model_id exists."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Guarantee valid model_id in model_runs
    cursor.execute("SELECT model_id FROM model_runs WHERE model_id = ?", (model_id,))
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO model_runs (model_name, model_version, evaluation_metrics, model_status)
        VALUES (?, ?, ?, ?);
        """, ("Active Classifier", "1.0.0", "{}", "Active"))
        model_id = cursor.lastrowid

    # If employee_id is passed, verify existence in employees table
    if employee_id is not None:
        cursor.execute("SELECT employee_id FROM employees WHERE employee_id = ?", (employee_id,))
        if not cursor.fetchone():
            employee_id = None

    cursor.execute("""
    INSERT INTO predictions 
    (employee_id, model_id, predicted_category, feature_snapshot, explanation_summary)
    VALUES (?, ?, ?, ?, ?);
    """, (employee_id, model_id, predicted_category, json.dumps(feature_snapshot), explanation_summary))
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id


def get_predictions_history(db_path=DB_PATH):
    """Retrieves logged predictions with model details."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    query = """
    SELECT 
        p.prediction_id,
        COALESCE(e.employee_code, 'Direct Query') AS employee_code,
        COALESCE(e.employee_name, 'Ad-hoc Assessment') AS employee_name,
        mr.model_name,
        p.predicted_category,
        p.prediction_timestamp,
        p.explanation_summary
    FROM predictions p
    LEFT JOIN employees e ON p.employee_id = e.employee_id
    JOIN model_runs mr ON p.model_id = mr.model_id
    ORDER BY p.prediction_timestamp DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
