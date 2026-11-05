"""
WorkPulse — REST API and Web Application Service.

Provides production-grade WSGI/HTTP endpoints for the WorkPulse platform,
handling authentication, executive dashboards, employee management,
review cycles, KPI frameworks, assessments, workforce analytics,
and machine learning predictions.
"""

import io
import json
import os
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, Response

from auth.auth_service import (
    authenticate_user,
    change_password,
    ensure_default_admin,
    generate_password_reset_token,
    get_audit_log,
    get_lockout_remaining_minutes,
    init_auth_tables,
    is_rate_limited,
    log_audit,
)
from database.db_manager import (
    DB_PATH,
    add_employee,
    get_all_employees,
    get_db_connection,
    import_records_from_df,
    init_db,
    resolve_db_path,
)
from models.train_model import (
    TARGET_CLASSES,
    train_and_evaluate_all_models,
)
from services.analytics_service import compute_kpis, get_department_summary
from services.employee_service import fetch_employee_history
from services.prediction_service import run_employee_prediction
from services.workpulse_service import (
    clear_demo_assessments,
    create_employee,
    delete_employee,
    delete_period,
    get_areas,
    get_assessments,
    get_dashboard_summary,
    get_employees,
    get_notifications,
    get_pending_reviews,
    get_periods,
    get_settings,
    initialize_database,
    mark_bundled_sample_records,
    mark_notifications_read,
    save_areas,
    save_assessment,
    save_period,
    save_settings,
    seed_demo_review_cycle,
    update_employee_profile,
)
from utils.validation import VALID_DEPARTMENTS


# -----------------------------------------------------------------------------
# Model Pipeline Cache
# -----------------------------------------------------------------------------
_CACHED_MODELS: Dict[str, Any] = {}


def _get_pipeline(model_name: str = "Random Forest"):
    """Load or train model pipeline on demand with caching."""
    global _CACHED_MODELS
    if model_name in _CACHED_MODELS:
        return _CACHED_MODELS[model_name]

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    model_filename = (
        "random_forest.pkl"
        if model_name == "Random Forest"
        else "decision_tree.pkl"
    )
    model_path = os.path.join(base_dir, "models", model_filename)

    if os.path.exists(model_path):
        try:
            pipeline = joblib.load(model_path)
            _CACHED_MODELS[model_name] = pipeline
            return pipeline
        except Exception:
            pass

    # Train if cached model not loadable
    df = get_all_employees()
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    _, pipelines, _ = train_and_evaluate_all_models(df, models_dir)
    _CACHED_MODELS.update(pipelines)
    return _CACHED_MODELS.get(model_name)


