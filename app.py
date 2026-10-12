"""
WorkPulse – Employee Performance Review System
Comprehensive, functional, professional Streamlit application for CSE Mini-Project.
"""

import os
import io
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Database & Services
from database.db_manager import (
    init_db, get_all_employees, get_predictions_history
)
from services.employee_service import (
    fetch_employees_dataset, create_new_employee, modify_employee,
    remove_employee, fetch_employee_history
)
from services.analytics_service import (
    compute_kpis, get_department_summary, get_time_series_trends
)
from services.prediction_service import run_employee_prediction
from services.report_service import generate_comprehensive_report
from utils.validation import (
    validate_csv_dataset, VALID_DEPARTMENTS, VALID_CATEGORIES
)
from models.train_model import (
    train_and_evaluate_all_models, get_feature_importances,
    FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL, TARGET_CLASSES
)

# -----------------------------------------------------------------------------
# App Setup & Theme Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="WorkPulse - Employee Performance Review System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = "styles.css"
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize database
init_db("data/workpulse.db")

# Cache models
@st.cache_resource
def load_or_train_models(df):
    results, pipelines, splits = train_and_evaluate_all_models(df, models_dir="models")
    return results, pipelines, splits

# Load application dataset
def get_current_data():
    df = fetch_employees_dataset("data/workpulse.db")
    if df.empty and os.path.exists("data/sample_employees.csv"):
        from database.db_manager import import_records_from_df
        sample_df = pd.read_csv("data/sample_employees.csv")
        import_records_from_df(sample_df, "data/workpulse.db")
        df = fetch_employees_dataset("data/workpulse.db")
    return df

raw_df = get_current_data()
eval_results, pipelines, splits = load_or_train_models(raw_df)

# Session state navigation
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "🏠 Home / Overview"

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 16px 0;">
    <h2 style="color: #FFFFFF; margin: 0; font-size: 1.6rem; letter-spacing: -0.02em;">💼 WorkPulse</h2>
    <p style="color: #93C5FD; margin: 4px 0 0 0; font-size: 0.85rem;">Understand Performance. Empower Growth.</p>
</div>
""", unsafe_allow_html=True)

nav_pages = [
    "🏠 Home / Overview",
    "📊 Dashboard",
    "👥 Employee Management",
    "📁 Dataset Management",
    "📈 Performance Analytics",
    "🔮 Performance Prediction",
    "🤖 Model Evaluation",
    "📑 Reports & Export"
]

page_selection = st.sidebar.radio(
    "Navigation Menu",
    nav_pages,
    index=nav_pages.index(st.session_state['current_page']) if st.session_state['current_page'] in nav_pages else 0
)
st.session_state['current_page'] = page_selection

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ System Controls")

selected_model_name = st.sidebar.selectbox(
    "Active ML Model",
    ["Random Forest", "Decision Tree"],
    index=0
)
active_pipeline = pipelines[selected_model_name]

# Database status badge
db_count = len(raw_df)
st.sidebar.markdown(f"""
<div style="background-color: #1E3A8A; padding: 10px 14px; border-radius: 8px; margin: 12px 0;">
    <div style="color: #93C5FD; font-size: 0.75rem; text-transform: uppercase; font-weight: 600;">Database Status</div>
    <div style="color: #FFFFFF; font-size: 1.15rem; font-weight: 700;">{db_count} Records Active</div>
    <div style="color: #34D399; font-size: 0.75rem;">● SQLite Connected</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="color: #94A3B8; font-size: 0.75rem; padding-top: 8px;">
    <b>Academic Project Note</b>: Decision support system for CSE 3rd Year Mini-Project. Predictions are experimental estimates requiring human review.
</div>
""", unsafe_allow_html=True)

# Helper function to render styled HTML KPI card
def render_kpi(col, label, value):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# PAGE 1: HOME / OVERVIEW
# =============================================================================
if page_selection == "🏠 Home / Overview":
    st.markdown("""
    <div class="workpulse-header">
        <h1 class="workpulse-title">WorkPulse – Employee Performance Review System</h1>
        <p class="workpulse-tagline">“Understand Performance. Empower Growth.”</p>
    </div>
    """, unsafe_allow_html=True)

    col_h1, col_h2 = st.columns([2, 1])

    with col_h1:
        st.markdown("### 📌 Project Objective & System Overview")
        st.write("""
        **WorkPulse** is a web-based workforce analytics and decision-support application built for 
        **Computer Science and Engineering Mini-Projects**. The system enables organizations to maintain 
        structured employee records, analyze performance trends across teams, and estimate performance 
        categories using explainable machine learning models.
        
        Traditional performance evaluation often relies on subjective appraisals or manual spreadsheet review. 
        **WorkPulse** introduces data-driven transparency by evaluating work-related indicators—such as 
        attendance consistency, task completion rates, training hours, and historical ratings—without capturing 
        sensitive personal demographics.
        """)

        st.markdown("### 🛠️ Core Functional Modules")
        st.markdown("""
        - **📊 Interactive Dashboard**: High-level KPI indicators and visual distributions of workforce metrics.
        - **👥 Employee Management**: Persistent SQLite CRUD operations to view, add, edit, and delete employee records.
        - **📁 Dataset Management**: CSV dataset upload, missing value validation, cleaning, and export.
        - **📈 Performance Analytics**: Departmental comparisons, correlation heatmaps, and dated trend analysis.
        - **🔮 Performance Prediction**: Live classification with local feature contribution explanations and confidence scores.
        - **🤖 Model Evaluation**: Side-by-side comparison of Decision Tree and Random Forest on held-out test data.
        - **📑 Reports & Export**: Formal executive performance summaries and CSV exports for academic demonstration.
        """)

        st.markdown("<br>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("▶️ Launch Dashboard & Analytics", type="primary", use_container_width=True):
                st.session_state['current_page'] = "📊 Dashboard"
                st.rerun()
        with btn_c2:
            if st.button("👥 Manage Employee Records", use_container_width=True):
                st.session_state['current_page'] = "👥 Employee Management"
                st.rerun()

    with col_h2:
        kpis = compute_kpis(raw_df)
        acc = eval_results[selected_model_name]['accuracy'] * 100
        dept_cnt = raw_df['department'].nunique() if 'department' in raw_df.columns else 0

        st.markdown(f"""
        <div class="content-card" style="text-align: center;">
            <h3 style="color: #172B4D; margin-top: 0;">📊 Live System Stats</h3>
            <p style="color: #64748B; font-size: 0.85rem;">Calculated directly from SQLite database</p>
            <hr style="border-color: #E2E8F0; margin: 15px 0;">
            <div style="color: #2563EB; font-size: 2.4rem; font-weight: 700; font-family: Poppins;">{kpis['total_employees']}</div>
            <div style="color: #64748B; font-size: 0.8rem; text-transform: uppercase; font-weight: 600;">Active Employees</div>
            <hr style="border-color: #E2E8F0; margin: 15px 0;">
            <div style="color: #10B981; font-size: 2.4rem; font-weight: 700; font-family: Poppins;">{acc:.1f}%</div>
            <div style="color: #64748B; font-size: 0.8rem; text-transform: uppercase; font-weight: 600;">{selected_model_name} Accuracy</div>
            <hr style="border-color: #E2E8F0; margin: 15px 0;">
            <div style="color: #F59E0B; font-size: 2.4rem; font-weight: 700; font-family: Poppins;">{dept_cnt}</div>
            <div style="color: #64748B; font-size: 0.8rem; text-transform: uppercase; font-weight: 600;">Departments Monitored</div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# PAGE 2: DASHBOARD
# =============================================================================
elif page_selection == "📊 Dashboard":
    st.subheader("📊 Workforce Performance Dashboard")
    st.markdown("High-level key performance indicators and interactive data distributions.")

    # Filter section
    with st.expander("🔍 Filter Dashboard Data", expanded=False):
        f_col1, f_col2 = st.columns(2)
        depts = sorted(raw_df['department'].unique().tolist()) if 'department' in raw_df.columns else []
        selected_depts = f_col1.multiselect("Select Department(s)", depts, default=depts)

        cats = sorted(raw_df['performance_category'].unique().tolist()) if 'performance_category' in raw_df.columns else []
        selected_cats = f_col2.multiselect("Select Performance Category", cats, default=cats)

    # Filter dataset
    filtered_df = raw_df.copy()
    if selected_depts:
        filtered_df = filtered_df[filtered_df['department'].isin(selected_depts)]
    if selected_cats:
        filtered_df = filtered_df[filtered_df['performance_category'].isin(selected_cats)]

    kpis = compute_kpis(filtered_df)

    # Display 5 KPI Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    render_kpi(k1, "Total Employees", f"{kpis['total_employees']}")
    render_kpi(k2, "Avg Rating", f"{kpis['avg_performance_score']} / 5")
    render_kpi(k3, "Avg Attendance", f"{kpis['avg_attendance']}%")
    render_kpi(k4, "Avg Task Completion", f"{kpis['avg_task_completion']}%")
    render_kpi(k5, "High Performers", f"{kpis['high_count']} ({kpis['high_pct']}%)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1
    r1_c1, r1_c2 = st.columns(2)

    with r1_c1:
        st.markdown("#### Performance Category Distribution")
        cat_counts = filtered_df['performance_category'].value_counts().reset_index()
        cat_counts.columns = ['Category', 'Count']
        fig_donut = px.pie(
            cat_counts, values='Count', names='Category', hole=0.45,
            color='Category',
            color_discrete_map={'High': '#10B981', 'Moderate': '#F59E0B', 'Needs Support': '#EF4444'}
        )
        fig_donut.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_donut, use_container_width=True)

    with r1_c2:
        st.markdown("#### Attendance vs Task Completion Rate")
        fig_scatter = px.scatter(
            filtered_df, x='attendance_rate', y='task_completion_rate',
            color='performance_category', size='experience_years' if 'experience_years' in filtered_df.columns else None,
            hover_data=['employee_code', 'department'] if 'employee_code' in filtered_df.columns else None,
            labels={'attendance_rate': 'Attendance Rate (%)', 'task_completion_rate': 'Task Completion Rate (%)'},
            color_discrete_map={'High': '#10B981', 'Moderate': '#F59E0B', 'Needs Support': '#EF4444'}
        )
        fig_scatter.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Charts Row 2
    r2_c1, r2_c2 = st.columns(2)

    with r2_c1:
        st.markdown("#### Department-wise Performance Distribution")
        dept_perf = pd.crosstab(filtered_df['department'], filtered_df['performance_category']).reset_index()
        bar_cols = [c for c in ['Needs Support', 'Moderate', 'High'] if c in dept_perf.columns]
        fig_bar = px.bar(
            dept_perf, x='department', y=bar_cols,
            barmode='group',
            color_discrete_map={'High': '#10B981', 'Moderate': '#F59E0B', 'Needs Support': '#EF4444'}
        )
        fig_bar.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Department", yaxis_title="Employees")
        st.plotly_chart(fig_bar, use_container_width=True)

    with r2_c2:
        st.markdown("#### Training Hours vs Performance Category")
        fig_box = px.box(
            filtered_df, x='performance_category', y='training_hours',
            color='performance_category',
            labels={'training_hours': 'Training Hours Completed', 'performance_category': 'Category'},
            color_discrete_map={'High': '#10B981', 'Moderate': '#F59E0B', 'Needs Support': '#EF4444'}
        )
        fig_box.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)


