"""Streamlit pages and interaction handlers for the WorkPulse application."""

import os
from html import escape
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
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
    mark_notifications_read,
    mark_bundled_sample_records,
    save_areas,
    save_assessment,
    save_period,
    save_settings,
    update_employee_profile,
)
from ui_components import (
    apply_chart_style,
    render_metric_card,
    render_page_heading,
    render_status,
    show_empty_state,
)
from homepage_view import render_homepage
from utils.validation import VALID_DEPARTMENTS

NAV_ITEMS = {
    "Dashboard": "⌂",
    "Employees": "♙",
    "Performance Periods": "▦",
    "Performance Areas": "◈",
    "Assessments": "✓",
    "Analytics": "▥",
    "Predictions": "⌁",
    "Reports": "▤",
    "Notifications": "◉",
    "Settings": "⚙",
}
STATUS_OPTIONS = ("Active", "On leave", "Inactive")
PERIOD_STATUS_OPTIONS = ("Draft", "Active", "Completed")


def _configure_page() -> None:
    st.set_page_config(
        page_title="WorkPulse · Employee Performance",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
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


def _sync_page_query() -> None:
    selected_page = st.session_state.get("active_page")
    if selected_page in NAV_ITEMS:
        st.query_params["page"] = selected_page


def _sidebar(summary: dict[str, int], admin_name: str, workspace_name: str) -> str:
    admin_name = escape(admin_name)
    workspace_name = escape(workspace_name)
    st.sidebar.markdown(
        f"""
        <div class="wp-brand">
          <div class="wp-brand-mark">W</div>
          <div><strong>{workspace_name}</strong><small>PEOPLE ANALYTICS</small></div>
        </div>
        <div class="wp-admin-card">
          <div class="wp-avatar">{escape(admin_name[:1].upper() or "A")}</div>
          <div class="wp-admin-copy"><strong>{admin_name}</strong><span>Workspace owner</span></div>
          <span class="wp-admin-menu" aria-hidden="true">⌄</span>
        </div>
        <div class="wp-sidebar-section">WORKSPACE</div>
        """,
        unsafe_allow_html=True,
    )
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Dashboard"
    selected = st.sidebar.radio(
        "Main navigation",
        options=list(NAV_ITEMS),
        format_func=lambda page: f"{NAV_ITEMS[page]}    {page}",
        label_visibility="collapsed",
        key="active_page",
        on_change=_sync_page_query,
    )
    st.sidebar.markdown(
        f"""
        <div class="wp-sidebar-footer">
          <div class="wp-sidebar-section">WORKSPACE STATUS</div>
          <div class="wp-db-status"><span></span> SQLite connected</div>
          <div class="wp-sidebar-count">{summary["total_employees"]:,} registered employees</div>
          {f'<div class="wp-sidebar-demo">Includes {summary["demo_employees"]:,} demo records</div>' if summary["demo_employees"] else ''}
          <div class="wp-sidebar-tagline">Understand Performance.<br>Empower Growth.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return selected


def _topbar(page: str, unread_count: int, admin_name: str) -> None:
    profile_name = admin_name.strip() or "Administrator"
    title_col, notification_col, profile_col, action_col = st.columns(
        [5.1, 0.9, 1.2, 1.8], vertical_alignment="center"
    )
    with title_col:
        st.markdown(
            f'<div class="wp-topbar-title">{page}</div>'
            '<div class="wp-breadcrumb">Workspace&nbsp; / &nbsp;'
            f'<span>{page}</span></div>',
            unsafe_allow_html=True,
        )
    with notification_col:
        if st.button(
            f"◉ {unread_count}" if unread_count else "◉",
            help="Open notifications",
            use_container_width=True,
            key="topbar_notifications",
        ):
            st.session_state.active_page = "Notifications"
            st.rerun()
    with profile_col:
        if st.button(
            f"{profile_name[0].upper()}  {profile_name.split()[0]}",
            help="Open workspace settings",
            use_container_width=True,
        ):
            st.session_state.active_page = "Settings"
            st.rerun()
    action = {
        "Dashboard": ("＋  New assessment", "Assessments"),
        "Employees": ("＋  Add employee", "Employees"),
        "Performance Periods": ("＋  New period", "Performance Periods"),
        "Performance Areas": ("Save indicators", "Performance Areas"),
        "Assessments": ("＋  New assessment", "Assessments"),
        "Analytics": ("View reports", "Reports"),
        "Predictions": ("Review assessments", "Assessments"),
        "Reports": ("Back to dashboard", "Dashboard"),
        "Notifications": ("Review queue", "Assessments"),
        "Settings": ("View notifications", "Notifications"),
    }[page]
    with action_col:
        st.button(
            action[0],
            type="primary",
            use_container_width=True,
            key=f"top_action_{page}",
            on_click=_open_action,
            args=(page, action[1]),
        )


def _open_action(source_page: str, destination: str) -> None:
    st.session_state.active_page = destination
    if source_page == "Employees":
        st.session_state.show_employee_form = True
    elif source_page in {"Dashboard", "Assessments", "Notifications"}:
        st.session_state.show_assessment_form = True
    elif source_page == "Performance Periods":
        st.session_state.show_period_form = True
    elif source_page == "Performance Areas":
        st.session_state.save_areas_requested = True


def _section_heading(title: str, caption: str | None = None) -> None:
    st.markdown(f'<div class="wp-section-title">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def _dashboard(
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
    summary: dict[str, int],
) -> None:
    render_page_heading(
        "Dashboard",
        "A clear view of workforce health, review progress, and performance trends.",
        "WORKSPACE  /  OVERVIEW",
    )
    cards = [
        (
            "Total employees",
            summary["total_employees"],
            "Bundled demo records" if summary["demo_employees"] else "Registered in the directory",
            "♙",
            "blue",
        ),
        ("Active review periods", summary["active_periods"], "Accepting assessments", "▦", "teal"),
        ("Completed assessments", summary["completed_assessments"], "Saved to review history", "✓", "green"),
        ("Performance KPIs", summary["performance_areas"], "Active weighted indicators", "▥", "amber"),
    ]
    details = [
        ("View employees", "Employees"),
        ("Manage periods", "Performance Periods"),
        ("Review history", "Assessments"),
        ("Configure KPIs", "Performance Areas"),
    ]
    card_columns = st.columns(4, gap="medium")
    for index, (column, card) in enumerate(zip(card_columns, cards)):
        with column:
            render_metric_card(*card)
            label, destination = details[index]
            if st.button(label, key=f"metric_details_{index}", use_container_width=True):
                st.session_state.active_page = destination
                st.rerun()

    if summary["demo_employees"]:
        st.warning(
            f"The directory currently contains {summary['demo_employees']:,} bundled "
            "demonstration employees. These are example records, not live workforce data."
        )
    if employees.empty:
        st.info(
            "Your employee directory is empty. Add employees to begin tracking real "
            "workforce metrics; dashboard values will remain at zero until records exist."
        )
    st.write("")
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        _section_heading("Performance distribution", "Latest recorded assessment outcomes")
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
            figure = px.pie(
                counts,
                names="Performance",
                values="Employees",
                hole=0.7,
                color="Performance",
                color_discrete_map={
                    "High": "#3A8D72",
                    "Moderate": "#D29A38",
                    "Needs Support": "#CF6C64",
                },
            )
            figure.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(apply_chart_style(figure), use_container_width=True)
        elif employees.get("performance_category", pd.Series(dtype=object)).notna().any():
            category_counts = (
                employees["performance_category"]
                .dropna()
                .value_counts()
                .rename_axis("Performance")
                .reset_index(name="Employees")
            )
            figure = px.pie(
                category_counts,
                names="Performance",
                values="Employees",
                hole=0.7,
                color="Performance",
                color_discrete_map={
                    "High": "#3A8D72",
                    "Moderate": "#D29A38",
                    "Needs Support": "#CF6C64",
                },
            )
            figure.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(apply_chart_style(figure), use_container_width=True)
            st.caption("Distribution uses imported latest review categories.")
        else:
            show_empty_state("No assessments yet", "Complete an assessment to see the real performance distribution.")
    with right:
        _section_heading("Department comparison", "Average overall score by department")
        if not assessments.empty:
            department_data = (
                assessments.groupby("department", as_index=False)["overall_score"]
                .mean()
                .sort_values("overall_score")
            )
            figure = px.bar(
                department_data,
                x="overall_score",
                y="department",
                orientation="h",
                labels={"overall_score": "Average score", "department": ""},
                range_x=[0, 100],
                color_discrete_sequence=["#147DA8"],
            )
            st.plotly_chart(apply_chart_style(figure), use_container_width=True)
        else:
            show_empty_state(
                "Department insights will appear here",
                "Department comparison becomes available after assessments are recorded.",
            )

    trend_col, queue_col = st.columns([1.2, 1], gap="large")
    with trend_col:
        _section_heading("Monthly performance trend", "Average assessment scores by month")
        if not assessments.empty:
            trend = assessments.copy()
            trend["month"] = pd.to_datetime(trend["assessment_date"]).dt.to_period("M").astype(str)
            monthly = (
                trend.groupby("month", as_index=False)["overall_score"]
                .mean()
                .sort_values("month")
            )
            figure = px.line(
                monthly,
                x="month",
                y="overall_score",
                markers=True,
                labels={"month": "", "overall_score": "Average score"},
                color_discrete_sequence=["#147DA8"],
            )
            figure.update_yaxes(range=[0, 100])
            st.plotly_chart(apply_chart_style(figure), use_container_width=True)
        else:
            show_empty_state("No trend data yet", "Historical trends appear after real assessments are submitted.")
    with queue_col:
        _section_heading("Employees requiring support", "Based on actual latest reviews or open review periods")
        support = employees[
            employees.get("performance_category", pd.Series(index=employees.index, dtype=object))
            .fillna("")
            .eq("Needs Support")
        ][["employee_code", "employee_name", "department"]].copy()
        if not assessments.empty:
            latest = assessments.sort_values(
                ["assessment_date", "assessment_id"]
            ).drop_duplicates("employee_id", keep="last")
            latest_support = latest[
                latest["overall_score"] < 60
            ][["employee_code", "employee_name", "department"]]
            support = pd.concat([support, latest_support]).drop_duplicates("employee_code")
        pending = get_pending_reviews()
        if not pending.empty:
            pending_display = pending[["employee_code", "employee_name", "department"]]
            support = pd.concat([support, pending_display]).drop_duplicates("employee_code")
        if support.empty:
            st.success("No employees currently meet the support or pending-review criteria.")
        else:
            st.dataframe(support.head(8), hide_index=True, use_container_width=True)

    _section_heading("Recent assessments", "Latest completed employee reviews")
    if assessments.empty:
        show_empty_state("Your assessment history is ready", "Newly submitted reviews will appear here.")
    else:
        recent = assessments.head(6).copy()
        recent["result"] = recent["overall_score"].map(_get_category)
        st.dataframe(
            recent[
                [
                    "employee_code", "employee_name", "department",
                    "period_name", "assessment_date", "overall_score", "result",
                ]
            ].rename(
                columns={
                    "employee_code": "Employee ID",
                    "employee_name": "Employee",
                    "department": "Department",
                    "period_name": "Review period",
                    "assessment_date": "Date",
                    "overall_score": "Score",
                    "result": "Outcome",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    _section_heading("Quick actions")
    action_columns = st.columns(3)
    quick_actions = [
        ("＋  Add employee", "Employees", "show_employee_form"),
        ("✓  Create assessment", "Assessments", "show_assessment_form"),
        ("▤  Generate report", "Reports", None),
    ]
    for column, (label, page, flag) in zip(action_columns, quick_actions):
        with column:
            if st.button(label, use_container_width=True):
                st.session_state.active_page = page
                if flag:
                    st.session_state[flag] = True
                st.rerun()


def _employees_page(employees: pd.DataFrame) -> None:
    render_page_heading("Employees", "Manage employee profiles and review eligibility.", "WORKSPACE  /  PEOPLE")
    if st.session_state.pop("show_employee_form", False):
        st.session_state.employee_form_open = True

    with st.expander("＋  Add employee", expanded=st.session_state.get("employee_form_open", False)):
        with st.form("create_employee_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            code = c1.text_input("Employee ID *")
            name = c2.text_input("Full name *")
            department = c3.selectbox("Department *", options=list(VALID_DEPARTMENTS))
            c4, c5, c6 = st.columns(3)
            designation = c4.text_input("Designation")
            joining_date = c5.date_input("Joining date", value=date.today())
            status = c6.selectbox("Status", options=STATUS_OPTIONS)
            experience = st.number_input("Experience (years)", 0.0, 80.0, 0.0, 0.5)
            submitted = st.form_submit_button("Save employee", type="primary")
        if submitted:
            try:
                create_employee(code, name, department, designation, joining_date, status, experience)
                st.session_state.employee_form_open = False
                st.success("Employee profile created.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not save the employee: {error}")

    if employees.empty:
        show_empty_state("No employees found", "Add an employee to start your directory.")
        return

    search_col, department_col, status_col = st.columns([2.4, 1, 1])
    query = search_col.text_input("Search employees", placeholder="Search name or employee ID")
    departments = ["All departments", *sorted(employees["department"].dropna().unique())]
    department_filter = department_col.selectbox("Department", departments)
    status_filter = status_col.selectbox("Status", ["All statuses", *STATUS_OPTIONS])
    filtered = employees.copy()
    if query.strip():
        mask = (
            filtered["employee_name"].fillna("").str.contains(query, case=False, regex=False)
            | filtered["employee_code"].fillna("").str.contains(query, case=False, regex=False)
        )
        filtered = filtered[mask]
    if department_filter != "All departments":
        filtered = filtered[filtered["department"] == department_filter]
    if status_filter != "All statuses":
        filtered = filtered[filtered["status"] == status_filter]
    columns = [
        "employee_code", "employee_name", "department", "designation",
        "joining_date", "status", "data_origin", "performance_category",
    ]
    st.caption(f"{len(filtered):,} of {len(employees):,} employees")
    st.dataframe(
        filtered[columns].rename(
            columns={
                "employee_code": "Employee ID", "employee_name": "Name",
                "department": "Department", "designation": "Designation",
                "joining_date": "Joining date", "status": "Status",
                "data_origin": "Data source",
                "performance_category": "Latest recorded outcome",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    employee_options = {
        f"{row.employee_code} · {row.employee_name}": row
        for row in employees.itertuples(index=False)
    }
    with st.expander("Edit an employee profile"):
        label = st.selectbox("Choose an employee", list(employee_options), key="employee_to_edit")
        employee = employee_options[label]
        with st.form("edit_employee_form"):
            a, b, c = st.columns(3)
            edit_code = a.text_input("Employee ID *", value=str(employee.employee_code))
            edit_name = b.text_input("Full name *", value=str(employee.employee_name))
            edit_department = c.selectbox(
                "Department *", list(VALID_DEPARTMENTS),
                index=_option_index(VALID_DEPARTMENTS, employee.department),
            )
            d, e, f = st.columns(3)
            edit_designation = d.text_input("Designation", value=str(employee.designation or ""))
            edit_joining_date = e.date_input(
                "Joining date",
                value=_safe_date(employee.joining_date),
                key="edit_employee_joining_date",
            )
            edit_status = f.selectbox(
                "Status", STATUS_OPTIONS,
                index=_option_index(STATUS_OPTIONS, employee.status),
            )
            edit_experience = st.number_input(
                "Experience (years)", min_value=0.0, max_value=80.0,
                value=float(employee.experience_years or 0), step=0.5,
                key="edit_employee_experience",
            )
            save = st.form_submit_button("Save changes", type="primary")
        if save:
            try:
                update_employee_profile(
                    employee.employee_id, edit_code, edit_name, edit_department,
                    edit_designation, edit_joining_date, edit_status, edit_experience,
                )
                st.success("Employee profile updated.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not update the employee: {error}")

    with st.expander("Delete an employee"):
        delete_label = st.selectbox("Employee to delete", list(employee_options), key="employee_to_delete")
        confirmed = st.checkbox(
            "I understand deleting this employee also removes their linked assessments.",
            key="confirm_employee_delete",
        )
        if st.button("Delete employee", type="secondary", disabled=not confirmed):
            try:
                delete_employee(employee_options[delete_label].employee_id)
                st.session_state.confirm_employee_delete = False
                st.success("Employee and linked assessments deleted.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not delete the employee: {error}")


def _periods_page(periods: pd.DataFrame) -> None:
    render_page_heading("Performance periods", "Set review windows and track completion.", "WORKSPACE  /  REVIEW CYCLES")
    if st.session_state.pop("show_period_form", False):
        st.session_state.period_form_open = True
    with st.expander("＋  Create review period", expanded=st.session_state.get("period_form_open", False)):
        with st.form("create_period_form", clear_on_submit=True):
            name = st.text_input("Period name *", placeholder="e.g. H1 2026 Review")
            a, b, c = st.columns(3)
            start = a.date_input("Start date", value=date.today())
            end = b.date_input("End date", value=date.today())
            status = c.selectbox("Status", PERIOD_STATUS_OPTIONS, index=1)
            submitted = st.form_submit_button("Create period", type="primary")
        if submitted:
            try:
                save_period(name, start, end, status)
                st.session_state.period_form_open = False
                st.success("Review period created.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not create the review period: {error}")
    if periods.empty:
        show_empty_state("No review periods yet", "Create a period before submitting performance assessments.")
        return
    st.dataframe(
        periods.rename(
            columns={
                "name": "Period", "start_date": "Start", "end_date": "End",
                "status": "Status", "assessment_count": "Assessments",
            }
        ).drop(columns=["period_id"]),
        hide_index=True,
        use_container_width=True,
    )
    period_options = {f"{r.name} · {r.status}": r for r in periods.itertuples(index=False)}
    with st.expander("Edit a review period"):
        label = st.selectbox("Period to edit", list(period_options), key="period_to_edit")
        period = period_options[label]
        with st.form("edit_period_form"):
            name = st.text_input("Period name *", value=period.name)
            a, b, c = st.columns(3)
            start = a.date_input("Start date", value=_safe_date(period.start_date), key="edit_period_start")
            end = b.date_input("End date", value=_safe_date(period.end_date), key="edit_period_end")
            status = c.selectbox(
                "Status", PERIOD_STATUS_OPTIONS,
                index=_option_index(PERIOD_STATUS_OPTIONS, period.status),
                key="edit_period_status",
            )
            save = st.form_submit_button("Save period changes", type="primary")
        if save:
            try:
                save_period(name, start, end, status, int(period.period_id))
                st.success("Review period updated.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not update the review period: {error}")
    with st.expander("Delete a review period"):
        label = st.selectbox("Period to delete", list(period_options), key="period_to_delete")
        period = period_options[label]
        if int(period.assessment_count):
            st.warning("This period has assessments and cannot be deleted.")
        else:
            confirmed = st.checkbox("Confirm deletion of this review period.", key="confirm_period_delete")
            if st.button("Delete review period", disabled=not confirmed):
                try:
                    delete_period(period.period_id)
                    st.success("Review period deleted.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not delete the period: {error}")


def _areas_page(areas: pd.DataFrame) -> None:
    render_page_heading("Performance areas", "Define review indicators and their contribution to the overall score.", "WORKSPACE  /  REVIEW FRAMEWORK")
    st.info("Active indicator weights must add up to exactly 100%. Assessment scores are entered from 0 to 100.")
    edited = st.data_editor(
        areas,
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="performance_area_editor",
        column_config={
            "area_id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Indicator", required=True),
            "description": st.column_config.TextColumn("Description"),
            "weight": st.column_config.NumberColumn("Weight (%)", min_value=0, max_value=100, step=1, format="%.1f"),
            "active": st.column_config.CheckboxColumn("Active"),
        },
        disabled=["area_id"],
    )
    if st.button("Save performance areas", type="primary") or st.session_state.pop(
        "save_areas_requested", False
    ):
        try:
            save_areas(edited.to_dict(orient="records"))
            st.success("Review indicators and weights saved.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not save performance areas: {error}")
    total = edited.loc[edited["active"].fillna(False), "weight"].fillna(0).sum()
    if abs(float(total) - 100) < 0.01:
        st.success(f"Active weights total {total:g}%.")
    else:
        st.warning(f"Active weights currently total {total:g}%; adjust to 100% before saving.")


def _assessments_page(
    employees: pd.DataFrame,
    periods: pd.DataFrame,
    areas: pd.DataFrame,
    assessments: pd.DataFrame,
) -> None:
    render_page_heading("Assessments", "Record evidence-based reviews and preserve assessment history.", "WORKSPACE  /  PERFORMANCE")
    if st.session_state.pop("show_assessment_form", False):
        st.session_state.assessment_form_open = True
    eligible_employees = employees[employees["status"] == "Active"]
    active_periods = periods[periods["status"] == "Active"]
    active_areas = areas[areas["active"].astype(bool)]
    if eligible_employees.empty:
        st.warning("Add an active employee before creating an assessment.")
    elif active_periods.empty:
        st.warning("Create and activate a review period before creating an assessment.")
    elif active_areas.empty:
        st.warning("Activate performance areas before creating an assessment.")
    else:
        employee_options = {
            f"{row.employee_code} · {row.employee_name}": int(row.employee_id)
            for row in eligible_employees.itertuples(index=False)
        }
        period_options = {
            f"{row.name} · due {row.end_date}": int(row.period_id)
            for row in active_periods.itertuples(index=False)
        }
        with st.expander("＋  New assessment", expanded=st.session_state.get("assessment_form_open", False)):
            with st.form("create_assessment_form"):
                employee_label = st.selectbox("Employee *", list(employee_options))
                period_label = st.selectbox("Review period *", list(period_options))
                assessor, review_day = st.columns(2)
                reviewer = assessor.text_input("Reviewer *")
                assessment_date = review_day.date_input("Assessment date", value=date.today())
                scores: dict[str, float] = {}
                score_columns = st.columns(2)
                for index, area in enumerate(active_areas.itertuples(index=False)):
                    scores[area.name] = score_columns[index % 2].number_input(
                        f"{area.name} · weight {area.weight:g}%",
                        min_value=0.0,
                        max_value=100.0,
                        value=75.0,
                        step=1.0,
                        key=f"score_{area.area_id}",
                    )
                comments = st.text_area("Reviewer comments", max_chars=5000)
                preview = sum(
                    scores[row.name] * float(row.weight) / 100
                    for row in active_areas.itertuples(index=False)
                )
                st.caption(f"Weighted overall score: **{preview:.1f} / 100** · {_get_category(preview)}")
                submitted = st.form_submit_button("Save assessment", type="primary")
            if submitted:
                try:
                    save_assessment(
                        employee_options[employee_label],
                        period_options[period_label],
                        assessment_date,
                        reviewer,
                        scores,
                        comments,
                    )
                    st.session_state.assessment_form_open = False
                    st.success("Assessment saved to the employee’s review history.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not save the assessment: {error}")
    _section_heading("Assessment history", "Search, filter, and export completed reviews.")
    if assessments.empty:
        show_empty_state("No assessments recorded", "Submitted reviews will be listed here.")
        return
    search = st.text_input("Search assessments", placeholder="Employee, department, reviewer, or review period")
    filter_col, period_col = st.columns(2)
    dept_values = ["All departments", *sorted(assessments["department"].dropna().unique())]
    department = filter_col.selectbox("Department", dept_values, key="assessment_department")
    period_values = ["All periods", *sorted(assessments["period_name"].unique())]
    period = period_col.selectbox("Review period", period_values, key="assessment_period")
    filtered = assessments.copy()
    if department != "All departments":
        filtered = filtered[filtered["department"] == department]
    if period != "All periods":
        filtered = filtered[filtered["period_name"] == period]
    if search.strip():
        mask = pd.Series(False, index=filtered.index)
        for column in ("employee_name", "employee_code", "department", "reviewer", "period_name"):
            mask |= filtered[column].fillna("").astype(str).str.contains(search, case=False, regex=False)
        filtered = filtered[mask]
    table = filtered.copy()
    table["Outcome"] = table["overall_score"].map(_get_category)
    st.dataframe(
        table[
            ["employee_code", "employee_name", "department", "period_name",
             "assessment_date", "reviewer", "overall_score", "Outcome", "comments"]
        ].rename(
            columns={
                "employee_code": "Employee ID", "employee_name": "Employee",
                "department": "Department", "period_name": "Review period",
                "assessment_date": "Date", "reviewer": "Reviewer",
                "overall_score": "Score", "comments": "Comments",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.download_button(
        "Download filtered assessments (CSV)",
        filtered.drop(columns=["scores_json"], errors="ignore").to_csv(index=False).encode("utf-8"),
        file_name="workpulse-assessments.csv",
        mime="text/csv",
    )


def _analytics_page(
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
) -> None:
    render_page_heading("Analytics", "Explore actual review outcomes by department and period.", "WORKSPACE  /  INSIGHTS")
    if assessments.empty:
        show_empty_state(
            "Analytics need completed assessments",
            "Create a review period and record assessments to see score trends and comparisons.",
        )
        if not employees.empty and employees["performance_category"].notna().any():
            st.caption("Existing imported review categories are available on the dashboard.")
        return
    period_names = ["All periods", *sorted(assessments["period_name"].unique())]
    department_names = ["All departments", *sorted(assessments["department"].unique())]
    a, b = st.columns(2)
    selected_period = a.selectbox("Review period", period_names)
    selected_department = b.selectbox("Department", department_names)
    filtered = assessments.copy()
    if selected_period != "All periods":
        filtered = filtered[filtered["period_name"] == selected_period]
    if selected_department != "All departments":
        filtered = filtered[filtered["department"] == selected_department]
    avg_score = float(filtered["overall_score"].mean()) if not filtered.empty else 0.0
    average_col, total_col, high_col = st.columns(3)
    average_col.metric("Average score", f"{avg_score:.1f} / 100" if not filtered.empty else "—")
    total_col.metric("Assessments", f"{len(filtered):,}")
    high_col.metric("High outcomes", f"{int((filtered['overall_score'] >= 80).sum()):,}" if not filtered.empty else "0")
    if filtered.empty:
        st.info("No assessments match the selected filters.")
        return
    left, right = st.columns(2, gap="large")
    with left:
        _section_heading("Department comparison", "Mean assessment score")
        department_summary = (
            filtered.groupby("department", as_index=False)["overall_score"]
            .mean()
            .sort_values("overall_score", ascending=False)
        )
        fig = px.bar(
            department_summary,
            x="department", y="overall_score",
            labels={"department": "", "overall_score": "Average score"},
            range_y=[0, 100], color_discrete_sequence=["#147DA8"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with right:
        _section_heading("Performance mix", "Score bands derived from recorded weighted assessments")
        category_data = filtered["overall_score"].map(_get_category).value_counts().rename_axis("Outcome").reset_index(name="Assessments")
        fig = px.pie(
            category_data, names="Outcome", values="Assessments", hole=0.68,
            color="Outcome",
            color_discrete_map={"High": "#3A8D72", "Moderate": "#D29A38", "Needs Support": "#CF6C64"},
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    _section_heading("Monthly trend")
    monthly = filtered.copy()
    monthly["Month"] = pd.to_datetime(monthly["assessment_date"]).dt.to_period("M").astype(str)
    monthly = monthly.groupby("Month", as_index=False)["overall_score"].mean().sort_values("Month")
    fig = px.line(
        monthly, x="Month", y="overall_score", markers=True,
        labels={"overall_score": "Average score"},
        color_discrete_sequence=["#147DA8"],
    )
    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    _section_heading("Score distribution by department")
    fig = px.box(
        filtered, x="department", y="overall_score", points="all",
        labels={"department": "", "overall_score": "Assessment score"},
        color_discrete_sequence=["#147DA8"],
    )
    st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def _predictions_page(employees: pd.DataFrame) -> None:
    render_page_heading("Predictions", "Experimental model outputs are separate from completed assessments.", "WORKSPACE  /  DECISION SUPPORT")
    st.warning(
        "Predictions are experimental decision-support estimates, not employee assessment "
        "results. Never use them alone to make employment decisions."
    )
    labelled = _training_frame(employees)
    if labelled.empty:
        st.info("No complete, labelled historical records are available for model evaluation.")
        return
    counts = labelled["performance_category"].value_counts()
    if len(counts) < 2 or counts.min() < 2:
        st.info("At least two complete labelled records in each observed class are needed for a held-out evaluation.")
        return
    if len(labelled) < 10:
        st.info("Add more complete labelled historical records before evaluating a model.")
        return
    model_features = FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL
    if "performance_category" in model_features:
        st.error("Model configuration error: target label appears in the feature list.")
        return
    try:
        with st.spinner("Training and evaluating Decision Tree and Random Forest models…"):
            results, pipelines = _train_models(labelled)
    except Exception as error:
        st.error(f"Models could not be evaluated on the available labelled data: {error}")
        return
    st.caption(
        f"Evaluation uses {len(labelled):,} complete labelled historical records. "
        "The target category is kept out of the input features; the models use a held-out test split."
    )
    models = list(pipelines)
    selected = st.selectbox("Model", models)
    metrics = results[selected]
    metric_cols = st.columns(4)
    for column, name in zip(metric_cols, ("accuracy", "precision", "recall", "f1_score")):
        column.metric(name.replace("_", " ").title(), f"{float(metrics[name]):.1%}")
    if "confusion_matrix" in metrics:
        st.caption(
            f"Held-out samples: {metrics.get('test_samples', '—')} · "
            f"Training samples: {metrics.get('train_samples', '—')}"
        )
        matrix = np.asarray(metrics["confusion_matrix"])
        labels = metrics.get("classes", TARGET_CLASSES)
        fig = px.imshow(
            matrix,
            x=labels,
            y=labels,
            text_auto=True,
            color_continuous_scale="Blues",
            labels={"x": "Predicted", "y": "Actual", "color": "Records"},
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    _section_heading("Estimate a performance category", "Use current operational indicators; the result is not an assessment.")
    if employees.empty:
        st.info("Add an employee with historical performance inputs before generating a prediction.")
        return
    employee_options = {"Manual entry": None}
    employee_options.update(
        {
            f"{row.employee_code} · {row.employee_name}": row
            for row in employees.itertuples(index=False)
        }
    )
    selected_employee = st.selectbox("Use employee data", list(employee_options), key="prediction_employee")
    employee = employee_options[selected_employee]
    with st.form("prediction_form"):
        departments = sorted(set(VALID_DEPARTMENTS) | set(employees["department"].dropna().astype(str)))
        default_dept = getattr(employee, "department", departments[0])
        department = st.selectbox(
            "Department",
            departments,
            index=_option_index(departments, default_dept),
        )
        left, right = st.columns(2)
        attendance = left.number_input(
            "Attendance (%)", 0.0, 100.0,
            _finite(getattr(employee, "attendance_rate", None), 90), 1.0,
        )
        task_completion = right.number_input(
            "Task completion (%)", 0.0, 100.0,
            _finite(getattr(employee, "task_completion_rate", None), 80), 1.0,
        )
        training = left.number_input(
            "Training hours", 0.0, 2000.0,
            _finite(getattr(employee, "training_hours", None), 30), 1.0,
        )
        experience = right.number_input(
            "Experience (years)", 0.0, 80.0,
            _finite(getattr(employee, "experience_years", None), 3), 0.5,
        )
        previous = left.number_input(
            "Previous performance (1–5)", 1.0, 5.0,
            _finite(getattr(employee, "previous_performance", None), 3.0), 0.1,
        )
        submitted = st.form_submit_button("Generate estimate", type="primary")
    if submitted:
        features = {
            "department": department,
            "attendance_rate": attendance,
            "task_completion_rate": task_completion,
            "training_hours": training,
            "experience_years": experience,
            "previous_performance": previous,
        }
        try:
            output = run_employee_prediction(
                pipelines[selected],
                features,
                employee_id=getattr(employee, "employee_id", None),
                population_df=labelled,
            )
            st.markdown(
                f'<div class="wp-prediction-result"><span>MODEL ESTIMATE</span>'
                f'<strong>{output["predicted_category"]}</strong>'
                f'<small>Not a completed assessment</small></div>',
                unsafe_allow_html=True,
            )
            probabilities = pd.DataFrame(
                [{"Category": category, "Probability": value} for category, value in output["probabilities"].items()]
            )
            fig = px.bar(
                probabilities, x="Category", y="Probability",
                range_y=[0, 1], text_auto=".0%",
                color_discrete_sequence=["#147DA8"],
            )
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
            if not output["contributions"].empty:
                st.dataframe(output["contributions"], hide_index=True, use_container_width=True)
            st.caption(output["disclaimer"])
        except Exception as error:
            st.error(f"Prediction failed: {error}")


def _reports_page(assessments: pd.DataFrame) -> None:
    render_page_heading("Reports", "Filter, summarize, and export actual review records.", "WORKSPACE  /  REPORTING")
    if assessments.empty:
        show_empty_state("No reportable assessments yet", "Completed assessments will become available here.")
        return
    department_options = ["All departments", *sorted(assessments["department"].dropna().unique())]
    employee_options = ["All employees", *sorted(assessments["employee_name"].dropna().unique())]
    period_options = ["All periods", *sorted(assessments["period_name"].dropna().unique())]
    a, b, c = st.columns(3)
    department = a.selectbox("Department", department_options, key="report_department")
    employee = b.selectbox("Employee", employee_options, key="report_employee")
    period = c.selectbox("Review period", period_options, key="report_period")
    filtered = assessments.copy()
    if department != "All departments":
        filtered = filtered[filtered["department"] == department]
    if employee != "All employees":
        filtered = filtered[filtered["employee_name"] == employee]
    if period != "All periods":
        filtered = filtered[filtered["period_name"] == period]
    if filtered.empty:
        st.info("No assessments match those report filters.")
        return
    x, y, z = st.columns(3)
    x.metric("Assessments", f"{len(filtered):,}")
    y.metric("Average score", f"{filtered['overall_score'].mean():.1f} / 100")
    z.metric("Employees reviewed", f"{filtered['employee_id'].nunique():,}")
    report = filtered.copy()
    report["outcome"] = report["overall_score"].map(_get_category)
    st.dataframe(
        report[
            ["employee_code", "employee_name", "department", "period_name",
             "assessment_date", "reviewer", "overall_score", "outcome", "comments"]
        ].rename(
            columns={
                "employee_code": "Employee ID", "employee_name": "Employee",
                "department": "Department", "period_name": "Review period",
                "assessment_date": "Date", "reviewer": "Reviewer",
                "overall_score": "Score", "outcome": "Outcome",
                "comments": "Reviewer comments",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.download_button(
        "Download report as CSV",
        report.drop(columns=["scores_json"], errors="ignore").to_csv(index=False).encode("utf-8"),
        file_name="workpulse-performance-report.csv",
        mime="text/csv",
        type="primary",
    )
    st.caption("PDF export is not configured; the filtered CSV contains the reportable assessment records.")


def _notifications_page() -> None:
    render_page_heading("Notifications", "Review workflow updates and employees awaiting an assessment.", "WORKSPACE  /  INBOX")
    notifications = get_notifications()
    pending = get_pending_reviews()
    unread = notifications[notifications["read_at"].isna()]
    top = st.columns([1, 4])
    top[0].metric("Unread updates", len(unread))
    if top[1].button("Mark all updates as read", disabled=unread.empty):
        mark_notifications_read()
        st.success("All notifications marked as read.")
        st.rerun()
    _section_heading("Pending assessments", "Active employees with no submitted assessment in an active period")
    if pending.empty:
        st.success("There are no pending assessments in active review periods.")
    else:
        st.dataframe(
            pending[
                ["employee_code", "employee_name", "department", "period_name", "end_date"]
            ].rename(
                columns={
                    "employee_code": "Employee ID", "employee_name": "Employee",
                    "department": "Department", "period_name": "Review period",
                    "end_date": "Due date",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
        if st.button("Start an assessment"):
            st.session_state.active_page = "Assessments"
            st.session_state.show_assessment_form = True
            st.rerun()
    _section_heading("Workspace updates")
    if notifications.empty:
        show_empty_state("All quiet", "Employee, period, and assessment updates will appear here.")
    else:
        for notification in notifications.itertuples(index=False):
            state = "Unread" if pd.isna(notification.read_at) else "Read"
            with st.container(border=True):
                heading, marker = st.columns([5, 1])
                heading.markdown(f"**{notification.title}**")
                marker.markdown(render_status(state), unsafe_allow_html=True)
                st.write(notification.message)
                st.caption(notification.created_at)
                if pd.isna(notification.read_at) and st.button(
                    "Mark as read", key=f"read_{notification.notification_id}"
                ):
                    mark_notifications_read([int(notification.notification_id)])
                    st.rerun()


def _settings_page() -> None:
    render_page_heading("Settings", "Manage workspace preferences and administrator profile details.", "WORKSPACE  /  PREFERENCES")
    settings = get_settings()
    st.info(
        "Authentication and role-based access are not configured in this project. "
        "The administrator profile is a workspace label, not a verified account."
    )
    with st.form("workspace_settings_form"):
        name = st.text_input("Administrator display name", value=settings.get("admin_name", "Administrator"))
        workspace = st.text_input("Workspace name", value=settings.get("workspace_name", "WorkPulse"))
        save = st.form_submit_button("Save preferences", type="primary")
    if save:
        try:
            save_settings(
                {"admin_name": name, "workspace_name": workspace}
            )
            st.success("Workspace preferences saved.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not save preferences: {error}")
    _section_heading("Data and privacy")
    st.markdown(
        "- Employee profiles and assessments are stored in the local SQLite database.\n"
        "- Reports contain only the rows selected by your active filters.\n"
        "- No login system is currently configured; do not expose the app publicly with sensitive employee data."
    )
    st.caption(f"Database file: `{DB_PATH}`")


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


def main() -> None:
    _configure_page()
    initialize_database()
    mark_bundled_sample_records()
    summary = get_dashboard_summary()
    settings = get_settings()
    admin_name = settings.get("admin_name", "Administrator")
    requested_page = st.query_params.get("page")
    if requested_page:
        for page_name in NAV_ITEMS:
            if page_name.casefold() == str(requested_page).strip().casefold():
                st.session_state.active_page = page_name
                break
    elif "active_page" not in st.session_state:
        st.session_state.active_page = "Home"

    if st.session_state.active_page == "Home":
        st.query_params["page"] = "Home"
        render_homepage(
            summary,
            get_employees(),
            get_assessments(),
            get_periods(),
            get_areas(),
            settings,
        )
        return

    page = _sidebar(
        summary,
        admin_name,
        settings.get("workspace_name", "WorkPulse"),
    )
    notifications = get_notifications()
    unread_count = int(notifications["read_at"].isna().sum()) if not notifications.empty else 0
    pending_count = len(get_pending_reviews())
    _topbar(page, unread_count + pending_count, admin_name)
    employees = get_employees()
    periods = get_periods()
    areas = get_areas()
    assessments = get_assessments()
    if page == "Dashboard":
        _dashboard(employees, assessments, summary)
    elif page == "Employees":
        _employees_page(employees)
    elif page == "Performance Periods":
        _periods_page(periods)
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
