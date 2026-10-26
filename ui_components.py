"""
WorkPulse — Reusable Visual Components & SVG Icon Library.
High-end Enterprise SaaS design primitives matching Deep Navy & Teal aesthetic.
"""

from html import escape
from typing import Any
import streamlit as st


# -----------------------------------------------------------------------------
# Crisp Enterprise SVG Icons (Lucide-inspired)
# -----------------------------------------------------------------------------
ICONS = {
    "dashboard": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "employees": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "calendar": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>',
    "sliders": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/></svg>',
    "assessments": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "analytics": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/></svg>',
    "sparkles": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>',
    "reports": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>',
    "notifications": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    "settings": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    "pulse": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    "check": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "alert": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>',
    "target": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "user-check": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>',
    "trending-up": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
}


def get_icon(name: str) -> str:
    """Returns SVG icon markup or fallback."""
    return ICONS.get(name.lower(), ICONS["pulse"])


# -----------------------------------------------------------------------------
# Page Header & Breadcrumbs
# -----------------------------------------------------------------------------
def render_page_heading(
    title: str, subtitle: str, breadcrumb: str | None = None, badge: str | None = None
) -> None:
    safe_title = escape(title)
    safe_sub = escape(subtitle)
    bc_html = ""
    if breadcrumb:
        safe_bc = escape(breadcrumb)
        bc_html = f'<div class="wp-breadcrumb">WORKSPACE &nbsp;/&nbsp; <span>{safe_bc}</span></div>'
    
    badge_html = ""
    if badge:
        safe_badge = escape(badge)
        badge_html = f'<span class="wp-badge wp-badge-active" style="margin-left:0.75rem;">{safe_badge}</span>'

    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem;">
            {bc_html}
            <div style="display:flex; align-items:center;">
                <h1 class="wp-page-title">{safe_title}</h1>
                {badge_html}
            </div>
            <p class="wp-page-subtitle">{safe_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Metric / KPI Cards
# -----------------------------------------------------------------------------
def render_metric_card(
    label: str,
    value: Any,
    detail: str,
    icon: str = "dashboard",
    tone: str = "navy",
    trend: str | None = None,
) -> None:
    safe_label = escape(str(label))
    safe_value = escape(str(value))
    safe_detail = escape(str(detail))
    safe_tone = escape(str(tone))
    icon_svg = get_icon(icon)

    trend_html = ""
    if trend:
        safe_trend = escape(str(trend))
        trend_html = f'<span class="wp-metric-trend-up">{ICONS["trending-up"]} {safe_trend}</span> &nbsp;'

    st.markdown(
        f"""
        <div class="wp-metric-card wp-tone-{safe_tone}">
            <div class="wp-metric-top">
                <span class="wp-metric-label">{safe_label}</span>
                <div class="wp-metric-icon-wrap" aria-hidden="true">{icon_svg}</div>
            </div>
            <div class="wp-metric-value">{safe_value}</div>
            <div class="wp-metric-detail">{trend_html}{safe_detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Active Review Cycle Progress Banner
# -----------------------------------------------------------------------------
def render_cycle_banner(
    cycle_name: str,
    status: str,
    due_date: str,
    progress_pct: float,
    total_reviews: int,
    pending_reviews: int,
) -> None:
    safe_name = escape(cycle_name)
    safe_status = escape(status)
    safe_due = escape(due_date)
    pct = max(0, min(100, int(progress_pct)))
    
    st.markdown(
        f"""
        <div class="wp-cycle-banner">
            <div class="wp-cycle-info">
                <span class="wp-cycle-badge">{safe_status} CYCLE</span>
                <div class="wp-cycle-text">
                    <strong>{safe_name}</strong>
                    <span>Due: {safe_due} &nbsp;·&nbsp; {total_reviews} completed &nbsp;·&nbsp; {pending_reviews} pending</span>
                </div>
            </div>
            <div style="min-width: 180px; text-align: right;">
                <span style="font-size:0.75rem; font-weight:700; color:var(--wp-teal);">{pct}% COMPLETE</span>
                <div class="wp-progress-wrap">
                    <div class="wp-progress-bar" style="width: {pct}%;"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Status & Outcome Badges
# -----------------------------------------------------------------------------
def render_status_badge(value: str) -> str:
    """Returns HTML for modern status chips with dot indicator."""
    val_clean = value.strip().casefold()
    classes = {
        "high": ("wp-badge-high", "#0D9488"),
        "active": ("wp-badge-active", "#059669"),
        "completed": ("wp-badge-completed", "#168C83"),
        "moderate": ("wp-badge-moderate", "#D97706"),
        "on leave": ("wp-badge-on-leave", "#D97706"),
        "needs support": ("wp-badge-needs-support", "#E11D48"),
        "draft": ("wp-badge-draft", "#64748B"),
        "inactive": ("wp-badge-draft", "#64748B"),
    }
    badge_class, dot_color = classes.get(val_clean, ("wp-badge-draft", "#64748B"))
    return (
        f'<span class="wp-badge {badge_class}">'
        f'<span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:{dot_color};margin-right:2px;"></span>'
        f'{escape(value)}</span>'
    )


# Backward compatibility alias
def render_status(value: str) -> str:
    return render_status_badge(value)


# -----------------------------------------------------------------------------
# Dedicated Employee Profile Dossier
# -----------------------------------------------------------------------------
def render_employee_profile_card(emp: dict[str, Any]) -> None:
    """Renders a comprehensive, high-end employee performance card."""
    name = escape(str(emp.get("employee_name", "Employee")))
    code = escape(str(emp.get("employee_code", "WP-000")))
    dept = escape(str(emp.get("department", "General")))
    desig = escape(str(emp.get("designation") or "Staff Member"))
    status = str(emp.get("status", "Active"))
    tenure = f"{float(emp.get('experience_years', 0)):.1f} yrs"
    
    att = float(emp.get("attendance_rate") or 90.0)
    task = float(emp.get("task_completion_rate") or 85.0)
    training = float(emp.get("training_hours") or 24.0)
    rating = float(emp.get("previous_performance") or 3.5)
    
    initials = "".join(part[0].upper() for part in name.split()[:2]) or "E"
    status_chip = render_status_badge(status)

    st.markdown(
        f"""
        <div class="wp-profile-card">
            <div class="wp-profile-top">
                <div class="wp-profile-avatar">{initials}</div>
                <div class="wp-profile-info">
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <h3>{name}</h3>
                        {status_chip}
                    </div>
                    <div class="wp-profile-meta">
                        <span><strong>{code}</strong></span>
                        <span>•</span>
                        <span>{desig}</span>
                        <span>•</span>
                        <span>{dept}</span>
                        <span>•</span>
                        <span>Tenure: {tenure}</span>
                    </div>
                </div>
            </div>
            <div class="wp-profile-metrics-grid">
                <div class="wp-profile-metric-box">
                    <div class="wp-profile-metric-label">Attendance Rate</div>
                    <div class="wp-profile-metric-val">{att:.1f}%</div>
                    <div class="wp-progress-wrap"><div class="wp-progress-bar" style="width:{min(100, int(att))}%;"></div></div>
                </div>
                <div class="wp-profile-metric-box">
                    <div class="wp-profile-metric-label">Task Completion</div>
                    <div class="wp-profile-metric-val">{task:.1f}%</div>
                    <div class="wp-progress-wrap"><div class="wp-progress-bar" style="width:{min(100, int(task))}%;"></div></div>
                </div>
                <div class="wp-profile-metric-box">
                    <div class="wp-profile-metric-label">Training Logged</div>
                    <div class="wp-profile-metric-val">{training:.0f} hrs</div>
                    <div class="wp-progress-wrap"><div class="wp-progress-bar" style="width:{min(100, int(training * 2))}%;"></div></div>
                </div>
                <div class="wp-profile-metric-box">
                    <div class="wp-profile-metric-label">Prior Score</div>
                    <div class="wp-profile-metric-val">{rating:.1f} / 5.0</div>
                    <div class="wp-progress-wrap"><div class="wp-progress-bar" style="width:{min(100, int(rating * 20))}%;"></div></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# High-End Empty State
# -----------------------------------------------------------------------------
def render_empty_state(
    title: str, description: str, icon: str = "sparkles"
) -> None:
    safe_title = escape(title)
    safe_desc = escape(description)
    icon_svg = get_icon(icon)

    st.markdown(
        f"""
        <div class="wp-empty-state">
            <div class="wp-empty-icon" aria-hidden="true">{icon_svg}</div>
            <strong>{safe_title}</strong>
            <p>{safe_desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Backward compatibility alias
def show_empty_state(title: str, description: str) -> None:
    render_empty_state(title, description, icon="sparkles")


# -----------------------------------------------------------------------------
# Chart Styling (Plotly White & Enterprise Palette)
# -----------------------------------------------------------------------------
def apply_chart_style(figure: Any) -> Any:
    """Applies refined, distraction-free typography and clean palette to Plotly figures."""
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=16, r=16, t=32, b=16),
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            color="#0F172A",
            size=12,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#475569"),
        ),
        hoverlabel=dict(
            bgcolor="#102A43",
            font_size=12,
            font_color="#FFFFFF",
            font_family="Inter, sans-serif",
        ),
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        color="#475569",
        tickfont=dict(size=11, color="#475569"),
    )
    figure.update_yaxes(
        gridcolor="#F1F5F9",
        zeroline=False,
        color="#475569",
        tickfont=dict(size=11, color="#475569"),
    )
    return figure


# -----------------------------------------------------------------------------
# Printable Executive Report Header
# -----------------------------------------------------------------------------
def render_executive_report_header(
    report_title: str,
    cycle_name: str,
    dept_filter: str,
    employee_count: int,
    avg_score: float,
) -> None:
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid var(--wp-border); border-radius:var(--wp-radius-lg); padding:1.75rem; margin-bottom:1.5rem; box-shadow:var(--wp-shadow-sm);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid var(--wp-border); padding-bottom:1rem; margin-bottom:1.25rem;">
                <div>
                    <span style="font-size:0.6875rem; font-weight:700; color:var(--wp-teal); letter-spacing:0.08em; text-transform:uppercase;">WORKPULSE EXECUTIVE AUDIT</span>
                    <h2 style="font-size:1.5rem; font-weight:700; color:var(--wp-navy); margin:0.25rem 0 0 0;">{escape(report_title)}</h2>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:0.75rem; font-weight:600; color:var(--wp-text-secondary);">Cycle: <strong>{escape(cycle_name)}</strong></span><br>
                    <span style="font-size:0.75rem; color:var(--wp-text-muted);">Department: {escape(dept_filter)}</span>
                </div>
            </div>
            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:1rem;">
                <div style="background:var(--wp-bg); padding:0.75rem 1rem; border-radius:var(--wp-radius-md);">
                    <div style="font-size:0.6875rem; font-weight:600; color:var(--wp-text-secondary); text-transform:uppercase;">Records Audited</div>
                    <div style="font-size:1.25rem; font-weight:700; color:var(--wp-navy);">{employee_count}</div>
                </div>
                <div style="background:var(--wp-bg); padding:0.75rem 1rem; border-radius:var(--wp-radius-md);">
                    <div style="font-size:0.6875rem; font-weight:600; color:var(--wp-text-secondary); text-transform:uppercase;">Workforce Mean Score</div>
                    <div style="font-size:1.25rem; font-weight:700; color:var(--wp-navy);">{avg_score:.1f} / 100</div>
                </div>
                <div style="background:var(--wp-bg); padding:0.75rem 1rem; border-radius:var(--wp-radius-md);">
                    <div style="font-size:0.6875rem; font-weight:600; color:var(--wp-text-secondary); text-transform:uppercase;">Overall Standing</div>
                    <div style="font-size:1.25rem; font-weight:700; color:var(--wp-teal);">{render_status_badge('High' if avg_score >= 80 else ('Moderate' if avg_score >= 60 else 'Needs Support'))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )