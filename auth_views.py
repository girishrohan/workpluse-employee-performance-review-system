"""
WorkPulse — Authentication Views.
Enterprise SaaS Authentication Experience for WorkPulse.
Architected with an asymmetric split-screen layout (60% brand / 40% auth),
premium visual identity, and zero-compromise security validation.
"""

from datetime import datetime
from html import escape

import streamlit as st

from auth.auth_service import (
    authenticate_user,
    authenticate_user_with_status,
    is_rate_limited,
    get_lockout_remaining_minutes,
    change_password,
    generate_password_reset_token,
    validate_reset_token,
    consume_reset_token,
    register_pending_user,
    log_audit,
)


def _on_quick_fill(email: str, password: str, role_name: str) -> None:
    """Widget callback: prefill demo credentials before the form rerenders."""
    st.session_state["login_email_input"] = email
    st.session_state["login_password_input"] = password
    st.session_state["active_role_badge"] = role_name


# ---------------------------------------------------------------------------
# CSS Injection — Enterprise SaaS Identity System (Premium Redesign)
# ---------------------------------------------------------------------------

_AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ==========================================================================
   CSS CUSTOM PROPERTIES — WORKPULSE PREMIUM PALETTE
   ========================================================================== */
:root {
    /* Core Brand Palette */
    --wp-navy-900: #101B2D;        /* Deep Navy — primary brand */
    --wp-navy-800: #172B45;        /* Midnight Blue — elevation */
    --wp-navy-700: #1E3A5F;        /* Elevated surfaces */
    --wp-navy-600: #284B6E;        /* Borders, subtle accents */
    --wp-navy-500: #3B5E7E;        /* Muted text on dark */

    --wp-cyan-500: #00D4FF;        /* Electric Cyan — primary action */
    --wp-cyan-400: #00B8E6;        /* Hover */
    --wp-cyan-600: #00A3CC;        /* Active/pressed */

    --wp-slate-100: #F1F5F9;       /* Light backgrounds */
    --wp-slate-200: #E2E8F0;       /* Borders, dividers */
    --wp-slate-300: #CBD5E1;       /* Disabled borders */
    --wp-slate-500: #64748B;       /* Secondary text */
    --wp-slate-600: #475569;       /* Body text */
    --wp-slate-700: #334155;       /* Heading text */
    --wp-slate-900: #0F172A;       /* Primary headings */

    --wp-surface: #FFFFFF;         /* Pure white surfaces */
    --wp-surface-elevated: #FAFBFC; /* Elevated cards */

    --wp-success: #10B981;         /* Success states */
    --wp-warning: #F59E0B;         /* Warning states */
    --wp-error: #EF4444;           /* Error states */

    /* Typography Scale */
    --font-display: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

    /* Spacing System (4px base) */
    --space-1: 0.25rem;   /* 4px */
    --space-2: 0.5rem;    /* 8px */
    --space-3: 0.75rem;   /* 12px */
    --space-4: 1rem;      /* 16px */
    --space-5: 1.25rem;   /* 20px */
    --space-6: 1.5rem;    /* 24px */
    --space-8: 2rem;      /* 32px */
    --space-10: 2.5rem;   /* 40px */
    --space-12: 3rem;     /* 48px */
    --space-16: 4rem;     /* 64px */

    /* Border Radius */
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --radius-xl: 20px;
    --radius-full: 9999px;

    /* Shadows */
    --shadow-xs: 0 1px 2px rgba(16, 27, 45, 0.04);
    --shadow-sm: 0 2px 4px rgba(16, 27, 45, 0.06), 0 1px 2px rgba(16, 27, 45, 0.04);
    --shadow-md: 0 8px 16px -4px rgba(16, 27, 45, 0.12), 0 4px 8px -4px rgba(16, 27, 45, 0.08);
    --shadow-lg: 0 20px 40px -12px rgba(16, 27, 45, 0.18), 0 8px 16px -8px rgba(16, 27, 45, 0.1);
    --shadow-glow: 0 0 0 3px rgba(0, 212, 255, 0.25);

    /* Transitions */
    --transition-fast: 120ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 180ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 240ms cubic-bezier(0.4, 0, 0.2, 1);

    /* Z-Index Scale */
    --z-base: 1;
    --z-elevated: 10;
    --z-overlay: 100;
    --z-modal: 1000;
}

/* ==========================================================================
   GLOBAL VIEWPORT & STREAMLIT CHROME OVERRIDES
   ========================================================================== */
html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden !important;
    font-family: var(--font-ui) !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    background-color: var(--wp-surface) !important;
    color: var(--wp-slate-900) !important;
}

/* Hide default Streamlit chrome completely on auth views */
[data-testid="stSidebar"],
[data-testid="stHeader"],
header[data-testid="stHeader"],
footer,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
#MainMenu {
    display: none !important;
}

/* Force Streamlit app view to edge-to-edge 100vw */
[data-testid="stAppViewContainer"] {
    background: var(--wp-surface) !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow-x: hidden !important;
}

[data-testid="stAppViewContainer"] > .main {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

[data-testid="stMainBlockContainer"],
.main .block-container,
div.block-container {
    max-width: 100vw !important;
    width: 100vw !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* ==========================================================================
   ASYMMETRIC SPLIT-SCREEN LAYOUT (60% BRAND / 40% AUTH)
   ========================================================================== */
/* The top-level horizontal block containing left brand & right auth columns */
[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type,
div[data-testid="stHorizontalBlock"]:first-of-type {
    min-height: 100vh !important;
    width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    display: flex !important;
    align-items: stretch !important;
    background: var(--wp-surface) !important;
}

/* Left Brand Experience Column (60%) */
[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:first-child,
div[data-testid="stHorizontalBlock"]:first-of-type > div:first-child {
    flex: 60 1 0% !important;
    min-width: 0 !important;
    background: linear-gradient(155deg, var(--wp-navy-900) 0%, var(--wp-navy-800) 35%, var(--wp-navy-700) 70%, var(--wp-navy-900) 100%) !important;
    color: var(--wp-surface) !important;
    position: relative !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    padding: 0 !important;
}

/* Right Auth Experience Column (40%) */
[data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:last-child,
div[data-testid="stHorizontalBlock"]:first-of-type > div:last-child {
    flex: 40 1 0% !important;
    min-width: 0 !important;
    background: var(--wp-surface) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    padding: var(--space-10) var(--space-12) !important;
    box-sizing: border-box !important;
    border-left: 1px solid var(--wp-slate-200) !important;
    position: relative !important;
}

/* Reset any nested horizontal blocks inside the right column */
[data-testid="stHorizontalBlock"]:first-of-type > div:last-child [data-testid="stHorizontalBlock"] {
    min-height: auto !important;
    width: 100% !important;
    gap: var(--space-3) !important;
    margin: var(--space-2) 0 var(--space-4) 0 !important;
    background: transparent !important;
}

[data-testid="stHorizontalBlock"]:first-of-type > div:last-child [data-testid="stHorizontalBlock"] > div {
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
    flex: 1 1 0% !important;
}

/* ==========================================================================
   LEFT PANEL — VISUAL STORYTELLING & WORKFORCE INTELLIGENCE
   ========================================================================== */
.wp-brand-hero-panel {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 100vh;
    padding: var(--space-10) var(--space-12);
    box-sizing: border-box;
    position: relative;
    z-index: var(--z-base);
    color: var(--wp-surface) !important;
}

/* Subtle ambient radial glows */
.wp-ambient-glow-1 {
    position: absolute;
    top: -120px;
    right: -120px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}

.wp-ambient-glow-2 {
    position: absolute;
    bottom: -140px;
    left: -140px;
    width: 550px;
    height: 550px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}

.wp-ambient-glow-3 {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 800px;
    height: 800px;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.04) 0%, transparent 60%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}

/* Top brand identity bar */
.wp-brand-topbar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    position: relative;
    z-index: 1;
}

.wp-brand-mark-box {
    width: 3.25rem;
    height: 3.25rem;
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300D4FF' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-4l-3 9L9 3l-3 9H2'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    background-size: 26px 26px;
    border: 1px solid rgba(0, 212, 255, 0.4);
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
        0 8px 24px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.15),
        0 0 0 1px rgba(0, 212, 255, 0.2);
    position: relative;
}

.wp-brand-mark-box::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: calc(var(--radius-lg) + 2px);
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.3), rgba(16, 185, 129, 0.2));
    z-index: -1;
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.wp-brand-mark-box:hover::before {
    opacity: 1;
}

.wp-brand-title-wrap {
    display: flex;
    flex-direction: column;
}

.wp-brand-title {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--wp-surface) !important;
    letter-spacing: -0.03em;
    line-height: 1.1;
}

.wp-brand-badge {
    font-size: 0.625rem;
    font-weight: 700;
    color: var(--wp-cyan-500) !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.15rem;
}

/* Left Hero Content Section */
.wp-hero-content-body {
    margin: var(--space-8) 0;
    position: relative;
    z-index: 1;
}

.wp-hero-kicker {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--wp-cyan-500) !important;
    background: rgba(0, 212, 255, 0.12);
    border: 1px solid rgba(0, 212, 255, 0.25);
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius-full);
    margin-bottom: var(--space-4);
}

.wp-hero-kicker svg {
    width: 12px;
    height: 12px;
    flex-shrink: 0;
}

.wp-hero-headline {
    font-family: var(--font-display);
    font-size: clamp(2.25rem, 5vw, 3.25rem);
    font-weight: 800;
    color: var(--wp-surface) !important;
    line-height: 1.12;
    letter-spacing: -0.035em;
    margin: 0 0 var(--space-4) 0;
}

.wp-hero-headline .wp-gradient-text {
    background: linear-gradient(135deg, var(--wp-cyan-500) 0%, #22D3EE 40%, #10B981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.wp-hero-desc {
    color: rgba(248, 250, 252, 0.7) !important;
    font-size: 1.125rem;
    line-height: 1.7;
    margin: 0 0 var(--space-6) 0;
    max-width: 540px;
    font-weight: 400;
}

/* ==========================================================================
   WORKFORCE INTELLIGENCE VISUAL COMPOSITION
   ========================================================================== */
.wp-viz-container {
    background: rgba(16, 27, 45, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-xl);
    padding: var(--space-5) var(--space-6);
    box-shadow:
        0 24px 48px -16px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
    position: relative;
    max-width: 560px;
    display: block !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

.wp-viz-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: var(--space-3);
    margin-bottom: var(--space-4);
}

.wp-viz-status-pill {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: 0.6875rem;
    font-weight: 700;
    color: var(--wp-success);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.wp-viz-pulse-dot {
    width: 8px;
    height: 8px;
    background: var(--wp-success);
    border-radius: 50%;
    box-shadow: 0 0 12px var(--wp-success);
    display: inline-block;
    animation: wpPulse 2s ease-in-out infinite;
}

@keyframes wpPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.9); }
}

.wp-viz-badge {
    font-family: var(--font-mono);
    font-size: 0.625rem;
    color: rgba(248, 250, 252, 0.5);
    background: rgba(255, 255, 255, 0.05);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    letter-spacing: 0.06em;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

/* Calibrated Talent Matrix Cards */
.wp-talent-matrix {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
}

.wp-talent-node {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-md);
    padding: var(--space-3) var(--space-4);
    transition: all var(--transition-normal);
}

.wp-talent-node:hover {
    background: rgba(0, 212, 255, 0.05);
    border-color: rgba(0, 212, 255, 0.15);
    transform: translateX(4px);
}

.wp-talent-node.active {
    background: rgba(0, 212, 255, 0.08);
    border-color: rgba(0, 212, 255, 0.25);
}

.wp-talent-left {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    min-width: 0;
}

.wp-talent-avatar {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8125rem;
    font-weight: 700;
    color: var(--wp-surface);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    flex-shrink: 0;
}

.wp-talent-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.wp-talent-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--wp-surface) !important;
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.wp-talent-role {
    font-size: 0.75rem;
    font-weight: 400;
    color: rgba(248, 250, 252, 0.55) !important;
    margin-left: 0.25rem;
}

.wp-talent-metric {
    font-size: 0.75rem;
    color: rgba(248, 250, 252, 0.5) !important;
    margin-top: 0.125rem;
    font-family: var(--font-ui);
}

.wp-talent-metric strong {
    color: var(--wp-cyan-500) !important;
    font-weight: 600;
}

.wp-talent-chip {
    font-size: 0.5625rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    flex-shrink: 0;
    white-space: nowrap;
}

.wp-talent-chip.top {
    color: var(--wp-success);
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.wp-talent-chip.progress {
    color: var(--wp-cyan-500);
    background: rgba(0, 212, 255, 0.15);
    border: 1px solid rgba(0, 212, 255, 0.3);
}

.wp-talent-chip.aligned {
    color: #A78BFA;
    background: rgba(167, 139, 250, 0.15);
    border: 1px solid rgba(167, 139, 250, 0.3);
}

/* Telemetry Micro-Metrics Row */
.wp-viz-telemetry-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-3);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: var(--space-4);
}

