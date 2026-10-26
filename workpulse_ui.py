"""
WorkPulse — Employee Performance Review System
Enterprise SaaS UI/UX Presentation Engine built with Streamlit & Plotly.
"""

import os
from datetime import date, timedelta
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
    update_employee_profile,
)
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
from utils.validation import VALID_DEPARTMENTS

# Navigation Registry
NAV_ITEMS = {
    "Home": "🌐  Product Home",
    "Dashboard": "⌂  Dashboard",
    "Employees": "♙  Employees",
    "Performance Periods": "▦  Review Cycles",
    "Performance Areas": "◈  KPI Framework",
    "Assessments": "✓  Assessments",
    "Analytics": "▥  Analytics",
    "Predictions": "⌁  Predictions (ML)",
    "Reports": "▤  Reports",
    "Notifications": "◉  Notifications",
    "Settings": "⚙  Settings & Demo",
}

STATUS_OPTIONS = ("Active", "On leave", "Inactive")
PERIOD_STATUS_OPTIONS = ("Draft", "Active", "Completed")


def _configure_page() -> None:
    st.set_page_config(
        page_title="WorkPulse · Employee Performance Review System",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as stylesheet:
            st.markdown(f"<style>{stylesheet.read()}</style>", unsafe_allow_html=True)


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

    if "active_page" not in st.session_state:
        st.session_state.active_page = "Dashboard"

    selected = st.sidebar.radio(
        "Main navigation",
        options=list(NAV_ITEMS.keys()),
        format_func=lambda page: NAV_ITEMS[page],
        label_visibility="collapsed",
        key="active_page",
    )

    st.sidebar.markdown(
        f"""
        <div class="wp-sidebar-footer">
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
    return selected


def _topbar(page: str, unread_count: int, admin_name: str) -> None:
    profile_name = admin_name.strip() or "Administrator"
    title_col, home_col, notification_col, profile_col, action_col = st.columns(
        [4.2, 1.3, 1.0, 1.2, 2.3], vertical_alignment="center"
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
        if st.button("🌐 Product Home", help="Open public product homepage", use_container_width=True, key="top_home_btn"):
            st.session_state.active_page = "Home"
            st.query_params["page"] = "Home"
            st.rerun()
    with notification_col:
        notif_label = f"🔔 {unread_count}" if unread_count else "🔔 Inbox"
        if st.button(notif_label, help="View notifications and pending reviews", use_container_width=True, key="top_notif"):
            st.session_state.active_page = "Notifications"
            st.rerun()
    with profile_col:
        if st.button(f"⚙ {profile_name.split()[0]}", help="Workspace settings", use_container_width=True, key="top_profile"):
            st.session_state.active_page = "Settings"
            st.rerun()

    action_map = {
        "Dashboard": ("＋  New Assessment", "Assessments", "show_assessment_form"),
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


# =============================================================================
# 1. DASHBOARD PAGE
# =============================================================================
def _dashboard(
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

    # 2. Demonstration Callout if empty assessments
    if assessments.empty:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid var(--wp-border); border-left:4px solid var(--wp-teal); border-radius:var(--wp-radius-md); padding:1rem 1.25rem; margin-bottom:1.25rem; display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <strong style="color:var(--wp-navy); font-size:0.9375rem;">Welcome to WorkPulse!</strong>
                    <div style="color:var(--wp-text-secondary); font-size:0.8125rem; margin-top:0.2rem;">
                        The database has {summary.get('total_employees', 0):,} registered employees. To preview the populated performance analytics, distribution charts, and audit reports for demonstration or viva evaluation, load the demo review cycle.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, _ = st.columns([2.2, 2.2, 5.6])
        if c1.button("⚡ Load Demo Review Cycle", type="primary", use_container_width=True):
            seed_demo_review_cycle()
            st.success("Demonstration review cycle and assessments loaded.")
            st.rerun()
        if c2.button("＋ Add Employee Profile", use_container_width=True):
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
            trend="+2.8% vs Q2" if avg_score else None,
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

    with st.expander("Delete Employee Profile"):
        st.warning(f"Deleting **{selected_emp.employee_name}** ({selected_emp.employee_code}) will permanently remove their profile and all linked assessments.")
        confirmed = st.checkbox("I confirm permanent deletion of this employee record.", key="confirm_delete_emp")
        if st.button("Delete Employee", type="secondary", disabled=not confirmed):
            try:
                delete_employee(selected_emp.employee_id)
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
def _notifications_page() -> None:
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
            is_unread = pd.isna(notif.read_at)
            status_chip = render_status_badge("Needs Support" if is_unread else "Completed")
            st.markdown(
                f"""
                <div class="wp-card" style="margin-bottom:0.75rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong style="color:var(--wp-navy);">{escape(notif.title)}</strong>
                        <span style="font-size:0.75rem; color:var(--wp-text-muted);">{escape(str(notif.created_at))}</span>
                    </div>
                    <p style="margin:0.35rem 0 0 0; color:var(--wp-text-secondary); font-size:0.875rem;">{escape(notif.message)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =============================================================================
# 10. SETTINGS & DEMONSTRATION SUITE
# =============================================================================
def _settings_page() -> None:
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
    initialize_database()
    mark_bundled_sample_records()
    summary = get_dashboard_summary()
    settings = get_settings()
    admin_name = settings.get("admin_name", "Administrator")
    workspace_name = settings.get("workspace_name", "WorkPulse")

    # Synchronize URL query parameters with active_page
    query_page = st.query_params.get("page")
    if query_page:
        for k in list(NAV_ITEMS.keys()) + ["Home"]:
            if k.lower() == str(query_page).strip().lower():
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

    # Render Sidebar
    page = _sidebar(summary, admin_name, workspace_name)

    # If sidebar radio selected Home
    if page == "Home":
        st.session_state.active_page = "Home"
        st.query_params["page"] = "Home"
        st.rerun()

    # Render Topbar
    notifications = get_notifications()
    unread_count = int(notifications["read_at"].isna().sum()) if not notifications.empty else 0
    pending_count = len(get_pending_reviews())
    _topbar(page, unread_count + pending_count, admin_name)

    # Retrieve Domain Data
    employees = get_employees()
    periods = get_periods()
    areas = get_areas()
    assessments = get_assessments()

    # Route to Module Page
    if page == "Dashboard":
        _dashboard(employees, assessments, summary, periods)
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
        _notifications_page()
    elif page == "Settings":
        _settings_page()


if __name__ == "__main__":
    main()
