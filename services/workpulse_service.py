"""Persistent database operations for the WorkPulse review workflow."""

import json
import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any

import pandas as pd

from database.db_manager import get_db_connection, init_db

DB_PATH = os.path.join("data", "workpulse.db")

DEFAULT_AREAS = (
    ("Attendance", "Reliability and attendance over the review period.", 20),
    ("Task completion", "Delivery of agreed work and responsibilities.", 25),
    ("Productivity", "Quality and consistency of work output.", 25),
    ("Teamwork", "Collaboration and communication with colleagues.", 15),
    ("Learning and development", "Engagement with training and skill development.", 15),
)


@lru_cache(maxsize=8)
def initialize_database(db_path: str = DB_PATH) -> None:
    """Initialize the original WorkPulse schema and migrate in the new workflow."""
    init_db(db_path)
    with closing(get_db_connection(db_path)) as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(employees)").fetchall()
        }
        migrations = {
            "designation": "TEXT NOT NULL DEFAULT ''",
            "joining_date": "TEXT NOT NULL DEFAULT ''",
            "status": "TEXT NOT NULL DEFAULT 'Active'",
            "data_origin": "TEXT NOT NULL DEFAULT 'user'",
        }
        for name, definition in migrations.items():
            if name not in columns:
                connection.execute(
                    f"ALTER TABLE employees ADD COLUMN {name} {definition}"
                )

        connection.executescript(
            """
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
                category TEXT NOT NULL DEFAULT 'Moderate',
                comments TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Completed',
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
            """
        )
        area_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(performance_areas)")
        }
        if "active" not in area_columns:
            connection.execute(
                "ALTER TABLE performance_areas ADD COLUMN active INTEGER NOT NULL DEFAULT 1"
            )
            if "is_active" in area_columns:
                connection.execute(
                    "UPDATE performance_areas SET active = is_active"
                )

        period_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(performance_periods)")
        }
        if "name" not in period_columns:
            connection.execute("ALTER TABLE performance_periods ADD COLUMN name TEXT")
        if "title" in period_columns:
            connection.execute(
                "UPDATE performance_periods SET name = title WHERE name IS NULL OR name = ''"
            )
        legacy_period_schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'performance_periods'"
        ).fetchone()[0]
        if "'Planned'" in legacy_period_schema and "'Draft'" not in legacy_period_schema:
            connection.execute(
                "UPDATE performance_periods SET status = 'Planned' WHERE status = 'Draft'"
            )

        _migrate_legacy_assessments(connection)
        assessment_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(assessments)")
        }
        for name, definition in (
            ("category", "TEXT NOT NULL DEFAULT 'Moderate'"),
            ("status", "TEXT NOT NULL DEFAULT 'Completed'"),
        ):
            if name not in assessment_columns:
                connection.execute(
                    f"ALTER TABLE assessments ADD COLUMN {name} {definition}"
                )

        notification_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(notifications)")
        }
        if "read_at" not in notification_columns:
            connection.execute("ALTER TABLE notifications ADD COLUMN read_at TEXT")
        if "is_read" in notification_columns:
            connection.execute(
                "UPDATE notifications SET read_at = created_at "
                "WHERE is_read = 1 AND read_at IS NULL"
            )

        area_count = connection.execute(
            "SELECT COUNT(*) FROM performance_areas"
        ).fetchone()[0]
        if area_count == 0:
            connection.executemany(
                """
                INSERT INTO performance_areas (name, description, weight)
                VALUES (?, ?, ?)
                """,
                DEFAULT_AREAS,
            )
        active_areas = connection.execute(
            "SELECT area_id, weight FROM performance_areas WHERE active = 1 ORDER BY area_id"
        ).fetchall()
        active_weight_total = sum(float(row["weight"]) for row in active_areas)
        if active_areas and active_weight_total > 0 and abs(active_weight_total - 100) > 0.01:
            normalized_weights = [
                (round(float(row["weight"]) * 100 / active_weight_total, 2), int(row["area_id"]))
                for row in active_areas
            ]
            normalized_weights[-1] = (
                round(100 - sum(weight for weight, _ in normalized_weights[:-1]), 2),
                normalized_weights[-1][1],
            )
            connection.executemany(
                "UPDATE performance_areas SET weight = ? WHERE area_id = ?",
                normalized_weights,
            )
        connection.commit()


def _migrate_legacy_assessments(connection: sqlite3.Connection) -> None:
    table = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'assessments'"
    ).fetchone()
    if table is None:
        return
    compact_sql = "".join(table["sql"].lower().split())
    if "overall_scorebetween1and5" not in compact_sql:
        return

    legacy_rows = connection.execute("SELECT * FROM assessments").fetchall()
    legacy_columns = {row["name"] for row in connection.execute("PRAGMA table_info(assessments)")}
    connection.execute("DROP INDEX IF EXISTS idx_assessments_employee_date")
    connection.execute("DROP INDEX IF EXISTS idx_assessments_period")
    connection.execute("ALTER TABLE assessments RENAME TO assessments_legacy")
    connection.execute(
        """
        CREATE TABLE assessments (
            assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            period_id INTEGER,
            assessment_date TEXT NOT NULL,
            reviewer TEXT NOT NULL,
            scores_json TEXT NOT NULL,
            overall_score REAL NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
            category TEXT NOT NULL DEFAULT 'Moderate',
            comments TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Completed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
            FOREIGN KEY (period_id) REFERENCES performance_periods(period_id) ON DELETE SET NULL
        )
        """
    )
    for row in legacy_rows:
        old_score = float(row["overall_score"])
        score = old_score * 20 if old_score <= 5 else old_score
        scores = _migrate_legacy_scores(row["scores_json"])
        assessment_category = _category_for_score(score)
        connection.execute(
            """
            INSERT INTO assessments
                (assessment_id, employee_id, period_id, assessment_date, reviewer,
                 scores_json, overall_score, category, comments, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["assessment_id"],
                row["employee_id"],
                row["period_id"] if "period_id" in legacy_columns else None,
                row["assessment_date"],
                row["reviewer"],
                json.dumps(scores, sort_keys=True),
                min(100, max(0, score)),
                assessment_category,
                row["comments"] if "comments" in legacy_columns else "",
                row["status"] if "status" in legacy_columns else "Completed",
                row["created_at"] if "created_at" in legacy_columns else datetime.now().isoformat(),
            ),
        )
    connection.execute("DROP TABLE assessments_legacy")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_assessments_employee_date "
        "ON assessments(employee_id, assessment_date DESC)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_assessments_period ON assessments(period_id)"
    )


def _migrate_legacy_scores(value: str) -> dict[str, Any]:
    try:
        scores = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(scores, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key, raw_value in scores.items():
        try:
            score = float(raw_value)
        except (TypeError, ValueError):
            normalized[str(key)] = raw_value
            continue
        normalized[str(key)] = score * 20 if 0 <= score <= 5 else score
    return normalized


def _category_for_score(score: float) -> str:
    if score < 60:
        return "Needs Support"
    if score < 80:
        return "Moderate"
    return "High"


@contextmanager
def _connection(db_path: str):
    initialize_database(db_path)
    connection = get_db_connection(db_path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def get_employees(db_path: str = DB_PATH) -> pd.DataFrame:
    with _connection(db_path) as connection:
        return pd.read_sql_query(
            """
            SELECT employee_id, employee_code, employee_name, department,
                   designation, joining_date, status, experience_years,
                   data_origin,
                   attendance_rate, task_completion_rate, training_hours,
                   previous_performance, performance_category, review_date
            FROM (
                SELECT e.employee_id, e.employee_code, e.employee_name, e.department,
                       e.designation, e.joining_date, e.status, e.experience_years,
                       e.data_origin,
                       pr.attendance_rate, pr.task_completion_rate, pr.training_hours,
                       pr.previous_performance, pr.performance_category, pr.review_date,
                       ROW_NUMBER() OVER (
                           PARTITION BY e.employee_id
                           ORDER BY pr.review_date DESC, pr.record_id DESC
                       ) AS review_rank
                FROM employees e
                LEFT JOIN performance_records pr ON pr.employee_id = e.employee_id
            )
            WHERE review_rank = 1
            ORDER BY employee_name COLLATE NOCASE
            """,
            connection,
        )


def mark_bundled_sample_records(db_path: str = DB_PATH) -> bool:
    """Tag the bundled CSV as demo data only when the entire DB matches it."""
    sample_path = os.path.join("data", "sample_employees.csv")
    if not os.path.exists(sample_path):
        return False
    sample = pd.read_csv(sample_path)
    employees = get_employees(db_path)
    if len(sample) != len(employees) or employees.empty:
        return False

    compared_columns = [
        "employee_code",
        "employee_name",
        "department",
        "experience_years",
        "attendance_rate",
        "task_completion_rate",
        "training_hours",
        "previous_performance",
        "performance_category",
        "review_date",
    ]
    if any(column not in employees.columns or column not in sample.columns for column in compared_columns):
        return False
    merged = sample[compared_columns].merge(
        employees[compared_columns],
        on="employee_code",
        how="outer",
        suffixes=("_sample", "_database"),
        indicator=True,
        validate="one_to_one",
    )
    if not merged["_merge"].eq("both").all():
        return False
    for column in compared_columns[1:]:
        left = merged[f"{column}_sample"]
        right = merged[f"{column}_database"]
        if column in {
            "experience_years", "attendance_rate", "task_completion_rate",
            "training_hours", "previous_performance",
        }:
            equal = (
                pd.to_numeric(left, errors="coerce")
                .sub(pd.to_numeric(right, errors="coerce"))
                .abs()
                .fillna(0)
                .le(1e-8)
            )
        else:
            equal = left.fillna("").astype(str).eq(right.fillna("").astype(str))
        if not equal.all():
            return False

    with _connection(db_path) as connection:
        connection.execute("UPDATE employees SET data_origin = 'demo'")
        connection.commit()
    return True


def create_employee(
    employee_code: str,
    employee_name: str,
    department: str,
    designation: str,
    joining_date: date | str,
    status: str,
    experience_years: float,
    db_path: str = DB_PATH,
) -> int:
    values = [employee_code.strip(), employee_name.strip(), department.strip()]
    if not all(values):
        raise ValueError("Employee ID, name, and department are required.")
    if status not in {"Active", "On leave", "Inactive"}:
        raise ValueError("Choose a valid employee status.")
    experience = float(experience_years)
    if not 0 <= experience <= 80:
        raise ValueError("Experience must be between 0 and 80 years.")
    join_date = _iso_date(joining_date, "Joining date")
    with _connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO employees
                (employee_code, employee_name, department, designation,
                 joining_date, status, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values[0], values[1], values[2], designation.strip(),
                join_date, status, experience,
            ),
        )
        _notify(connection, "Employee added", f"{values[1]} was added to the employee directory.")
        connection.commit()
        return int(cursor.lastrowid)


def update_employee_profile(
    employee_id: int,
    employee_code: str,
    employee_name: str,
    department: str,
    designation: str,
    joining_date: date | str,
    status: str,
    experience_years: float,
    db_path: str = DB_PATH,
) -> None:
    values = [employee_code.strip(), employee_name.strip(), department.strip()]
    if not all(values):
        raise ValueError("Employee ID, name, and department are required.")
    if status not in {"Active", "On leave", "Inactive"}:
        raise ValueError("Choose a valid employee status.")
    experience = float(experience_years)
    if not 0 <= experience <= 80:
        raise ValueError("Experience must be between 0 and 80 years.")
    with _connection(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE employees
            SET employee_code = ?, employee_name = ?, department = ?,
                designation = ?, joining_date = ?, status = ?, experience_years = ?
            WHERE employee_id = ?
            """,
            (
                values[0], values[1], values[2], designation.strip(),
                _iso_date(joining_date, "Joining date"), status,
                experience, int(employee_id),
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError("The selected employee no longer exists.")
        connection.commit()


def delete_employee(employee_id: int, db_path: str = DB_PATH) -> None:
    with _connection(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM employees WHERE employee_id = ?", (int(employee_id),)
        )
        if cursor.rowcount != 1:
            raise ValueError("The selected employee no longer exists.")
        connection.commit()


def get_periods(db_path: str = DB_PATH) -> pd.DataFrame:
    with _connection(db_path) as connection:
        return pd.read_sql_query(
            """
            SELECT p.period_id, p.name, p.start_date, p.end_date,
                   CASE WHEN p.status = 'Planned' THEN 'Draft' ELSE p.status END AS status,
                   COUNT(a.assessment_id) AS assessment_count
            FROM performance_periods p
            LEFT JOIN assessments a ON a.period_id = p.period_id
            GROUP BY p.period_id
            ORDER BY p.start_date DESC, p.period_id DESC
            """,
            connection,
        )


def save_period(
    name: str,
    start_date: date | str,
    end_date: date | str,
    status: str,
    period_id: int | None = None,
    db_path: str = DB_PATH,
) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Enter a name for the review period.")
    start = _iso_date(start_date, "Start date")
    end = _iso_date(end_date, "End date")
    if end < start:
        raise ValueError("The end date must be on or after the start date.")
    if status not in {"Draft", "Active", "Completed"}:
        raise ValueError("Choose a valid review period status.")
    with _connection(db_path) as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(performance_periods)")
        }
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'performance_periods'"
        ).fetchone()[0]
        stored_status = (
            "Planned"
            if status == "Draft" and "'Planned'" in schema and "'Draft'" not in schema
            else status
        )
        if period_id is None:
            if "title" in columns:
                cursor = connection.execute(
                    """
                    INSERT INTO performance_periods (title, name, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, name, start, end, stored_status),
                )
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO performance_periods (name, start_date, end_date, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, start, end, stored_status),
                )
            _notify(connection, "Review period created", f"{name} is now available for review.")
        else:
            if "title" in columns:
                cursor = connection.execute(
                    """
                    UPDATE performance_periods
                    SET title = ?, name = ?, start_date = ?, end_date = ?, status = ?
                    WHERE period_id = ?
                    """,
                    (name, name, start, end, stored_status, int(period_id)),
                )
            else:
                cursor = connection.execute(
                    """
                    UPDATE performance_periods
                    SET name = ?, start_date = ?, end_date = ?, status = ?
                    WHERE period_id = ?
                    """,
                    (name, start, end, stored_status, int(period_id)),
                )
            if cursor.rowcount != 1:
                raise ValueError("The selected review period no longer exists.")
        connection.commit()
        return int(cursor.lastrowid if period_id is None else period_id)


def delete_period(period_id: int, db_path: str = DB_PATH) -> None:
    with _connection(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM performance_periods WHERE period_id = ?", (int(period_id),)
        )
        if cursor.rowcount != 1:
            raise ValueError("The selected review period no longer exists.")
        connection.commit()


def get_areas(db_path: str = DB_PATH) -> pd.DataFrame:
    with _connection(db_path) as connection:
        return pd.read_sql_query(
            "SELECT area_id, name, description, weight, active "
            "FROM performance_areas ORDER BY area_id",
            connection,
        )


def save_areas(areas: list[dict[str, Any]], db_path: str = DB_PATH) -> None:
    cleaned: list[tuple[int | None, str, str, float, int]] = []
    names: set[str] = set()
    for area in areas:
        name = str(area.get("name", "")).strip()
        if not name:
            continue
        normalized = name.casefold()
        if normalized in names:
            raise ValueError(f"Performance area '{name}' is listed more than once.")
        names.add(normalized)
        weight = float(area.get("weight", 0))
        if not 0 <= weight <= 100:
            raise ValueError("Each area weight must be between 0 and 100.")
        cleaned.append(
            (
                _optional_int(area.get("area_id")), name,
                str(area.get("description", "")).strip(),
                weight, int(bool(area.get("active", True))),
            )
        )
    if not cleaned:
        raise ValueError("Keep at least one performance area.")
    active_weight = sum(item[3] for item in cleaned if item[4])
    if abs(active_weight - 100) > 0.01:
        raise ValueError(
            f"Active indicator weights must total 100% (currently {active_weight:g}%)."
        )

    with _connection(db_path) as connection:
        existing = {
            int(row["area_id"])
            for row in connection.execute("SELECT area_id FROM performance_areas")
        }
        retained: set[int] = set()
        for area_id, name, description, weight, active in cleaned:
            if area_id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO performance_areas (name, description, weight, active)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, description, weight, active),
                )
                retained.add(int(cursor.lastrowid))
            else:
                if area_id not in existing:
                    raise ValueError(
                        "A performance area was changed by another user; reload and retry."
                    )
                connection.execute(
                    """
                    UPDATE performance_areas
                    SET name = ?, description = ?, weight = ?, active = ?
                    WHERE area_id = ?
                    """,
                    (name, description, weight, active, area_id),
                )
                retained.add(area_id)
        removed = existing - retained
        if removed:
            connection.executemany(
                "DELETE FROM performance_areas WHERE area_id = ?",
                [(area_id,) for area_id in removed],
            )
        connection.commit()


def get_assessments(db_path: str = DB_PATH) -> pd.DataFrame:
    with _connection(db_path) as connection:
        return pd.read_sql_query(
            """
            SELECT a.assessment_id, a.assessment_date, a.reviewer,
                   a.overall_score, a.comments, a.scores_json,
                   e.employee_id, e.employee_code, e.employee_name, e.department,
                   p.period_id, COALESCE(p.name, 'Historical (no period)') AS period_name
            FROM assessments a
            JOIN employees e ON e.employee_id = a.employee_id
            LEFT JOIN performance_periods p ON p.period_id = a.period_id
            ORDER BY a.assessment_date DESC, a.assessment_id DESC
            """,
            connection,
        )


def save_assessment(
    employee_id: int,
    period_id: int,
    assessment_date: date | str,
    reviewer: str,
    scores: dict[str, float],
    comments: str,
    db_path: str = DB_PATH,
) -> int:
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("Enter the reviewer’s name.")
    date_value = _iso_date(assessment_date, "Assessment date")
    with _connection(db_path) as connection:
        period = connection.execute(
            "SELECT name, status FROM performance_periods WHERE period_id = ?",
            (int(period_id),),
        ).fetchone()
        if period is None:
            raise ValueError("Select an existing review period.")
        if period["status"] != "Active":
            raise ValueError("Assessments can only be submitted to an active review period.")

        areas = connection.execute(
            "SELECT name, weight FROM performance_areas WHERE active = 1"
        ).fetchall()
        if not areas:
            raise ValueError("Activate at least one performance area before assessing.")
        normalized_scores: dict[str, float] = {}
        weighted_total = 0.0
        for area in areas:
            if area["name"] not in scores:
                raise ValueError(f"Enter a score for {area['name']}.")
            value = float(scores[area["name"]])
            if not 0 <= value <= 100:
                raise ValueError(f"{area['name']} must be scored from 0 to 100.")
            normalized_scores[area["name"]] = value
            weighted_total += value * float(area["weight"]) / 100

        cursor = connection.execute(
            """
            INSERT INTO assessments
                (employee_id, period_id, assessment_date, reviewer, scores_json,
                 overall_score, category, comments, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(employee_id), int(period_id), date_value, reviewer,
                json.dumps(normalized_scores, sort_keys=True),
                round(weighted_total, 2), _category_for_score(weighted_total),
                comments.strip(), "Completed",
            ),
        )
        employee = connection.execute(
            "SELECT employee_name FROM employees WHERE employee_id = ?",
            (int(employee_id),),
        ).fetchone()
        if employee is None:
            raise ValueError("Select an existing employee.")
        _notify(
            connection,
            "Assessment completed",
            f"{employee['employee_name']}’s {period['name']} assessment was recorded.",
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_notifications(db_path: str = DB_PATH) -> pd.DataFrame:
    with _connection(db_path) as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(notifications)")
        }
        read_expression = (
            "CASE WHEN is_read = 1 THEN COALESCE(read_at, created_at) "
            "ELSE read_at END"
            if "is_read" in columns
            else "read_at"
        )
        return pd.read_sql_query(
            f"""
            SELECT notification_id, title, message, created_at,
                   {read_expression} AS read_at
            FROM notifications ORDER BY created_at DESC, notification_id DESC
            """,
            connection,
        )


def mark_notifications_read(
    notification_ids: list[int] | None = None, db_path: str = DB_PATH
) -> None:
    with _connection(db_path) as connection:
        if notification_ids is None:
            connection.execute(
                "UPDATE notifications SET read_at = ? WHERE read_at IS NULL",
                (datetime.now().isoformat(timespec="seconds"),),
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(notifications)")
            }
            if "is_read" in columns:
                connection.execute("UPDATE notifications SET is_read = 1")
        elif notification_ids:
            placeholders = ",".join("?" for _ in notification_ids)
            connection.execute(
                f"UPDATE notifications SET read_at = ? "
                f"WHERE read_at IS NULL AND notification_id IN ({placeholders})",
                [datetime.now().isoformat(timespec="seconds"), *map(int, notification_ids)],
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(notifications)")
            }
            if "is_read" in columns:
                connection.execute(
                    f"UPDATE notifications SET is_read = 1 "
                    f"WHERE notification_id IN ({placeholders})",
                    list(map(int, notification_ids)),
                )
        connection.commit()


def get_pending_reviews(db_path: str = DB_PATH) -> pd.DataFrame:
    with _connection(db_path) as connection:
        return pd.read_sql_query(
            """
            SELECT e.employee_id, e.employee_code, e.employee_name, e.department,
                   p.period_id, p.name AS period_name, p.end_date
            FROM performance_periods p
            JOIN employees e ON e.status = 'Active'
            LEFT JOIN assessments a
                ON a.employee_id = e.employee_id AND a.period_id = p.period_id
            WHERE p.status = 'Active' AND a.assessment_id IS NULL
            ORDER BY p.end_date, e.department, e.employee_name
            """,
            connection,
        )


def get_dashboard_summary(db_path: str = DB_PATH) -> dict[str, int]:
    with _connection(db_path) as connection:
        employee_count = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]
        period_count = connection.execute(
            "SELECT COUNT(*) FROM performance_periods WHERE status = 'Active'"
        ).fetchone()[0]
        assessment_count = connection.execute(
            "SELECT COUNT(*) FROM assessments"
        ).fetchone()[0]
        area_count = connection.execute(
            "SELECT COUNT(*) FROM performance_areas WHERE active = 1"
        ).fetchone()[0]
        demo_count = connection.execute(
            "SELECT COUNT(*) FROM employees WHERE data_origin = 'demo'"
        ).fetchone()[0]
        unread_count = connection.execute(
            "SELECT COUNT(*) FROM notifications WHERE read_at IS NULL"
        ).fetchone()[0]
    return {
        "total_employees": int(employee_count),
        "active_periods": int(period_count),
        "completed_assessments": int(assessment_count),
        "performance_areas": int(area_count),
        "demo_employees": int(demo_count),
        "unread_notifications": int(unread_count),
    }


def get_settings(db_path: str = DB_PATH) -> dict[str, str]:
    with _connection(db_path) as connection:
        rows = connection.execute(
            "SELECT setting_key, setting_value FROM app_settings"
        ).fetchall()
    return {row["setting_key"]: row["setting_value"] for row in rows}


def save_settings(values: dict[str, str], db_path: str = DB_PATH) -> None:
    for key in ("admin_name", "workspace_name"):
        if key in values and not str(values[key]).strip():
            raise ValueError(f"{key.replace('_', ' ').title()} cannot be blank.")
    with _connection(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """,
            [(str(key), str(value).strip()) for key, value in values.items()],
        )
        connection.commit()


def _notify(connection: sqlite3.Connection, title: str, message: str) -> None:
    connection.execute(
        "INSERT INTO notifications (title, message) VALUES (?, ?)",
        (title, message),
    )


def _iso_date(value: date | str, label: str) -> str:
    try:
        return (
            date.fromisoformat(value).isoformat()
            if isinstance(value, str)
            else value.isoformat()
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Enter a valid {label.lower()}.") from exc


def _optional_int(value: Any) -> int | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    return int(value)


def seed_demo_review_cycle(db_path: str = DB_PATH) -> int:
    """Seeds demonstration review periods and realistic assessments for demo/evaluation."""
    with _connection(db_path) as connection:
        areas = connection.execute(
            "SELECT area_id, name, weight FROM performance_areas WHERE active = 1"
        ).fetchall()
        if not areas:
            for name, desc, weight in DEFAULT_AREAS:
                connection.execute(
                    "INSERT OR IGNORE INTO performance_areas (name, description, weight) VALUES (?, ?, ?)",
                    (name, desc, weight),
                )
            areas = connection.execute(
                "SELECT area_id, name, weight FROM performance_areas WHERE active = 1"
            ).fetchall()

        period_cols = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(performance_periods)")
        }
        has_title = "title" in period_cols

        query_sql = (
            "SELECT period_id FROM performance_periods WHERE name = ? OR title = ?"
            if has_title
            else "SELECT period_id FROM performance_periods WHERE name = ?"
        )
        query_args_q2 = ("FY2026 Q2 Review Cycle", "FY2026 Q2 Review Cycle") if has_title else ("FY2026 Q2 Review Cycle",)
        query_args_q3 = ("FY2026 Q3 Review Cycle", "FY2026 Q3 Review Cycle") if has_title else ("FY2026 Q3 Review Cycle",)

        p_q2 = connection.execute(query_sql, query_args_q2).fetchone()
        if not p_q2:
            start_q2 = (date.today() - timedelta(days=120)).isoformat()
            end_q2 = (date.today() - timedelta(days=35)).isoformat()
            if has_title:
                cur = connection.execute(
                    "INSERT INTO performance_periods (title, name, start_date, end_date, status) VALUES (?, ?, ?, ?, 'Completed')",
                    ("FY2026 Q2 Review Cycle", "FY2026 Q2 Review Cycle", start_q2, end_q2),
                )
            else:
                cur = connection.execute(
                    "INSERT INTO performance_periods (name, start_date, end_date, status) VALUES (?, ?, ?, 'Completed')",
                    ("FY2026 Q2 Review Cycle", start_q2, end_q2),
                )
            p_q2_id = cur.lastrowid
        else:
            p_q2_id = p_q2["period_id"]

        p_q3 = connection.execute(query_sql, query_args_q3).fetchone()
        if not p_q3:
            start_q3 = (date.today() - timedelta(days=30)).isoformat()
            end_q3 = (date.today() + timedelta(days=45)).isoformat()
            if has_title:
                cur = connection.execute(
                    "INSERT INTO performance_periods (title, name, start_date, end_date, status) VALUES (?, ?, ?, ?, 'Active')",
                    ("FY2026 Q3 Review Cycle", "FY2026 Q3 Review Cycle", start_q3, end_q3),
                )
            else:
                cur = connection.execute(
                    "INSERT INTO performance_periods (name, start_date, end_date, status) VALUES (?, ?, ?, 'Active')",
                    ("FY2026 Q3 Review Cycle", start_q3, end_q3),
                )
            p_q3_id = cur.lastrowid
        else:
            p_q3_id = p_q3["period_id"]

        emps = connection.execute(
            """
            SELECT e.employee_id, e.employee_code, e.employee_name, e.department,
                   pr.attendance_rate, pr.task_completion_rate, pr.training_hours, pr.previous_performance
            FROM employees e
            LEFT JOIN performance_records pr ON e.employee_id = pr.employee_id
            ORDER BY e.employee_id ASC
            LIMIT 45
            """
        ).fetchall()

        reviewers = [
            "Dr. Marcus Vance (Operations VP)",
            "Sarah Jenkins (People & Culture Director)",
            "Elena Rostova (Engineering Lead)",
            "David Chen (Head of Product)",
        ]

        comments_library = {
            "High": [
                "Exemplary performance across all core competencies. Met and exceeded project milestones ahead of schedule.",
                "Demonstrated outstanding initiative, strong mentorship towards peers, and flawless execution on key deliverables.",
                "Consistently drives high quality outcomes, exhibits proactive problem solving, and maintains impeccable reliability.",
            ],
            "Moderate": [
                "Dependable performance consistently meeting team standards. Recommended to pursue advanced technical certifications next quarter.",
                "Solid operational track record with steady output. Opportunities to enhance cross-functional communication and velocity.",
                "Good core execution. With targeted coaching in project planning, this employee has strong potential for high-tier contribution.",
            ],
            "Needs Support": [
                "Performance indicators indicate need for structured coaching. Focused improvement plan initiated for task completion turnaround.",
                "Below expected completion thresholds this quarter. Recommended weekly 1:1 check-ins and dedicated skill-enhancement hours.",
            ],
        }

        inserted_count = 0
        for i, emp in enumerate(emps):
            target_period_id = p_q3_id if (i % 3 != 0) else p_q2_id
            existing = connection.execute(
                "SELECT assessment_id FROM assessments WHERE employee_id = ? AND period_id = ?",
                (emp["employee_id"], target_period_id),
            ).fetchone()
            if existing:
                continue

            att = float(emp["attendance_rate"]) if emp["attendance_rate"] is not None else 85.0
            tsk = float(emp["task_completion_rate"]) if emp["task_completion_rate"] is not None else 80.0
            trn = float(emp["training_hours"]) if emp["training_hours"] is not None else 25.0
            prev = float(emp["previous_performance"]) if emp["previous_performance"] is not None else 3.5

            scores = {}
            for a in areas:
                name = a["name"]
                if "attendance" in name.lower():
                    s = min(100.0, max(45.0, att + (i % 7 - 3)))
                elif "task" in name.lower():
                    s = min(100.0, max(40.0, tsk + (i % 5 - 2)))
                elif "productivity" in name.lower():
                    s = min(100.0, max(40.0, (tsk * 0.7 + att * 0.3) + (i % 6 - 3)))
                elif "teamwork" in name.lower():
                    s = min(100.0, max(50.0, (prev * 18.0) + (i % 8 - 4)))
                elif "learning" in name.lower():
                    s = min(100.0, max(40.0, (trn * 2.2) + 20.0))
                else:
                    s = 75.0 + (i % 15 - 7)
                scores[name] = round(s, 1)

            overall_score = sum(scores[a["name"]] * float(a["weight"]) / 100.0 for a in areas)
            overall_score = round(min(100.0, max(0.0, overall_score)), 2)
            category = _category_for_score(overall_score)

            rev = reviewers[i % len(reviewers)]
            comm_list = comments_library.get(category, comments_library["Moderate"])
            comment = comm_list[i % len(comm_list)]

            days_offset = (i * 2) % 40
            a_date = (date.today() - timedelta(days=days_offset)).isoformat()

            connection.execute(
                """
                INSERT INTO assessments (
                    employee_id, period_id, assessment_date, reviewer,
                    scores_json, overall_score, category, comments, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Completed')
                """,
                (
                    emp["employee_id"],
                    target_period_id,
                    a_date,
                    rev,
                    json.dumps(scores),
                    overall_score,
                    category,
                    comment,
                ),
            )
            inserted_count += 1

        if inserted_count > 0:
            _notify(
                connection,
                "Demonstration Review Cycle Populated",
                f"Generated {inserted_count} demonstration assessments across active review periods for evaluation.",
            )
        connection.commit()
    return inserted_count


def clear_demo_assessments(db_path: str = DB_PATH) -> int:
    """Removes seeded demonstration review periods and assessments."""
    with _connection(db_path) as connection:
        deleted = connection.execute(
            """
            DELETE FROM assessments WHERE period_id IN (
                SELECT period_id FROM performance_periods 
                WHERE name IN ('FY2026 Q3 Review Cycle', 'FY2026 Q2 Review Cycle')
            )
            """
        ).rowcount
        connection.execute(
            "DELETE FROM performance_periods WHERE name IN ('FY2026 Q3 Review Cycle', 'FY2026 Q2 Review Cycle')"
        )
        _notify(
            connection,
            "Demonstration Data Cleared",
            "Reset demonstration review cycles and associated assessments.",
        )
        connection.commit()
    return deleted