.wp-viz-telemetry-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-md);
    padding: var(--space-3) var(--space-3);
    text-align: center;
    transition: all var(--transition-fast);
}

.wp-viz-telemetry-item:hover {
    background: rgba(0, 212, 255, 0.04);
    border-color: rgba(0, 212, 255, 0.12);
}

.wp-viz-metric-label {
    font-size: 0.5625rem;
    font-weight: 700;
    color: rgba(248, 250, 252, 0.45) !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: var(--space-1);
}

.wp-viz-metric-val {
    font-family: var(--font-display);
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--wp-surface) !important;
    letter-spacing: -0.02em;
    line-height: 1.2;
}

.wp-viz-metric-sub {
    font-size: 0.625rem;
    color: var(--wp-cyan-500) !important;
    font-weight: 500;
    margin-top: 0.125rem;
}

/* Left Footer Trust Anchors */
.wp-hero-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: var(--space-4);
    margin-top: var(--space-4);
    position: relative;
    z-index: 1;
}

.wp-trust-badges-grid {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-4);
    font-size: 0.75rem;
    color: rgba(248, 250, 252, 0.5);
    font-weight: 500;
}

.wp-trust-item {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    color: rgba(248, 250, 252, 0.6) !important;
    transition: color var(--transition-fast);
}

.wp-trust-item:hover {
    color: var(--wp-cyan-500) !important;
}

.wp-trust-item svg {
    color: var(--wp-cyan-500) !important;
    flex-shrink: 0;
    width: 14px;
    height: 14px;
}

/* ==========================================================================
   RIGHT PANEL — ENTERPRISE AUTHENTICATION FORM
   ========================================================================== */
.wp-auth-panel-wrapper {
    max-width: 420px;
    width: 100%;
    margin: 0 auto;
    background: var(--wp-surface) !important;
    color: var(--wp-slate-900) !important;
}

.wp-auth-top-brand {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-4);
}

.wp-auth-mini-logo {
    width: 2.25rem;
    height: 2.25rem;
    background: linear-gradient(135deg, var(--wp-slate-100) 0%, var(--wp-slate-200) 100%);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300D4FF' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-4l-3 9L9 3l-3 9H2'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    background-size: 20px 20px;
    border: 1px solid var(--wp-slate-200);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
}

.wp-auth-mini-brand {
    font-family: var(--font-display);
    font-size: 1.125rem;
    font-weight: 800;
    color: var(--wp-slate-900) !important;
    letter-spacing: -0.02em;
}

.wp-auth-mini-sep {
    color: var(--wp-slate-300) !important;
    font-weight: 300;
}

.wp-auth-mini-label {
    font-size: 0.625rem;
    font-weight: 700;
    color: var(--wp-cyan-500) !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.wp-auth-card-top {
    margin-bottom: var(--space-6);
}

.wp-auth-header-title {
    font-family: var(--font-display);
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--wp-slate-900) !important;
    letter-spacing: -0.03em;
    margin: 0 0 var(--space-2) 0;
    line-height: 1.15;
}

.wp-auth-header-sub {
    font-size: 1rem;
    color: var(--wp-slate-500) !important;
    margin: 0;
    line-height: 1.55;
    font-weight: 400;
}

/* Role Selector Header & Active Badge */
.wp-role-selector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: var(--space-5) 0 var(--space-2) 0;
}

.wp-role-selector-title {
    font-size: 0.625rem;
    font-weight: 700;
    color: var(--wp-slate-500) !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.wp-role-active-badge {
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--wp-cyan-600) !important;
    background: rgba(0, 212, 255, 0.1) !important;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    border: 1px solid rgba(0, 212, 255, 0.2);
}

/* Quick Role Buttons — 1-Click Demo Profiles */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:has(button[key^="btn_quick_"]) {
    background: transparent !important;
    padding: 0 !important;
}

div.stButton > button[key^="btn_quick_"] {
    height: 42px !important;
    background: var(--wp-surface) !important;
    border: 1.5px solid var(--wp-slate-200) !important;
    border-radius: var(--radius-md) !important;
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
    color: var(--wp-slate-700) !important;
    letter-spacing: -0.01em !important;
    transition: all var(--transition-fast) !important;
    box-shadow: var(--shadow-xs) !important;
    font-family: var(--font-ui) !important;
}

div.stButton > button[key^="btn_quick_"]:hover {
    background: var(--wp-slate-100) !important;
    border-color: var(--wp-cyan-400) !important;
    color: var(--wp-slate-900) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

div.stButton > button[key^="btn_quick_"]:active {
    transform: translateY(0) !important;
    box-shadow: var(--shadow-xs) !important;
}

/* Streamlit Text Input Overrides inside Auth Form */
div[data-testid="stTextInput"] {
    margin-bottom: var(--space-4) !important;
}

div[data-testid="stTextInput"] label {
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
    color: var(--wp-slate-700) !important;
    margin-bottom: var(--space-1) !important;
    letter-spacing: -0.01em !important;
    font-family: var(--font-ui) !important;
}

div[data-testid="stTextInput"] input {
    height: 52px !important;
    background: var(--wp-surface) !important;
    border: 1.5px solid var(--wp-slate-200) !important;
    border-radius: var(--radius-md) !important;
    padding: 0 var(--space-4) !important;
    font-size: 1rem !important;
    color: var(--wp-slate-900) !important;
    font-family: var(--font-ui) !important;
    transition: all var(--transition-fast) !important;
    box-shadow: var(--shadow-xs) !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: var(--wp-slate-400) !important;
}

div[data-testid="stTextInput"] input:focus {
    background: var(--wp-surface) !important;
    border-color: var(--wp-cyan-500) !important;
    box-shadow: var(--shadow-glow), var(--shadow-xs) !important;
    outline: none !important;
}

div[data-testid="stTextInput"] input:disabled {
    background: var(--wp-slate-100) !important;
    color: var(--wp-slate-500) !important;
    cursor: not-allowed !important;
}

/* Password eye button inside text input */
div[data-testid="stTextInput"] button {
    border: none !important;
    background: transparent !important;
    color: var(--wp-slate-500) !important;
    box-shadow: none !important;
    transform: none !important;
    padding: 0 var(--space-2) !important;
}

div[data-testid="stTextInput"] button:hover {
    color: var(--wp-cyan-500) !important;
}

/* Checkbox (Remember me) */
div[data-testid="stCheckbox"] {
    margin: var(--space-1) 0 var(--space-4) 0 !important;
}

div[data-testid="stCheckbox"] label {
    font-size: 0.875rem !important;
    color: var(--wp-slate-600) !important;
    font-weight: 500 !important;
    font-family: var(--font-ui) !important;
}

div[data-testid="stCheckbox"] input[type="checkbox"] {
    accent-color: var(--wp-cyan-500) !important;
    width: 18px !important;
    height: 18px !important;
}

/* Primary Form Submit Button */
div[data-testid="stFormSubmitButton"] > button {
    height: 52px !important;
    background: var(--wp-slate-900) !important;
    color: var(--wp-surface) !important;
    border: 1px solid var(--wp-slate-900) !important;
    border-radius: var(--radius-md) !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    font-family: var(--font-display) !important;
    box-shadow:
        0 4px 16px rgba(16, 27, 45, 0.18),
        inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
    transition: all var(--transition-fast) !important;
    margin-top: var(--space-2) !important;
    cursor: pointer !important;
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--wp-navy-800) !important;
    border-color: var(--wp-navy-800) !important;
    box-shadow:
        0 8px 24px rgba(16, 27, 45, 0.25),
        inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
    transform: translateY(-2px) !important;
}

div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0) !important;
    box-shadow:
        0 2px 8px rgba(16, 27, 45, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

div[data-testid="stFormSubmitButton"] > button:disabled {
    background: var(--wp-slate-300) !important;
    border-color: var(--wp-slate-300) !important;
    color: var(--wp-slate-500) !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: var(--shadow-xs) !important;
}

/* Secondary Action Links */
.wp-auth-action-links {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: var(--space-5);
    padding-top: var(--space-4);
    border-top: 1px solid var(--wp-slate-200);
}

.wp-auth-action-link {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--wp-cyan-600) !important;
    background: transparent;
    border: none;
    padding: 0;
    cursor: pointer;
    transition: color var(--transition-fast);
    font-family: var(--font-ui);
}

.wp-auth-action-link:hover {
    color: var(--wp-cyan-500) !important;
    text-decoration: underline;
}

/* Pre-seeded Evaluation Drawer */
.wp-auth-eval-drawer {
    background: var(--wp-slate-100);
    border: 1px solid var(--wp-slate-200);
    border-radius: var(--radius-md);
    padding: var(--space-4) var(--space-4);
    margin-top: var(--space-6);
}

.wp-auth-eval-head {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: 0.625rem;
    font-weight: 700;
    color: var(--wp-cyan-600);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: var(--space-3);
}

.wp-auth-eval-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-2) 0;
    border-bottom: 1px solid var(--wp-slate-200);
    font-size: 0.8125rem;
}

.wp-auth-eval-item:last-child {
    border-bottom: none;
}

.wp-auth-eval-role {
    font-weight: 600;
    color: var(--wp-slate-800);
}

.wp-auth-eval-code {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--wp-slate-500);
    background: var(--wp-surface);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    border: 1px solid var(--wp-slate-200);
}

/* ==========================================================================
   STANDALONE CENTER CARD (FORGOT, RESET, REGISTER, CHANGE PW, LOGOUT)
   ========================================================================== */
.wp-auth-center-shell {
    min-height: 100vh;
    width: 100vw;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(155deg, var(--wp-navy-900) 0%, var(--wp-navy-800) 40%, var(--wp-navy-700) 100%);
    padding: var(--space-6) var(--space-4);
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
}

.wp-auth-center-shell::before {
    content: '';
    position: absolute;
    top: -150px;
    right: -150px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.wp-auth-center-shell::after {
    content: '';
    position: absolute;
    bottom: -180px;
    left: -180px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.06) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.wp-auth-center-card {
    background: var(--wp-surface);
    border: 1px solid var(--wp-slate-200);
    border-radius: var(--radius-xl);
    padding: var(--space-8) var(--space-7);
    box-shadow:
        0 32px 64px -20px rgba(16, 27, 45, 0.35),
        0 0 0 1px rgba(255, 255, 255, 0.05);
    max-width: 480px;
    width: 100%;
    margin: 0 auto;
    box-sizing: border-box;
    position: relative;
    z-index: 2;
    animation: wpCardEntrance 400ms cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes wpCardEntrance {
    from {
        opacity: 0;
        transform: translateY(20px) scale(0.98);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Loading Spinner */
.wp-spinner {
    width: 20px;
    height: 20px;
    border: 2.5px solid transparent;
    border-top-color: var(--wp-surface);
    border-radius: 50%;
    animation: wpSpin 0.8s linear infinite;
    display: inline-block;
    margin-right: var(--space-2);
    vertical-align: middle;
}

@keyframes wpSpin {
    to { transform: rotate(360deg); }
}

.wp-spinner-white {
    border-top-color: var(--wp-cyan-500);
}

/* Error / Success Alert Overrides */
.stAlert {
    border-radius: var(--radius-md) !important;
    font-size: 0.875rem !important;
    font-family: var(--font-ui) !important;
    border: none !important;
}

.stAlert[data-baseweb="notification"][kind="error"] {
    background: #FEF2F2 !important;
    color: var(--wp-error) !important;
    border-left: 4px solid var(--wp-error) !important;
}

.stAlert[data-baseweb="notification"][kind="success"] {
    background: #F0FDF4 !important;
    color: var(--wp-success) !important;
    border-left: 4px solid var(--wp-success) !important;
}

.stAlert[data-baseweb="notification"][kind="warning"] {
    background: #FFFBEB !important;
    color: var(--wp-warning) !important;
    border-left: 4px solid var(--wp-warning) !important;
}

.stAlert[data-baseweb="notification"][kind="info"] {
    background: #EFF6FF !important;
    color: var(--wp-cyan-600) !important;
    border-left: 4px solid var(--wp-cyan-500) !important;
}

/* ==========================================================================
   RESPONSIVE DESIGN BREAKPOINTS
   ========================================================================== */
/* Tablet — ≤1024px: Stacked layout, brand panel max 40vh */
@media (max-width: 1024px) {
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type,
    div[data-testid="stHorizontalBlock"]:first-of-type {
        flex-direction: column !important;
        min-height: auto !important;
    }

    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:first-child,
    div[data-testid="stHorizontalBlock"]:first-of-type > div:first-child {
        flex: 0 0 auto !important;
        min-height: auto !important;
        max-height: 40vh !important;
    }

    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:last-child,
    div[data-testid="stHorizontalBlock"]:first-of-type > div:last-child {
        flex: 1 1 100% !important;
        min-height: auto !important;
        padding: var(--space-8) var(--space-6) !important;
        border-left: none !important;
        border-top: 1px solid var(--wp-slate-200) !important;
    }

    .wp-brand-hero-panel {
        min-height: 40vh !important;
        padding: var(--space-6) var(--space-6) !important;
        justify-content: flex-start !important;
    }

    .wp-hero-content-body {
        margin: var(--space-4) 0 !important;
    }

    .wp-hero-headline {
        font-size: 2rem !important;
    }

    .wp-viz-container {
        display: none !important;
    }

    .wp-hero-footer {
        margin-top: var(--space-4) !important;
        padding-top: var(--space-3) !important;
    }

    .wp-trust-badges-grid {
        gap: var(--space-3) !important;
        font-size: 0.6875rem !important;
    }
}

/* Mobile — ≤640px: Single column, reduced padding, brand panel collapsible */
@media (max-width: 640px) {
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:first-child,
    div[data-testid="stHorizontalBlock"]:first-of-type > div:first-child {
        max-height: 35vh !important;
    }

    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:last-child,
    div[data-testid="stHorizontalBlock"]:first-of-type > div:last-child {
        padding: var(--space-6) var(--space-4) !important;
    }

    .wp-brand-hero-panel {
        min-height: 35vh !important;
        padding: var(--space-4) var(--space-4) !important;
    }

    .wp-brand-topbar {
        gap: var(--space-2) !important;
    }

    .wp-brand-mark-box {
        width: 2.75rem !important;
        height: 2.75rem !important;
    }

    .wp-brand-title {
        font-size: 1.25rem !important;
    }

    .wp-hero-headline {
        font-size: 1.75rem !important;
    }

    .wp-hero-desc {
        font-size: 1rem !important;
    }

    .wp-auth-header-title {
        font-size: 1.75rem !important;
    }

    .wp-auth-header-sub {
        font-size: 0.9375rem !important;
    }

    .wp-auth-center-card {
        padding: var(--space-6) var(--space-5) !important;
        border-radius: var(--radius-lg) !important;
    }

    .wp-auth-eval-item {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: var(--space-1) !important;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        padding: 0 !important;
    }

    div.stButton > button[key^="btn_quick_"] {
        height: 38px !important;
        font-size: 0.75rem !important;
        padding: 0 var(--space-2) !important;
    }

    .wp-viz-telemetry-row {
        grid-template-columns: 1fr !important;
    }

    .wp-trust-badges-grid {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: var(--space-2) !important;
    }
}

/* Large Desktop — ≥1440px: Expand layout */
@media (min-width: 1440px) {
    .wp-brand-hero-panel {
        padding: var(--space-12) var(--space-16);
    }

    .wp-hero-headline {
        font-size: 3.5rem;
    }

    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div:last-child,
    div[data-testid="stHorizontalBlock"]:first-of-type > div:last-child {
        padding: var(--space-12) var(--space-16) !important;
    }
}

/* Accessibility: respect user preference for reduced motion */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }

    .wp-viz-pulse-dot {
        animation: none !important;
    }

    .wp-brand-mark-box::before {
        transition: none !important;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --wp-slate-200: #94A3B8;
        --wp-slate-300: #64748B;
        --wp-cyan-500: #0099CC;
    }

    div[data-testid="stTextInput"] input:focus {
        box-shadow: 0 0 0 3px var(--wp-cyan-500) !important;
    }
}

/* Focus visible for keyboard navigation */
*:focus-visible {
    outline: 2px solid var(--wp-cyan-500) !important;
    outline-offset: 2px !important;
}

/* Prevent text selection on brand elements */
.wp-brand-mark-box,
.wp-talent-avatar,
.wp-viz-pulse-dot {
    user-select: none;
    -webkit-user-select: none;
}

</style>
"""


def _inject_auth_css() -> None:
    """Inject full-screen auth page CSS."""
    st.html(_AUTH_CSS)


# ---------------------------------------------------------------------------
# Login Page — Master Redesigned Split-Screen Enterprise Sign-In
# ---------------------------------------------------------------------------

def render_login_page() -> None:
    """Render the master redesigned WorkPulse split-screen enterprise sign-in experience."""
    _inject_auth_css()

    if st.session_state.pop("session_expired", False):
        st.warning("Your session expired after 12 hours of inactivity. Please sign in again.")

    left_col, right_col = st.columns([60, 40], gap="small")

    # =========================================================================
    # LEFT PANEL — WORKPULSE IDENTITY & WORKFORCE INTELLIGENCE
    # =========================================================================
    with left_col:
        st.html("""
        <div class="wp-ambient-glow-1"></div>
        <div class="wp-ambient-glow-2"></div>
        <div class="wp-ambient-glow-3"></div>
        <div class="wp-brand-hero-panel">
            <!-- Brand Mark & Identity Bar -->
            <div class="wp-brand-topbar">
                <div class="wp-brand-mark-box">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                         stroke="#00D4FF" stroke-width="2.5"
                         stroke-linecap="round" stroke-linejoin="round"
                         style="display: block;">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                    </svg>
                </div>
                <div class="wp-brand-title-wrap">
                    <span class="wp-brand-title">WorkPulse</span>
                    <span class="wp-brand-badge">Enterprise Workforce OS · v2.4</span>
                </div>
            </div>

            <!-- Visual Storytelling Hero Content -->
            <div class="wp-hero-content-body">
                <div class="wp-hero-kicker">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                    </svg>
                    <span>Continuous Performance Governance</span>
                </div>

                <h1 class="wp-hero-headline">
                    Understand People.<br>
                    <span class="wp-gradient-text">Elevate Performance.</span>
                </h1>

                <p class="wp-hero-desc">
                    Bring employee performance, workforce insights and meaningful progress together
                    in one intelligent workspace.
                </p>

                <!-- Workforce Intelligence Visual Composition -->
                <div class="wp-viz-container">
                    <div class="wp-viz-header">
                        <div class="wp-viz-status-pill">
                            <span class="wp-viz-pulse-dot"></span>
                            <span>Q4 Continuous Review Cycle</span>
                        </div>
                        <span class="wp-viz-badge">CALIBRATION ENGINE</span>
                    </div>

                    <!-- Calibrated Talent Matrix Cards -->
                    <div class="wp-talent-matrix">
                        <div class="wp-talent-node">
                            <div class="wp-talent-left">
                                <div class="wp-talent-avatar" style="background: linear-gradient(135deg, #0284C7, #0369A1);">SJ</div>
                                <div class="wp-talent-info">
                                    <div class="wp-talent-name">Sarah Jenkins <span class="wp-talent-role">Staff Engineer</span></div>
                                    <div class="wp-talent-metric">Core Architecture · <strong>4.92 / 5.0</strong></div>
                                </div>
                            </div>
                            <span class="wp-talent-chip top">TOP 5%</span>
                        </div>

                        <div class="wp-talent-node active">
                            <div class="wp-talent-left">
                                <div class="wp-talent-avatar" style="background: linear-gradient(135deg, #6366F1, #4F46E5);">MV</div>
                                <div class="wp-talent-info">
                                    <div class="wp-talent-name">Marcus Vance <span class="wp-talent-role">Product Lead</span></div>
                                    <div class="wp-talent-metric">KPI Delivery · <strong>Velocity +24%</strong></div>
                                </div>
                            </div>
                            <span class="wp-talent-chip progress">CALIBRATED</span>
                        </div>

                        <div class="wp-talent-node">
                            <div class="wp-talent-left">
                                <div class="wp-talent-avatar" style="background: linear-gradient(135deg, #0D9488, #0F766E);">ER</div>
                                <div class="wp-talent-info">
                                    <div class="wp-talent-name">Elena Rostova <span class="wp-talent-role">Lead Analyst</span></div>
                                    <div class="wp-talent-metric">Rubric Consensus · <strong>Aligned</strong></div>
                                </div>
                            </div>
                            <span class="wp-talent-chip aligned">CONSENSUS</span>
                        </div>
                    </div>

                    <!-- Telemetry Data Strip -->
                    <div class="wp-viz-telemetry-row">
                        <div class="wp-viz-telemetry-item">
                            <div class="wp-viz-metric-label">Review Velocity</div>
                            <div class="wp-viz-metric-val">3.4 Days</div>
                            <div class="wp-viz-metric-sub">▲ 42% Faster</div>
                        </div>
                        <div class="wp-viz-telemetry-item">
                            <div class="wp-viz-metric-label">Rubric Fairness</div>
                            <div class="wp-viz-metric-val">99.8%</div>
                            <div class="wp-viz-metric-sub">✓ Validated</div>
                        </div>
                        <div class="wp-viz-telemetry-item">
                            <div class="wp-viz-metric-label">Retention Risk</div>
                            <div class="wp-viz-metric-val">Low</div>
                            <div class="wp-viz-metric-sub">ML Confidence 96%</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Left Footer Trust Anchors -->
            <div class="wp-hero-footer">
                <div class="wp-trust-badges-grid">
                    <span class="wp-trust-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        SOC 2 Type II
                    </span>
                    <span class="wp-trust-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                        bcrypt-12 Storage
                    </span>
                    <span class="wp-trust-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>
                        Zero-Trust RBAC
                    </span>
                    <span class="wp-trust-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                        Audit Trail Logged
                    </span>
                </div>
            </div>
        </div>
        """)

    # =========================================================================
    # RIGHT PANEL — ENTERPRISE AUTHENTICATION PANEL
    # =========================================================================
    with right_col:
        # Check role from query parameters for dynamic context adaptation
        query_role = st.query_params.get("role", "").lower().strip()
        role_demo = {
            "admin": ("admin@workpulse.local", "Admin@WorkPulse2024", "Administrator"),
            "hr": ("hr@workpulse.local", "Hr@WorkPulse2024", "HR Manager"),
            "employee": ("employee@workpulse.local", "Emp@WorkPulse2024", "Employee"),
        }.get(query_role, ("admin@workpulse.local", "Admin@WorkPulse2024", "Administrator"))

        # Default credentials initialization if not yet set
        if "login_email_input" not in st.session_state:
            st.session_state["login_email_input"] = role_demo[0]
        if "login_password_input" not in st.session_state:
            st.session_state["login_password_input"] = role_demo[1]
        if "active_role_badge" not in st.session_state:
            st.session_state["active_role_badge"] = role_demo[2]

        active_badge_label = st.session_state.get("active_role_badge", "Administrator")

        # Top Heading Area with Logo & Enterprise Identity
        st.html(f"""
        <div class="wp-auth-panel-wrapper">
            <div class="wp-auth-top-brand">
                <div class="wp-auth-mini-logo">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00D4FF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                    </svg>
                </div>
                <span class="wp-auth-mini-brand">WorkPulse</span>
                <span class="wp-auth-mini-sep">/</span>
                <span class="wp-auth-mini-label">ENTERPRISE IDENTITY SYSTEM</span>
            </div>
            <div class="wp-auth-card-top">
                <h1 class="wp-auth-header-title">Welcome back</h1>
                <p class="wp-auth-header-sub">Sign in to continue to your workspace.</p>
            </div>
            <div class="wp-role-selector-header">
                <span class="wp-role-selector-title">QUICK EVALUATION PROFILES (1-CLICK FILL)</span>
                <span class="wp-role-active-badge">{escape(active_badge_label)}</span>
            </div>
        </div>
        """)

        # 1-Click Demo Evaluation Profiles Switcher
        col_adm, col_hr, col_emp = st.columns(3)
        with col_adm:
            st.button(
                "🔑 Admin",
                key="btn_quick_admin",
                use_container_width=True,
                help="Autofill Administrator credentials",
                on_click=_on_quick_fill,
                args=("admin@workpulse.local", "Admin@WorkPulse2024", "Administrator"),
            )
        with col_hr:
            st.button(
                "💼 HR Manager",
                key="btn_quick_hr",
                use_container_width=True,
                help="Autofill HR Manager credentials",
                on_click=_on_quick_fill,
                args=("hr@workpulse.local", "Hr@WorkPulse2024", "HR Manager"),
            )
        with col_emp:
            st.button(
                "👤 Employee",
                key="btn_quick_emp",
                use_container_width=True,
                help="Autofill Employee credentials",
                on_click=_on_quick_fill,
                args=("employee@workpulse.local", "Emp@WorkPulse2024", "Employee"),
            )

        # Primary Authentication Form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Work email",
                placeholder="alex.morgan@workpulse.local",
                key="login_email_input",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your account password",
                key="login_password_input",
            )
            remember_me = st.checkbox(
                "Remember this device for 30 days",
                value=st.session_state.get("login_remember_device", True),
                key="login_remember_device",
            )
            submitted = st.form_submit_button(
                "Sign In to WorkPulse",
                type="primary",
                use_container_width=True,
            )

        # Action links row (Forgot password, Create Account, Product Home)
        c_fp, c_reg, c_home = st.columns([1.2, 1.25, 0.95])
        with c_fp:
            if st.button("Forgot password?", key="go_forgot_pw", use_container_width=True):
                st.session_state.auth_page = "forgot_password"
                st.rerun()
        with c_reg:
            if st.button("Request access", key="go_register", use_container_width=True):
                st.session_state.auth_page = "register"
                st.rerun()
        with c_home:
            if st.button("Product Home", key="go_home_from_login", use_container_width=True):
                st.session_state.active_page = "Home"
                st.query_params["page"] = "Home"
                st.rerun()

        # Handle form submission and authentication
        if submitted:
            email_clean = email.strip()
            if not email_clean or not password:
                st.error("Please enter both work email address and password.")
            elif is_rate_limited(email_clean):
                mins = get_lockout_remaining_minutes(email_clean)
                st.error(
                    f"⚠️ Account temporarily locked after repeated failed attempts. "
                    f"Please try again in **{mins} minute(s)**."
                )
            else:
                with st.spinner("Authenticating with WorkPulse Identity Gateway..."):
                    status, user = authenticate_user_with_status(email_clean, password)

                if status == "pending":
                    st.warning(
                        "Your account is awaiting administrator approval. "
                        "You will receive access once the registration is approved."
                    )
                elif status != "success" or user is None:
                    st.error("Invalid credentials. Please verify your work email and password.")
                else:
                    st.session_state.user = user
                    st.session_state.auth_page = None
                    st.session_state.session_started_at = datetime.utcnow()
                    st.session_state.active_page = "Dashboard"
                    st.query_params["page"] = "Dashboard"
                    st.query_params.pop("role", None)
                    st.session_state.pop("show_logout_confirm", None)
                    if user.get("must_change_password"):
                        st.session_state.auth_page = "change_password"
                    st.rerun()

        # Configured Evaluation Accounts Reference Drawer
        st.html("""
        <div class="wp-auth-eval-drawer">
            <div class="wp-auth-eval-head">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2.5"
                     stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                <span>Configured Evaluation Accounts</span>
            </div>
            <div class="wp-auth-eval-item">
                <span class="wp-auth-eval-role">Administrator</span>
                <span class="wp-auth-eval-code">admin@workpulse.local · Admin@WorkPulse2024</span>
            </div>
            <div class="wp-auth-eval-item">
                <span class="wp-auth-eval-role">HR Manager</span>
                <span class="wp-auth-eval-code">hr@workpulse.local · Hr@WorkPulse2024</span>
            </div>
            <div class="wp-auth-eval-item">
                <span class="wp-auth-eval-role">Employee</span>
                <span class="wp-auth-eval-code">employee@workpulse.local · Emp@WorkPulse2024</span>
            </div>
        </div>
        """)


# ---------------------------------------------------------------------------
# Self-service Registration Page
# ---------------------------------------------------------------------------

def render_register_page() -> None:
    """Employee access request. Accounts stay inactive until an admin approves them."""
    _inject_auth_css()

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html("""
        <div class="wp-auth-center-shell">
            <div class="wp-auth-center-card" style="margin-top: 3.5rem;">
                <div class="wp-auth-top-brand" style="margin-bottom: 1rem;">
                    <div class="wp-auth-mini-logo">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D4FF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                        </svg>
                    </div>
                    <span class="wp-auth-mini-brand">WorkPulse</span>
                    <span class="wp-auth-mini-sep">/</span>
                    <span class="wp-auth-mini-label">EMPLOYEE ACCESS REQUEST</span>
                </div>
                <div class="wp-auth-card-top">
                    <h1 class="wp-auth-header-title">Create your account</h1>
                    <p class="wp-auth-header-sub">
                        Register with your work email. Requests are verified and approved by
                        system administrators before workspace access is provisioned.
                    </p>
                </div>
            </div>
        </div>
        """)

        if st.session_state.pop("registration_success", False):
            st.success("Access request submitted successfully. An administrator will review it shortly.")
            st.info(
                "Demo tip: sign in as **admin@workpulse.local** and open **User Management** "
                "to approve the new account."
            )
            if st.button("← Back to Sign In", key="register_done_login", use_container_width=True):
                st.session_state.auth_page = "login"
                st.rerun()
            return

        with st.form("register_form", clear_on_submit=False):
            full_name = st.text_input("Full Name *", placeholder="e.g. Maya Patel")
            email = st.text_input("Work Email *", placeholder="name@workpulse.local")
            employee_code = st.text_input(
                "Employee ID (optional)",
                placeholder="e.g. WP-1001",
                help="Link your existing HR dossier. Leave blank if you do not have an ID yet.",
            )
            c1, c2 = st.columns(2)
            password = c1.text_input("Password *", type="password", placeholder="Minimum 8 characters")
            confirm = c2.text_input("Confirm Password *", type="password")
            submitted = st.form_submit_button(
                "Submit Access Request",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not full_name.strip() or not email.strip():
                st.error("Full name and work email are required.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    register_pending_user(
                        email=email,
                        full_name=full_name,
                        password=password,
                        employee_code=employee_code or None,
                    )
                    st.session_state["registration_success"] = True
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
                except Exception:
                    st.error("Could not submit your request. Please try again.")

        if st.button("Already have an account? Sign In", key="register_back", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Change Password Page (forced on first login)
# ---------------------------------------------------------------------------

def render_change_password_page(user: dict) -> None:
    """Render the forced password-change page for new accounts."""
    _inject_auth_css()

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html("""
        <div class="wp-auth-center-shell">
            <div class="wp-auth-center-card" style="margin-top: 3.5rem;">
                <div class="wp-auth-top-brand" style="margin-bottom: 1rem;">
                    <div class="wp-auth-mini-logo">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D4FF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                        </svg>
                    </div>
                    <span class="wp-auth-mini-brand">WorkPulse</span>
                    <span class="wp-auth-mini-sep">/</span>
                    <span class="wp-auth-mini-label">SECURITY POLICY</span>
                </div>
                <div class="wp-auth-card-top">
                    <h1 class="wp-auth-header-title">Set your new password</h1>
                    <p class="wp-auth-header-sub">
                        Your account requires a password update before workspace access is granted.
                        Choose a strong password with at least 8 characters.
                    </p>
                </div>
            </div>
        </div>
        """)

        with st.form("change_pw_form", clear_on_submit=True):
            new_pw = st.text_input("New Password", type="password", placeholder="Minimum 8 characters")
            confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Repeat your new password")
            submitted = st.form_submit_button("Update Password & Continue →", type="primary", use_container_width=True)

        if submitted:
            if len(new_pw) < 8:
                st.error("Password must be at least 8 characters long.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match. Please try again.")
            else:
                if change_password(user["user_id"], new_pw):
                    st.session_state.user["must_change_password"] = False
                    st.session_state.auth_page = None
                    st.success("✓ Password updated successfully. Redirecting to workspace...")
                    st.rerun()
                else:
                    st.error("Could not update password. Please try again or contact your administrator.")

        st.markdown("")
        if st.button("Sign Out Instead", key="change_pw_logout", use_container_width=True):
            del st.session_state.user
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Forgot Password Page
# ---------------------------------------------------------------------------

def render_forgot_password_page() -> None:
    """Render the forgot-password page with cryptographic reset token generation."""
    _inject_auth_css()

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html("""
        <div class="wp-auth-center-shell">
            <div class="wp-auth-center-card" style="margin-top: 3.5rem;">
                <div class="wp-auth-top-brand" style="margin-bottom: 1rem;">
                    <div class="wp-auth-mini-logo">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D4FF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                        </svg>
                    </div>
                    <span class="wp-auth-mini-brand">WorkPulse</span>
                    <span class="wp-auth-mini-sep">/</span>
                    <span class="wp-auth-mini-label">ACCOUNT RECOVERY</span>
                </div>
                <div class="wp-auth-card-top">
                    <h1 class="wp-auth-header-title">Reset your password</h1>
                    <p class="wp-auth-header-sub">
                        Enter your registered work email. A single-use cryptographic recovery token
                        will be generated for offline workspace access restoration.
                    </p>
                </div>
            </div>
        </div>
        """)

        with st.form("forgot_pw_form", clear_on_submit=True):
            email = st.text_input("Work Email Address", placeholder="name@workpulse.local")
            submitted = st.form_submit_button("Generate Reset Token →", type="primary", use_container_width=True)

        if submitted:
            if not email.strip():
                st.error("Please enter your work email address.")
            else:
                token = generate_password_reset_token(email.strip())
                if token:
                    st.success("✓ Cryptographic reset token generated successfully.")
                    st.code(token, language=None)
                    st.caption(
                        "This single-use token expires in 2 hours. Continue below to set "
                        "your new password."
                    )
                    st.session_state["pending_reset_token"] = token
                    if st.button(
                        "Continue to Set New Password →",
                        type="primary",
                        use_container_width=True,
                        key="forgot_continue",
                    ):
                        st.session_state.auth_page = "reset_password"
                        st.rerun()
                else:
                    st.info(
                        "If that email address is registered, a reset token has been generated. "
                        "Contact your system administrator to retrieve it."
                    )

        st.markdown("")
        if st.button("← Back to Sign In", key="forgot_back", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Password Reset Token Entry Page
# ---------------------------------------------------------------------------

def render_password_reset_page() -> None:
    """Render the page where user enters a reset token to set a new password."""
    _inject_auth_css()

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html("""
        <div class="wp-auth-center-shell">
            <div class="wp-auth-center-card" style="margin-top: 3.5rem;">
                <div class="wp-auth-top-brand" style="margin-bottom: 1rem;">
                    <div class="wp-auth-mini-logo">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D4FF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                        </svg>
                    </div>
                    <span class="wp-auth-mini-brand">WorkPulse</span>
                    <span class="wp-auth-mini-sep">/</span>
                    <span class="wp-auth-mini-label">TOKEN VERIFICATION</span>
                </div>
                <div class="wp-auth-card-top">
                    <h1 class="wp-auth-header-title">Enter reset token</h1>
                    <p class="wp-auth-header-sub">
                        Paste the 64-character token you received to set your new account password.
                    </p>
                </div>
            </div>
        </div>
        """)

        with st.form("reset_token_form", clear_on_submit=False):
            token = st.text_input(
                "Password Reset Token",
                type="password",
                value=st.session_state.get("pending_reset_token", ""),
                placeholder="64-character hex token",
            )
            new_pw = st.text_input("New Password", type="password", placeholder="Minimum 8 characters")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Reset Password & Sign In →", type="primary", use_container_width=True)

        if submitted:
            if not token.strip():
                st.error("Please enter your reset token.")
            elif not new_pw or len(new_pw) < 8:
                st.error("Password must be at least 8 characters long.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match. Please try again.")
            elif not consume_reset_token(token.strip(), new_pw):
                st.error("Invalid or expired token. Please request a new password reset.")
            else:
                st.session_state.pop("pending_reset_token", None)
                st.success("✓ Password reset successfully!")
                st.info("You can now sign in with your new password.")
                if st.button("Go to Login", key="reset_done_login"):
                    st.session_state.auth_page = "login"
                    st.rerun()

        if st.button("← Back to Sign In", key="reset_back", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Logout Confirmation Page
# ---------------------------------------------------------------------------

def render_logout_confirmation_page() -> None:
    """Render logout confirmation dialog before terminating the session."""
    _inject_auth_css()
    user = st.session_state.get("user", {})
    user_name = user.get("full_name", "User").split()[0]

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html(f"""
        <div class="wp-auth-center-shell">
            <div class="wp-auth-center-card" style="margin-top: 5rem; text-align: center;">
                <div style="width: 3.25rem; height: 3.25rem; background: #FFF1F2; border: 1px solid #FECDD3; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem auto; color: #E11D48;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
                    </svg>
                </div>
                <h1 class="wp-auth-header-title" style="margin-bottom: 0.5rem;">Sign out of WorkPulse</h1>
                <p class="wp-auth-header-sub" style="margin-bottom: 1.5rem;">
                    Are you sure you want to end your active workspace session, <strong>{escape(user_name)}</strong>?
                </p>
            </div>
        </div>
        """)

        c_confirm, c_cancel = st.columns([1, 1])
        with c_confirm:
            if st.button("Yes, Sign Out", type="primary", use_container_width=True, key="confirm_signout"):
                if "user" in st.session_state:
                    u_id = st.session_state.user.get("user_id")
                    log_audit(u_id, "LOGOUT", "user", u_id, f"User {st.session_state.user.get('email')} signed out")
                    del st.session_state.user
                st.session_state.auth_page = "login"
                st.session_state.active_page = "Home"
                st.session_state.pop("session_started_at", None)
                st.session_state.pop("show_logout_confirm", None)
                st.rerun()
        with c_cancel:
            if st.button("Cancel", use_container_width=True, key="cancel_signout"):
                st.session_state.pop("show_logout_confirm", None)
                st.rerun()


# ---------------------------------------------------------------------------
# Navigation Link Helpers
# ---------------------------------------------------------------------------

def go_to_home() -> None:
    """Navigate to the Product Home page."""
    st.session_state.active_page = "Home"
    st.query_params["page"] = "Home"
    st.rerun()


def go_to_login() -> None:
    """Navigate to the login page."""
    st.session_state.auth_page = "login"
    st.query_params.clear()
    st.rerun()