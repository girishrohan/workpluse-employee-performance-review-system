"""
WorkPulse — Employee Performance Review System
Enterprise SaaS UI/UX Presentation Engine built with Streamlit & Plotly.
"""

import json
import os
from datetime import date, datetime, timedelta
from html import escape
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from models.train_model import (
    FEATURE_COLS_CATEGORICAL,
    FEATURE_COLS_NUMERIC,
    TARGET_CLASSES,
    train_and_evaluate_all_models,
)
from services.prediction_service import run_employee_prediction
from services.workpulse_service import (
    DB_PATH,
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
    update_employee_metrics,
    update_employee_profile,
)
from database.db_manager import import_records_from_df
from ui_components import (
    ICONS,
    apply_chart_style,
    get_icon,
    render_cycle_banner,
    render_employee_profile_card,
    render_empty_state,
    render_executive_report_header,
    render_metric_card,
    render_page_heading,
    render_status_badge,
    show_empty_state,
)
from homepage_view import render_homepage
from utils.validation import VALID_DEPARTMENTS, validate_csv_dataset
from auth.auth_service import (
    init_auth_tables,
    ensure_default_admin,
    log_audit,
    get_all_users,
    get_audit_log,
    update_user,
    create_user,
    approve_user,
    delete_user,
    find_employee_by_code,
    link_demo_employee_account,
)
from auth_views import (
    render_login_page,
    render_register_page,
    render_change_password_page,
    render_forgot_password_page,
    render_password_reset_page,
    render_logout_confirmation_page,
    go_to_home,
)

# Navigation Registry - Premium Enterprise SaaS Design
NAV_ITEMS = {
    "Home": "Product Home",
    "Dashboard": "Dashboard",
    "My Profile": "My Profile",
    "Employees": "Employees",
    "Performance Periods": "Review Cycles",
    "Performance Areas": "KPI Framework",
    "Assessments": "Assessments",
    "Analytics": "Analytics",
    "Predictions": "Predictions",
    "Reports": "Reports",
    "Notifications": "Notifications",
    "Settings": "Settings",
}

# Admin-only navigation items (visible only to Admin role)
ADMIN_NAV_ITEMS = {
    "User Management": "User Management",
}

# Navigation Icon Registry - Maps page names to Material Icon keys
NAV_ICONS = {
    "Home": ":material/home:",
    "Dashboard": ":material/dashboard:",
    "My Profile": ":material/account_circle:",
    "Employees": ":material/group:",
    "Performance Periods": ":material/calendar_month:",
    "Performance Areas": ":material/tune:",
    "Assessments": ":material/fact_check:",
    "Analytics": ":material/insights:",
    "Predictions": ":material/auto_awesome:",
    "Reports": ":material/description:",
    "Notifications": ":material/notifications:",
    "Settings": ":material/settings:",
    "User Management": ":material/manage_accounts:",
}

STATUS_OPTIONS = ("Active", "On leave", "Inactive")
PERIOD_STATUS_OPTIONS = ("Draft", "Active", "Completed")
SESSION_MAX_AGE_HOURS = 12

# Authoritative route permissions. Keep this in sync with navigation rendering.
PAGE_ROLES: dict[str, set[str]] = {
    "Home": {"admin", "hr", "employee"},
    "Dashboard": {"admin", "hr", "employee"},
    "My Profile": {"admin", "hr", "employee"},
    "Employees": {"admin", "hr"},
    "Performance Periods": {"admin", "hr"},
    "Performance Areas": {"admin", "hr"},
    "Assessments": {"admin", "hr"},
    "Analytics": {"admin", "hr"},
    "Predictions": {"admin", "hr"},
    "Reports": {"admin", "hr"},
    "Notifications": {"admin", "hr", "employee"},
    "Settings": {"admin"},
    "User Management": {"admin"},
}


def can_access_page(page: str, role: str) -> bool:
    """Return True when the given role may open the given page."""
    return role.lower() in PAGE_ROLES.get(page, {"admin"})



# ---------------------------------------------------------------------------
# Role-based Route Guards
# ---------------------------------------------------------------------------

def require_role(*roles: str) -> bool:
    """
    Check if the current user has one of the required roles.
    Returns True if authorized, False otherwise.
    """
    user = st.session_state.get("user", {})
    user_role = user.get("role", "").lower()
    return user_role in [r.lower() for r in roles]


def require_admin(func):
    """Decorator for admin-only pages."""
    def wrapper(*args, **kwargs):
        if not require_role("admin"):
            st.error("Access denied. Admin privileges required.")
            st.sidebar.button("← Go to Dashboard", key="admin_back")
            return
        return func(*args, **kwargs)
    return wrapper


def require_hr_or_admin(func):
    """Decorator for HR/Admin-only pages."""
    def wrapper(*args, **kwargs):
        if not require_role("hr", "admin"):
            st.error("Access denied. HR or Admin privileges required.")
            st.sidebar.button("← Go to Dashboard", key="hr_admin_back")
            return
        return func(*args, **kwargs)
    return wrapper


def _admin_alert(message: str) -> None:
    """Display an admin-level alert."""
    st.warning(f"⚠️ {message}")


def _unauthorized_alert() -> None:
    """Display an access denied message."""
    st.error("❌ You do not have permission to access this page.")
    st.info("Please contact an administrator if you believe this is an error.")


def _section_heading(label: str, caption: str = "") -> None:
    """Render a section heading with optional caption."""
    st.markdown(
        f"""
        <div style="margin:1.75rem 0 0.75rem 0;">
            <h3 style="font-size:1.0625rem; font-weight:700; color:var(--wp-navy); margin:0 0 0.25rem 0;">{escape(label)}</h3>
            {f'<p style="font-size:0.8125rem; color:var(--wp-text-secondary); margin:0;">{escape(caption)}</p>' if caption else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def _load_styles() -> str:
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as stylesheet:
            return stylesheet.read()
    return ""


def _configure_page() -> None:
    st.set_page_config(
        page_title="WorkPulse · Employee Performance Review System",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css = _load_styles()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _get_category(score: float) -> str:
    if score < 60:
        return "Needs Support"
    if score < 80:
        return "Moderate"
    return "High"


def _training_frame(employees: pd.DataFrame) -> pd.DataFrame:
    required = FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL + ["performance_category"]
    missing = [column for column in required if column not in employees.columns]
    if missing:
        return pd.DataFrame(columns=required)
    if "performance_category" in FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL:
        raise ValueError("The model target must not be included in the input features.")
    frame = employees[required].copy().dropna(subset=required)
    return frame[frame["performance_category"].isin(TARGET_CLASSES)].reset_index(drop=True)


@st.cache_resource(show_spinner="Evaluating models on a held-out test split…")
def _train_models(labelled_data: pd.DataFrame) -> tuple[dict, dict]:
    results, pipelines, _ = train_and_evaluate_all_models(
        labelled_data, models_dir="models"
    )
    return results, pipelines


def _sidebar(summary: dict[str, int], admin_name: str, workspace_name: str) -> str:
    admin_name = escape(admin_name)
    workspace_name = escape(workspace_name)
    user = st.session_state.get("user", {})
    role = user.get("role", "admin").lower()
    full_name = user.get("full_name", admin_name)

    st.sidebar.markdown(
        f"""
        <div class="wp-brand">
            <div class="wp-brand-mark">
                {ICONS['pulse']}
            </div>
            <div class="wp-brand-title">
                <strong>{workspace_name}</strong>
                <small>PEOPLE ANALYTICS</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="wp-sidebar-section">NAVIGATION</div>', unsafe_allow_html=True)

    # Role-based navigation access control (authoritative map: PAGE_ROLES)
    allowed_pages = [
        page
        for page in list(NAV_ITEMS.keys()) + list(ADMIN_NAV_ITEMS.keys())
        if can_access_page(page, role)
    ]

    visible_nav = {k: v for k, v in NAV_ITEMS.items() if k in allowed_pages}
    # Also add admin-only nav items
    for k, v in ADMIN_NAV_ITEMS.items():
        if k in allowed_pages:
            visible_nav[k] = v

    if "active_page" not in st.session_state or st.session_state.active_page not in allowed_pages:
        st.session_state.active_page = "Dashboard"

    # Keep _nav_radio in sync with active_page if set by another component
    if st.session_state.active_page in visible_nav:
        st.session_state["_nav_radio"] = st.session_state.active_page

    selected_idx = list(visible_nav.keys()).index(st.session_state.active_page) if st.session_state.active_page in visible_nav else 0

    # Render navigation using radio with clean Material icons
    def nav_formatter(p):
        icon = NAV_ICONS.get(p, ":material/arrow_right:")
        label = visible_nav.get(p, p)
        return f"{icon} {label}"

    def _on_nav_change():
        chosen = st.session_state.get("_nav_radio")
        if chosen and chosen in visible_nav:
            st.session_state.active_page = chosen
            st.query_params["page"] = chosen

    st.sidebar.radio(
        "Navigation",
        options=list(visible_nav.keys()),
        format_func=nav_formatter,
        label_visibility="collapsed",
        key="_nav_radio",
        on_change=_on_nav_change,
    )

    role_colors = {"admin": "#168C83", "hr": "#D97706", "employee": "#102A43"}
    role_color = role_colors.get(role, "#64748B")

    st.sidebar.markdown(
        f"""
        <div class="wp-sidebar-footer">
            <div class="wp-sidebar-section" style="margin-top:0;">SIGNED IN AS</div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:0.65rem 0.75rem; margin-bottom:0.75rem;">
                <div style="font-size:0.8125rem; font-weight:700; color:var(--wp-navy);">{escape(full_name)}</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.25rem;">
                    <span style="font-size:0.7rem; color:#64748B;">{escape(user.get('email', ''))}</span>
                    <span style="font-size:0.6rem; font-weight:700; color:{role_color}; text-transform:uppercase; letter-spacing:0.06em; background:{role_color}18; padding:0.12rem 0.4rem; border-radius:4px;">{escape(role.upper())}</span>
                </div>
            </div>
            <div class="wp-sidebar-section" style="margin-top:0;">WORKSPACE SYSTEM</div>
            <div class="wp-db-status">
                <span class="wp-status-dot"></span>
                <span>SQLite Connected</span>
            </div>
            <div class="wp-sidebar-count">{summary["total_employees"]:,} registered employees</div>
            {f'<div style="font-size:0.7rem; color:var(--wp-teal); font-weight:600; margin-bottom:0.75rem;">Includes {summary["demo_employees"]:,} demo records</div>' if summary.get("demo_employees") else ''}
            <div class="wp-sidebar-tagline">
                Understand Performance.<br>
                <span>Empower Growth.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sign Out Button
    if st.sidebar.button(":material/logout: Sign Out", use_container_width=True, key="sidebar_logout_btn"):
        st.session_state["show_logout_confirm"] = True
        st.rerun()

    return st.session_state.active_page


def _topbar(page: str, unread_count: int, admin_name: str) -> None:
    user = st.session_state.get("user", {})
    role = user.get("role", "admin").lower()
    display_name = user.get("full_name", admin_name).strip() or "User"
    first_name = display_name.split()[0]

    title_col, home_col, notification_col, profile_col, action_col = st.columns(
        [3.8, 1.4, 1.1, 1.5, 2.2], vertical_alignment="center"
    )
    with title_col:
        page_label = NAV_ITEMS.get(page, page)
        st.markdown(
            f"""
            <div class="wp-topbar-title-group">
                <div class="wp-breadcrumb">WORKSPACE &nbsp;/&nbsp; <span>{escape(page_label).upper()}</span></div>
                <div style="font-size:1.375rem; font-weight:700; color:var(--wp-navy); letter-spacing:-0.025em;">{escape(page_label)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with home_col:
        if st.button(":material/home: Home", help="Open public product homepage", use_container_width=True, key="top_home_btn"):
            st.session_state.active_page = "Home"
            st.query_params["page"] = "Home"
            st.rerun()
    with notification_col:
        notif_label = f":material/notifications: {unread_count}" if unread_count else ":material/notifications: Inbox"
        if st.button(notif_label, help="View notifications and pending reviews", use_container_width=True, key="top_notif"):
            st.session_state.active_page = "Notifications"
            st.query_params["page"] = "Notifications"
            st.rerun()
    with profile_col:
        role_tag = f"({role.upper()})"
        if st.button(
            f":material/account_circle: {first_name} {role_tag}",
            help="Open your profile and account details",
            use_container_width=True,
            key="top_profile",
        ):
            st.session_state.active_page = "My Profile"
            st.query_params["page"] = "My Profile"
            st.rerun()

    action_map = {
        "Dashboard": ("＋  New Assessment", "Assessments", "show_assessment_form"),
        "My Profile": ("⌂  Dashboard", "Dashboard", None),
        "Employees": ("＋  Add Employee", "Employees", "show_employee_form"),
        "Performance Periods": ("＋  New Period", "Performance Periods", "show_period_form"),
        "Performance Areas": ("✓  Save Weights", "Performance Areas", "save_areas_requested"),
        "Assessments": ("＋  New Assessment", "Assessments", "show_assessment_form"),
        "Analytics": ("▤  Export Reports", "Reports", None),
        "Predictions": ("✓  Conduct Review", "Assessments", "show_assessment_form"),
        "Reports": ("⌂  Dashboard", "Dashboard", None),
        "Notifications": ("✓  Review Queue", "Assessments", "show_assessment_form"),
        "Settings": ("🔔  View Alerts", "Notifications", None),
    }

    if role == "employee":
        btn_label, dest_page, flag = ("⌂  My Overview", "Dashboard", None)
    else:
        btn_label, dest_page, flag = action_map.get(page, ("＋  New Assessment", "Assessments", "show_assessment_form"))

    with action_col:
        if st.button(btn_label, type="primary", use_container_width=True, key=f"top_btn_{page}"):
            st.session_state.active_page = dest_page
            if flag:
                st.session_state[flag] = True
            st.rerun()


def _section_heading(title: str, caption: str | None = None) -> None:
    cap_html = f'<span class="wp-section-caption">{escape(caption)}</span>' if caption else ""
    st.markdown(
        f"""
        <div class="wp-section-header">
            <h2 class="wp-section-title">{escape(title)}</h2>
            {cap_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _get_current_employee_record(user: dict, employees: pd.DataFrame) -> pd.Series | None:
    """Resolve only the employee profile explicitly linked to this account.

    A missing link returns None instead of falling back to another person's
    record, which would leak another employee's review history.
    """
    if employees.empty:
        return None
    emp_id = user.get("employee_id")
    if emp_id is not None and not (isinstance(emp_id, float) and np.isnan(emp_id)):
        try:
            wanted = int(emp_id)
        except (TypeError, ValueError):
            wanted = None
        if wanted is not None:
            match = employees[
                pd.to_numeric(employees["employee_id"], errors="coerce") == wanted
            ]
            return match.iloc[0] if not match.empty else None
    full_name = str(user.get("full_name", "")).strip().lower()
    if full_name:
        matches = employees[
            employees["employee_name"].fillna("").str.lower().str.strip() == full_name
        ]
        if len(matches) == 1:
            return matches.iloc[0]
    return None


def _metric_value(record: Any, key: str) -> float | None:
    """Return a finite numeric metric value, or None when it is missing."""
    value = record.get(key) if hasattr(record, "get") else getattr(record, key, None)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _employee_dashboard(
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
    periods: pd.DataFrame,
    user: dict,
) -> None:
    emp = _get_current_employee_record(user, employees)
    if emp is None:
        render_empty_state("No Employee Profile Linked", "No employee profile is currently associated with your account.")
        return

    emp_id = int(emp["employee_id"])
    emp_name = str(emp["employee_name"])
    emp_code = str(emp["employee_code"])
    emp_dept = str(emp.get("department", "General"))
    emp_desig = str(emp.get("designation") or "Staff Member")

    emp_assessments = (
        assessments[assessments["employee_id"] == emp_id].sort_values("assessment_date", ascending=False)
        if not assessments.empty
        else pd.DataFrame()
    )

    active_period = periods[periods["status"] == "Active"] if not periods.empty else pd.DataFrame()
    if not active_period.empty:
        curr = active_period.iloc[0]
        has_reviewed = not emp_assessments.empty and any(emp_assessments["period_id"] == curr["period_id"])
        render_cycle_banner(
            cycle_name=curr["name"],
            status="Active",
            due_date=str(curr["end_date"]),
            progress_pct=100.0 if has_reviewed else 0.0,
            total_reviews=1 if has_reviewed else 0,
            pending_reviews=0 if has_reviewed else 1,
        )

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid var(--wp-border); border-left:4px solid var(--wp-teal); border-radius:var(--wp-radius-md); padding:1.25rem 1.5rem; margin-bottom:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:var(--wp-teal); letter-spacing:0.06em; text-transform:uppercase;">PERSONAL PERFORMANCE PORTAL</span>
                    <h2 style="font-size:1.5rem; font-weight:700; color:var(--wp-navy); margin:0.25rem 0 0.25rem 0;">Welcome, {escape(emp_name)}</h2>
                    <span style="font-size:0.875rem; color:var(--wp-text-secondary);">{escape(emp_code)} · {escape(emp_desig)} · {escape(emp_dept)}</span>
                </div>
                <div>
                    {render_status_badge(str(emp.get('status', 'Active')))}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    latest_score = float(emp_assessments.iloc[0]["overall_score"]) if not emp_assessments.empty else None
    latest_score_disp = f"{latest_score:.1f} / 100" if latest_score is not None else "— / 100"
    latest_cat = _get_category(latest_score) if latest_score is not None else "Pending"

    att_rate = _metric_value(emp, "attendance_rate")
    task_rate = _metric_value(emp, "task_completion_rate")
    train_hrs = _metric_value(emp, "training_hours")
    training_target = 40.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Latest Review Score",
            value=latest_score_disp,
            detail=f"Standing: {latest_cat}" if latest_score is not None else "Awaiting review",
            icon="target",
            tone="navy",
            trend=None,
        )
    with c2:
        render_metric_card(
            label="Attendance Rate",
            value=f"{att_rate:.1f}%" if att_rate is not None else "Not recorded",
            detail="Tracked work attendance" if att_rate is not None else "No attendance metric on file",
            icon="calendar",
            tone="teal",
        )
    with c3:
        render_metric_card(
            label="Task Completion",
            value=f"{task_rate:.1f}%" if task_rate is not None else "Not recorded",
            detail="Deliverables completed on-time" if task_rate is not None else "No delivery metric on file",
            icon="assessments",
            tone="green",
        )
    with c4:
        render_metric_card(
            label="Training Completed",
            value=f"{train_hrs:.0f} hrs" if train_hrs is not None else "Not recorded",
            detail=(
                f"{min(100, train_hrs / training_target * 100):.0f}% of {training_target:.0f}h annual target"
                if train_hrs is not None
                else "No training hours logged"
            ),
            icon="sparkles",
            tone="amber",
        )

    st.write("")

    _section_heading("Your Profile Dossier", "Holistic indicators and professional milestones")
    render_employee_profile_card(emp.to_dict())

    _section_heading("Development Focus", "Personalised growth signals drawn from your recorded indicators")
    focus_left, focus_right = st.columns(2, gap="large")
    with focus_left:
        training_pct = (
            min(100.0, train_hrs / training_target * 100) if train_hrs is not None else 0.0
        )
        training_text = (
            f"{train_hrs:.0f} of {training_target:.0f} recommended annual hours"
            if train_hrs is not None
            else "Training hours have not been logged yet"
        )
        st.markdown(
            f"""
            <div class="wp-card" style="margin-bottom:0;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <strong style="color:var(--wp-navy); font-size:0.9375rem;">Learning Progress</strong>
                    <span style="font-size:0.75rem; font-weight:700; color:var(--wp-teal);">{training_pct:.0f}%</span>
                </div>
                <div class="wp-progress-wrap" style="height:8px;">
                    <div class="wp-progress-bar" style="width:{training_pct:.0f}%;"></div>
                </div>
                <p style="font-size:0.8125rem; color:var(--wp-text-secondary); margin:0.6rem 0 0 0;">{escape(training_text)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if train_hrs is not None:
            remaining = max(0.0, training_target - train_hrs)
            st.caption(
                f"{remaining:.0f} hours remain to reach the recommended annual development target."
                if remaining
                else "Annual development target reached — excellent commitment to growth."
            )
    with focus_right:
        focus_points: list[str] = []
        if not emp_assessments.empty and "scores_json" in emp_assessments.columns:
            try:
                latest_scores = json.loads(str(emp_assessments.iloc[0]["scores_json"]))
                ordered = sorted(
                    ((k, float(v)) for k, v in latest_scores.items()),
                    key=lambda item: item[1],
                )
                for indicator, score in ordered[:2]:
                    focus_points.append(
                        f"<strong>{escape(indicator)}</strong> scored {score:.1f}/100 — agree a focused development plan with your manager."
                    )
            except (ValueError, TypeError, json.JSONDecodeError):
                pass
        if att_rate is not None and att_rate < 90:
            focus_points.append(
                f"Attendance is {att_rate:.1f}%. Discuss any workplace barriers and agree a sustainable schedule."
            )
        if task_rate is not None and task_rate < 85:
            focus_points.append(
                f"Task completion is {task_rate:.1f}%. Review workload and priority-setting with your manager."
            )
        if not focus_points:
            focus_points.append(
                "No improvement signals are recorded yet. Your development focus will update after your next review."
            )
        st.markdown(
            '<div class="wp-card" style="margin-bottom:0;">'
            '<strong style="color:var(--wp-navy); font-size:0.9375rem;">Suggested Focus Areas</strong>'
            "<ul style='margin:0.6rem 0 0 1rem; padding:0; font-size:0.8125rem; color:var(--wp-text-secondary); line-height:1.6;'>"
            + "".join(f"<li style='margin-bottom:0.35rem;'>{point}</li>" for point in focus_points[:3])
            + "</ul></div>",
            unsafe_allow_html=True,
        )

    left, right = st.columns(2, gap="large")
    with left:
        _section_heading("Competency Breakdown", "Scores by performance indicator from latest review")
        if not emp_assessments.empty and "scores_json" in emp_assessments.columns:
            try:
                scores_map = json.loads(str(emp_assessments.iloc[0]["scores_json"]))
                comp_df = pd.DataFrame(
                    [{"Indicator": k, "Score": float(v)} for k, v in scores_map.items()]
                )
                fig = px.bar(
                    comp_df,
                    x="Score",
                    y="Indicator",
                    orientation="h",
                    range_x=[0, 100],
                    color_discrete_sequence=["#168C83"],
                    text_auto=".1f",
                )
                st.plotly_chart(apply_chart_style(fig), use_container_width=True)
            except Exception:
                render_empty_state("No Breakdown Recorded", "Detailed competency scoring will appear after your evaluation.")
        else:
            render_empty_state("No Competency Breakdown", "Evaluations for the current cycle have not yet been submitted.")

    with right:
        _section_heading("Review History Trajectory", "Historical review scores across performance cycles")
        if not emp_assessments.empty and len(emp_assessments) > 1:
            traj_df = emp_assessments.sort_values("assessment_date").copy()
            fig = px.line(
                traj_df,
                x="assessment_date",
                y="overall_score",
                markers=True,
                labels={"assessment_date": "Date", "overall_score": "Score"},
                color_discrete_sequence=["#102A43"],
            )
            fig.update_yaxes(range=[40, 100])
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        elif not emp_assessments.empty:
            single_score = float(emp_assessments.iloc[0]["overall_score"])
            st.info(f"You have 1 recorded evaluation with score **{single_score:.1f} / 100** ({_get_category(single_score)}). Historical trajectory graphs will populate across multiple review cycles.")
        else:
            render_empty_state("No Review Trajectory", "Previous cycle data will appear here.")

    _section_heading("Evaluation History & Feedback", "Timestamped managerial reviews and feedback notes")
    if emp_assessments.empty:
        render_empty_state("No Reviews Recorded", "Once your manager submits an assessment, the detailed feedback will appear here.")
    else:
        table = emp_assessments.copy()
        table["Outcome"] = table["overall_score"].map(_get_category)
        st.dataframe(
            table[
                ["period_name", "assessment_date", "reviewer", "overall_score", "Outcome", "comments"]
            ].rename(
                columns={
                    "period_name": "Review Cycle",
                    "assessment_date": "Date",
                    "reviewer": "Reviewer",
                    "overall_score": "Score",
                    "Outcome": "Tier",
                    "comments": "Manager Feedback & Guidance",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )


# =============================================================================
# 1. DASHBOARD PAGE
# =============================================================================
def _my_profile_page(employees: pd.DataFrame, assessments: pd.DataFrame) -> None:
    """Self-service account and profile page. Never exposes another employee."""
    user = st.session_state.get("user", {})
    role = str(user.get("role", "employee")).lower()
    full_name = str(user.get("full_name") or "User")
    email = str(user.get("email") or "—")
    emp = _get_current_employee_record(user, employees)

    render_page_heading(
        title="My Profile",
        subtitle="Your account details, linked employee dossier, and personal review history.",
        breadcrumb="PERSONAL WORKSPACE",
        badge=role.upper(),
    )

    role_note = {
        "admin": "System administrator account. Workspace settings and user access are managed from the administration pages.",
        "hr": "HR manager account. Employee records and review workflows are available from the navigation.",
        "employee": "Employee account. You can only view your own dossier, evaluations, and notifications.",
    }.get(role, "")

    st.markdown(
        f"""
        <div class="wp-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.6875rem; font-weight:700; color:var(--wp-teal); letter-spacing:0.08em; text-transform:uppercase;">SIGNED-IN ACCOUNT</div>
                    <h2 style="margin:0.25rem 0 0.25rem 0; font-size:1.375rem; color:var(--wp-navy);">{escape(full_name)}</h2>
                    <div style="font-size:0.875rem; color:var(--wp-text-secondary);">{escape(email)} · {role.upper()}</div>
                </div>
                <div style="text-align:right; font-size:0.8125rem; color:var(--wp-text-secondary);">
                    <div><strong>Linked employee ID:</strong> {escape(str(user.get('employee_id') or 'Not linked'))}</div>
                </div>
            </div>
            <p style="margin:0.85rem 0 0 0; font-size:0.8125rem; color:var(--wp-text-secondary);">{escape(role_note)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if emp is None:
        if role == "employee":
            st.warning(
                "Your account is not yet linked to an employee profile. "
                "Contact your HR administrator so they can connect your account to your personnel record."
            )
        else:
            st.info(
                "This account is not linked to an employee profile. That is expected for administrative accounts."
            )
        return

    _section_heading("My Employee Dossier", "Operational indicators maintained by HR")
    render_employee_profile_card(emp.to_dict())

    _section_heading("My Review History", "Assessments recorded against your profile")
    emp_assessments = (
        assessments[assessments["employee_id"] == int(emp["employee_id"])]
        if not assessments.empty
        else pd.DataFrame()
    )
    if emp_assessments.empty:
        render_empty_state(
            "No Reviews Recorded",
            "Your assessment history will appear here after your manager completes a review.",
        )
        return

    history = emp_assessments.copy()
    history["Outcome"] = history["overall_score"].map(_get_category)
    st.dataframe(
        history[
            ["period_name", "assessment_date", "reviewer", "overall_score", "Outcome", "comments"]
        ].rename(
            columns={
                "period_name": "Review Cycle",
                "assessment_date": "Date",
                "reviewer": "Reviewer",
                "overall_score": "Score",
                "Outcome": "Tier",
                "comments": "Manager Feedback & Guidance",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )


def _dashboard(
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
    summary: dict[str, int],
    periods: pd.DataFrame,
) -> None:
    role = st.session_state.get("user", {}).get("role", "employee").lower()
    if role == "employee":
        _employee_dashboard(employees, assessments, periods, st.session_state.get("user", {}))
    elif role == "admin":
        _admin_dashboard(employees, assessments, summary, periods)
    else:
        _hr_dashboard(employees, assessments, summary, periods)


def _admin_dashboard(
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
    summary: dict[str, int],
    periods: pd.DataFrame,
) -> None:
    """Administrator cockpit: access governance, data readiness, and system health."""
    users = get_all_users()
    pending_users = [user for user in users if not user.get("is_active")]
    active_users = [user for user in users if user.get("is_active")]
    admin_users = [user for user in active_users if user.get("role") == "admin"]

    active_period = periods[periods["status"] == "Active"] if not periods.empty else pd.DataFrame()
    if not active_period.empty:
        current = active_period.iloc[0]
        current_assessments = (
            assessments[assessments["period_id"] == current["period_id"]]
            if not assessments.empty
            else pd.DataFrame()
        )
        active_employee_count = int((employees["status"] == "Active").sum()) if not employees.empty else 0
        completed = len(current_assessments)
        render_cycle_banner(
            cycle_name=current["name"],
            status="Active",
            due_date=str(current["end_date"]),
            progress_pct=(completed / active_employee_count * 100) if active_employee_count else 0.0,
            total_reviews=completed,
            pending_reviews=max(0, active_employee_count - completed),
        )

    avg_score = float(assessments["overall_score"].mean()) if not assessments.empty else None
    active_employee_count = int((employees["status"] == "Active").sum()) if not employees.empty else 0
    reviewed_ids = (
        set(pd.to_numeric(assessments["employee_id"], errors="coerce").dropna().astype(int))
        if not assessments.empty
        else set()
    )
    active_ids = (
        set(pd.to_numeric(employees.loc[employees["status"] == "Active", "employee_id"], errors="coerce").dropna().astype(int))
        if not employees.empty
        else set()
    )
    unreviewed_count = len(active_ids - reviewed_ids)
    coverage = (
        (len(active_ids & reviewed_ids) / len(active_ids) * 100) if active_ids else 0.0
    )

    metric_columns = ["attendance_rate", "task_completion_rate", "training_hours", "previous_performance"]
    available_metric_columns = [column for column in metric_columns if column in employees.columns]
    missing_metrics = (
        int(employees[available_metric_columns].isna().any(axis=1).sum())
        if available_metric_columns and not employees.empty
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            label="Workforce Mean Score",
            value=f"{avg_score:.1f} / 100" if avg_score is not None else "— / 100",
            detail="Overall review benchmark" if avg_score is not None else "No reviews recorded yet",
            icon="target",
            tone="navy",
        )
    with col2:
        render_metric_card(
            label="Active Workforce",
            value=f"{active_employee_count:,}",
            detail=f"{summary.get('total_employees', 0):,} total employee profiles",
            icon="employees",
            tone="teal",
        )
    with col3:
        render_metric_card(
            label="Review Coverage",
            value=f"{coverage:.0f}%",
            detail=f"{unreviewed_count:,} active employees not yet reviewed",
            icon="assessments",
            tone="green",
        )
    with col4:
        render_metric_card(
            label="Pending Access Requests",
            value=f"{len(pending_users):,}",
            detail="Accounts awaiting administrator approval",
            icon="user-check",
            tone="amber",
        )

    st.write("")
    _section_heading(
        "Governance & Data Readiness",
        "Access control, evidence quality, and operational follow-ups that need an administrator",
    )
    left, right = st.columns(2, gap="large")

    with left:
        pending_rows = "".join(
            f"<li style='margin-bottom:0.3rem;'>{escape(str(user.get('full_name') or user.get('email')))} "
            f"<span style='color:var(--wp-text-muted);'>({escape(str(user.get('email')))})</span></li>"
            for user in pending_users[:4]
        )
        st.markdown(
            f"""
            <div class="wp-card" style="margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:var(--wp-navy); font-size:0.9375rem;">Account Governance</strong>
                    <span class="wp-badge wp-badge-active">{len(active_users):,} active accounts</span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.5rem; margin-top:0.85rem; text-align:center;">
                    <div style="background:var(--wp-bg); border-radius:6px; padding:0.5rem;">
                        <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">Admins</div>
                        <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{len(admin_users)}</div>
                    </div>
                    <div style="background:var(--wp-bg); border-radius:6px; padding:0.5rem;">
                        <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">HR</div>
                        <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{sum(1 for u in active_users if u.get('role') == 'hr')}</div>
                    </div>
                    <div style="background:var(--wp-bg); border-radius:6px; padding:0.5rem;">
                        <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">Staff</div>
                        <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{sum(1 for u in active_users if u.get('role') == 'employee')}</div>
                    </div>
                </div>
                <div style="margin-top:0.85rem; font-size:0.8125rem; color:var(--wp-text-secondary);">
                    <strong style="color:var(--wp-navy);">Pending approvals:</strong>
                    {f"<ul style='margin:0.35rem 0 0 1rem; padding:0;'>{pending_rows}</ul>" if pending_rows else "None — all access requests are processed."}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open User Management", use_container_width=True, key="admin_goto_users"):
            st.session_state.active_page = "User Management"
            st.query_params["page"] = "User Management"
            st.rerun()

    with right:
        st.markdown(
            f"""
            <div class="wp-card" style="margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:var(--wp-navy); font-size:0.9375rem;">Review & Data Readiness</strong>
                    <span style="font-size:0.75rem; font-weight:700; color:var(--wp-teal);">{coverage:.0f}% COVERAGE</span>
                </div>
                <div class="wp-progress-wrap" style="height:8px; margin:0.6rem 0 0.85rem 0;">
                    <div class="wp-progress-bar" style="width:{coverage:.0f}%;"></div>
                </div>
                <div style="font-size:0.8125rem; color:var(--wp-text-secondary); line-height:1.7;">
                    <div><strong style="color:var(--wp-navy);">Unreviewed active employees:</strong> {unreviewed_count:,}</div>
                    <div><strong style="color:var(--wp-navy);">Profiles missing operational metrics:</strong> {missing_metrics:,}</div>
                    <div><strong style="color:var(--wp-navy);">Demo records in dataset:</strong> {summary.get('demo_employees', 0):,}</div>
                </div>
                <p style="margin:0.75rem 0 0 0; font-size:0.75rem; color:var(--wp-text-muted);">
                    Operational metrics feed the ML feature set. Missing metrics reduce prediction quality; record them from the employee dossier.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Employee Directory", use_container_width=True, key="admin_goto_employees"):
            st.session_state.active_page = "Employees"
            st.query_params["page"] = "Employees"
            st.rerun()

    _section_heading("Recent Audit Activity", "Security-relevant account and configuration events")
    audit_entries = get_audit_log(limit=10)
    if audit_entries:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Time": str(entry.get("performed_at", ""))[:19],
                        "Action": entry.get("action", ""),
                        "Actor": entry.get("performed_by_email") or "System",
                        "Detail": entry.get("detail", ""),
                    }
                    for entry in audit_entries
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        render_empty_state("No Audit Activity", "Account and configuration events will be recorded here.")

    _section_heading("Administration Launchpad")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("＋  Add Employee", use_container_width=True, key="admin_add_emp"):
            st.session_state.active_page = "Employees"
            st.session_state.show_employee_form = True
            st.rerun()
    with c2:
        if st.button("👥  Manage Access", use_container_width=True, key="admin_manage_access"):
            st.session_state.active_page = "User Management"
            st.rerun()
    with c3:
        if st.button("⌁  ML Predictions", use_container_width=True, key="admin_predictions"):
            st.session_state.active_page = "Predictions"
            st.rerun()
    with c4:
        if st.button("▤  Executive Report", use_container_width=True, key="admin_report"):
            st.session_state.active_page = "Reports"
            st.rerun()


def _hr_dashboard(
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
    summary: dict[str, int],
    periods: pd.DataFrame,
) -> None:
    # 1. Active Period Progress Banner
    active_period = periods[periods["status"] == "Active"] if not periods.empty else pd.DataFrame()
    if not active_period.empty:
        curr = active_period.iloc[0]
        curr_assessments = assessments[assessments["period_id"] == curr["period_id"]] if not assessments.empty else pd.DataFrame()
        active_emp_count = len(employees[employees["status"] == "Active"]) if not employees.empty else 0
        comp_count = len(curr_assessments)
        pct = (comp_count / active_emp_count * 100) if active_emp_count > 0 else 0
        render_cycle_banner(
            cycle_name=curr["name"],
            status="Active",
            due_date=str(curr["end_date"]),
            progress_pct=pct,
            total_reviews=comp_count,
            pending_reviews=max(0, active_emp_count - comp_count),
        )

    # 2. Empty-state guidance (no fabricated data or demo seeding from HR view)
    if assessments.empty:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid var(--wp-border); border-left:4px solid var(--wp-teal); border-radius:var(--wp-radius-md); padding:1rem 1.25rem; margin-bottom:1.25rem;">
                <strong style="color:var(--wp-navy); font-size:0.9375rem;">No assessments recorded yet</strong>
                <div style="color:var(--wp-text-secondary); font-size:0.8125rem; margin-top:0.2rem;">
                    The workspace has {summary.get('total_employees', 0):,} employee profiles.
                    Start a review cycle and complete the first assessment to populate analytics and executive reports.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, _ = st.columns([2.2, 2.2, 5.6])
        if c1.button("＋ Conduct Assessment", type="primary", use_container_width=True, key="hr_empty_assess"):
            st.session_state.active_page = "Assessments"
            st.session_state.show_assessment_form = True
            st.rerun()
        if c2.button("＋ Add Employee Profile", use_container_width=True, key="hr_empty_add"):
            st.session_state.active_page = "Employees"
            st.session_state.show_employee_form = True
            st.rerun()

    # 3. Primary KPI Metric Cards
    avg_score = float(assessments["overall_score"].mean()) if not assessments.empty else None
    avg_score_display = f"{avg_score:.1f} / 100" if avg_score is not None else "— / 100"
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            label="Workforce Mean Score",
            value=avg_score_display,
            detail="Overall review benchmark" if avg_score else "Awaiting reviews",
            icon="target",
            tone="navy",
            trend=None,
        )
    with col2:
        render_metric_card(
            label="Registered Workforce",
            value=f"{summary['total_employees']:,}",
            detail="Active talent profiles in system",
            icon="employees",
            tone="teal",
        )
    with col3:
        render_metric_card(
            label="Active Cycles",
            value=f"{summary['active_periods']:,}",
            detail="Accepting evaluations",
            icon="calendar",
            tone="green",
        )
    with col4:
        render_metric_card(
            label="Completed Reviews",
            value=f"{summary['completed_assessments']:,}",
            detail="Logged to review history",
            icon="assessments",
            tone="amber",
        )

    st.write("")

    # 4. Main Visualizations Row
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        _section_heading("Performance Distribution", "Outcome tier breakdown based on weighted scores")
        if not assessments.empty:
            chart_data = (
                assessments.sort_values(["assessment_date", "assessment_id"])
                .drop_duplicates("employee_id", keep="last")
                .copy()
            )
            chart_data["Performance"] = chart_data["overall_score"].map(_get_category)
            counts = (
                chart_data["Performance"]
                .value_counts()
                .reindex(["High", "Moderate", "Needs Support"], fill_value=0)
                .rename_axis("Performance")
                .reset_index(name="Employees")
            )
            fig = px.pie(
                counts,
                names="Performance",
                values="Employees",
                hole=0.68,
                color="Performance",
                color_discrete_map={
                    "High": "#0D9488",
                    "Moderate": "#D97706",
                    "Needs Support": "#E11D48",
                },
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hoverinfo="label+value+percent",
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        else:
            render_empty_state("No Review Distribution Yet", "Log employee performance assessments to reveal distribution tiers.")

    with right:
        _section_heading("Department Benchmark", "Average overall performance score by department")
        if not assessments.empty:
            dept_data = (
                assessments.groupby("department", as_index=False)["overall_score"]
                .mean()
                .sort_values("overall_score", ascending=True)
            )
            fig = px.bar(
                dept_data,
                x="overall_score",
                y="department",
                orientation="h",
                labels={"overall_score": "Average Score", "department": ""},
                range_x=[0, 100],
                color_discrete_sequence=["#168C83"],
                text_auto=".1f",
            )
            fig.add_vline(x=75.0, line_dash="dash", line_color="#94A3B8", annotation_text="Benchmark (75)")
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        else:
            render_empty_state("Department Benchmark", "Department comparisons appear once assessments are recorded.")

    # 5. Trajectory & Action Queue
    trend_col, queue_col = st.columns([1.15, 1], gap="large")
    with trend_col:
        _section_heading("Performance Trajectory", "Historical review score progression across quarters")
        if not assessments.empty:
            trend = assessments.copy()
            trend["month"] = pd.to_datetime(trend["assessment_date"]).dt.to_period("M").astype(str)
            monthly = (
                trend.groupby("month", as_index=False)["overall_score"]
                .mean()
                .sort_values("month")
            )
            fig = px.line(
                monthly,
                x="month",
                y="overall_score",
                markers=True,
                labels={"month": "", "overall_score": "Average Score"},
                color_discrete_sequence=["#168C83"],
            )
            fig.update_traces(line=dict(width=3))
            fig.update_yaxes(range=[40, 100])
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        else:
            render_empty_state("No Trajectory Data", "Historical trend analysis populates with ongoing review cycles.")

    with queue_col:
        _section_heading("Action & Attention Queue", "Employees requiring developmental coaching or awaiting review")
        support = pd.DataFrame()
        if not assessments.empty:
            latest = assessments.sort_values(["assessment_date", "assessment_id"]).drop_duplicates("employee_id", keep="last")
            support = latest[latest["overall_score"] < 60][["employee_code", "employee_name", "department", "overall_score"]].copy()
            support.rename(columns={"overall_score": "Latest Score"}, inplace=True)
            support["Attention"] = "Needs Support"

        pending = get_pending_reviews()
        if not pending.empty:
            pending_rows = pending[["employee_code", "employee_name", "department"]].copy()
            pending_rows["Latest Score"] = "Pending"
            pending_rows["Attention"] = "Awaiting Review"
            support = pd.concat([support, pending_rows]).drop_duplicates("employee_code")

        if support.empty:
            st.success("All employees in active cycles are on track and reviewed.")
        else:
            st.dataframe(
                support.head(7).rename(
                    columns={
                        "employee_code": "Employee ID",
                        "employee_name": "Full Name",
                        "department": "Department",
                        "Latest Score": "Score",
                        "Attention": "Status",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

    # 6. Recent Reviews Roster
    _section_heading("Recent Evaluations", "Latest validated performance records")
    if assessments.empty:
        render_empty_state("No Recorded Reviews", "Completed reviews will be catalogued here.")
    else:
        recent = assessments.head(6).copy()
        recent["Result"] = recent["overall_score"].map(_get_category)
        st.dataframe(
            recent[
                [
                    "employee_code", "employee_name", "department",
                    "period_name", "assessment_date", "overall_score", "Result", "reviewer",
                ]
            ].rename(
                columns={
                    "employee_code": "Employee ID",
                    "employee_name": "Employee",
                    "department": "Department",
                    "period_name": "Cycle",
                    "assessment_date": "Date",
                    "overall_score": "Score",
                    "Result": "Tier",
                    "reviewer": "Reviewer",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    # 7. Quick Workflow Launchpad
    _section_heading("Quick Launchpad")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("＋  Add Employee", use_container_width=True, key="dash_add_emp"):
            st.session_state.active_page = "Employees"
            st.session_state.show_employee_form = True
            st.rerun()
    with c2:
        if st.button("✓  Conduct Assessment", use_container_width=True, key="dash_add_assess"):
            st.session_state.active_page = "Assessments"
            st.session_state.show_assessment_form = True
            st.rerun()
    with c3:
        if st.button("▤  Executive Report", use_container_width=True, key="dash_gen_rep"):
            st.session_state.active_page = "Reports"
            st.rerun()
    with c4:
        if st.button("⌁  Run ML Prediction", use_container_width=True, key="dash_run_ml"):
            st.session_state.active_page = "Predictions"
            st.rerun()


# =============================================================================
# 2. EMPLOYEES DIRECTORY & PROFILE DOSSIER
# =============================================================================
def _employees_page(employees: pd.DataFrame, assessments: pd.DataFrame) -> None:
    if not require_role("hr", "admin"):
        _unauthorized_alert()
        return

    render_page_heading(
        title="Employee Directory",
        subtitle="Manage employee records, review eligibility, and historical performance profiles.",
        breadcrumb="TALENT DIRECTORY",
        badge=f"{len(employees):,} Registered" if not employees.empty else None,
    )

    if st.session_state.pop("show_employee_form", False):
        st.session_state.employee_form_open = True

    # Add Employee Expander Form
    with st.expander("＋  Register New Employee", expanded=st.session_state.get("employee_form_open", False)):
        with st.form("create_employee_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            code = c1.text_input("Employee ID *", placeholder="e.g. WP-2045")
            name = c2.text_input("Full Name *", placeholder="e.g. Maya Patel")
            department = c3.selectbox("Department *", options=list(VALID_DEPARTMENTS))

            c4, c5, c6 = st.columns(3)
            designation = c4.text_input("Designation", placeholder="e.g. Senior Software Engineer")
            joining_date = c5.date_input("Joining Date", value=date.today())
            status = c6.selectbox("Status", options=STATUS_OPTIONS)

            experience = st.number_input("Experience (years)", 0.0, 60.0, 2.5, 0.5)
            submitted = st.form_submit_button("Save Employee Profile", type="primary")

        if submitted:
            try:
                create_employee(code, name, department, designation, joining_date, status, experience)
                st.session_state.employee_form_open = False
                st.success(f"Profile created for {name} ({code}).")
                st.rerun()
            except Exception as error:
                st.error(f"Could not save profile: {error}")

    # Bulk Import Dataset Expander
    with st.expander("📁  Bulk Import Dataset (CSV/Excel)", expanded=False):
        st.caption("Upload a CSV or Excel file with employee performance data. Required columns: employee_code, department, attendance_rate, task_completion_rate, performance_category. Optional: employee_name, experience_years, training_hours, previous_performance, review_date.")
        uploaded_file = st.file_uploader("Choose file", type=["csv", "xlsx", "xls"], key="bulk_import_file")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)

                st.write("**Preview of uploaded data:**")
                st.dataframe(df_upload.head(10), use_container_width=True)

                if st.button("Validate & Import Dataset", type="primary", key="validate_import_btn"):
                    with st.spinner("Validating and importing dataset..."):
                        is_valid, cleaned_df, issues, stats = validate_csv_dataset(df_upload)

                    if issues:
                        for issue in issues:
                            st.warning(issue)

                    if not is_valid:
                        st.error("Dataset validation failed. Please check the issues above.")
                    else:
                        st.success(f"Validation passed! {stats['valid_rows']:,} valid rows ready for import.")

                        # Import to database
                        try:
                            inserted_count, skipped_count = import_records_from_df(cleaned_df)
                            st.success(f"Import complete! {inserted_count:,} new employees added, {skipped_count:,} existing employees updated with new performance records.")
                            st.rerun()
                        except Exception as import_error:
                            st.error(f"Import failed: {import_error}")

            except Exception as e:
                st.error(f"Could not read file: {e}")

    if employees.empty:
        render_empty_state("No Employees in System", "Register your first employee above to populate the directory.")
        return

    # Filter Bar
    s_col, d_col, st_col = st.columns([2.5, 1.2, 1.2])
    query = s_col.text_input("Search employees", placeholder="Search by name, ID, or title...")
    departments = ["All departments", *sorted(employees["department"].dropna().unique())]
    department_filter = d_col.selectbox("Department filter", departments)
    status_filter = st_col.selectbox("Status filter", ["All statuses", *STATUS_OPTIONS])

    filtered = employees.copy()
    if query.strip():
        mask = (
            filtered["employee_name"].fillna("").str.contains(query, case=False, regex=False)
            | filtered["employee_code"].fillna("").str.contains(query, case=False, regex=False)
            | filtered["designation"].fillna("").str.contains(query, case=False, regex=False)
        )
        filtered = filtered[mask]
    if department_filter != "All departments":
        filtered = filtered[filtered["department"] == department_filter]
    if status_filter != "All statuses":
        filtered = filtered[filtered["status"] == status_filter]

    st.caption(f"Displaying {len(filtered):,} of {len(employees):,} workforce members")

    display_cols = [
        "employee_code", "employee_name", "department", "designation",
        "experience_years", "status", "performance_category"
    ]
    st.dataframe(
        filtered[display_cols].rename(
            columns={
                "employee_code": "Employee ID",
                "employee_name": "Full Name",
                "department": "Department",
                "designation": "Designation",
                "experience_years": "Experience (Yrs)",
                "status": "Status",
                "performance_category": "Latest Outcome",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    # Dedicated Employee Profile Dossier View
    _section_heading("Employee Performance Dossier", "Inspect holistic employee indicators and review track record")
    emp_options = {
        f"{row.employee_code} · {row.employee_name} ({row.department})": row
        for row in employees.itertuples(index=False)
    }
    selected_label = st.selectbox("Select Employee Dossier", list(emp_options.keys()))
    selected_emp = emp_options[selected_label]

    render_employee_profile_card(selected_emp._asdict())

    # Employee Assessment History
    emp_assessments = (
        assessments[assessments["employee_id"] == selected_emp.employee_id]
        if not assessments.empty
        else pd.DataFrame()
    )
    if not emp_assessments.empty:
        st.markdown(f"**Assessment History for {escape(selected_emp.employee_name)}:**")
        hist_table = emp_assessments.copy()
        hist_table["Outcome"] = hist_table["overall_score"].map(_get_category)
        st.dataframe(
            hist_table[
                ["period_name", "assessment_date", "reviewer", "overall_score", "Outcome", "comments"]
            ].rename(
                columns={
                    "period_name": "Cycle",
                    "assessment_date": "Date",
                    "reviewer": "Reviewer",
                    "overall_score": "Score",
                    "Outcome": "Tier",
                    "comments": "Feedback",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info(f"No performance reviews have been conducted for {selected_emp.employee_name} yet.")

    # Edit & Delete Expanders
    with st.expander("Edit Employee Profile Details"):
        with st.form("edit_employee_form"):
            a, b, c = st.columns(3)
            edit_code = a.text_input("Employee ID *", value=str(selected_emp.employee_code))
            edit_name = b.text_input("Full Name *", value=str(selected_emp.employee_name))
            edit_dept = c.selectbox(
                "Department *", list(VALID_DEPARTMENTS),
                index=_option_index(VALID_DEPARTMENTS, selected_emp.department),
            )
            d, e, f = st.columns(3)
            edit_desig = d.text_input("Designation", value=str(selected_emp.designation or ""))
            edit_jdate = e.date_input("Joining Date", value=_safe_date(selected_emp.joining_date))
            edit_stat = f.selectbox("Status", STATUS_OPTIONS, index=_option_index(STATUS_OPTIONS, selected_emp.status))
            edit_exp = st.number_input(
                "Experience (years)", 0.0, 60.0,
                value=float(selected_emp.experience_years or 0), step=0.5,
            )
            saved = st.form_submit_button("Update Profile", type="primary")

        if saved:
            try:
                update_employee_profile(
                    selected_emp.employee_id, edit_code, edit_name, edit_dept,
                    edit_desig, edit_jdate, edit_stat, edit_exp
                )
                st.success("Profile updated successfully.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not update profile: {error}")

    with st.expander("Update Operational Metrics (ML inputs)"):
        st.caption(
            "Attendance, task completion, training hours, and prior rating are current operational "
            "measurements used by the predictive models. Saving here does not create a review score."
        )
        att_value = _metric_value(selected_emp, "attendance_rate")
        task_value = _metric_value(selected_emp, "task_completion_rate")
        train_value = _metric_value(selected_emp, "training_hours")
        prev_value = _metric_value(selected_emp, "previous_performance")
        if all(value is None for value in (att_value, task_value, train_value, prev_value)):
            st.info("No operational metrics are recorded for this employee yet. Enter the first measured values below.")
        with st.form(f"metrics_form_{selected_emp.employee_id}"):
            m1, m2 = st.columns(2)
            new_att = m1.number_input(
                "Attendance Rate (%)", 0.0, 100.0,
                value=float(att_value) if att_value is not None else 0.0, step=0.5,
            )
            new_task = m2.number_input(
                "Task Completion Rate (%)", 0.0, 100.0,
                value=float(task_value) if task_value is not None else 0.0, step=0.5,
            )
            m3, m4 = st.columns(2)
            new_train = m3.number_input(
                "Training Hours", 0.0, 1000.0,
                value=float(train_value) if train_value is not None else 0.0, step=1.0,
            )
            new_prev = m4.slider(
                "Previous Performance Rating (1–5)", 1.0, 5.0,
                value=float(prev_value) if prev_value is not None else 3.0, step=0.1,
            )
            metrics_saved = st.form_submit_button("Save Operational Metrics", type="primary")
        if metrics_saved:
            try:
                update_employee_metrics(
                    selected_emp.employee_id, new_att, new_task, new_train, new_prev
                )
                st.success("Operational metrics updated. Predictive models will use the new values.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not update metrics: {error}")

    if require_role("admin"):
        with st.expander("Delete Employee Profile"):
            st.warning(f"Deleting **{selected_emp.employee_name}** ({selected_emp.employee_code}) will permanently remove their profile and all linked assessments.")
            confirmed = st.checkbox("I confirm permanent deletion of this employee record.", key="confirm_delete_emp")
            if st.button("Delete Employee", type="secondary", disabled=not confirmed):
                try:
                    delete_employee(selected_emp.employee_id)
                    log_audit(
                        st.session_state.get("user", {}).get("user_id"),
                        "DELETE_EMPLOYEE",
                        "employee",
                        int(selected_emp.employee_id),
                        f"Deleted {selected_emp.employee_name} ({selected_emp.employee_code})",
                    )
                    st.success("Employee record deleted.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not delete: {error}")


# =============================================================================
# 3. REVIEW PERIODS / CYCLES
# =============================================================================
def _periods_page(periods: pd.DataFrame, assessments: pd.DataFrame) -> None:
    render_page_heading(
        title="Review Cycles",
        subtitle="Schedule review windows, track evaluation progress, and close completed assessment cycles.",
        breadcrumb="PERFORMANCE CADENCE",
        badge=f"{len(periods)} Configured" if not periods.empty else None,
    )

    if st.session_state.pop("show_period_form", False):
        st.session_state.period_form_open = True

    with st.expander("＋  Create Review Cycle", expanded=st.session_state.get("period_form_open", False)):
        with st.form("create_period_form", clear_on_submit=True):
            name = st.text_input("Cycle Name *", placeholder="e.g. FY2026 Q4 Performance Review")
            a, b, c = st.columns(3)
            start = a.date_input("Start Date", value=date.today())
            end = b.date_input("End Date", value=date.today() + timedelta(days=60))
            status = c.selectbox("Initial Status", PERIOD_STATUS_OPTIONS, index=1)
            submitted = st.form_submit_button("Create Cycle", type="primary")

        if submitted:
            try:
                save_period(name, start, end, status)
                st.session_state.period_form_open = False
                st.success("Review cycle established.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not create cycle: {error}")

    if periods.empty:
        render_empty_state("No Review Cycles Configured", "Establish a performance review cycle above to begin evaluating workforce members.")
        return

    _section_heading("Review Cycle Overview")
    st.dataframe(
        periods.rename(
            columns={
                "name": "Cycle Name",
                "start_date": "Start Date",
                "end_date": "End Date",
                "status": "Status",
                "assessment_count": "Logged Assessments",
            }
        ).drop(columns=["period_id"]),
        hide_index=True,
        use_container_width=True,
    )

    period_options = {f"{r.name} · {r.status}": r for r in periods.itertuples(index=False)}
    with st.expander("Edit or Update Review Cycle"):
        selected_p_label = st.selectbox("Select Cycle to Edit", list(period_options.keys()))
        selected_p = period_options[selected_p_label]
        with st.form("edit_period_form"):
            p_name = st.text_input("Cycle Name *", value=selected_p.name)
            a, b, c = st.columns(3)
            p_start = a.date_input("Start Date", value=_safe_date(selected_p.start_date))
            p_end = b.date_input("End Date", value=_safe_date(selected_p.end_date))
            p_stat = c.selectbox("Cycle Status", PERIOD_STATUS_OPTIONS, index=_option_index(PERIOD_STATUS_OPTIONS, selected_p.status))
            saved = st.form_submit_button("Update Cycle", type="primary")

        if saved:
            try:
                save_period(p_name, p_start, p_end, p_stat, int(selected_p.period_id))
                st.success("Review cycle updated.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not update cycle: {error}")

    with st.expander("Delete Review Cycle"):
        selected_del_label = st.selectbox("Select Cycle to Delete", list(period_options.keys()), key="del_cycle_sel")
        p_to_del = period_options[selected_del_label]
        if int(p_to_del.assessment_count) > 0:
            st.warning("This cycle has existing assessments attached. Cycles with assessments cannot be deleted to maintain compliance history.")
        else:
            conf = st.checkbox("Confirm permanent deletion of this review cycle.", key="conf_del_cycle")
            if st.button("Delete Cycle", disabled=not conf):
                try:
                    delete_period(p_to_del.period_id)
                    st.success("Cycle deleted.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not delete: {error}")


# =============================================================================
# 4. KPI FRAMEWORK / PERFORMANCE AREAS
# =============================================================================
def _areas_page(areas: pd.DataFrame) -> None:
    render_page_heading(
        title="KPI Framework & Areas",
        subtitle="Define the core competency indicators and their mathematical weights in the overall score calculation.",
        breadcrumb="EVALUATION FRAMEWORK",
    )

    # Visual Weight Distribution Breakdown
    total_weight = float(areas.loc[areas["active"].fillna(False), "weight"].sum())
    is_valid_total = abs(total_weight - 100.0) < 0.01

    if is_valid_total:
        st.success(f"✓ Weight validation passed: Active indicators total exactly {total_weight:g}%.")
    else:
        st.warning(f"⚠️ Active indicator weights currently total {total_weight:g}%. Adjust weights to equal exactly 100% before saving assessments.")

    edited = st.data_editor(
        areas,
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="performance_area_editor",
        column_config={
            "area_id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("KPI Indicator", required=True),
            "description": st.column_config.TextColumn("Competency Criteria & Expectations"),
            "weight": st.column_config.NumberColumn("Weight (%)", min_value=0, max_value=100, step=1, format="%.1f"),
            "active": st.column_config.CheckboxColumn("Active"),
        },
        disabled=["area_id"],
    )

    if st.button("Save KPI Framework", type="primary") or st.session_state.pop("save_areas_requested", False):
        try:
            save_areas(edited.to_dict(orient="records"))
            st.success("KPI framework and weights saved successfully.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not save framework: {error}")


# =============================================================================
# 5. ASSESSMENTS ENGINE
# =============================================================================
def _assessments_page(
    employees: pd.DataFrame,
    periods: pd.DataFrame,
    areas: pd.DataFrame,
    assessments: pd.DataFrame,
) -> None:
    render_page_heading(
        title="Performance Assessments",
        subtitle="Conduct structured, evidence-based employee reviews with real-time weighted scoring.",
        breadcrumb="EVALUATION ENGINE",
        badge=f"{len(assessments)} Completed" if not assessments.empty else None,
    )

    if st.session_state.pop("show_assessment_form", False):
        st.session_state.assessment_form_open = True

    active_employees = employees[employees["status"] == "Active"] if not employees.empty else pd.DataFrame()
    active_periods = periods[periods["status"] == "Active"] if not periods.empty else pd.DataFrame()
    active_areas = areas[areas["active"].astype(bool)] if not areas.empty else pd.DataFrame()

    if active_employees.empty:
        st.warning("Please add an active employee in the directory before creating an assessment.")
    elif active_periods.empty:
        st.warning("An active review cycle is required. Please activate a review cycle under 'Review Cycles'.")
    elif active_areas.empty:
        st.warning("Please activate at least one performance KPI indicator in 'KPI Framework'.")
    else:
        emp_map = {
            f"{r.employee_code} · {r.employee_name} ({r.department})": int(r.employee_id)
            for r in active_employees.itertuples(index=False)
        }
        per_map = {
            f"{r.name} (Due {r.end_date})": int(r.period_id)
            for r in active_periods.itertuples(index=False)
        }

        with st.expander("＋  Conduct New Performance Review", expanded=st.session_state.get("assessment_form_open", False)):
            with st.form("create_assessment_form"):
                c1, c2 = st.columns(2)
                selected_emp_lbl = c1.selectbox("Employee *", list(emp_map.keys()))
                selected_per_lbl = c2.selectbox("Review Cycle *", list(per_map.keys()))

                c3, c4 = st.columns(2)
                reviewer = c3.text_input("Reviewer Name & Designation *", placeholder="e.g. Dr. Sarah Jenkins (Engineering VP)")
                assessment_date = c4.date_input("Assessment Date", value=date.today())

                st.markdown("**Competency Scores (0 – 100):**")
                scores: dict[str, float] = {}
                score_cols = st.columns(2)
                for i, area in enumerate(active_areas.itertuples(index=False)):
                    col = score_cols[i % 2]
                    scores[area.name] = col.number_input(
                        f"{area.name} (Weight: {area.weight:g}%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=78.0,
                        step=1.0,
                        key=f"eval_score_{area.area_id}",
                    )

                comments = st.text_area(
                    "Qualitative Reviewer Feedback & Development Objectives *",
                    placeholder="Provide actionable feedback detailing achievements, areas for coaching, and upcoming growth goals...",
                    max_chars=4000,
                )

                # Real-time score calculator preview
                calculated_score = sum(
                    scores[row.name] * float(row.weight) / 100.0
                    for row in active_areas.itertuples(index=False)
                )
                category_preview = _get_category(calculated_score)

                st.markdown(
                    f"""
                    <div style="background:var(--wp-bg); border:1px solid var(--wp-border); border-radius:var(--wp-radius-md); padding:0.75rem 1rem; margin-top:0.75rem; display:flex; align-items:center; justify-content:space-between;">
                        <span style="font-size:0.875rem; color:var(--wp-text-secondary); font-weight:500;">Calculated Weighted Overall Score:</span>
                        <div style="display:flex; align-items:center; gap:0.5rem;">
                            <strong style="font-size:1.125rem; color:var(--wp-navy);">{calculated_score:.1f} / 100</strong>
                            {render_status_badge(category_preview)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                submitted = st.form_submit_button("Submit & Save Assessment", type="primary")

            if submitted:
                if not reviewer.strip():
                    st.error("Please specify the reviewer name.")
                else:
                    try:
                        save_assessment(
                            employee_id=emp_map[selected_emp_lbl],
                            period_id=per_map[selected_per_lbl],
                            assessment_date=assessment_date,
                            reviewer=reviewer,
                            scores=scores,
                            comments=comments,
                        )
                        st.session_state.assessment_form_open = False
                        st.success("Performance review submitted and logged to employee history.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not save assessment: {error}")

    # History & Search
    _section_heading("Assessment History", "Filter, inspect, and export verified employee reviews")
    if assessments.empty:
        render_empty_state("No Recorded Reviews", "Submitted employee reviews will appear in this audit log.")
        return

    f1, f2, f3 = st.columns([2, 1, 1])
    search_q = f1.text_input("Search assessments", placeholder="Search employee, reviewer, or cycle...")
    depts = ["All departments", *sorted(assessments["department"].dropna().unique())]
    dept_sel = f2.selectbox("Department", depts, key="assess_dept_filter")
    pers = ["All periods", *sorted(assessments["period_name"].dropna().unique())]
    per_sel = f3.selectbox("Review cycle", pers, key="assess_per_filter")

    filtered = assessments.copy()
    if dept_sel != "All departments":
        filtered = filtered[filtered["department"] == dept_sel]
    if per_sel != "All periods":
        filtered = filtered[filtered["period_name"] == per_sel]
    if search_q.strip():
        mask = (
            filtered["employee_name"].fillna("").str.contains(search_q, case=False, regex=False)
            | filtered["employee_code"].fillna("").str.contains(search_q, case=False, regex=False)
            | filtered["reviewer"].fillna("").str.contains(search_q, case=False, regex=False)
        )
        filtered = filtered[mask]

    table = filtered.copy()
    table["Outcome"] = table["overall_score"].map(_get_category)

    st.dataframe(
        table[
            ["employee_code", "employee_name", "department", "period_name",
             "assessment_date", "reviewer", "overall_score", "Outcome", "comments"]
        ].rename(
            columns={
                "employee_code": "Employee ID",
                "employee_name": "Full Name",
                "department": "Department",
                "period_name": "Review Cycle",
                "assessment_date": "Date",
                "reviewer": "Reviewer",
                "overall_score": "Score",
                "Outcome": "Tier",
                "comments": "Reviewer Feedback",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.download_button(
        "Download Filtered Assessments (CSV)",
        filtered.drop(columns=["scores_json"], errors="ignore").to_csv(index=False).encode("utf-8"),
        file_name="workpulse-assessments-audit.csv",
        mime="text/csv",
    )


# =============================================================================
# 6. ANALYTICS ENGINE
# =============================================================================
def _analytics_page(employees: pd.DataFrame, assessments: pd.DataFrame) -> None:
    render_page_heading(
        title="Workforce Analytics",
        subtitle="Quantitative insights into performance distributions, departmental variance, and operational correlations.",
        breadcrumb="ANALYTICS & REPORTING",
    )

    if assessments.empty:
        render_empty_state("Analytics Awaiting Assessment Data", "Record reviews or seed demonstration data to activate the deep analytics engine.")
        return

    # Slicers
    f1, f2 = st.columns(2)
    periods = ["All cycles", *sorted(assessments["period_name"].unique())]
    sel_p = f1.selectbox("Filter Cycle", periods)
    depts = ["All departments", *sorted(assessments["department"].unique())]
    sel_d = f2.selectbox("Filter Department", depts)

    filtered = assessments.copy()
    if sel_p != "All cycles":
        filtered = filtered[filtered["period_name"] == sel_p]
    if sel_d != "All departments":
        filtered = filtered[filtered["department"] == sel_d]

    avg_score = float(filtered["overall_score"].mean()) if not filtered.empty else 0.0
    high_count = int((filtered["overall_score"] >= 80).sum()) if not filtered.empty else 0
    high_pct = (high_count / len(filtered) * 100) if not filtered.empty else 0
    needs_support_count = int((filtered["overall_score"] < 60).sum()) if not filtered.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cycle Mean Score", f"{avg_score:.1f} / 100")
    c2.metric("Audited Reviews", f"{len(filtered):,}")
    c3.metric("High Outcome Rate", f"{high_pct:.1f}%", f"{high_count} staff")
    c4.metric("Coaching Needed", f"{needs_support_count}", "Below 60 score")

    st.write("")

    # Visualizations Grid
    left, right = st.columns(2, gap="large")
    with left:
        _section_heading("Department Benchmark Breakdown", "Mean assessment score across departments")
        dept_summary = (
            filtered.groupby("department", as_index=False)["overall_score"]
            .mean()
            .sort_values("overall_score", ascending=False)
        )
        fig = px.bar(
            dept_summary,
            x="department",
            y="overall_score",
            labels={"department": "", "overall_score": "Mean Score"},
            range_y=[0, 100],
            color_discrete_sequence=["#168C83"],
            text_auto=".1f",
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    with right:
        _section_heading("Performance Tier Mix", "Proportion of workforce across evaluation tiers")
        cat_data = (
            filtered["overall_score"]
            .map(_get_category)
            .value_counts()
            .reindex(["High", "Moderate", "Needs Support"], fill_value=0)
            .rename_axis("Tier")
            .reset_index(name="Reviews")
        )
        fig = px.pie(
            cat_data,
            names="Tier",
            values="Reviews",
            hole=0.68,
            color="Tier",
            color_discrete_map={"High": "#0D9488", "Moderate": "#D97706", "Needs Support": "#E11D48"},
        )
        fig.update_traces(marker=dict(line=dict(color="#FFFFFF", width=2)))
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    # Secondary Charts Row
    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        _section_heading("Score Distribution by Department", "Variance and dispersion box plot")
        fig = px.box(
            filtered,
            x="department",
            y="overall_score",
            points="all",
            labels={"department": "", "overall_score": "Score"},
            color_discrete_sequence=["#102A43"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    with c_right:
        _section_heading("Performance Trajectory by Month", "Mean historical scores over calendar months")
        monthly = filtered.copy()
        monthly["Month"] = pd.to_datetime(monthly["assessment_date"]).dt.to_period("M").astype(str)
        monthly_avg = monthly.groupby("Month", as_index=False)["overall_score"].mean().sort_values("Month")
        fig = px.line(
            monthly_avg,
            x="Month",
            y="overall_score",
            markers=True,
            labels={"Month": "", "overall_score": "Score"},
            color_discrete_sequence=["#168C83"],
        )
        fig.update_yaxes(range=[40, 100])
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)


# =============================================================================
# 7. MACHINE LEARNING & DECISION SUPPORT
# =============================================================================
def _predictions_page(employees: pd.DataFrame) -> None:
    render_page_heading(
        title="Decision Support & Predictive Intelligence",
        subtitle="Machine learning classification models (Decision Tree & Random Forest) for performance forecasting.",
        breadcrumb="PREDICTIVE ENGINE",
    )

    st.markdown(
        """
        <div class="wp-decision-notice">
            <strong>⚠️ Ethical AI & Decision Support Notice:</strong> Machine learning forecasts are strictly statistical estimates derived from historical indicators. They provide operational guidance and must <em>never</em> substitute for human managerial judgment or independently determine employment decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    labelled = _training_frame(employees)
    if labelled.empty or len(labelled) < 10:
        render_empty_state(
            "Insufficient Training Records",
            "At least 10 complete historical records with attendance, task completion, and training hours are required to train the predictive pipeline.",
        )
        return

    try:
        with st.spinner("Training Decision Tree and Random Forest classifiers on held-out test split…"):
            results, pipelines = _train_models(labelled)
    except Exception as error:
        st.error(f"Model training encountered an error: {error}")
        return

    # Model Evaluation Benchmark Section
    _section_heading("Model Architecture Benchmark", "Held-out test split evaluation (80/20 train/test split)")
    model_names = list(pipelines.keys())

    # Side-by-side benchmark comparison cards
    m_col1, m_col2 = st.columns(2)
    for col, m_name in zip([m_col1, m_col2], model_names):
        m_metrics = results[m_name]
        with col:
            st.markdown(
                f"""
                <div class="wp-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                        <strong style="color:var(--wp-navy); font-size:1.0625rem;">{m_name}</strong>
                        <span class="wp-badge wp-badge-completed">Trained & Validated</span>
                    </div>
                    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:0.5rem; text-align:center;">
                        <div style="background:var(--wp-bg); padding:0.5rem; border-radius:6px;">
                            <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">Accuracy</div>
                            <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{float(m_metrics['accuracy']):.1%}</div>
                        </div>
                        <div style="background:var(--wp-bg); padding:0.5rem; border-radius:6px;">
                            <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">Precision</div>
                            <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{float(m_metrics['precision']):.1%}</div>
                        </div>
                        <div style="background:var(--wp-bg); padding:0.5rem; border-radius:6px;">
                            <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">Recall</div>
                            <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{float(m_metrics['recall']):.1%}</div>
                        </div>
                        <div style="background:var(--wp-bg); padding:0.5rem; border-radius:6px;">
                            <div style="font-size:0.6875rem; color:var(--wp-text-secondary); text-transform:uppercase;">F1-Score</div>
                            <div style="font-size:1.125rem; font-weight:700; color:var(--wp-navy);">{float(m_metrics['f1_score']):.1%}</div>
                        </div>
                    </div>
                    <div style="font-size:0.75rem; color:var(--wp-text-muted); margin-top:0.75rem;">
                        Training samples: {m_metrics.get('train_samples', '—')} &nbsp;·&nbsp; Test samples: {m_metrics.get('test_samples', '—')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    selected_model = st.selectbox("Inspect Confusion Matrix for Model", model_names)
    matrix_metrics = results[selected_model]
    if "confusion_matrix" in matrix_metrics:
        cm_matrix = np.asarray(matrix_metrics["confusion_matrix"])
        labels = matrix_metrics.get("classes", TARGET_CLASSES)
        cm_fig = px.imshow(
            cm_matrix,
            x=labels,
            y=labels,
            text_auto=True,
            color_continuous_scale="Blues",
            labels={"x": "Predicted Tier", "y": "Actual Tier", "color": "Evaluated Records"},
        )
        st.plotly_chart(apply_chart_style(cm_fig), use_container_width=True)

    # Single-Employee Inference & What-If Simulator
    _section_heading("Predictive Simulation & What-If Analysis", "Project employee performance tier and explore sensitivity factors")
    emp_options = {"Manual parameter input": None}
    emp_options.update(
        {
            f"{r.employee_code} · {r.employee_name} ({r.department})": r
            for r in employees.itertuples(index=False)
        }
    )
    sel_emp_label = st.selectbox("Populate with employee data", list(emp_options.keys()))
    sel_emp = emp_options[sel_emp_label]

    with st.form("ml_prediction_form"):
        depts = sorted(set(VALID_DEPARTMENTS) | set(employees["department"].dropna().astype(str)))
        def_dept = getattr(sel_emp, "department", depts[0])
        dept = st.selectbox("Department", depts, index=_option_index(depts, def_dept))

        p1, p2 = st.columns(2)
        att = p1.slider("Attendance Rate (%)", 0.0, 100.0, _finite(getattr(sel_emp, "attendance_rate", None), 90.0), 0.5)
        task = p2.slider("Task Completion Rate (%)", 0.0, 100.0, _finite(getattr(sel_emp, "task_completion_rate", None), 85.0), 0.5)

        p3, p4 = st.columns(2)
        trn = p3.number_input("Training Hours", 0.0, 1000.0, _finite(getattr(sel_emp, "training_hours", None), 30.0), 1.0)
        exp = p4.number_input("Experience (years)", 0.0, 60.0, _finite(getattr(sel_emp, "experience_years", None), 3.0), 0.5)

        prev = st.slider("Previous Performance Rating (1 – 5)", 1.0, 5.0, _finite(getattr(sel_emp, "previous_performance", None), 3.5), 0.1)

        run_pred = st.form_submit_button("Generate Prediction & Explanation", type="primary")

    if run_pred:
        input_features = {
            "department": dept,
            "attendance_rate": att,
            "task_completion_rate": task,
            "training_hours": trn,
            "experience_years": exp,
            "previous_performance": prev,
        }
        try:
            output = run_employee_prediction(
                pipelines[selected_model],
                input_features,
                employee_id=getattr(sel_emp, "employee_id", None),
                population_df=labelled,
            )
            pred_tier = output["predicted_category"]

            st.markdown(
                f"""
                <div class="wp-decision-result">
                    <div class="wp-decision-result-left">
                        <small>MODEL FORECAST ({selected_model})</small>
                        <strong>{escape(pred_tier)}</strong>
                        <span style="font-size:0.8125rem; color:var(--wp-text-secondary);">{output.get('summary', '')}</span>
                    </div>
                    <div>
                        {render_status_badge(pred_tier)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Probability Breakdown
            prob_df = pd.DataFrame(
                [{"Tier": k, "Confidence": v} for k, v in output["probabilities"].items()]
            )
            prob_fig = px.bar(
                prob_df,
                x="Tier",
                y="Confidence",
                range_y=[0, 1],
                text_auto=".1%",
                color="Tier",
                color_discrete_map={"High": "#0D9488", "Moderate": "#D97706", "Needs Support": "#E11D48"},
            )
            st.plotly_chart(apply_chart_style(prob_fig), use_container_width=True)

            if not output["contributions"].empty:
                st.markdown("**Local Feature Contributions (Why the model reached this prediction):**")
                st.dataframe(output["contributions"], hide_index=True, use_container_width=True)

        except Exception as error:
            st.error(f"Inference pipeline failed: {error}")


# =============================================================================
# 8. EXECUTIVE REPORTS
# =============================================================================
def _reports_page(assessments: pd.DataFrame) -> None:
    render_page_heading(
        title="Executive Performance Reports",
        subtitle="Compile, audit, and export formal performance evaluations for organizational leadership.",
        breadcrumb="EXECUTIVE AUDIT",
    )

    if assessments.empty:
        render_empty_state("No Reportable Records", "Completed assessments will appear in this executive reporting suite.")
        return

    r1, r2, r3 = st.columns(3)
    depts = ["All departments", *sorted(assessments["department"].dropna().unique())]
    sel_dept = r1.selectbox("Filter Department", depts, key="rep_dept")
    cycles = ["All cycles", *sorted(assessments["period_name"].dropna().unique())]
    sel_cycle = r2.selectbox("Filter Review Cycle", cycles, key="rep_cycle")
    emps = ["All employees", *sorted(assessments["employee_name"].dropna().unique())]
    sel_emp = r3.selectbox("Filter Employee", emps, key="rep_emp")

    filtered = assessments.copy()
    if sel_dept != "All departments":
        filtered = filtered[filtered["department"] == sel_dept]
    if sel_cycle != "All cycles":
        filtered = filtered[filtered["period_name"] == sel_cycle]
    if sel_emp != "All employees":
        filtered = filtered[filtered["employee_name"] == sel_emp]

    if filtered.empty:
        st.info("No assessment records match the selected reporting filters.")
        return

    avg_score = float(filtered["overall_score"].mean())
    render_executive_report_header(
        report_title=f"Performance Audit — {sel_dept}",
        cycle_name=sel_cycle,
        dept_filter=sel_dept,
        employee_count=len(filtered),
        avg_score=avg_score,
    )

    report_table = filtered.copy()
    report_table["Tier"] = report_table["overall_score"].map(_get_category)

    st.dataframe(
        report_table[
            ["employee_code", "employee_name", "department", "period_name",
             "assessment_date", "reviewer", "overall_score", "Tier", "comments"]
        ].rename(
            columns={
                "employee_code": "Employee ID",
                "employee_name": "Full Name",
                "department": "Department",
                "period_name": "Review Cycle",
                "assessment_date": "Date",
                "reviewer": "Reviewer",
                "overall_score": "Score",
                "Tier": "Standing",
                "comments": "Executive Notes",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    c1, c2 = st.columns([2, 5])
    c1.download_button(
        "📥 Download Report as CSV",
        report_table.drop(columns=["scores_json"], errors="ignore").to_csv(index=False).encode("utf-8"),
        file_name="workpulse-executive-report.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )


# =============================================================================
# 9. NOTIFICATIONS & INBOX
# =============================================================================
def _notifications_page(employees: pd.DataFrame, assessments: pd.DataFrame) -> None:
    user = st.session_state.get("user", {})
    role = str(user.get("role", "employee")).lower()

    if role == "employee":
        render_page_heading(
            title="My Review Updates",
            subtitle="Feedback, cycle milestones, and announcements relevant to your employee profile.",
            breadcrumb="PERSONAL INBOX",
        )
        emp = _get_current_employee_record(user, employees)
        if emp is None:
            st.warning(
                "Your account is not linked to an employee profile yet. "
                "Ask HR to connect your account to see personal review updates."
            )
            return

        emp_name = str(emp["employee_name"])
        emp_assessments = (
            assessments[assessments["employee_id"] == int(emp["employee_id"])]
            if not assessments.empty
            else pd.DataFrame()
        )

        _section_heading("Review Feedback", "Manager guidance recorded against your profile")
        if emp_assessments.empty:
            render_empty_state(
                "No Review Feedback Yet",
                "Feedback from completed assessments will appear here.",
            )
        else:
            for row in emp_assessments.itertuples(index=False):
                st.markdown(
                    f"""
                    <div class="wp-card" style="margin-bottom:0.75rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; flex-wrap:wrap;">
                            <strong style="color:var(--wp-navy);">{escape(str(row.period_name))}</strong>
                            <span>{render_status_badge(_get_category(float(row.overall_score)))}</span>
                        </div>
                        <div style="font-size:0.75rem; color:var(--wp-text-muted); margin-top:0.2rem;">
                            {escape(str(row.assessment_date))} · Reviewer: {escape(str(row.reviewer))} · Score: {float(row.overall_score):.1f}/100
                        </div>
                        <p style="margin:0.5rem 0 0 0; color:var(--wp-text-secondary); font-size:0.875rem;">
                            {escape(str(row.comments or 'No written feedback was attached to this review.'))}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        _section_heading("Workspace Announcements", "System alerts that mention your profile")
        notifications = get_notifications()
        personal = (
            notifications[
                notifications["message"].fillna("").str.contains(emp_name, case=False, regex=False)
                | notifications["title"].fillna("").str.contains(emp_name, case=False, regex=False)
            ]
            if not notifications.empty
            else pd.DataFrame()
        )
        if personal.empty:
            render_empty_state("No Personal Announcements", "Relevant workspace alerts will appear here.")
        else:
            for notif in personal.head(10).itertuples(index=False):
                st.markdown(
                    f"""
                    <div class="wp-card" style="margin-bottom:0.75rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:var(--wp-navy);">{escape(str(notif.title))}</strong>
                            <span style="font-size:0.75rem; color:var(--wp-text-muted);">{escape(str(notif.created_at))}</span>
                        </div>
                        <p style="margin:0.35rem 0 0 0; color:var(--wp-text-secondary); font-size:0.875rem;">{escape(str(notif.message))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        return

    render_page_heading(
        title="Notifications & Task Queue",
        subtitle="Review workflow alerts, upcoming cycle deadlines, and unassessed employee queues.",
        breadcrumb="TASK INBOX",
    )

    notifications = get_notifications()
    pending = get_pending_reviews()
    unread = notifications[notifications["read_at"].isna()] if not notifications.empty else pd.DataFrame()

    c1, c2 = st.columns([1.5, 4.5])
    c1.metric("Unread Alerts", len(unread))
    with c2:
        if st.button("Mark All Alerts as Read", disabled=unread.empty):
            mark_notifications_read()
            st.success("All alerts marked as read.")
            st.rerun()

    _section_heading("Pending Review Queue", "Active staff members awaiting evaluations in open cycles")
    if pending.empty:
        st.success("All active staff members in open review cycles have been evaluated.")
    else:
        st.dataframe(
            pending[["employee_code", "employee_name", "department", "period_name", "end_date"]].rename(
                columns={
                    "employee_code": "Employee ID",
                    "employee_name": "Staff Name",
                    "department": "Department",
                    "period_name": "Open Cycle",
                    "end_date": "Due Date",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
        if st.button("Start Assessment for Pending Staff", type="primary"):
            st.session_state.active_page = "Assessments"
            st.session_state.show_assessment_form = True
            st.rerun()

    _section_heading("Audit & Workflow Event Log")
    if notifications.empty:
        render_empty_state("No Notification History", "System events and review cycle milestones will appear here.")
    else:
        for notif in notifications.itertuples(index=False):
            st.markdown(
                f"""
                <div class="wp-card" style="margin-bottom:0.75rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong style="color:var(--wp-navy);">{escape(str(notif.title))}</strong>
                        <span style="font-size:0.75rem; color:var(--wp-text-muted);">{escape(str(notif.created_at))}</span>
                    </div>
                    <p style="margin:0.35rem 0 0 0; color:var(--wp-text-secondary); font-size:0.875rem;">{escape(str(notif.message))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =============================================================================
# 10. SETTINGS & DEMONSTRATION SUITE
# =============================================================================
def _user_management_page() -> None:
    """Admin-only page for account access, role management, and audit review."""
    if not require_role("admin"):
        _unauthorized_alert()
        return

    current_user = st.session_state.get("user", {})
    current_user_id = current_user.get("user_id")

    render_page_heading(
        title="User Management",
        subtitle="Approve access requests, assign roles, and review account security activity.",
        breadcrumb="ADMINISTRATION",
    )

    users = get_all_users()
    pending_users = [user for user in users if not user.get("is_active")]
    active_users = [user for user in users if user.get("is_active")]

    # ------------------------------------------------------------------
    # Pending registration approvals
    # ------------------------------------------------------------------
    _section_heading(
        "Pending Access Requests",
        "Self-service registrations stay inactive until an administrator approves them",
    )
    if not pending_users:
        st.success("No pending access requests. All registered accounts have been processed.")
    else:
        for pending in pending_users:
            p1, p2, p3 = st.columns([5, 1.1, 1.1], vertical_alignment="center")
            with p1:
                st.markdown(
                    f"""
                    <div style="padding:0.35rem 0;">
                        <strong style="color:var(--wp-navy);">{escape(str(pending.get('full_name') or 'Unnamed'))}</strong>
                        <span style="font-size:0.8125rem; color:var(--wp-text-secondary);"> · {escape(str(pending.get('email')))}</span>
                        <div style="font-size:0.72rem; color:var(--wp-text-muted); margin-top:0.15rem;">
                            Requested {escape(str(pending.get('created_at') or '—'))[:19][:19]}
                            · Linked employee: {escape(str(pending.get('employee_name') or 'Not linked'))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with p2:
                if st.button("Approve", type="primary", use_container_width=True, key=f"approve_{pending['user_id']}"):
                    if approve_user(int(pending["user_id"]), current_user_id):
                        st.success(f"Approved access for {pending.get('email')}.")
                        st.rerun()
                    else:
                        st.error("Could not approve this account.")
            with p3:
                if st.button("Reject", use_container_width=True, key=f"reject_{pending['user_id']}"):
                    if delete_user(int(pending["user_id"]), current_user_id):
                        st.success(f"Rejected and removed {pending.get('email')}.")
                        st.rerun()
                    else:
                        st.error("Could not remove this request.")

    # ------------------------------------------------------------------
    # Account directory
    # ------------------------------------------------------------------
    _section_heading("Account Directory", "Active identities with workspace access")
    if active_users:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "User": user.get("full_name", "—"),
                        "Email": user.get("email", "—"),
                        "Role": str(user.get("role", "employee")).upper(),
                        "Linked Employee": user.get("employee_name") or "Not linked",
                        "Last Login": str(user.get("last_login") or "Never")[:19],
                    }
                    for user in active_users
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No active user accounts found.")

    # ------------------------------------------------------------------
    # Manage one account at a time (avoids nested widgets in loops)
    # ------------------------------------------------------------------
    _section_heading("Manage Account", "Edit identity, role, and activation state")
    if active_users:
        account_options = {
            f"{user.get('full_name', 'User')} · {user.get('email', '')} ({str(user.get('role', '')).upper()})": user
            for user in active_users
        }
        selected_label = st.selectbox("Select account", list(account_options.keys()), key="admin_account_select")
        selected = account_options[selected_label]
        selected_id = int(selected["user_id"])
        is_self = selected_id == current_user_id
        role_options = ["employee", "hr", "admin"]
        current_role = str(selected.get("role", "employee")).lower()
        role_index = role_options.index(current_role) if current_role in role_options else 0

        with st.form(f"edit_user_form_{selected_id}"):
            e1, e2 = st.columns(2)
            edit_name = e1.text_input("Full Name", value=str(selected.get("full_name") or ""))
            edit_email = e2.text_input("Email", value=str(selected.get("email") or ""))
            e3, e4 = st.columns(2)
            edit_role = e3.selectbox(
                "Role",
                role_options,
                index=role_index,
                disabled=is_self,
                help="You cannot change your own administrative role.",
            )
            edit_active = e4.checkbox(
                "Account active",
                value=bool(selected.get("is_active")),
                disabled=is_self,
                help="You cannot deactivate your own account.",
            )
            st.caption(
                "Employee profile link: "
                + (str(selected.get("employee_name") or "Not linked"))
                + f" (ID {selected.get('employee_id')})"
            )
            save_user = st.form_submit_button("Save Changes", type="primary")

        if save_user:
            try:
                updated = update_user(
                    selected_id,
                    full_name=edit_name.strip(),
                    email=edit_email.strip().lower(),
                    role=current_role if is_self else edit_role,
                    is_active=True if is_self else edit_active,
                )
                if updated:
                    if is_self:
                        st.session_state.user["full_name"] = edit_name.strip()
                        st.session_state.user["email"] = edit_email.strip().lower()
                    log_audit(
                        current_user_id,
                        "UPDATE_USER",
                        "user",
                        selected_id,
                        f"Account updated for {edit_email.strip().lower()}",
                    )
                    st.success("Account updated successfully.")
                    st.rerun()
                else:
                    st.error("No changes were applied. Verify the account still exists.")
            except Exception as error:
                st.error(f"Could not update account: {error}")

        if not is_self:
            with st.expander("Delete Account"):
                st.warning(
                    f"Deleting **{selected.get('email')}** permanently removes workspace access. "
                    "The linked employee profile and assessments are not deleted."
                )
                confirm_delete = st.checkbox(
                    "I understand this account will be permanently removed.",
                    key=f"confirm_delete_user_{selected_id}",
                )
                if st.button(
                    "Delete Account",
                    disabled=not confirm_delete,
                    key=f"delete_user_{selected_id}",
                ):
                    if delete_user(selected_id, current_user_id):
                        st.success("Account deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete this account.")

    # ------------------------------------------------------------------
    # Create account
    # ------------------------------------------------------------------
    _section_heading("Create Account", "Provision a new identity with a temporary password")
    with st.form("create_user_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        new_email = c1.text_input("Email *", placeholder="user@workpulse.local")
        new_name = c2.text_input("Full Name *", placeholder="User Name")
        new_role = c3.selectbox("Role *", options=["employee", "hr", "admin"])
        c4, c5 = st.columns(2)
        new_employee_code = c4.text_input(
            "Employee ID (optional)",
            placeholder="e.g. WP-1001",
            help="Link this account to an existing employee profile.",
        )
        new_password = c5.text_input(
            "Temporary Password *",
            type="password",
            placeholder="Minimum 8 characters",
            help="Share this securely. The user should change it after signing in.",
        )
        create_account = st.form_submit_button("Create Account", type="primary")

    if create_account:
        if not new_email.strip() or not new_name.strip():
            st.error("Email and Full Name are required.")
        elif "@" not in new_email:
            st.error("Please enter a valid email address.")
        elif len(new_password) < 8:
            st.error("Temporary password must be at least 8 characters long.")
        else:
            employee_id = None
            try:
                if new_employee_code.strip():
                    employee = find_employee_by_code(new_employee_code)
                    if employee is None:
                        raise ValueError("That Employee ID was not found.")
                    employee_id = int(employee["employee_id"])
                create_user(
                    email=new_email,
                    full_name=new_name,
                    role=new_role,
                    created_by_user_id=current_user_id,
                    employee_id=employee_id,
                    plain_password=new_password,
                    require_password_change=True,
                    is_active=True,
                )
                st.success(
                    f"Account created for {new_email}. Share the temporary password securely; "
                    "the user must change it at first sign-in."
                )
                st.rerun()
            except Exception as error:
                st.error(f"Failed to create account: {error}")

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------
    _section_heading("Recent Audit Activity", "Account and configuration events recorded by the system")
    audit_entries = get_audit_log(limit=25)
    if audit_entries:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Time": str(entry.get("performed_at", ""))[:19],
                        "Action": entry.get("action", ""),
                        "Actor": entry.get("performed_by_email") or "System",
                        "Detail": entry.get("detail", ""),
                    }
                    for entry in audit_entries
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No recent audit activity recorded.")


def _settings_page() -> None:
    if not require_role("admin"):
        _unauthorized_alert()
        return

    render_page_heading(
        title="Workspace Settings & Demo Suite",
        subtitle="Manage workspace preferences, system diagnostics, and evaluation demo records.",
        breadcrumb="SYSTEM PREFERENCES",
    )

    settings = get_settings()

    with st.form("workspace_settings_form"):
        st.markdown("**Workspace Configuration:**")
        name = st.text_input("Administrator Display Name", value=settings.get("admin_name", "Administrator"))
        workspace = st.text_input("Workspace Name", value=settings.get("workspace_name", "WorkPulse"))
        saved = st.form_submit_button("Save Preferences", type="primary")

    if saved:
        try:
            save_settings({"admin_name": name, "workspace_name": workspace})
            st.success("Workspace preferences updated.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not update preferences: {error}")

    # Demonstration Suite
    _section_heading("Viva Demonstration & Evaluation Suite", "Seed realistic demonstration review cycles and assessment records with one click")
    st.markdown(
        """
        <div class="wp-card">
            <p style="margin:0 0 1rem 0; color:var(--wp-text-secondary); font-size:0.875rem;">
                When presenting WorkPulse to evaluators, professors, or stakeholders, click below to populate authentic review cycles, weighted assessments across multiple departments, and performance trajectories. You can clear demonstration records at any time.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, _ = st.columns([2.5, 2.5, 5])
    with c1:
        if st.button("⚡ Seed Demo Review Cycle", type="primary", use_container_width=True):
            count = seed_demo_review_cycle()
            st.success(f"Successfully generated {count} demonstration assessments across review cycles!")
            st.rerun()
    with c2:
        if st.button("🗑 Reset Demonstration Data", use_container_width=True):
            del_count = clear_demo_assessments()
            st.info(f"Cleared {del_count} demonstration assessment records.")
            st.rerun()

    _section_heading("System Diagnostics & SQLite Status")
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    st.markdown(
        f"""
        <div style="background:var(--wp-bg); border:1px solid var(--wp-border); border-radius:var(--wp-radius-md); padding:1rem; font-size:0.8125rem; color:var(--wp-text-secondary);">
            <div><strong>Database File:</strong> <code>{DB_PATH}</code></div>
            <div style="margin-top:0.35rem;"><strong>File Size:</strong> {db_size / 1024:.1f} KB</div>
            <div style="margin-top:0.35rem;"><strong>Integrity:</strong> SQLite foreign keys enabled, parameterized queries active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# HELPER UTILITIES
# =============================================================================
def _safe_date(value: Any) -> date:
    if value is None or pd.isna(value) or not str(value).strip():
        return date.today()
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return date.today()


def _option_index(options: Any, value: Any) -> int:
    try:
        return list(options).index(value)
    except ValueError:
        return 0


def _finite(value: Any, fallback: float) -> float:
    try:
        result = float(value)
        return result if np.isfinite(result) else fallback
    except (TypeError, ValueError):
        return fallback


# =============================================================================
# APPLICATION ENTRYPOINT
# =============================================================================
def main() -> None:
    _configure_page()
    if not st.session_state.get("_db_bootstrapped"):
        initialize_database()
        init_auth_tables()
        ensure_default_admin()
        link_demo_employee_account()
        mark_bundled_sample_records()
        st.session_state["_db_bootstrapped"] = True
    summary = get_dashboard_summary()
    settings = get_settings()
    admin_name = settings.get("admin_name", "Administrator")
    workspace_name = settings.get("workspace_name", "WorkPulse")

    # Get current user info for role-based decisions
    user = st.session_state.get("user", {})
    role = user.get("role", "admin").lower()

    # Add admin-only navigation items
    if role == "admin":
        visible_nav = {**NAV_ITEMS, **ADMIN_NAV_ITEMS}
    else:
        visible_nav = NAV_ITEMS

    # Synchronize URL query parameters with active_page or auth
    query_page = st.query_params.get("page")
    if query_page:
        qp_clean = str(query_page).strip().lower()
        if qp_clean in (
            "login", "signin", "sign_in", "employee/login", "hr/login",
            "admin/login", "reset_password", "register", "forgot_password",
        ):
            if "user" not in st.session_state:
                auth_targets = {
                    "reset_password": "reset_password",
                    "register": "register",
                    "forgot_password": "forgot_password",
                }
                st.session_state.auth_page = auth_targets.get(qp_clean, "login")
                st.session_state.active_page = "login"
                if "employee" in qp_clean:
                    st.query_params["role"] = "employee"
                elif "hr" in qp_clean:
                    st.query_params["role"] = "hr"
                elif "admin" in qp_clean:
                    st.query_params["role"] = "admin"
            else:
                st.query_params["page"] = st.session_state.get("active_page", "Dashboard")
        else:
            for k in list(visible_nav.keys()) + ["Home"]:
                if k.lower() == qp_clean:
                    st.session_state.active_page = k
                    break

    if "active_page" not in st.session_state:
        st.session_state.active_page = "Home"

    # If active_page is Home, render dedicated full-width SaaS homepage
    if st.session_state.active_page == "Home":
        st.query_params["page"] = "Home"
        employees = get_employees()
        periods = get_periods()
        areas = get_areas()
        assessments = get_assessments()
        render_homepage(summary, employees, assessments, periods, areas, settings)
        return

    # Authentication Gate for internal workspace
    if "user" not in st.session_state:
        auth_page = st.session_state.get("auth_page", "login")
        if auth_page == "reset_password":
            render_password_reset_page()
        elif auth_page == "forgot_password":
            render_forgot_password_page()
        elif auth_page == "register":
            render_register_page()
        else:
            render_login_page()
        return

    # Enforce a maximum session lifetime based on the sign-in timestamp
    session_started = st.session_state.get("session_started_at")
    now_utc = datetime.utcnow()
    if not isinstance(session_started, datetime):
        st.session_state["session_started_at"] = now_utc
    elif now_utc - session_started > timedelta(hours=SESSION_MAX_AGE_HOURS):
        st.session_state.pop("user", None)
        st.session_state.pop("session_started_at", None)
        st.session_state.pop("show_logout_confirm", None)
        st.session_state["session_expired"] = True
        st.session_state.auth_page = "login"
        st.session_state.active_page = "Home"
        st.query_params["page"] = "login"
        st.rerun()

    # Enforce password change if required
    if st.session_state.user.get("must_change_password"):
        render_change_password_page(st.session_state.user)
        return

    # Check for logout confirmation
    if st.session_state.get("show_logout_confirm"):
        render_logout_confirmation_page()
        return

    # Render Sidebar
    page = _sidebar(summary, admin_name, workspace_name)

    # Check if navigating to Home - render homepage directly
    if page == "Home":
        employees = get_employees()
        periods = get_periods()
        areas = get_areas()
        assessments = get_assessments()
        st.query_params["page"] = "Home"
        render_homepage(summary, employees, assessments, periods, areas, settings)
        return

    # Render Topbar (badge reflects unread system alerts only)
    notifications = get_notifications()
    unread_count = int(notifications["read_at"].isna().sum()) if not notifications.empty else 0
    _topbar(page, unread_count, admin_name)

    # Retrieve Domain Data
    employees = get_employees()
    periods = get_periods()
    areas = get_areas()
    assessments = get_assessments()

    # Server-side route guard: URL manipulation cannot bypass role boundaries
    if not can_access_page(page, role):
        _unauthorized_alert()
        return

    # Route to Module Page
    if page == "Dashboard":
        _dashboard(employees, assessments, summary, periods)
    elif page == "My Profile":
        _my_profile_page(employees, assessments)
    elif page == "Employees":
        _employees_page(employees, assessments)
    elif page == "Performance Periods":
        _periods_page(periods, assessments)
    elif page == "Performance Areas":
        _areas_page(areas)
    elif page == "Assessments":
        _assessments_page(employees, periods, areas, assessments)
    elif page == "Analytics":
        _analytics_page(employees, assessments)
    elif page == "Predictions":
        _predictions_page(employees)
    elif page == "Reports":
        _reports_page(assessments)
    elif page == "Notifications":
        _notifications_page(employees, assessments)
    elif page == "Settings":
        _settings_page()
    elif page == "User Management":
        _user_management_page()


if __name__ == "__main__":
    main()
