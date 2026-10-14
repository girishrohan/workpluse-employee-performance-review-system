"""Reusable visual primitives for the WorkPulse Streamlit interface."""

from html import escape
from typing import Any

import streamlit as st


def render_page_heading(title: str, subtitle: str, breadcrumb: str | None = None) -> None:
    if breadcrumb:
        st.caption(breadcrumb)
    st.markdown(f'<h1 class="wp-page-title">{escape(title)}</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="wp-page-subtitle">{escape(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str, value: Any, detail: str, icon: str, tone: str = "blue"
) -> None:
    safe_values = [escape(str(item)) for item in (label, value, detail, icon, tone)]
    st.markdown(
        f"""
        <section class="wp-metric-card wp-tone-{safe_values[4]}">
            <div class="wp-metric-top">
                <span class="wp-metric-label">{safe_values[0]}</span>
                <span class="wp-metric-icon" aria-hidden="true">{safe_values[3]}</span>
            </div>
            <div class="wp-metric-value">{safe_values[1]}</div>
            <div class="wp-metric-detail">{safe_values[2]}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_status(value: str) -> str:
    statuses = {
        "active": "wp-status-positive",
        "completed": "wp-status-positive",
        "high": "wp-status-positive",
        "draft": "wp-status-neutral",
        "on leave": "wp-status-warning",
        "moderate": "wp-status-warning",
        "inactive": "wp-status-neutral",
        "needs support": "wp-status-danger",
    }
    class_name = statuses.get(value.strip().casefold(), "wp-status-neutral")
    return (
        f'<span class="wp-status {class_name}">'
        f"{escape(value)}</span>"
    )


def apply_chart_style(figure: Any) -> Any:
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=12, r=12, t=30, b=12),
        font=dict(family="Inter, sans-serif", color="#263238", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(gridcolor="#EEF2F6", zeroline=False)
    return figure


def show_empty_state(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="wp-empty-state">
            <div class="wp-empty-mark" aria-hidden="true">↗</div>
            <strong>{escape(title)}</strong>
            <p>{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )