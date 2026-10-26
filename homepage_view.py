"""
WorkPulse — Premium SaaS Marketing & Product Homepage.
Crafted for WorkPulse: Employee Performance Review System.
Tagline: Understand Performance. Empower Growth.
"""

from html import escape
import json
from typing import Any
import pandas as pd
import streamlit as st

from ui_components import ICONS


def render_homepage(
    summary: dict[str, int],
    employees: pd.DataFrame,
    assessments: pd.DataFrame,
    periods: pd.DataFrame,
    areas: pd.DataFrame,
    settings: dict[str, Any] | None = None,
) -> None:
    """Render the WorkPulse product homepage."""
    settings = settings or {}
    workspace_name = settings.get("workspace_name", "WorkPulse")

    total_emp = summary.get("total_employees", len(employees))
    active_periods = summary.get("active_periods", 0)
    completed_assessments = summary.get("completed_assessments", len(assessments))
    active_areas = summary.get("performance_areas", len(areas))
    demo_emp = summary.get("demo_employees", 0)

    scored_assessments = assessments.dropna(subset=["overall_score"]).copy()
    assessment_count = len(scored_assessments)
    average_score = (
        float(scored_assessments["overall_score"].mean())
        if assessment_count
        else None
    )
    high_count = int((scored_assessments["overall_score"] >= 80).sum())
    moderate_count = int(
        (
            (scored_assessments["overall_score"] >= 60)
            & (scored_assessments["overall_score"] < 80)
        ).sum()
    )
    support_count = int((scored_assessments["overall_score"] < 60).sum())
    active_period_rows = periods[periods["status"] == "Active"]
    active_period_name = (
        str(active_period_rows.iloc[0]["name"])
        if not active_period_rows.empty
        else "No active review cycle"
    )
    active_employee_count = (
        int((employees["status"] == "Active").sum())
        if "status" in employees.columns
        else len(employees)
    )
    active_period_assessments = (
        int(active_period_rows.iloc[0].get("assessment_count", 0))
        if not active_period_rows.empty
        else 0
    )
    review_completion = (
        min(100, round(active_period_assessments / active_employee_count * 100))
        if active_employee_count
        else 0
    )
    workspace_data_label = (
        "DEMO WORKSPACE DATA"
        if total_emp and demo_emp == total_emp
        else "LIVE WORKSPACE DATA"
        if not demo_emp
        else "LIVE + DEMO WORKSPACE DATA"
    )

    latest_assessment = (
        scored_assessments.iloc[0] if assessment_count else None
    )
    latest_employee = None
    latest_scores: dict[str, Any] = {}
    latest_category = "No review yet"
    if latest_assessment is not None:
        matching_employees = employees[
            employees["employee_id"] == latest_assessment["employee_id"]
        ]
        if not matching_employees.empty:
            latest_employee = matching_employees.iloc[0]
        latest_scores = json.loads(str(latest_assessment["scores_json"]))
        latest_score = float(latest_assessment["overall_score"])
        latest_category = (
            "High" if latest_score >= 80
            else "Moderate" if latest_score >= 60
            else "Needs Support"
        )
    else:
        latest_score = None

    employee_name = (
        str(latest_assessment["employee_name"])
        if latest_assessment is not None
        else "No assessment recorded"
    )
    employee_code = (
        str(latest_assessment["employee_code"])
        if latest_assessment is not None
        else "Add a review to see employee details"
    )
    employee_department = (
        str(latest_assessment["department"])
        if latest_assessment is not None
        else "—"
    )
    employee_designation = (
        str(latest_employee.get("designation", ""))
        if latest_employee is not None
        else ""
    )
    employee_experience = (
        f'{float(latest_employee["experience_years"]):g} yrs'
        if latest_employee is not None
        and pd.notna(latest_employee.get("experience_years"))
        else ""
    )
    employee_details = " · ".join(
        part for part in (
            employee_code,
            employee_designation,
            employee_department,
            employee_experience,
        ) if part
    )
    employee_initials = "".join(
        part[0].upper()
        for part in employee_name.split()
        if part
    )[:2] or "WP"
    average_score_label = (
        f"{average_score:.1f} / 100" if average_score is not None else "—"
    )
    latest_score_label = (
        f"{latest_score:.1f}" if latest_score is not None else "—"
    )
    review_completion_label = (
        f"{review_completion}%"
        if not active_period_rows.empty
        else "—"
    )
    assessment_date_label = (
        str(latest_assessment["assessment_date"])
        if latest_assessment is not None
        else "No review activity yet"
    )
    distribution_total = max(assessment_count, 1)
    high_percent = round(high_count / distribution_total * 100)
    moderate_percent = round(moderate_count / distribution_total * 100)
    support_percent = round(support_count / distribution_total * 100)
    donut_style = (
        f"conic-gradient(#0D9488 0% {high_percent}%, "
        f"#D97706 {high_percent}% {high_percent + moderate_percent}%, "
        f"#E11D48 {high_percent + moderate_percent}% 100%)"
        if assessment_count
        else "conic-gradient(#E2E8F0 0% 100%)"
    )

    area_preview_rows = []
    active_area_rows = areas[areas["active"] == 1].head(4)
    for _, area in active_area_rows.iterrows():
        score_value = latest_scores.get(str(area["name"]))
        score_label = (
            f"{float(score_value):.1f}%"
            if score_value is not None
            else "Not recorded"
        )
        fill_width = (
            max(0, min(100, float(score_value)))
            if score_value is not None
            else 0
        )
        area_preview_rows.append(
            f"""
            <div class="wp-hp-preview-bar-item">
                <div class="wp-hp-pbar-head">
                    <span>{escape(str(area["name"]))} ({float(area["weight"]):g}%)</span>
                    <strong>{score_label}</strong>
                </div>
                <div class="wp-hp-pbar-track"><div class="wp-hp-pbar-fill" style="width:{fill_width:.1f}%;"></div></div>
            </div>
            """
        )
    area_preview_html = "".join(area_preview_rows) or (
        '<p class="wp-hp-empty-note">Configure performance indicators to see the review breakdown.</p>'
    )

    department_summary = (
        scored_assessments.groupby("department", as_index=False)
        .agg(mean_score=("overall_score", "mean"), review_count=("assessment_id", "count"))
        .sort_values("mean_score", ascending=False)
        .head(6)
    )
    department_rows = []
    for _, department in department_summary.iterrows():
        score = float(department["mean_score"])
        bar_color = "#168C83" if score >= 80 else "#D97706" if score >= 60 else "#E11D48"
        department_rows.append(
            f"""
            <div class="wp-hp-dept-bar-row">
                <span class="wp-hp-dept-name">{escape(str(department["department"]))}</span>
                <div class="wp-hp-dept-track"><div class="wp-hp-dept-fill" style="width:{max(0, min(100, score)):.1f}%; background:{bar_color};"></div></div>
                <span class="wp-hp-dept-score">{score:.1f}</span>
            </div>
            """
        )
    department_rows_html = "".join(department_rows) or (
        '<p class="wp-hp-empty-note">Department comparisons appear after assessments are recorded.</p>'
    )

    recent_rows = []
    for _, assessment in scored_assessments.head(4).iterrows():
        score = float(assessment["overall_score"])
        category = (
            "High" if score >= 80
            else "Moderate" if score >= 60
            else "Needs Support"
        )
        chip_class = (
            "wp-hp-chip-high" if category == "High"
            else "wp-hp-chip-mod" if category == "Moderate"
            else "wp-hp-chip-need"
        )
        recent_rows.append(
            f"""
            <div class="wp-hp-table-row">
                <span><strong>{escape(str(assessment["employee_name"]))}</strong> &nbsp;<small style="color:#64748B;">{escape(str(assessment["employee_code"]))}</small></span>
                <span>{escape(str(assessment["department"]))}</span>
                <span>{escape(str(assessment["period_name"]))}</span>
                <span>{escape(str(assessment["reviewer"]))}</span>
                <span><strong>{score:.1f} / 100</strong></span>
                <span><span class="wp-hp-chip {chip_class}">{category}</span></span>
            </div>
            """
        )
    recent_rows_html = "".join(recent_rows) or (
        '<div class="wp-hp-empty-note">No assessments have been recorded yet.</div>'
    )

    period_scores = (
        scored_assessments.groupby("period_id", as_index=False)
        .agg(mean_score=("overall_score", "mean"))
        .merge(
            periods[["period_id", "name", "start_date"]],
            on="period_id",
            how="left",
        )
        .dropna(subset=["name"])
        .sort_values("start_date")
        .tail(5)
    )
    period_columns = []
    for _, period in period_scores.iterrows():
        score = float(period["mean_score"])
        period_columns.append(
            f'<div class="wp-hp-mcol-wrap"><div class="wp-hp-mcol" style="height:{max(0, min(100, score)):.1f}%;"></div><span>{escape(str(period["name"]))}</span></div>'
        )
    period_columns_html = "".join(period_columns) or (
        '<p class="wp-hp-empty-note">Cycle comparisons appear after reviews are recorded.</p>'
    )

    directory_rows = []
    for _, employee in employees.head(3).iterrows():
        initials = "".join(
            part[0].upper()
            for part in str(employee["employee_name"]).split()
            if part
        )[:2] or "WP"
        is_active = str(employee.get("status", "Active")) == "Active"
        status = str(employee.get("status", "Active"))
        status_class = "wp-hp-chip-high" if is_active else "wp-hp-chip-mod"
        designation = str(employee.get("designation", "")).strip()
        employee_summary = " · ".join(
            part for part in (
                designation,
                str(employee["department"]),
            ) if part
        )
        directory_rows.append(
            f"""
            <div class="wp-hp-micro-emp-row">
                <div class="wp-hp-micro-avatar">{escape(initials)}</div>
                <div><strong>{escape(str(employee["employee_name"]))}</strong><br><small>{escape(employee_summary)}</small></div>
                <span class="wp-hp-chip {status_class}">{escape(status)}</span>
            </div>
            """
        )
    directory_rows_html = "".join(directory_rows) or (
        '<p class="wp-hp-empty-note">Add an employee to begin building your directory.</p>'
    )

    area_feature_rows = []
    for _, area in areas[areas["active"] == 1].head(4).iterrows():
        weight = max(0, min(100, float(area["weight"])))
        area_feature_rows.append(
            f"""
            <div class="wp-hp-slider-preview">
                <div class="wp-hp-sl-head"><span>{escape(str(area["name"]))}</span><strong>{weight:g}% wt</strong></div>
                <div class="wp-hp-sl-track"><div class="wp-hp-sl-bar" style="width:{weight:g}%;"></div></div>
            </div>
            """
        )
    area_feature_rows_html = "".join(area_feature_rows) or (
        '<p class="wp-hp-empty-note">No active indicators are configured.</p>'
    )

    # -------------------------------------------------------------------------
    # 1. Scoped CSS Overrides for Immersive Homepage Experience
    # -------------------------------------------------------------------------
    st.html("""
        <style>
        /* Hide default Streamlit sidebar and maximize viewport on Homepage */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        header[data-testid="stHeader"] {
            display: none !important;
        }
        footer {
            display: none !important;
        }
        html {
            scroll-behavior: smooth;
        }
        </style>
        """
    )

    # -------------------------------------------------------------------------
    # 2. Navigation Bar
    # -------------------------------------------------------------------------
    nav_html = f"""
    <nav class="wp-hp-navbar" id="top">
        <div class="wp-hp-nav-inner">
            <a href="?page=Home" target="_self" class="wp-hp-brand">
                <div class="wp-hp-brand-mark">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                </div>
                <div class="wp-hp-brand-text">
                    <span class="wp-hp-brand-title">WorkPulse</span>
                    <span class="wp-hp-brand-pill">PEOPLE ANALYTICS</span>
                </div>
            </a>

            <!-- Desktop Nav Links -->
            <div class="wp-hp-nav-links">
                <a href="#product" class="wp-hp-nav-link">Product</a>
                <a href="#features" class="wp-hp-nav-link">Features</a>
                <a href="#how-it-works" class="wp-hp-nav-link">How It Works</a>
                <a href="#analytics-showcase" class="wp-hp-nav-link">Analytics</a>
                <a href="#about" class="wp-hp-nav-link">About</a>
            </div>

            <!-- Right Actions -->
            <div class="wp-hp-nav-actions">
                <a href="?page=Settings" target="_self" class="wp-hp-nav-signin">Workspace settings</a>
                <a href="?page=Dashboard" target="_self" class="wp-hp-btn wp-hp-btn-nav">
                    <span>Open Dashboard</span>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                    </svg>
                </a>
            </div>

            <!-- Mobile Hamburger Toggle (Pure CSS, robust on any browser) -->
            <input type="checkbox" id="wp-mobile-menu-toggle" class="wp-hp-mobile-checkbox" aria-label="Toggle navigation menu">
            <label for="wp-mobile-menu-toggle" class="wp-hp-mobile-toggle-btn" aria-label="Toggle menu">
                <span></span>
                <span></span>
                <span></span>
            </label>

            <!-- Mobile Drawer -->
            <div class="wp-hp-mobile-drawer">
                <a href="#product" class="wp-hp-mobile-link">Product</a>
                <a href="#features" class="wp-hp-mobile-link">Features</a>
                <a href="#how-it-works" class="wp-hp-mobile-link">How It Works</a>
                <a href="#analytics-showcase" class="wp-hp-mobile-link">Analytics</a>
                <a href="#about" class="wp-hp-mobile-link">About</a>
                <div class="wp-hp-mobile-divider"></div>
                <a href="?page=Settings" target="_self" class="wp-hp-mobile-link">Workspace settings</a>
                <a href="?page=Dashboard" target="_self" class="wp-hp-btn wp-hp-btn-primary" style="margin-top:0.75rem; text-align:center;">Open Dashboard</a>
            </div>
        </div>
    </nav>
    """
    st.html(nav_html)

    # -------------------------------------------------------------------------
    # 3. Hero Section
    # -------------------------------------------------------------------------
    hero_html = f"""
    <section class="wp-hp-hero-section">
        <div class="wp-hp-hero-container">
            <!-- Left Hero Content -->
            <div class="wp-hp-hero-content">
                <div class="wp-hp-eyebrow">
                    <span class="wp-hp-eyebrow-dot"></span>
                    <span>EMPLOYEE PERFORMANCE MANAGEMENT</span>
                    <span class="wp-hp-eyebrow-badge">{workspace_data_label}</span>
                </div>

                <h1 class="wp-hp-hero-title">
                    Turn Performance Data Into <span class="wp-hp-text-accent">Meaningful Progress.</span>
                </h1>

                <p class="wp-hp-hero-lead">
                    Bring employee reviews, performance analytics, and actionable insights together in one clear workspace.
                </p>

                <div class="wp-hp-hero-ctas">
                    <a href="?page=Dashboard" target="_self" class="wp-hp-btn wp-hp-btn-primary">
                        <span>Explore WorkPulse</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                            <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                    </a>
                    <a href="#how-it-works" class="wp-hp-btn wp-hp-btn-secondary">
                        <span>See How It Works</span>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </a>
                </div>

                <!-- Grounded Trust Pillars -->
                <div class="wp-hp-trust-row">
                    <div class="wp-hp-trust-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Workspace-backed metrics</span>
                    </div>
                    <div class="wp-hp-trust-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Weighted KPI Framework</span>
                    </div>
                    <div class="wp-hp-trust-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Predictions kept distinct</span>
                    </div>
                </div>
            </div>

            <!-- Right Hero Product Preview (Real Interface Components) -->
            <div class="wp-hp-hero-preview-col">
                <div class="wp-hp-window-card">
                    <!-- Window Top Chrome -->
                    <div class="wp-hp-window-chrome">
                        <div class="wp-hp-window-dots">
                            <span></span><span></span><span></span>
                        </div>
                        <div class="wp-hp-window-title">WorkPulse Workspace · {escape(active_period_name)}</div>
                        <div class="wp-hp-window-tag">{workspace_data_label}</div>
                    </div>

                    <!-- Inner Product Interface -->
                    <div class="wp-hp-window-body">
                        <!-- Top Mini Stat Bar -->
                        <div class="wp-hp-preview-metrics-bar">
                            <div class="wp-hp-preview-metric">
                                <span class="wp-hp-metric-micro-label">DIRECTORY</span>
                                <span class="wp-hp-metric-micro-val">{total_emp:,} Profiles</span>
                            </div>
                            <div class="wp-hp-preview-metric">
                                <span class="wp-hp-metric-micro-label">CYCLE COMPLETION</span>
                                <span class="wp-hp-metric-micro-val">{review_completion_label}</span>
                            </div>
                            <div class="wp-hp-preview-metric">
                                <span class="wp-hp-metric-micro-label">MEAN REVIEW SCORE</span>
                                <span class="wp-hp-metric-micro-val" style="color:#0D9488;">{average_score_label}</span>
                            </div>
                        </div>

                        <!-- Real Employee Assessment Dossier Preview -->
                        <div class="wp-hp-preview-dossier">
                            <div class="wp-hp-dossier-header">
                                <div class="wp-hp-dossier-avatar">{escape(employee_initials)}</div>
                                <div class="wp-hp-dossier-info">
                                    <div class="wp-hp-dossier-name-row">
                                        <strong>{escape(employee_name)}</strong>
                                        <span class="wp-hp-chip {('wp-hp-chip-high' if latest_category == 'High' else 'wp-hp-chip-mod' if latest_category == 'Moderate' else 'wp-hp-chip-need' if latest_category == 'Needs Support' else '')}">{escape(latest_category)}</span>
                                    </div>
                                    <span class="wp-hp-dossier-sub">{escape(employee_details)}</span>
                                </div>
                                <div class="wp-hp-dossier-score-box">
                                    <span class="wp-hp-score-num">{latest_score_label}</span>
                                    <span class="wp-hp-score-lbl">OVERALL</span>
                                </div>
                            </div>

                            <div class="wp-hp-preview-bars">{area_preview_html}</div>

                            <!-- Reviewer Sign-off note -->
                            <div class="wp-hp-preview-signoff">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                                <span>{f'Reviewed by <strong>{escape(str(latest_assessment["reviewer"]))}</strong>' if latest_assessment is not None else 'No reviewer activity recorded yet'} &nbsp;·&nbsp; {escape(assessment_date_label)}</span>
                            </div>
                        </div>

                        <!-- Mini Trend Footer -->
                        <div class="wp-hp-preview-trend-strip">
                            <span class="wp-hp-trend-title">Latest assessment:</span>
                            <div class="wp-hp-spark-nodes">
                                <span class="wp-hp-spark-tag wp-hp-spark-active">{latest_score_label} / 100</span>
                            </div>
                            <span class="wp-hp-trend-badge">{escape(assessment_date_label)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(hero_html)

    # -------------------------------------------------------------------------
    # 4. Large Product Dashboard Preview Section
    # -------------------------------------------------------------------------
    preview_section_html = f"""
    <section class="wp-hp-section wp-hp-preview-section" id="product">
        <div class="wp-hp-container">
            <div class="wp-hp-section-header">
                <span class="wp-hp-section-eyebrow">COMMAND CENTER</span>
                <h2 class="wp-hp-section-title">One workspace for every review decision.</h2>
                <p class="wp-hp-section-sub">
                    A closer look at the workspace: employee records, review completion, weighted indicators, and recorded assessments.
                </p>
            </div>

            <!-- Full-width Browser Dashboard Frame -->
            <div class="wp-hp-large-browser-frame">
                <div class="wp-hp-browser-topbar">
                    <div class="wp-hp-browser-controls">
                        <span></span><span></span><span></span>
                    </div>
                    <div class="wp-hp-browser-url-pill">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                        <span>WorkPulse / Workspace / Reviews</span>
                    </div>
                    <div class="wp-hp-browser-badges">
                        <span class="wp-hp-live-indicator">● {workspace_data_label}</span>
                    </div>
                </div>

                <!-- Embedded Dashboard View -->
                <div class="wp-hp-browser-canvas">
                    <!-- Dashboard Toolbar Filter Strip -->
                    <div class="wp-hp-dash-toolbar">
                        <div class="wp-hp-dash-filters">
                            <div class="wp-hp-filter-pill">
                                <span class="wp-hp-filter-label">CYCLE:</span>
                                <strong>{escape(active_period_name)}</strong>
                            </div>
                            <div class="wp-hp-filter-pill">
                                <span class="wp-hp-filter-label">DEPARTMENT:</span>
                                <strong>{department_summary["department"].nunique() if not department_summary.empty else 0} Reviewed Departments</strong>
                            </div>
                            <div class="wp-hp-filter-pill">
                                <span class="wp-hp-filter-label">STATUS:</span>
                                <strong>Employee profiles ({total_emp:,})</strong>
                            </div>
                        </div>
                        <div class="wp-hp-dash-quickaction">
                            <span class="wp-hp-search-box">🔍 Search by employee code or name...</span>
                        </div>
                    </div>

                    <!-- 4 Metric Cards Row -->
                    <div class="wp-hp-dash-metrics-grid">
                        <div class="wp-hp-dash-mcard">
                            <div class="wp-hp-mcard-top">
                                <span>TOTAL EMPLOYEES</span>
                                <div class="wp-hp-mcard-icon">{ICONS['employees']}</div>
                            </div>
                            <div class="wp-hp-mcard-val">{total_emp:,}</div>
                            <div class="wp-hp-mcard-sub">Stored in this workspace</div>
                        </div>

                        <div class="wp-hp-dash-mcard">
                            <div class="wp-hp-mcard-top">
                                <span>ACTIVE PERIODS</span>
                                <div class="wp-hp-mcard-icon">{ICONS['calendar']}</div>
                            </div>
                            <div class="wp-hp-mcard-val">{active_periods:,}</div>
                            <div class="wp-hp-mcard-sub">{escape(active_period_name)}</div>
                        </div>

                        <div class="wp-hp-dash-mcard">
                            <div class="wp-hp-mcard-top">
                                <span>COMPLETED ASSESSMENTS</span>
                                <div class="wp-hp-mcard-icon">{ICONS['assessments']}</div>
                            </div>
                            <div class="wp-hp-mcard-val">{completed_assessments:,}</div>
                            <div class="wp-hp-mcard-sub">Recorded human assessments</div>
                        </div>

                        <div class="wp-hp-dash-mcard">
                            <div class="wp-hp-mcard-top">
                                <span>WEIGHTED KPI AREAS</span>
                                <div class="wp-hp-mcard-icon">{ICONS['sliders']}</div>
                            </div>
                            <div class="wp-hp-mcard-val">{active_areas:,}</div>
                            <div class="wp-hp-mcard-sub">Active weights total exactly 100%</div>
                        </div>
                    </div>

                    <!-- Main Charts Row -->
                    <div class="wp-hp-dash-charts-split">
                        <!-- Department Comparison (Orientation horizontal bar) -->
                        <div class="wp-hp-dash-panel" style="flex: 1.4;">
                            <div class="wp-hp-panel-header">
                                <div>
                                    <h4 class="wp-hp-panel-title">Department Performance Comparison</h4>
                                    <span class="wp-hp-panel-caption">Mean recorded assessment score (100-point scale)</span>
                                </div>
                                <span class="wp-hp-legend-pill">High-score threshold: 80</span>
                            </div>
                            <div class="wp-hp-dept-bars-list">{department_rows_html}</div>
                        </div>

                        <!-- Performance Category Distribution (Donut style) -->
                        <div class="wp-hp-dash-panel" style="flex: 1;">
                            <div class="wp-hp-panel-header">
                                <div>
                                    <h4 class="wp-hp-panel-title">Performance Distribution</h4>
                                    <span class="wp-hp-panel-caption">Recorded assessments by score bracket</span>
                                </div>
                            </div>
                            <div class="wp-hp-dist-donut-wrap">
                                <div class="wp-hp-dist-graphic">
                                    <div class="wp-hp-dist-circle" style="background:{donut_style};">
                                        <div class="wp-hp-dist-center">
                                            <strong>{average_score_label.split(" / ")[0]}</strong>
                                            <span>MEAN REVIEW SCORE</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="wp-hp-dist-legend-rows">
                                    <div class="wp-hp-dist-legend-row">
                                        <span class="wp-hp-legend-dot" style="background:#0D9488;"></span>
                                        <span class="wp-hp-legend-text">High (≥ 80.0)</span>
                                        <strong>{high_percent}% ({high_count})</strong>
                                    </div>
                                    <div class="wp-hp-dist-legend-row">
                                        <span class="wp-hp-legend-dot" style="background:#D97706;"></span>
                                        <span class="wp-hp-legend-text">Moderate (60.0 - 79.9)</span>
                                        <strong>{moderate_percent}% ({moderate_count})</strong>
                                    </div>
                                    <div class="wp-hp-dist-legend-row">
                                        <span class="wp-hp-legend-dot" style="background:#E11D48;"></span>
                                        <span class="wp-hp-legend-text">Needs Support (&lt; 60.0)</span>
                                        <strong>{support_percent}% ({support_count})</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Assessments Table Preview -->
                    <div class="wp-hp-dash-panel" style="margin-top: 1rem;">
                        <div class="wp-hp-panel-header">
                            <div>
                                <h4 class="wp-hp-panel-title">Recent Workforce Assessments</h4>
                                <span class="wp-hp-panel-caption">Recent assessments recorded in this workspace</span>
                            </div>
                            <a href="?page=Assessments" target="_self" class="wp-hp-text-link">View Assessment Log →</a>
                        </div>
                        <div class="wp-hp-mini-table">
                            <div class="wp-hp-table-row wp-hp-table-head">
                                <span>EMPLOYEE</span>
                                <span>DEPARTMENT</span>
                                <span>REVIEW CYCLE</span>
                                <span>REVIEWER</span>
                                <span>COMPOSITE</span>
                                <span>STATUS</span>
                            </div>
                            {recent_rows_html}
                        </div>
                    </div>
                </div>

                <!-- Footer Transparency Strip -->
                <div class="wp-hp-browser-footer">
                    <div class="wp-hp-transparency-note">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                        <span>{escape(workspace_data_label.title())}. Figures above use stored workspace records; predictions remain separate from human assessments.</span>
                    </div>
                    <a href="?page=Dashboard" target="_self" class="wp-hp-btn wp-hp-btn-sm">Open Workspace</a>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(preview_section_html)

    # -------------------------------------------------------------------------
    # 5. Features Bento Section (Varied Layout — NOT Identical Cards)
    # -------------------------------------------------------------------------
    features_html = f"""
    <section class="wp-hp-section wp-hp-features-section" id="features">
        <div class="wp-hp-container">
            <div class="wp-hp-section-header">
                <span class="wp-hp-section-eyebrow">CORE CAPABILITIES</span>
                <h2 class="wp-hp-section-title">Built for consistency, context, and better conversations.</h2>
                <p class="wp-hp-section-sub">
                    Six connected capabilities, with workspace examples drawn from the records above and predictions kept distinct from reviews.
                </p>
            </div>

            <!-- Bento Grid with varied card geometry and embedded micro-UIs -->
            <div class="wp-hp-bento-grid">
                <!-- Feature 1: Wide Card (Employee Management) -->
                <div class="wp-hp-bento-card wp-hp-bento-wide">
                    <div class="wp-hp-bento-content">
                        <div class="wp-hp-feature-pill">01 · ROSTER MANAGEMENT</div>
                        <h3 class="wp-hp-bento-title">Employee Management</h3>
                        <p class="wp-hp-bento-desc">
                            Keep employee records together with department, designation, and tenure. Employee profiles remain distinct from assessment outcomes.
                        </p>
                        <ul class="wp-hp-bento-checklist">
                            <li>Instant search by employee code, name, and department</li>
                            <li>Independent profile lifecycle with safe deletion protections</li>
                            <li>Integrated historical attendance and task completion logging</li>
                        </ul>
                    </div>
                    <div class="wp-hp-bento-preview-wrap">
                        <div class="wp-hp-bento-micro-ui">
                            <div class="wp-hp-micro-header">
                                <span>DIRECTORY ({total_emp:,} PROFILES)</span>
                                <span class="wp-hp-chip wp-hp-chip-high">{employees["department"].nunique() if "department" in employees.columns else 0} Departments</span>
                            </div>
                            {directory_rows_html}
                        </div>
                    </div>
                </div>

                <!-- Feature 2: Performance Reviews -->
                <div class="wp-hp-bento-card">
                    <div class="wp-hp-feature-pill">02 · WEIGHTED RUBRIC</div>
                    <h3 class="wp-hp-bento-title">Performance Reviews</h3>
                    <p class="wp-hp-bento-desc">
                        Conduct reviews with weighted multi-indicator rubrics where active weights must total exactly 100%. Reviewer notes and date stamps are locked into audit history.
                    </p>
                    <div class="wp-hp-bento-formula-box">
                        <span class="wp-hp-formula-label">COMPOSITE CALCULATION</span>
                        <code>Score = Σ (Indicator Score × Weight %)</code>
                    </div>
                    <div class="wp-hp-bento-micro-sliders">{area_feature_rows_html}</div>
                </div>

                <!-- Feature 3: Interactive Analytics -->
                <div class="wp-hp-bento-card">
                    <div class="wp-hp-feature-pill">03 · WORKFORCE INTELLIGENCE</div>
                    <h3 class="wp-hp-bento-title">Interactive Analytics</h3>
                    <p class="wp-hp-bento-desc">
                        Filter historical review performance by review period and department. Explore score distributions, department benchmarking, and multi-cycle monthly trends.
                    </p>
                    <div class="wp-hp-bento-chart-card">
                        <div class="wp-hp-chart-card-head">
                            <span>RECORDED CYCLE AVERAGES</span>
                        </div>
                        <div class="wp-hp-micro-columns">{period_columns_html}</div>
                    </div>
                </div>

                <!-- Feature 4: Machine Learning Predictions -->
                <div class="wp-hp-bento-card">
                    <div class="wp-hp-feature-pill" style="color:#7C3AED; background:#F5F3FF;">04 · EXPERIMENTAL AI</div>
                    <h3 class="wp-hp-bento-title">Machine Learning Predictions</h3>
                    <p class="wp-hp-bento-desc">
                        Compare Decision Tree and Random Forest models on held-out data. Predictions are decision-support estimates and never replace or alter human reviews.
                    </p>
                    <div class="wp-hp-ml-box">
                        <div class="wp-hp-ml-status">
                            <span class="wp-hp-ml-badge">MODEL EVALUATION</span>
                            <span class="wp-hp-ml-accuracy">Results use available labelled data</span>
                        </div>
                        <div class="wp-hp-ml-legend">
                            <span>Decision Tree</span>
                            <span>Random Forest</span>
                            <span>Held-out evaluation</span>
                        </div>
                    </div>
                </div>

                <!-- Feature 5: Explainable Insights & What-If Simulation -->
                <div class="wp-hp-bento-card">
                    <div class="wp-hp-feature-pill">05 · TRANSPARENT REASONING</div>
                    <h3 class="wp-hp-bento-title">Explainable Insights</h3>
                    <p class="wp-hp-bento-desc">
                        Eliminate black-box guesswork. Feature importance displays the exact drivers behind score tiers, accompanied by What-If sensitivity simulations for growth planning.
                    </p>
                    <div class="wp-hp-explain-list">
                        <span class="wp-hp-ml-badge">EXAMPLE FACTORS · OUTPUT VARIES BY MODEL</span>
                        <div class="wp-hp-explain-item">
                            <span>Task Completion Rate</span>
                            <div class="wp-hp-ex-bar-wrap"><div class="wp-hp-ex-bar" style="width:82%;"></div></div>
                            <strong>Factor</strong>
                        </div>
                        <div class="wp-hp-explain-item">
                            <span>Attendance & Reliability</span>
                            <div class="wp-hp-ex-bar-wrap"><div class="wp-hp-ex-bar" style="width:64%;"></div></div>
                            <strong>Factor</strong>
                        </div>
                        <div class="wp-hp-explain-item">
                            <span>Prior Review History</span>
                            <div class="wp-hp-ex-bar-wrap"><div class="wp-hp-ex-bar" style="width:45%;"></div></div>
                            <strong>Factor</strong>
                        </div>
                    </div>
                </div>

                <!-- Feature 6: Wide Card (Reports & Export) -->
                <div class="wp-hp-bento-card wp-hp-bento-wide">
                    <div class="wp-hp-bento-content">
                        <div class="wp-hp-feature-pill">06 · AUDIT & EXPORT</div>
                        <h3 class="wp-hp-bento-title">Reports and Export</h3>
                        <p class="wp-hp-bento-desc">
                            Filter assessment records by department, employee, and review cycle, then export the results as CSV for further review.
                        </p>
                        <div class="wp-hp-export-action-bar">
                            <span class="wp-hp-export-pill">Recorded Assessments: {completed_assessments:,}</span>
                            <span class="wp-hp-export-pill">UTF-8 Encoded CSV</span>
                            <span class="wp-hp-export-pill">Zero Cloud Telemetry</span>
                        </div>
                    </div>
                    <div class="wp-hp-bento-preview-wrap">
                        <div class="wp-hp-export-doc-card">
                            <div class="wp-hp-doc-header">
                                <div class="wp-hp-doc-icon">{ICONS['reports']}</div>
                                <div>
                                    <strong>WorkPulse_Assessment_Export.csv</strong>
                                    <small>Workspace export · {completed_assessments:,} recorded rows</small>
                                </div>
                            </div>
                            <div class="wp-hp-doc-meta">
                                <span>Includes: Employee Code, Reviewer, Indicators, Scores, Categories</span>
                            </div>
                            <a href="?page=Reports" target="_self" class="wp-hp-btn wp-hp-btn-sm" style="margin-top:0.75rem; display:inline-flex;">Open Export Module</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(features_html)

    # -------------------------------------------------------------------------
    # 6. How It Works Section (01 - 05 Workflow Sequence)
    # -------------------------------------------------------------------------
    how_it_works_html = """
    <section class="wp-hp-section wp-hp-workflow-section" id="how-it-works">
        <div class="wp-hp-container">
            <div class="wp-hp-section-header">
                <span class="wp-hp-section-eyebrow">STRUCTURED PROCESS</span>
                <h2 class="wp-hp-section-title">A Clear, Five-Step Review Lifecycle</h2>
                <p class="wp-hp-section-sub">
                    WorkPulse guides people leaders through an orderly, transparent sequence from workforce baseline to executive reporting.
                </p>
            </div>

            <!-- Workflow Cards with Connecting Sequence Treatment -->
            <div class="wp-hp-workflow-track">
                <!-- Step 01 -->
                <div class="wp-hp-step-card">
                    <div class="wp-hp-step-top">
                        <span class="wp-hp-step-num">01</span>
                        <div class="wp-hp-step-line"></div>
                    </div>
                    <h3 class="wp-hp-step-title">Manage employee records</h3>
                    <p class="wp-hp-step-desc">
                        Register employees with accurate department assignments, designations, and tenure. Profiles remain unpolluted by fabricated assessments until formal reviews commence.
                    </p>
                    <div class="wp-hp-step-tag">Directory Roster</div>
                </div>

                <!-- Step 02 -->
                <div class="wp-hp-step-card">
                    <div class="wp-hp-step-top">
                        <span class="wp-hp-step-num">02</span>
                        <div class="wp-hp-step-line"></div>
                    </div>
                    <h3 class="wp-hp-step-title">Conduct performance reviews</h3>
                    <p class="wp-hp-step-desc">
                        Managers assess staff against active weighted criteria totaling 100%. Transparent formulas calculate overall scores while timestamped comments capture qualitative nuance.
                    </p>
                    <div class="wp-hp-step-tag">Weighted Rubric</div>
                </div>

                <!-- Step 03 -->
                <div class="wp-hp-step-card">
                    <div class="wp-hp-step-top">
                        <span class="wp-hp-step-num">03</span>
                        <div class="wp-hp-step-line"></div>
                    </div>
                    <h3 class="wp-hp-step-title">Analyse performance indicators</h3>
                    <p class="wp-hp-step-desc">
                        Examine department variance, identify high performers, and spot areas needing support through interactive Plotly distribution charts and monthly progress trajectories.
                    </p>
                    <div class="wp-hp-step-tag">Visual Analytics</div>
                </div>

                <!-- Step 04 -->
                <div class="wp-hp-step-card">
                    <div class="wp-hp-step-top">
                        <span class="wp-hp-step-num">04</span>
                        <div class="wp-hp-step-line"></div>
                    </div>
                    <h3 class="wp-hp-step-title">Explore predictions and insights</h3>
                    <p class="wp-hp-step-desc">
                        Evaluate Decision Tree and Random Forest models on held-out test splits. Run What-If sensitivity scenarios to understand key drivers without compromising human discretion.
                    </p>
                    <div class="wp-hp-step-tag">Explainable ML</div>
                </div>

                <!-- Step 05 -->
                <div class="wp-hp-step-card">
                    <div class="wp-hp-step-top">
                        <span class="wp-hp-step-num">05</span>
                    </div>
                    <h3 class="wp-hp-step-title">Generate reports</h3>
                    <p class="wp-hp-step-desc">
                        Export filtered CSV summaries by department or review period for transparent follow-up and recordkeeping.
                    </p>
                    <div class="wp-hp-step-tag">Audit Export</div>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(how_it_works_html)

    # -------------------------------------------------------------------------
    # 7. Analytics Showcase Section
    # -------------------------------------------------------------------------
    analytics_showcase_html = f"""
    <section class="wp-hp-section wp-hp-analytics-showcase-section" id="analytics-showcase">
        <div class="wp-hp-container">
            <div class="wp-hp-section-header">
                <span class="wp-hp-section-eyebrow">DATA INTEGRITY</span>
                <h2 class="wp-hp-section-title">Understand Outcomes. Distinguish Fact from Forecast.</h2>
                <p class="wp-hp-section-sub">
                    WorkPulse treats human assessments as the unalterable source of truth, while treating machine learning models strictly as transparent, held-out decision support.
                </p>
            </div>

            <div class="wp-hp-analytics-compare-grid">
                <!-- Left: Actual Human Assessments -->
                <div class="wp-hp-compare-card wp-hp-compare-source">
                    <div class="wp-hp-compare-head">
                        <div class="wp-hp-compare-badge">SOURCE OF TRUTH</div>
                        <h3 class="wp-hp-compare-title">Human Assessments</h3>
                        <p class="wp-hp-compare-sub">Human evaluations with reviewer details recorded</p>
                    </div>

                    <div class="wp-hp-compare-body">
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Scoring Methodology:</span>
                            <span class="wp-hp-spec-val">Weighted sum of active indicators (Must = 100%)</span>
                        </div>
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Category Tiers:</span>
                            <span class="wp-hp-spec-val">Needs Support (&lt;60) · Moderate (60-79) · High (≥80)</span>
                        </div>
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Audit Trail:</span>
                            <span class="wp-hp-spec-val">Recorded assessment date, reviewer name, and comments</span>
                        </div>
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Status in System:</span>
                            <span class="wp-hp-spec-val" style="color:#0D9488; font-weight:700;">Official Workforce Record</span>
                        </div>

                        <!-- Mini Demo Sample Card -->
                        <div class="wp-hp-sample-box">
                            <div class="wp-hp-sample-top">
                                <strong>{f'Assessment #{int(latest_assessment["assessment_id"])} · {escape(employee_name)}' if latest_assessment is not None else 'No assessment recorded yet'}</strong>
                                <span class="wp-hp-chip {('wp-hp-chip-high' if latest_category == 'High' else 'wp-hp-chip-mod' if latest_category == 'Moderate' else 'wp-hp-chip-need' if latest_category == 'Needs Support' else '')}">{f'{latest_score_label} {latest_category}' if latest_assessment is not None else 'Awaiting review'}</span>
                            </div>
                            <p class="wp-hp-sample-comment">{escape(str(latest_assessment["comments"])) if latest_assessment is not None else 'Recorded assessments and reviewer comments will appear here.'}</p>
                            <span class="wp-hp-sample-reviewer">{f'Reviewer: {escape(str(latest_assessment["reviewer"]))} · {escape(assessment_date_label)}' if latest_assessment is not None else 'Reviewer details are shown after an assessment is recorded.'}</span>
                        </div>
                    </div>
                </div>

                <!-- Right: ML Decision Support -->
                <div class="wp-hp-compare-card wp-hp-compare-ml">
                    <div class="wp-hp-compare-head">
                        <div class="wp-hp-compare-badge" style="background:#F5F3FF; color:#7C3AED;">DECISION SUPPORT ONLY</div>
                        <h3 class="wp-hp-compare-title">Machine Learning Predictions</h3>
                        <p class="wp-hp-compare-sub">Model estimates are shown separately from recorded review outcomes</p>
                    </div>

                    <div class="wp-hp-compare-body">
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Implemented Models:</span>
                            <span class="wp-hp-spec-val">Decision Tree Classifier & Random Forest</span>
                        </div>
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Validation Rigor:</span>
                            <span class="wp-hp-spec-val">Strict 80/20 train/test split on held-out data</span>
                        </div>
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">Data Safeguard:</span>
                            <span class="wp-hp-spec-val">Evaluation depends on the available labelled data</span>
                        </div>
                        <div class="wp-hp-spec-row">
                            <span class="wp-hp-spec-key">System Boundary:</span>
                            <span class="wp-hp-spec-val" style="color:#7C3AED; font-weight:700;">Never overwrites human review scores</span>
                        </div>

                        <!-- Prediction caveat -->
                        <div class="wp-hp-sample-box" style="background:#FAF5FF; border-color:#DDD6FE;">
                            <div class="wp-hp-sample-top">
                                <strong>Prediction and what-if tools</strong>
                                <span class="wp-hp-chip" style="background:#EDE9FE; color:#6D28D9;">Decision Aid</span>
                            </div>
                            <p class="wp-hp-sample-comment">Explore how model estimates respond to changed inputs. Outputs depend on available records and should not replace manager evaluations.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(analytics_showcase_html)

    # -------------------------------------------------------------------------
    # 8. About Section
    # -------------------------------------------------------------------------
    about_html = """
    <section class="wp-hp-section wp-hp-about-section" id="about">
        <div class="wp-hp-container">
            <div class="wp-hp-about-wrapper">
                <div class="wp-hp-about-header">
                    <span class="wp-hp-section-eyebrow">ABOUT WORKPULSE</span>
                    <h2 class="wp-hp-section-title">Engineered for Principled Workforce Management</h2>
                    <p class="wp-hp-about-lead">
                        WorkPulse was created on a single conviction: organizational growth requires transparent review standards, complete data ownership, and respect for individual craft.
                    </p>
                </div>

                <div class="wp-hp-about-pillars-grid">
                    <div class="wp-hp-pillar-card">
                        <div class="wp-hp-pillar-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
                        </div>
                        <h4>Empirical Integrity</h4>
                        <p>
                            We never manufacture unearned scores or mask missing data. When review records don't exist, WorkPulse tells you plainly rather than filling screens with vanity metrics.
                        </p>
                    </div>

                    <div class="wp-hp-pillar-card">
                        <div class="wp-hp-pillar-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                        </div>
                        <h4>Weighted Accountability</h4>
                        <p>
                            Performance indicators and their weights are fully configurable by your organization. Active weights must strictly equal 100%, ensuring fair, mathematical consistency across all departments.
                        </p>
                    </div>

                    <div class="wp-hp-pillar-card">
                        <div class="wp-hp-pillar-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#168C83" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                        </div>
                        <h4>Local Data Ownership</h4>
                        <p>
                            Employee profiles, assessments, and review history are stored in the workspace's local SQLite database.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(about_html)

    # -------------------------------------------------------------------------
    # 9. Closing Section
    # -------------------------------------------------------------------------
    closing_html = f"""
    <section class="wp-hp-closing-section">
        <div class="wp-hp-container">
            <div class="wp-hp-closing-card">
                <div class="wp-hp-closing-inner">
                    <span class="wp-hp-closing-eyebrow">TAKE THE NEXT STEP</span>
                    <h2 class="wp-hp-closing-title">Better insights. More meaningful reviews.</h2>
                    <p class="wp-hp-closing-lead">
                        Bring performance information together and make employee development easier to understand.
                    </p>

                    <div class="wp-hp-closing-actions">
                        <a href="?page=Dashboard" target="_self" class="wp-hp-btn wp-hp-btn-closing-primary">
                            <span>Explore WorkPulse</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                        </a>
                        <a href="?page=Assessments" target="_self" class="wp-hp-btn wp-hp-btn-closing-secondary">
                            <span>Conduct an Assessment</span>
                        </a>
                    </div>

                    <div class="wp-hp-closing-meta">
                        <span>SQLite local storage</span>
                        <span>•</span>
                        <span>{total_emp:,} Employee Profiles</span>
                        <span>•</span>
                        <span>Zero External Vendor Lock-in</span>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    st.html(closing_html)

    # -------------------------------------------------------------------------
    # 10. Minimal & Consistent SaaS Footer
    # -------------------------------------------------------------------------
    footer_html = f"""
    <footer class="wp-hp-footer">
        <div class="wp-hp-container">
            <div class="wp-hp-footer-grid">
                <!-- Col 1: Brand & Mission -->
                <div class="wp-hp-fcol wp-hp-fcol-brand">
                    <div class="wp-hp-brand" style="margin-bottom:0.75rem;">
                        <div class="wp-hp-brand-mark">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                            </svg>
                        </div>
                        <span class="wp-hp-brand-title">WorkPulse</span>
                    </div>
                    <p class="wp-hp-footer-tagline">
                        Understand Performance. Empower Growth.
                    </p>
                    <p class="wp-hp-footer-desc">
                        A local-first, privacy-respecting employee performance review system combining structured human evaluations with held-out machine learning insights.
                    </p>
                    <div class="wp-hp-db-indicator">
                        <span class="wp-hp-live-dot"></span>
                        <span>SQLite database connected ({total_emp} profiles)</span>
                    </div>
                </div>

                <!-- Col 2: Workspace Modules -->
                <div class="wp-hp-fcol">
                    <span class="wp-hp-fcol-title">WORKSPACE</span>
                    <ul class="wp-hp-flinks">
                        <li><a href="?page=Dashboard" target="_self">Dashboard Overview</a></li>
                        <li><a href="?page=Employees" target="_self">Employee Directory</a></li>
                        <li><a href="?page=Performance Periods" target="_self">Review Periods</a></li>
                        <li><a href="?page=Performance Areas" target="_self">Performance Areas</a></li>
                        <li><a href="?page=Assessments" target="_self">Assessments Workflow</a></li>
                    </ul>
                </div>

                <!-- Col 3: Intelligence & Audit -->
                <div class="wp-hp-fcol">
                    <span class="wp-hp-fcol-title">INTELLIGENCE</span>
                    <ul class="wp-hp-flinks">
                        <li><a href="?page=Analytics" target="_self">Analytics Explorer</a></li>
                        <li><a href="?page=Predictions" target="_self">Machine Learning Models</a></li>
                        <li><a href="?page=Reports" target="_self">Audit Reports & Export</a></li>
                        <li><a href="?page=Notifications" target="_self">Workflow Notifications</a></li>
                        <li><a href="?page=Settings" target="_self">Workspace Settings</a></li>
                    </ul>
                </div>

                <!-- Col 4: Project Info -->
                <div class="wp-hp-fcol">
                    <span class="wp-hp-fcol-title">SYSTEM ARCHITECTURE</span>
                    <ul class="wp-hp-flinks">
                        <li><span>Stack: Streamlit + SQLite</span></li>
                        <li><span>ML: Scikit-learn Decision Tree & Random Forest</span></li>
                        <li><span>Validation: Held-out Test Split</span></li>
                        <li><span>Workspace: {escape(workspace_name)}</span></li>
                    </ul>
                </div>
            </div>

            <!-- Footer Bottom Row -->
            <div class="wp-hp-footer-bottom">
                <div class="wp-hp-footer-copy">
                    © 2026 WorkPulse. Understand Performance. Empower Growth. All rights reserved.
                </div>
                <div class="wp-hp-footer-sublinks">
                    <a href="#top">Back to Top ↑</a>
                    <a href="?page=Dashboard" target="_self">Launch App</a>
                </div>
            </div>
        </div>
    </footer>
    """
    st.html(footer_html)