# =============================================================================
# PAGE 3: EMPLOYEE MANAGEMENT
# =============================================================================
elif page_selection == "👥 Employee Management":
    st.subheader("👥 Employee Records Management")
    st.markdown("Search, view, add, modify, and delete employee records stored in the SQLite database.")

    tab_view, tab_add, tab_edit, tab_hist = st.tabs([
        "📋 View & Search Records", "➕ Add New Employee", "✏️ Edit Employee Details", "📜 Performance History"
    ])

    # 1. View & Search Tab
    with tab_view:
        search_query = st.text_input("🔍 Search by Employee Name or Code:", placeholder="e.g. WP-1005 or Sharma")
        col_f1, col_f2 = st.columns(2)
        depts_list = ['All'] + sorted(raw_df['department'].unique().tolist()) if 'department' in raw_df.columns else ['All']
        filter_dept = col_f1.selectbox("Filter by Department:", depts_list)
        cats_list = ['All'] + sorted(raw_df['performance_category'].unique().tolist()) if 'performance_category' in raw_df.columns else ['All']
        filter_cat = col_f2.selectbox("Filter by Performance Category:", cats_list)

        view_df = raw_df.copy()
        if search_query.strip():
            sq = search_query.strip().lower()
            view_df = view_df[
                view_df['employee_code'].str.lower().str.contains(sq, na=False) |
                view_df['employee_name'].str.lower().str.contains(sq, na=False)
            ]
        if filter_dept != 'All':
            view_df = view_df[view_df['department'] == filter_dept]
        if filter_cat != 'All':
            view_df = view_df[view_df['performance_category'] == filter_cat]

        st.dataframe(view_df, use_container_width=True)

        # Delete Action with explicit confirmation
        st.markdown("#### 🗑️ Remove Employee Record")
        del_emp_id = st.selectbox("Select Employee to Remove:", raw_df['employee_code'].tolist()) if not raw_df.empty else None
        if del_emp_id:
            del_row = raw_df[raw_df['employee_code'] == del_emp_id].iloc[0]
            confirm_del = st.checkbox(f"Confirm permanent deletion of {del_row['employee_name']} ({del_emp_id})")
            if st.button("Delete Employee", type="secondary", disabled=not confirm_del):
                success, msg = remove_employee(del_row['employee_id'])
                if success:
                    st.success(msg)
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.error(msg)

    # 2. Add New Employee Tab
    with tab_add:
        st.markdown("#### ➕ Register New Employee Record")
        with st.form("add_employee_form"):
            ac1, ac2 = st.columns(2)
            new_code = ac1.text_input("Employee Code*", placeholder="e.g. WP-1601")
            new_name = ac2.text_input("Employee Full Name*", placeholder="e.g. Priya Nair")

            ac3, ac4 = st.columns(2)
            new_dept = ac3.selectbox("Department*", VALID_DEPARTMENTS)
            new_exp = ac4.number_input("Experience (Years)*", min_value=0.0, max_value=50.0, value=3.0, step=0.5)

            ac5, ac6 = st.columns(2)
            new_att = ac5.slider("Attendance Rate (%)*", 0.0, 100.0, 90.0, 0.5)
            new_tc = ac6.slider("Task Completion Rate (%)*", 0.0, 100.0, 85.0, 0.5)

            ac7, ac8 = st.columns(2)
            new_train = ac7.number_input("Training Hours Completed*", min_value=0.0, max_value=300.0, value=25.0, step=1.0)
            new_prev = ac8.slider("Previous Performance Rating (1-5)*", 1.0, 5.0, 3.5, 0.1)

            ac9, ac10 = st.columns(2)
            new_cat = ac9.selectbox("Current Performance Category*", ['Needs Support', 'Moderate', 'High'], index=1)
            new_date = ac10.date_input("Review Date*", value=datetime.today())

            submitted_add = st.form_submit_button("Add Employee Record", type="primary")
            if submitted_add:
                success, msg = create_new_employee(
                    employee_code=new_code,
                    employee_name=new_name,
                    department=new_dept,
                    experience_years=new_exp,
                    attendance_rate=new_att,
                    task_completion_rate=new_tc,
                    training_hours=new_train,
                    previous_performance=new_prev,
                    performance_category=new_cat,
                    review_date=new_date
                )
                if success:
                    st.success(msg)
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")

    # 3. Edit Employee Tab
    with tab_edit:
        st.markdown("#### ✏️ Modify Employee Record")
        if not raw_df.empty:
            edit_code = st.selectbox("Select Employee to Edit:", raw_df['employee_code'].tolist())
            edit_row = raw_df[raw_df['employee_code'] == edit_code].iloc[0]

            with st.form("edit_employee_form"):
                ec1, ec2 = st.columns(2)
                upd_name = ec1.text_input("Employee Name", value=str(edit_row['employee_name']))
                upd_dept = ec2.selectbox("Department", VALID_DEPARTMENTS, index=VALID_DEPARTMENTS.index(edit_row['department']) if edit_row['department'] in VALID_DEPARTMENTS else 0)

                ec3, ec4 = st.columns(2)
                upd_exp = ec3.number_input("Experience (Years)", min_value=0.0, max_value=50.0, value=float(edit_row['experience_years']), step=0.5)
                upd_train = ec4.number_input("Training Hours", min_value=0.0, max_value=300.0, value=float(edit_row['training_hours']), step=1.0)

                ec5, ec6 = st.columns(2)
                upd_att = ec5.slider("Attendance Rate (%)", 0.0, 100.0, float(edit_row['attendance_rate']), 0.5)
                upd_tc = ec6.slider("Task Completion (%)", 0.0, 100.0, float(edit_row['task_completion_rate']), 0.5)

                ec7, ec8 = st.columns(2)
                upd_prev = ec7.slider("Previous Rating (1-5)", 1.0, 5.0, float(edit_row['previous_performance']), 0.1)
                cat_idx = ['Needs Support', 'Moderate', 'High'].index(edit_row['performance_category']) if edit_row['performance_category'] in ['Needs Support', 'Moderate', 'High'] else 1
                upd_cat = ec8.selectbox("Performance Category", ['Needs Support', 'Moderate', 'High'], index=cat_idx)

                submitted_edit = st.form_submit_button("Update Employee Record", type="primary")
                if submitted_edit:
                    success, msg = modify_employee(
                        employee_id=edit_row['employee_id'],
                        employee_name=upd_name,
                        department=upd_dept,
                        experience_years=upd_exp,
                        attendance_rate=upd_att,
                        task_completion_rate=upd_tc,
                        training_hours=upd_train,
                        previous_performance=upd_prev,
                        performance_category=upd_cat,
                        review_date=datetime.today().strftime('%Y-%m-%d')
                    )
                    if success:
                        st.success(msg)
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")

    # 4. Performance History Tab
    with tab_hist:
        st.markdown("#### 📜 Employee Historical Review Records")
        if not raw_df.empty:
            hist_code = st.selectbox("Select Employee:", raw_df['employee_code'].tolist(), key="hist_sel")
            hist_row = raw_df[raw_df['employee_code'] == hist_code].iloc[0]
            hist_df = fetch_employee_history(hist_row['employee_id'])

            if not hist_df.empty:
                st.write(f"**Performance History for {hist_row['employee_name']} ({hist_code})**:")
                st.dataframe(hist_df, use_container_width=True)
            else:
                st.info("No historical review entries found for this employee.")


