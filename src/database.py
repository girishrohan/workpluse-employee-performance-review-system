"""
Employee Performance Analytics - Database Manager
Handles SQLite database connection, table initialization, and CRUD operations for the 5 schema tables.
"""

import os
import json
import sqlite3
import pandas as pd

DB_PATH = "data/employee_performance_db.sqlite"
SCHEMA_SQL_PATH = "sql/schema.sql"


def get_connection(db_path=DB_PATH):
    """Returns a SQLite connection object with foreign keys enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=DB_PATH, schema_path=SCHEMA_SQL_PATH):
    """Initializes SQLite database tables using sql/schema.sql."""
    conn = get_connection(db_path)
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        conn.executescript(sql_script)
    conn.commit()
    conn.close()


def populate_db_from_df(df, db_path=DB_PATH):
    """Populates 'employees' and 'performance_records' tables from a DataFrame."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        emp_code = row['employee_id']
        dept = row['department']
        exp = float(row['experience_years'])

        # Insert or ignore employee
        cursor.execute(
            """
            INSERT OR IGNORE INTO employees (employee_code, department, experience_years)
            VALUES (?, ?, ?)
            """,
            (emp_code, dept, exp)
        )

        cursor.execute("SELECT employee_id FROM employees WHERE employee_code = ?", (emp_code,))
        emp_id = cursor.fetchone()[0]

        att = float(row['attendance_rate'])
        tc = float(row['task_completion_rate'])
        train = float(row['training_hours'])
        prev_perf = str(row['previous_performance'])
        cat = str(row['performance_category'])

        # Insert performance record
        cursor.execute(
            """
            INSERT INTO performance_records
            (employee_id, attendance_rate, task_completion_rate, training_hours, previous_performance, performance_category)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (emp_id, att, tc, train, prev_perf, cat)
        )

    conn.commit()
    conn.close()


def log_model_metadata(model_name, version, algorithm, metrics_dict, model_path, db_path=DB_PATH):
    """Logs model version, algorithm, and metrics JSON to 'ml_models' table."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    metrics_json = json.dumps(metrics_dict)
    cursor.execute(
        """
        INSERT OR REPLACE INTO ml_models
        (model_name, model_version, algorithm, evaluation_metrics, model_file_path, model_status)
        VALUES (?, ?, ?, ?, ?, 'Active')
        """,
        (model_name, version, algorithm, metrics_json, model_path)
    )
    model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return model_id


def log_prediction(emp_code, model_name, predicted_cat, feature_snapshot, probability, explanations_list=None, db_path=DB_PATH):
    """Logs a single prediction and its local feature explanations to SQL database."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Get employee_id if available
    emp_id = None
    if emp_code:
        cursor.execute("SELECT employee_id FROM employees WHERE employee_code = ?", (emp_code,))
        res = cursor.fetchone()
        if res:
            emp_id = res[0]

    # Get model_id
    cursor.execute("SELECT model_id FROM ml_models WHERE model_name = ? ORDER BY model_id DESC LIMIT 1", (model_name,))
    m_res = cursor.fetchone()
    model_id = m_res[0] if m_res else 1

    feature_json = json.dumps(feature_snapshot)
    cursor.execute(
        """
        INSERT INTO predictions (employee_id, model_id, predicted_category, feature_snapshot, prediction_probability)
        VALUES (?, ?, ?, ?, ?)
        """,
        (emp_id, model_id, predicted_cat, feature_json, float(probability))
    )
    pred_id = cursor.lastrowid

    # Insert explanations if provided
    if explanations_list:
        for item in explanations_list:
            feat_name = item.get('Feature', '')
            val = float(item.get('Impact_Score', 0.0))
            text = f"Impact of {val:+.2f} relative to benchmark."
            cursor.execute(
                """
                INSERT INTO prediction_explanations (prediction_id, feature_name, contribution_value, explanation_text)
                VALUES (?, ?, ?, ?)
                """,
                (pred_id, feat_name, val, text)
            )

    conn.commit()
    conn.close()
    return pred_id


def get_prediction_history(db_path=DB_PATH):
    """Queries prediction logs joined with employee codes and model names."""
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
        SELECT
            p.prediction_id,
            COALESCE(e.employee_code, 'Custom Input') AS employee_code,
            m.model_name,
            p.predicted_category,
            p.prediction_probability,
            p.created_at
        FROM predictions p
        LEFT JOIN employees e ON p.employee_id = e.employee_id
        JOIN ml_models m ON p.model_id = m.model_id
        ORDER BY p.created_at DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", DB_PATH)