def _safe_json_record(record: dict) -> dict:
    """Sanitize numpy/pandas types for JSON serialization."""
    clean = {}
    for k, v in record.items():
        if pd.isna(v):
            clean[k] = None
        elif isinstance(v, (np.integer, int)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            clean[k] = round(float(v), 2)
        elif isinstance(v, (np.bool_, bool)):
            clean[k] = bool(v)
        else:
            clean[k] = str(v)
    return clean


def import_sample_data(db_path: str) -> None:
    """Import sample employee records from bundled CSV on first deployment.

    In serverless environments, the DB path resolve copies data/workpulse.db to /tmp.
    This function ensures sample employee records and default performance areas
    are seeded on first run.
    """
    import pandas as pd
    import numpy as np

    from database.db_manager import init_db, import_records_from_df
    from services.workpulse_service import DEFAULT_AREAS

    sample_path = os.path.join("data", "sample_employees.csv")
    if not os.path.exists(sample_path):
        return  # No sample data to import

    sample = pd.read_csv(sample_path)
    if len(sample) == 0:
        return

    # Ensure DB schema exists
    init_db(db_path)

    # Import from sample CSV (idempotent - will skip if already exists)
    inserted, skipped = import_records_from_df(sample, db_path)
    if inserted > 0:
        # Initialize default performance areas if not present
        from database.db_manager import get_db_connection

        conn = get_db_connection(db_path)
        area_count = conn.execute(
            "SELECT COUNT(*) FROM performance_areas"
        ).fetchone()[0]
        if area_count == 0:
            conn.executemany(
                "INSERT INTO performance_areas (name, description, weight) VALUES (?, ?, ?)",
                DEFAULT_AREAS,
            )
            conn.commit()
        conn.close()


# -----------------------------------------------------------------------------
# Application Factory
# -----------------------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # Initialize persistence - use resolved DB path for serverless compatibility
    db_path = resolve_db_path()
    try:
        initialize_database(db_path)
        init_auth_tables(db_path)
        ensure_default_admin()
        # Import sample employee data on first run (serverless: copies to /tmp)
        import_sample_data(db_path)
        mark_bundled_sample_records(db_path)
        # Seed demo review cycle with assessments for evaluation
        seed_demo_review_cycle(db_path)
    except Exception as e:
        print(f"[WorkPulse Init Warning] {e}", file=sys.stderr)

    # Enable CORS
    @app.after_request
    def apply_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    # -------------------------------------------------------------------------
    # Health & System Diagnostics
    # -------------------------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health():
        active_db = resolve_db_path()
        db_exists = os.path.exists(active_db)
        is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
        return jsonify({
            "status": "healthy",
            "service": "WorkPulse — Employee Performance Review System",
            "version": "1.0.0",
            "environment": "vercel_serverless" if is_serverless else "local_standard",
            "database": {
                "path": active_db,
                "exists": db_exists,
                "size_kb": round(os.path.getsize(active_db) / 1024, 1) if db_exists else 0,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

    @app.route("/api/diagnostics", methods=["GET"])
    def diagnostics():
        active_db = resolve_db_path()
        summary = get_dashboard_summary()
        settings = get_settings()
        return jsonify({
            "database_file": active_db,
            "database_size_bytes": os.path.getsize(active_db) if os.path.exists(active_db) else 0,
            "summary_counts": summary,
            "settings": settings,
            "valid_departments": list(VALID_DEPARTMENTS),
        })

    # -------------------------------------------------------------------------
    # Authentication Endpoints
    # -------------------------------------------------------------------------
    @app.route("/api/auth/login", methods=["POST", "OPTIONS"])
    def auth_login():
        if request.method == "OPTIONS":
            return "", 204

        data = request.get_json(silent=True) or {}
        email_or_user = (data.get("email") or data.get("username") or "").strip()
        password = data.get("password", "")

        if not email_or_user or not password:
            return jsonify({"error": "Email/username and password are required."}), 400

        # Map friendly username to standard email if needed
        clean_target = email_or_user.lower()
        if "@" not in clean_target:
            if clean_target == "admin":
                clean_target = "admin@workpulse.local"
            elif clean_target in ("hr", "hr_manager"):
                clean_target = "hr@workpulse.local"
            elif clean_target in ("employee", "emp"):
                clean_target = "employee@workpulse.local"

        if is_rate_limited(clean_target):
            mins = get_lockout_remaining_minutes(clean_target)
            return jsonify({
                "error": f"Account temporarily locked due to too many failed attempts. Try again in {mins} minutes.",
                "lockout_minutes": mins,
            }), 429

        user = authenticate_user(clean_target, password)
        if not user:
            return jsonify({"error": "Invalid credentials. Please verify your email/username and password."}), 401

        log_audit(user["user_id"], "LOGIN", "session", user["user_id"], "User logged in via REST API")
        return jsonify({
            "success": True,
            "message": "Authentication successful.",
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "employee_id": user["employee_id"],
                "must_change_password": bool(user["must_change_password"]),
            },
        })

    @app.route("/api/auth/logout", methods=["POST"])
    def auth_logout():
        return jsonify({"success": True, "message": "Successfully logged out."})

    @app.route("/api/auth/change-password", methods=["POST"])
    def auth_change_password():
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not user_id or not current_password or not new_password:
            return jsonify({"error": "user_id, current_password, and new_password are required."}), 400

        success, err = change_password(int(user_id), current_password, new_password)
        if not success:
            return jsonify({"error": err}), 400

        return jsonify({"success": True, "message": "Password changed successfully."})

    @app.route("/api/auth/forgot-password", methods=["POST"])
    def auth_forgot_password():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        if not email:
            return jsonify({"error": "Email is required."}), 400

        token = generate_password_reset_token(email)
        return jsonify({
            "success": True,
            "message": "If the email is registered, a password reset token has been created.",
            "reset_token": token,
        })

    @app.route("/api/auth/audit-logs", methods=["GET"])
    def auth_audit_logs():
        limit = min(int(request.args.get("limit", 50)), 200)
        logs = get_audit_log(limit=limit)
        return jsonify({"audit_logs": logs, "count": len(logs)})

    # -------------------------------------------------------------------------
    # Executive Dashboard Summary
    # -------------------------------------------------------------------------
    @app.route("/api/dashboard/summary", methods=["GET"])
    def dashboard_summary():
        summary = get_dashboard_summary()
        employees = get_employees()
        assessments = get_assessments()
        periods = get_periods()

        avg_score = 0.0
        distribution = {"High": 0, "Moderate": 0, "Needs Support": 0}
        if not assessments.empty and "overall_score" in assessments.columns:
            avg_score = round(float(assessments["overall_score"].mean()), 2)
            for score in assessments["overall_score"].dropna():
                if score >= 80:
                    distribution["High"] += 1
                elif score >= 60:
                    distribution["Moderate"] += 1
                else:
                    distribution["Needs Support"] += 1

        active_cycles = (
            periods[periods["status"] == "Active"].to_dict(orient="records")
            if not periods.empty
            else []
        )

        return jsonify({
            "metrics": {
                "total_employees": summary.get("total_employees", len(employees)),
                "active_periods": summary.get("active_periods", len(active_cycles)),
                "completed_assessments": summary.get("completed_assessments", len(assessments)),
                "unread_notifications": summary.get("unread_notifications", 0),
                "workforce_mean_score": avg_score,
                "benchmark_delta": round(avg_score - 75.0, 2),
            },
            "performance_distribution": distribution,
            "active_review_cycles": [
                {
                    "period_id": int(c.get("period_id", 0)),
                    "name": str(c.get("name", "")),
                    "start_date": str(c.get("start_date", "")),
                    "end_date": str(c.get("end_date", "")),
                    "status": str(c.get("status", "")),
                }
                for c in active_cycles
            ],
            "pending_reviews_count": len(get_pending_reviews()),
        })

    # -------------------------------------------------------------------------
    # Employee Management
    # -------------------------------------------------------------------------
    @app.route("/api/employees", methods=["GET", "POST"])
    def employees_endpoint():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            required = ["employee_code", "employee_name", "department"]
            for field in required:
                if not data.get(field):
                    return jsonify({"error": f"Field '{field}' is required."}), 400

            try:
                emp_id = create_employee(
                    employee_code=str(data["employee_code"]).strip(),
                    employee_name=str(data["employee_name"]).strip(),
                    department=str(data["department"]).strip(),
                    designation=str(data.get("designation", "Staff Member")).strip(),
                    joining_date=str(data.get("joining_date", date.today().isoformat())),
                    status=str(data.get("status", "Active")),
                    experience_years=float(data.get("experience_years", 2.0)),
                    attendance_rate=float(data.get("attendance_rate", 85.0)),
                    task_completion_rate=float(data.get("task_completion_rate", 80.0)),
                    training_hours=float(data.get("training_hours", 20.0)),
                    previous_performance=float(data.get("previous_performance", 3.0)),
                )
                return jsonify({
                    "success": True,
                    "message": "Employee created successfully.",
                    "employee_id": emp_id,
                }), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        # GET Employees
        df = get_employees()
        if df.empty:
            return jsonify({"employees": [], "count": 0})

        dept_filter = request.args.get("department")
        if dept_filter and dept_filter != "All":
            df = df[df["department"] == dept_filter]

        status_filter = request.args.get("status")
        if status_filter and status_filter != "All":
            df = df[df["status"] == status_filter]

        search_query = request.args.get("search", "").strip().lower()
        if search_query:
            mask = (
                df["employee_name"].str.lower().str.contains(search_query)
                | df["employee_code"].str.lower().str.contains(search_query)
                | df["department"].str.lower().str.contains(search_query)
            )
            df = df[mask]

        records = [_safe_json_record(r) for r in df.to_dict(orient="records")]
        return jsonify({"employees": records, "count": len(records)})

    @app.route("/api/employees/<int:emp_id>", methods=["GET", "PUT", "DELETE"])
    def single_employee_endpoint(emp_id: int):
        df = get_employees()
        match = df[df["employee_id"] == emp_id]
        if match.empty:
            return jsonify({"error": f"Employee {emp_id} not found."}), 404

        if request.method == "DELETE":
            try:
                delete_employee(emp_id)
                return jsonify({"success": True, "message": f"Employee {emp_id} deleted."})
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        if request.method == "PUT":
            data = request.get_json(silent=True) or {}
            try:
                update_employee_profile(
                    employee_id=emp_id,
                    employee_name=str(data.get("employee_name", match.iloc[0]["employee_name"])),
                    department=str(data.get("department", match.iloc[0]["department"])),
                    designation=str(data.get("designation", match.iloc[0].get("designation", ""))),
                    joining_date=str(data.get("joining_date", match.iloc[0].get("joining_date", ""))),
                    status=str(data.get("status", match.iloc[0].get("status", "Active"))),
                    experience_years=float(data.get("experience_years", match.iloc[0]["experience_years"])),
                    attendance_rate=float(data.get("attendance_rate", match.iloc[0].get("attendance_rate", 85.0))),
                    task_completion_rate=float(data.get("task_completion_rate", match.iloc[0].get("task_completion_rate", 80.0))),
                    training_hours=float(data.get("training_hours", match.iloc[0].get("training_hours", 20.0))),
                    previous_performance=float(data.get("previous_performance", match.iloc[0].get("previous_performance", 3.0))),
                )
                return jsonify({"success": True, "message": f"Employee {emp_id} updated."})
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        # GET
        emp_record = _safe_json_record(match.iloc[0].to_dict())
        history_df = fetch_employee_history(emp_id)
        history = (
            [_safe_json_record(r) for r in history_df.to_dict(orient="records")]
            if not history_df.empty
            else []
        )
        emp_record["performance_history"] = history
        return jsonify(emp_record)

    # -------------------------------------------------------------------------
    # Performance Review Cycles (Periods)
    # -------------------------------------------------------------------------
    @app.route("/api/periods", methods=["GET", "POST"])
    def periods_endpoint():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            for field in ["name", "start_date", "end_date"]:
                if not data.get(field):
                    return jsonify({"error": f"Field '{field}' is required."}), 400

            try:
                save_period(
                    name=str(data["name"]).strip(),
                    start_date=str(data["start_date"]).strip(),
                    end_date=str(data["end_date"]).strip(),
                    status=str(data.get("status", "Draft")),
                    period_id=int(data["period_id"]) if data.get("period_id") else None,
                )
                return jsonify({"success": True, "message": "Period saved successfully."}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        periods_df = get_periods()
        records = (
            [_safe_json_record(r) for r in periods_df.to_dict(orient="records")]
            if not periods_df.empty
            else []
        )
        return jsonify({"periods": records, "count": len(records)})

    @app.route("/api/periods/<int:period_id>", methods=["DELETE"])
    def delete_period_endpoint(period_id: int):
        try:
            delete_period(period_id)
            return jsonify({"success": True, "message": f"Period {period_id} deleted."})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # -------------------------------------------------------------------------
    # KPI Framework (Performance Areas & Weights)
    # -------------------------------------------------------------------------
    @app.route("/api/areas", methods=["GET", "POST"])
    def areas_endpoint():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            areas_list = data.get("areas")
            if not isinstance(areas_list, list):
                return jsonify({"error": "Payload must contain an 'areas' array."}), 400

            total_weight = sum(float(a.get("weight", 0)) for a in areas_list if a.get("active", True))
            if abs(total_weight - 100.0) > 0.05:
                return jsonify({
                    "error": f"Active competency weights must sum to exactly 100%. Current sum: {total_weight:.1f}%"
                }), 400

            try:
                save_areas(areas_list)
                return jsonify({"success": True, "message": "Performance areas updated."})
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        areas_df = get_areas()
        records = (
            [_safe_json_record(r) for r in areas_df.to_dict(orient="records")]
            if not areas_df.empty
            else []
        )
        return jsonify({"areas": records, "count": len(records)})

    # -------------------------------------------------------------------------
    # Structured Assessments
    # -------------------------------------------------------------------------
    @app.route("/api/assessments", methods=["GET", "POST"])
    def assessments_endpoint():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            for field in ["employee_id", "period_id", "reviewer_name", "scores"]:
                if data.get(field) is None:
                    return jsonify({"error": f"Field '{field}' is required."}), 400

            try:
                scores_dict = {str(k): float(v) for k, v in data["scores"].items()}
                save_assessment(
                    employee_id=int(data["employee_id"]),
                    period_id=int(data["period_id"]),
                    reviewer_name=str(data["reviewer_name"]).strip(),
                    assessment_date=str(data.get("assessment_date", date.today().isoformat())),
                    scores=scores_dict,
                    feedback=str(data.get("feedback", "")).strip(),
                    recommendations=str(data.get("recommendations", "")).strip(),
                    assessment_id=int(data["assessment_id"]) if data.get("assessment_id") else None,
                )
                return jsonify({"success": True, "message": "Assessment recorded successfully."}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        df = get_assessments()
        if df.empty:
            return jsonify({"assessments": [], "count": 0})

        if request.args.get("employee_id"):
            df = df[df["employee_id"] == int(request.args["employee_id"])]
        if request.args.get("period_id"):
            df = df[df["period_id"] == int(request.args["period_id"])]
        if request.args.get("department"):
            df = df[df["department"] == request.args["department"]]

        records = [_safe_json_record(r) for r in df.to_dict(orient="records")]
        return jsonify({"assessments": records, "count": len(records)})

    # -------------------------------------------------------------------------
    # Workforce Analytics
    # -------------------------------------------------------------------------
    @app.route("/api/analytics", methods=["GET"])
    def analytics_endpoint():
        df = get_all_employees()
        if df.empty:
            return jsonify({"kpis": {}, "department_summary": []})

        kpis = compute_kpis(df)
        dept_df = get_department_summary(df)
        dept_records = (
            [_safe_json_record(r) for r in dept_df.to_dict(orient="records")]
            if not dept_df.empty
            else []
        )

        return jsonify({
            "kpis": kpis,
            "department_benchmarks": dept_records,
        })

    # -------------------------------------------------------------------------
    # Machine Learning Decision Support & Inference
    # -------------------------------------------------------------------------
    @app.route("/api/predictions/models", methods=["GET"])
    def prediction_models_metrics():
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        summary_path = os.path.join(base_dir, "models", "evaluation_summary.pkl")

        if os.path.exists(summary_path):
            try:
                summary = joblib.load(summary_path)
                return jsonify({"model_evaluations": summary})
            except Exception:
                pass

        # Fallback to evaluating baseline
        df = get_all_employees()
        eval_results, _, _ = train_and_evaluate_all_models(df, os.path.join(base_dir, "models"))
        return jsonify({"model_evaluations": eval_results})

    @app.route("/api/predictions/predict", methods=["POST"])
    def predict_endpoint():
        data = request.get_json(silent=True) or {}
        model_type = data.get("model_type", "Random Forest")

        pipeline = _get_pipeline(model_type)
        if pipeline is None:
            return jsonify({"error": f"Model '{model_type}' could not be loaded."}), 500

        population_df = get_all_employees()

        # If employee_id is passed, fetch values from database
        if data.get("employee_id"):
            emp_id = int(data["employee_id"])
            match = population_df[population_df["employee_id"] == emp_id]
            if match.empty:
                return jsonify({"error": f"Employee {emp_id} not found."}), 404
            row = match.iloc[0].to_dict()
            input_dict = {
                "department": row.get("department", "Engineering"),
                "attendance_rate": float(row.get("attendance_rate", 85.0)),
                "task_completion_rate": float(row.get("task_completion_rate", 80.0)),
                "training_hours": float(row.get("training_hours", 20.0)),
                "experience_years": float(row.get("experience_years", 3.0)),
                "previous_performance": float(row.get("previous_performance", 3.0)),
            }
        else:
            # Direct feature input
            for field in ["department", "attendance_rate", "task_completion_rate", "training_hours", "experience_years", "previous_performance"]:
                if field not in data:
                    return jsonify({"error": f"Input field '{field}' is required."}), 400

            input_dict = {
                "department": str(data["department"]),
                "attendance_rate": float(data["attendance_rate"]),
                "task_completion_rate": float(data["task_completion_rate"]),
                "training_hours": float(data["training_hours"]),
                "experience_years": float(data["experience_years"]),
                "previous_performance": float(data["previous_performance"]),
            }

        try:
            prediction_result = run_employee_prediction(
                pipeline=pipeline,
                input_dict=input_dict,
                model_id=1 if model_type == "Random Forest" else 2,
                population_df=population_df,
            )

            contrib_df = prediction_result.get("contributions")
            contrib_list = (
                [_safe_json_record(r) for r in contrib_df.to_dict(orient="records")]
                if isinstance(contrib_df, pd.DataFrame)
                else []
            )

            return jsonify({
                "model_name": model_type,
                "input_features": input_dict,
                "predicted_category": prediction_result["predicted_category"],
                "probabilities": prediction_result["probabilities"],
                "factor_drivers": prediction_result["summary"],
                "feature_contributions": contrib_list,
                "disclaimer": prediction_result["disclaimer"],
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # -------------------------------------------------------------------------
    # Reports & Exports
    # -------------------------------------------------------------------------
    @app.route("/api/reports/summary", methods=["GET"])
    def reports_summary():
        assessments = get_assessments()
        periods = get_periods()
        employees = get_employees()

        total = len(assessments)
        avg = round(float(assessments["overall_score"].mean()), 2) if not assessments.empty else 0.0

        return jsonify({
            "report_title": "WorkPulse Executive Performance Audit & Review Summary",
            "generation_time": datetime.utcnow().isoformat() + "Z",
            "total_reviews": total,
            "average_workforce_score": avg,
            "active_periods": len(periods[periods["status"] == "Active"]) if not periods.empty else 0,
            "registered_headcount": len(employees),
        })

    @app.route("/api/reports/export-csv", methods=["GET"])
    def export_csv():
        export_type = request.args.get("type", "assessments")
        if export_type == "employees":
            df = get_employees()
            filename = "workpulse_employees.csv"
        else:
            df = get_assessments()
            filename = "workpulse_assessments.csv"

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # -------------------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------------------
    @app.route("/api/notifications", methods=["GET"])
    def notifications_endpoint():
        df = get_notifications()
        records = (
            [_safe_json_record(r) for r in df.to_dict(orient="records")]
            if not df.empty
            else []
        )
        unread = int(df["read_at"].isna().sum()) if not df.empty else 0
        return jsonify({"notifications": records, "unread_count": unread})

    @app.route("/api/notifications/mark-read", methods=["POST"])
    def mark_notifications_read_endpoint():
        count = mark_notifications_read()
        return jsonify({"success": True, "marked_count": count})

    # -------------------------------------------------------------------------
    # Demo Seed & Reset
    # -------------------------------------------------------------------------
    @app.route("/api/demo/seed", methods=["POST"])
    def demo_seed():
        count = seed_demo_review_cycle()
        return jsonify({"success": True, "message": f"Seeded {count} demonstration assessments."})

    @app.route("/api/demo/reset", methods=["POST"])
    def demo_reset():
        count = clear_demo_assessments()
        return jsonify({"success": True, "message": f"Cleared {count} demonstration assessments."})

    # -------------------------------------------------------------------------
    # WorkPulse Web Portal (Root Route for Vercel & Direct Browsing)
    # -------------------------------------------------------------------------
    @app.route("/", methods=["GET"])
    @app.route("/portal", methods=["GET"])
    def web_portal():
        summary = get_dashboard_summary()
        active_db = resolve_db_path()
        db_size_kb = round(os.path.getsize(active_db) / 1024, 1) if os.path.exists(active_db) else 0

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorkPulse · Employee Performance Review System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --wp-navy: #102A43;
            --wp-navy-light: #1E3A8A;
            --wp-teal: #168C83;
            --wp-teal-hover: #0E7C7B;
            --wp-teal-light: #F0FDFA;
            --wp-surface: #FFFFFF;
            --wp-bg: #F8FAFC;
            --wp-border: #E2E8F0;
            --wp-text: #1E293B;
            --wp-muted: #64748B;
            --wp-radius: 12px;
            --wp-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--wp-bg);
            color: var(--wp-text);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}
        header {{
            background: var(--wp-navy);
            color: white;
            padding: 1.25rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        .badge {{
            background: var(--wp-teal);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .hero {{
            background: linear-gradient(180deg, #102A43 0%, #1E3A8A 100%);
            color: white;
            padding: 3.5rem 2rem 4rem;
            text-align: center;
        }}
        .hero h1 {{
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.75rem;
        }}
        .hero p {{
            font-size: 1.1rem;
            color: #CBD5E1;
            max-width: 680px;
            margin: 0 auto 1.5rem;
        }}
        .container {{
            max-width: 1180px;
            margin: -2rem auto 3rem;
            padding: 0 1.5rem;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .kpi-card {{
            background: var(--wp-surface);
            border: 1px solid var(--wp-border);
            border-radius: var(--wp-radius);
            padding: 1.5rem;
            box-shadow: var(--wp-shadow);
        }}
        .kpi-title {{
            font-size: 0.8125rem;
            color: var(--wp-muted);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.04em;
        }}
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--wp-navy);
            margin: 0.35rem 0;
        }}
        .kpi-meta {{
            font-size: 0.8125rem;
            color: var(--wp-teal);
            font-weight: 500;
        }}
        .section-card {{
            background: var(--wp-surface);
            border: 1px solid var(--wp-border);
            border-radius: var(--wp-radius);
            padding: 2rem;
            box-shadow: var(--wp-shadow);
            margin-bottom: 2rem;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid var(--wp-border);
            padding-bottom: 0.875rem;
        }}
        .section-header h2 {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--wp-navy);
        }}
        .endpoints-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1rem;
        }}
        .endpoint-card {{
            border: 1px solid var(--wp-border);
            border-radius: 8px;
            padding: 1rem;
            background: #F8FAFC;
            transition: all 0.2s;
        }}
        .endpoint-card:hover {{
            border-color: var(--wp-teal);
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .endpoint-tag {{
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.2rem 0.45rem;
            border-radius: 4px;
            margin-right: 0.5rem;
        }}
        .tag-get {{ background: #E0F2FE; color: #0369A1; }}
        .tag-post {{ background: #DCFCE7; color: #15803D; }}
        .endpoint-url {{
            font-family: monospace;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--wp-navy);
        }}
        .endpoint-desc {{
            font-size: 0.8125rem;
            color: var(--wp-muted);
            margin-top: 0.4rem;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--wp-teal);
            color: white;
            font-weight: 600;
            font-size: 0.8125rem;
            padding: 0.45rem 0.875rem;
            border-radius: 6px;
            text-decoration: none;
            border: none;
            cursor: pointer;
            margin-top: 0.75rem;
            transition: background 0.15s;
        }}
        .btn:hover {{ background: var(--wp-teal-hover); }}
        .console-box {{
            background: #0F172A;
            color: #38BDF8;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.8125rem;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            max-height: 250px;
            margin-top: 0.75rem;
            display: none;
        }}
        .auth-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}
        .auth-table th, .auth-table td {{
            text-align: left;
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid var(--wp-border);
        }}
        .auth-table th {{
            background: #F1F5F9;
            color: var(--wp-muted);
            font-weight: 600;
        }}
        footer {{
            text-align: center;
            color: var(--wp-muted);
            font-size: 0.8125rem;
            padding: 2rem 1rem;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            <span>WorkPulse</span>
            <span class="badge">Vercel Serverless Ready</span>
        </div>
        <div style="font-size: 0.875rem; color: #CBD5E1;">
            SQLite: <strong>{db_size_kb} KB</strong> · Status: <span style="color:#34D399; font-weight:600;">● Online</span>
        </div>
    </header>

    <div class="hero">
        <h1>Understand Performance. Empower Growth.</h1>
        <p>Enterprise SaaS Employee Performance Review & Workforce Intelligence Platform. Full REST API and machine learning decision support operational.</p>
    </div>

    <div class="container">
        <!-- Live Metric Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Active Employees</div>
                <div class="kpi-value">{summary.get("total_employees", 600)}</div>
                <div class="kpi-meta">Across 8 Enterprise Departments</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Review Cycles</div>
                <div class="kpi-value">{summary.get("active_periods", 1)}</div>
                <div class="kpi-meta">Active Cadence & Evaluation</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Completed Reviews</div>
                <div class="kpi-value">{summary.get("completed_assessments", 45)}</div>
                <div class="kpi-meta">Normalized Weighted KPI Scores</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">ML Decision Support</div>
                <div class="kpi-value">Active</div>
                <div class="kpi-meta">Random Forest & Decision Tree Classifiers</div>
            </div>
        </div>

        <!-- Role Credentials Reference -->
        <div class="section-card">
            <div class="section-header">
                <h2>Pre-configured Access Roles & Credentials</h2>
                <span class="badge" style="background:#0F172A;">Bcrypt Hash Enforced</span>
            </div>
            <table class="auth-table">
                <thead>
                    <tr>
                        <th>Role</th>
                        <th>Email / Username</th>
                        <th>Default Demo Password</th>
                        <th>Access Scope</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Administrator</strong></td>
                        <td><code>admin@workpulse.local</code> (or <code>admin</code>)</td>
                        <td><code>Admin@WorkPulse2024</code></td>
                        <td>Full System Controls, Cycle Cadence, KPI Framework Tuning</td>
                    </tr>
                    <tr>
                        <td><strong>HR Manager</strong></td>
                        <td><code>hr@workpulse.local</code> (or <code>hr</code>)</td>
                        <td><code>Hr@WorkPulse2024</code></td>
                        <td>Directory Management, Assessments, Analytics & Reports</td>
                    </tr>
                    <tr>
                        <td><strong>Staff Employee</strong></td>
                        <td><code>employee@workpulse.local</code> (or <code>employee</code>)</td>
                        <td><code>Emp@WorkPulse2024</code></td>
                        <td>Self-Service Dossier, Review Trajectory, Feedback History</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Interactive API Explorer -->
        <div class="section-card">
            <div class="section-header">
                <h2>Live REST API Endpoints</h2>
                <span style="font-size:0.8125rem; color:var(--wp-muted);">Click "Test Endpoint" for instant JSON response</span>
            </div>
            <div class="endpoints-grid">
                <div class="endpoint-card">
                    <div><span class="endpoint-tag tag-get">GET</span><span class="endpoint-url">/api/health</span></div>
                    <div class="endpoint-desc">System health check, environment status, and SQLite integrity.</div>
                    <button class="btn" onclick="callApi('/api/health', 'out-health')">Test Endpoint</button>
                    <pre id="out-health" class="console-box"></pre>
                </div>
                <div class="endpoint-card">
                    <div><span class="endpoint-tag tag-get">GET</span><span class="endpoint-url">/api/dashboard/summary</span></div>
                    <div class="endpoint-desc">Executive summary KPI cards, mean scores, and tier distribution.</div>
                    <button class="btn" onclick="callApi('/api/dashboard/summary', 'out-dash')">Test Endpoint</button>
                    <pre id="out-dash" class="console-box"></pre>
                </div>
                <div class="endpoint-card">
                    <div><span class="endpoint-tag tag-get">GET</span><span class="endpoint-url">/api/employees?limit=5</span></div>
                    <div class="endpoint-desc">Employee directory roster with multi-metric performance indicators.</div>
                    <button class="btn" onclick="callApi('/api/employees', 'out-emp')">Test Endpoint</button>
                    <pre id="out-emp" class="console-box"></pre>
                </div>
                <div class="endpoint-card">
                    <div><span class="endpoint-tag tag-get">GET</span><span class="endpoint-url">/api/analytics</span></div>
                    <div class="endpoint-desc">Department benchmarks, score dispersion, and workforce KPIs.</div>
                    <button class="btn" onclick="callApi('/api/analytics', 'out-analytics')">Test Endpoint</button>
                    <pre id="out-analytics" class="console-box"></pre>
                </div>
                <div class="endpoint-card">
                    <div><span class="endpoint-tag tag-get">GET</span><span class="endpoint-url">/api/predictions/models</span></div>
                    <div class="endpoint-desc">Held-out test split evaluation metrics for ML classifiers.</div>
                    <button class="btn" onclick="callApi('/api/predictions/models', 'out-models')">Test Endpoint</button>
                    <pre id="out-models" class="console-box"></pre>
                </div>
                <div class="endpoint-card">
                    <div><span class="endpoint-tag tag-post">POST</span><span class="endpoint-url">/api/predictions/predict</span></div>
                    <div class="endpoint-desc">Real-time inference with probability breakdown and driver explanations.</div>
                    <button class="btn" onclick="callPredict('out-pred')">Run Test Inference</button>
                    <pre id="out-pred" class="console-box"></pre>
                </div>
            </div>
        </div>

        <!-- Deployment & Local Streamlit Guide -->
        <div class="section-card">
            <div class="section-header">
                <h2>WorkPulse Architecture & Running Modes</h2>
            </div>
            <div style="font-size:0.875rem; color:var(--wp-text); line-height:1.6;">
                <p>WorkPulse is architected with dual-mode operational capability:</p>
                <ul style="margin: 0.75rem 0 1rem 1.5rem;">
                    <li><strong>Vercel Serverless Function Mode:</strong> Serves this high-performance Web Portal and complete JSON REST API via WSGI entrypoint <code>app.py</code> with zero-config auto-detection.</li>
                    <li><strong>Streamlit Interactive Presentation Mode:</strong> Launch the full interactive multi-page data exploration application locally using:
                        <div style="margin-top:0.4rem; background:#0F172A; color:#E2E8F0; padding:0.6rem 0.8rem; border-radius:6px; font-family:monospace;">
                            python -m streamlit run app.py
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <footer>
        WorkPulse · Employee Performance Review System · Mini-Project Enterprise Suite
    </footer>

    <script>
        async function callApi(endpoint, outId) {{
            const el = document.getElementById(outId);
            el.style.display = 'block';
            el.textContent = 'Fetching ' + endpoint + '...';
            try {{
                const res = await fetch(endpoint);
                const data = await res.json();
                el.textContent = JSON.stringify(data, null, 2);
            }} catch (err) {{
                el.textContent = 'Error: ' + err.message;
            }}
        }}

        async function callPredict(outId) {{
            const el = document.getElementById(outId);
            el.style.display = 'block';
            el.textContent = 'Executing Random Forest real-time inference...';
            try {{
                const res = await fetch('/api/predictions/predict', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        department: "Engineering",
                        attendance_rate: 94.0,
                        task_completion_rate: 88.5,
                        training_hours: 42.0,
                        experience_years: 4.5,
                        previous_performance: 3.8,
                        model_type: "Random Forest"
                    }})
                }});
                const data = await res.json();
                el.textContent = JSON.stringify(data, null, 2);
            }} catch (err) {{
                el.textContent = 'Error: ' + err.message;
            }}
        }}
    </script>
</body>
</html>
"""
        return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

    return app