# =============================================================================
# PAGE 4: DATASET MANAGEMENT
# =============================================================================
elif page_selection == "📁 Dataset Management":
    st.subheader("📁 Dataset Management & CSV Import/Export")
    st.markdown("Upload CSV datasets, validate records against required schemas, and download templates.")

    tab_upload, tab_template, tab_export = st.tabs([
        "📤 Upload & Validate CSV", "📄 Sample CSV Template", "📥 Export Cleaned Dataset"
    ])

    with tab_upload:
        st.markdown("#### Upload Employee CSV File")
        uploaded_file = st.file_uploader("Select CSV File", type=["csv"])

        if uploaded_file is not None:
            try:
                raw_upload_df = pd.read_csv(uploaded_file)
                st.markdown("##### 1. Raw Preview (First 5 Rows)")
                st.dataframe(raw_upload_df.head(), use_container_width=True)

                # Run validation
                is_valid, clean_df, issues, stats = validate_csv_dataset(raw_upload_df)

                st.markdown("##### 2. Validation & Quality Checks")
                vc1, vc2, vc3, vc4 = st.columns(4)
                render_kpi(vc1, "Total Uploaded Rows", f"{stats['total_rows']}")
                render_kpi(vc2, "Missing Values", f"{stats['missing_values']}")
                render_kpi(vc3, "Duplicate Codes", f"{stats['duplicate_codes']}")
                render_kpi(vc4, "Valid Rows to Import", f"{stats['valid_rows']}")

                if issues:
                    st.warning("⚠️ Data Quality Notices:\n- " + "\n- ".join(issues))

                if is_valid:
                    st.success("✅ Dataset meets validation criteria and is ready to import.")
                    if st.button("🚀 Import Valid Records into Database", type="primary"):
                        from database.db_manager import import_records_from_df
                        ins, skp = import_records_from_df(clean_df, "data/workpulse.db")
                        st.success(f"Successfully imported {ins} new records ({skp} updated).")
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        st.rerun()
                else:
                    st.error("❌ Dataset could not be validated. Please check the error notices above.")

            except Exception as e:
                st.error(f"Failed to read file: {e}")

    with tab_template:
        st.markdown("#### Download CSV Template")
        st.write("Use this template to format employee records before importing into WorkPulse:")
        if os.path.exists("data/sample_template.csv"):
            template_df = pd.read_csv("data/sample_template.csv")
            st.dataframe(template_df, use_container_width=True)

            with open("data/sample_template.csv", "rb") as f:
                st.download_button(
                    label="📥 Download sample_template.csv",
                    data=f,
                    file_name="sample_template.csv",
                    mime="text/csv"
                )

    with tab_export:
        st.markdown("#### Export Current Database Records")
        st.write("Download all currently active employee review records from the database:")
        st.dataframe(raw_df, use_container_width=True)
        csv_bytes = raw_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Database as CSV",
            data=csv_bytes,
            file_name="workpulse_employees.csv",
            mime="text/csv"
        )


# =============================================================================
# PAGE 5: PERFORMANCE ANALYTICS
# =============================================================================
elif page_selection == "📈 Performance Analytics":
    st.subheader("📈 In-Depth Performance Analytics")
    st.markdown("Explore multi-variable correlations, training impacts, and departmental patterns.")

    # Department summary table
    dept_sum = get_department_summary(raw_df)
    st.markdown("#### Department-Wise Workforce Summary")
    st.dataframe(dept_sum, use_container_width=True)

    pa_c1, pa_c2 = st.columns(2)

    with pa_c1:
        st.markdown("#### Work Features Correlation Matrix")
        num_cols = [c for c in FEATURE_COLS_NUMERIC if c in raw_df.columns]
        corr_matrix = raw_df[num_cols].corr().round(2)
        fig_heat = px.imshow(
            corr_matrix, text_auto=True, color_continuous_scale='Blues',
            labels=dict(color="Correlation")
        )
        fig_heat.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_heat, use_container_width=True)

    with pa_c2:
        st.markdown("#### Training Hours vs Task Completion")
        fig_scatter_tr = px.scatter(
            raw_df, x='training_hours', y='task_completion_rate',
            color='performance_category',
            labels={'training_hours': 'Training Hours Completed', 'task_completion_rate': 'Task Completion Rate (%)'},
            color_discrete_map={'High': '#10B981', 'Moderate': '#F59E0B', 'Needs Support': '#EF4444'}
        )
        fig_scatter_tr.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_scatter_tr, use_container_width=True)

    # Monthly Trends
    st.markdown("#### Performance Review Trends Over Time")
    trends_df = get_time_series_trends(raw_df)
    if not trends_df.empty:
        fig_trend = px.line(
            trends_df, x='month_year', y=['Avg_Attendance', 'Avg_Task_Completion'],
            markers=True, labels={'month_year': 'Review Period (Month)', 'value': 'Percentage (%)'},
            title="Monthly Workforce Averages"
        )
        fig_trend.update_layout(template="plotly_white", margin=dict(t=30, b=20, l=20, r=20))
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Insufficient dated records to plot time-series trend analysis.")


# =============================================================================
# PAGE 6: PERFORMANCE PREDICTION
# =============================================================================
elif page_selection == "🔮 Performance Prediction":
    st.subheader("🔮 Machine Learning Performance Prediction")
    st.markdown("Estimate performance category using trained Decision Tree or Random Forest models with local factor explanations.")

    pred_mode = st.radio("Prediction Input Mode:", ["Select Registered Employee", "Custom Input Parameters"], horizontal=True)

    if pred_mode == "Select Registered Employee" and not raw_df.empty:
        p_emp_code = st.selectbox("Choose Employee Code:", raw_df['employee_code'].tolist())
        p_row = raw_df[raw_df['employee_code'] == p_emp_code].iloc[0]

        input_features = {
            'attendance_rate': float(p_row['attendance_rate']),
            'task_completion_rate': float(p_row['task_completion_rate']),
            'training_hours': float(p_row['training_hours']),
            'experience_years': float(p_row['experience_years']),
            'previous_performance': float(p_row['previous_performance']),
            'department': str(p_row['department'])
        }
        ref_emp_id = p_row['employee_id']
        actual_cat = p_row.get('performance_category', None)
    else:
        ref_emp_id = None
        actual_cat = None
        c1, c2, c3 = st.columns(3)
        with c1:
            in_att = st.slider("Attendance Rate (%)", 0.0, 100.0, 92.0, 0.5)
            in_tc = st.slider("Task Completion (%)", 0.0, 100.0, 86.0, 0.5)
        with c2:
            in_train = st.slider("Training Hours", 0.0, 120.0, 30.0, 1.0)
            in_exp = st.slider("Experience (Years)", 0.0, 25.0, 3.5, 0.5)
        with c3:
            in_prev = st.slider("Previous Performance Rating", 1.0, 5.0, 3.8, 0.1)
            in_dept = st.selectbox("Department", VALID_DEPARTMENTS)

        input_features = {
            'attendance_rate': in_att,
            'task_completion_rate': in_tc,
            'training_hours': in_train,
            'experience_years': in_exp,
            'previous_performance': in_prev,
            'department': in_dept
        }

    st.markdown("---")

    # Run Prediction
    pred_result = run_employee_prediction(
        pipeline=active_pipeline,
        input_dict=input_features,
        model_id=1 if selected_model_name == 'Random Forest' else 2,
        employee_id=ref_emp_id,
        population_df=raw_df
    )

    pred_cat = pred_result['predicted_category']
    probs = pred_result['probabilities']
    contribs = pred_result['contributions']

    res_col1, res_col2 = st.columns([1, 2])

    with res_col1:
        st.markdown("### Model Prediction")
        if pred_cat == 'High':
            st.markdown("<div class='badge-high'>🟢 High Performance</div>", unsafe_allow_html=True)
        elif pred_cat == 'Moderate':
            st.markdown("<div class='badge-moderate'>🟡 Moderate Performance</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='badge-support'>🔴 Needs Support</div>", unsafe_allow_html=True)

        if actual_cat:
            st.write(f"**Actual Record Category**: `{actual_cat}`")

        st.markdown("#### Confidence Probabilities")
        prob_df = pd.DataFrame(list(probs.items()), columns=['Category', 'Probability'])
        fig_prob = px.bar(
            prob_df, x='Probability', y='Category', orientation='h',
            color='Category', text_auto='.1%',
            color_discrete_map={'High': '#10B981', 'Moderate': '#F59E0B', 'Needs Support': '#EF4444'}
        )
        fig_prob.update_layout(template="plotly_white", height=200, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_prob, use_container_width=True)

    with res_col2:
        st.markdown("### Contributing Factors (Explainability)")
        fig_contrib = px.bar(
            contribs, x='Impact_Score', y='Feature', orientation='h',
            color='Direction',
            color_discrete_map={'Positive': '#10B981', 'Negative': '#EF4444'},
            hover_data=['Value', 'Benchmark'],
            labels={'Impact_Score': 'Relative Impact Score', 'Feature': 'Indicator'}
        )
        fig_contrib.update_layout(template="plotly_white", height=230, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_contrib, use_container_width=True)

        st.markdown(f"**Key Factor Summary**: {pred_result['summary']}")
        st.markdown(f"<div class='warning-box'>{pred_result['disclaimer']}</div>", unsafe_allow_html=True)


# =============================================================================
# PAGE 7: MODEL EVALUATION
# =============================================================================
elif page_selection == "🤖 Model Evaluation":
    st.subheader("🤖 Machine Learning Model Evaluation & Comparison")
    st.markdown("Evaluation metrics calculated on held-out test records (80/20 stratified split).")

    # Side-by-side comparison table
    comp_rows = []
    for m_name, m_dict in eval_results.items():
        comp_rows.append({
            "Algorithm": m_name,
            "Accuracy": f"{m_dict['accuracy']*100:.2f}%",
            "Precision (Weighted)": f"{m_dict['precision']:.4f}",
            "Recall (Weighted)": f"{m_dict['recall']:.4f}",
            "F1-Score (Weighted)": f"{m_dict['f1_score']:.4f}",
            "Train Samples": m_dict.get('train_samples', '-'),
            "Test Samples": m_dict.get('test_samples', '-')
        })
    st.table(pd.DataFrame(comp_rows))

    st.markdown("---")

    m_col1, m_col2 = st.columns(2)
    sel_metrics = eval_results[selected_model_name]

    with m_col1:
        st.markdown(f"#### Confusion Matrix ({selected_model_name})")
        cm_matrix = np.array(sel_metrics['confusion_matrix'])
        fig_cm = px.imshow(
            cm_matrix, x=TARGET_CLASSES, y=TARGET_CLASSES,
            text_auto=True, color_continuous_scale='Blues',
            labels=dict(x="Predicted Category", y="Actual Category", color="Count")
        )
        fig_cm.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_cm, use_container_width=True)

    with m_col2:
        st.markdown(f"#### Global Feature Importances ({selected_model_name})")
        df_feat = get_feature_importances(active_pipeline)
        fig_imp = px.bar(
            df_feat.head(6), x='Importance_Pct', y='Feature',
            orientation='h', color='Importance_Pct', color_continuous_scale='Viridis',
            labels={'Importance_Pct': 'Importance (%)', 'Feature': 'Work Feature'}
        )
        fig_imp.update_layout(template="plotly_white", yaxis=dict(autorange="reversed"), margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("#### Detailed Classification Report per Category")
    clf_rep_df = pd.DataFrame(sel_metrics['classification_report']).T
    clf_rep_df = clf_rep_df.loc[TARGET_CLASSES + ['macro avg', 'weighted avg']]
    st.dataframe(clf_rep_df, use_container_width=True)


# =============================================================================
# PAGE 8: REPORTS & EXPORT
# =============================================================================
elif page_selection == "📑 Reports & Export":
    st.subheader("📑 Formal Reports & College Submission Deliverables")
    st.markdown("Export performance summaries, download audit reports, and inspect prediction history.")

    tab_report, tab_pred_log = st.tabs(["📄 Executive Performance Report", "📜 SQLite Prediction Audit Log"])

    with tab_report:
        sel_eval = eval_results[selected_model_name]
        rep_content = generate_comprehensive_report(raw_df, selected_model_name, sel_eval)

        st.markdown(rep_content)

        st.download_button(
            label="📥 Download Official Report (.md)",
            data=rep_content,
            file_name=f"WorkPulse_Evaluation_Report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )

    with tab_pred_log:
        st.markdown("#### Prediction Audit Log (Persisted in SQLite)")
        pred_history = get_predictions_history("data/workpulse.db")
        if not pred_history.empty:
            st.dataframe(pred_history, use_container_width=True)
            csv_pred_bytes = pred_history.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Prediction Audit Log as CSV",
                data=csv_pred_bytes,
                file_name="workpulse_prediction_history.csv",
                mime="text/csv"
            )
        else:
            st.info("No predictions logged yet. Run a prediction on Page 6!")
