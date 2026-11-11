"""
WorkPulse — Authentication Views.
Login, Change Password, and Forgot Password pages.
Premium split-screen design matching the WorkPulse SaaS design system.
"""

from datetime import datetime

import streamlit as st
from html import escape

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


def _on_quick_fill(email: str, password: str) -> None:
    """Widget callback: prefill demo credentials before the form rerenders."""
    st.session_state["login_email_input"] = email
    st.session_state["login_password_input"] = password


# ---------------------------------------------------------------------------
# CSS Injection
# ---------------------------------------------------------------------------

_AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Hide default Streamlit chrome on auth pages */
[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }

[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    padding: 0 !important;
}

[data-testid="stAppViewContainer"] > .main {
    padding: 0 !important;
    background: #F8FAFC !important;
}

[data-testid="stAppViewContainer"] {
    background: #F8FAFC !important;
}

/* Auth split screen grid/columns */
[data-testid="stHorizontalBlock"] {
    min-height: 100vh;
    gap: 0 !important;
}

/* Left Branding Panel */
.wp-auth-left-panel {
    background: linear-gradient(145deg, #0B1D30 0%, #102A43 55%, #153E5C 100%);
    min-height: 100vh;
    padding: 3.5rem 3.5rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    color: #FFFFFF;
    box-sizing: border-box;
}

.wp-auth-left-panel::before {
    content: '';
    position: absolute;
    top: -120px;
    right: -120px;
    width: 380px;
    height: 380px;
    background: radial-gradient(circle, rgba(45, 212, 191, 0.12) 0%, rgba(22, 140, 131, 0) 70%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 1;
}

.wp-auth-left-panel::after {
    content: '';
    position: absolute;
    bottom: -80px;
    left: -80px;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(22, 140, 131, 0.15) 0%, rgba(16, 42, 67, 0) 70%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 1;
}

.wp-auth-brand {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    position: relative;
    z-index: 2;
    margin-bottom: 2rem;
}

.wp-auth-brand-mark {
    width: 2.85rem;
    height: 2.85rem;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2DD4BF;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    flex-shrink: 0;
}

.wp-auth-brand-name {
    font-size: 1.35rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.025em;
    line-height: 1.1;
    display: block;
}

.wp-auth-brand-pill {
    font-size: 0.65rem;
    font-weight: 700;
    color: #2DD4BF;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    display: block;
    margin-top: 0.15rem;
}

.wp-auth-content-wrap {
    position: relative;
    z-index: 2;
    margin: auto 0;
    padding: 1rem 0;
}

.wp-auth-tag {
    display: inline-block;
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #2DD4BF;
    text-transform: uppercase;
    background: rgba(45, 212, 191, 0.12);
    border: 1px solid rgba(45, 212, 191, 0.25);
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    margin-bottom: 1rem;
}

.wp-auth-headline {
    font-size: 2.15rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.2;
    letter-spacing: -0.03em;
    margin: 0 0 1rem 0;
}

.wp-auth-headline span {
    color: #2DD4BF;
}

.wp-auth-subline {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0 0 2.25rem 0;
    max-width: 480px;
}

.wp-auth-features {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.wp-auth-feature-item {
    display: flex;
    align-items: flex-start;
    gap: 0.875rem;
}

.wp-auth-check {
    width: 1.5rem;
    height: 1.5rem;
    background: rgba(22, 140, 131, 0.35);
    border: 1px solid rgba(45, 212, 191, 0.45);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2DD4BF;
    flex-shrink: 0;
    margin-top: 0.15rem;
}

.wp-auth-feature-item strong {
    display: block;
    font-size: 0.9rem;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 0.15rem;
}

.wp-auth-feature-item p {
    font-size: 0.8125rem;
    color: rgba(255, 255, 255, 0.65);
    margin: 0;
    line-height: 1.45;
}

.wp-auth-left-footer {
    position: relative;
    z-index: 2;
    padding-top: 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.wp-auth-trust-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 1.25rem;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.55);
    font-weight: 500;
}

/* Right Panel & Card Container */
.wp-auth-right-container {
    padding: 2.5rem 3rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 100vh;
    box-sizing: border-box;
}

.wp-auth-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 2.25rem 2.5rem;
    box-shadow: 0 10px 25px -5px rgba(16, 42, 67, 0.08), 0 8px 10px -6px rgba(16, 42, 67, 0.04);
    width: 100%;
    max-width: 520px;
    margin: 0 auto;
    box-sizing: border-box;
}

.wp-auth-card-header {
    margin-bottom: 1.25rem;
}

.wp-auth-top-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.wp-auth-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.6875rem;
    font-weight: 700;
    color: #168C83;
    background: #EBF7F6;
    border: 1px solid #99F6E4;
    padding: 0.2rem 0.55rem;
    border-radius: 9999px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.wp-auth-title {
    font-size: 1.625rem;
    font-weight: 800;
    color: #102A43;
    letter-spacing: -0.025em;
    margin: 0 0 0.35rem 0;
}

.wp-auth-sub {
    font-size: 0.875rem;
    color: #64748B;
    margin: 0;
    line-height: 1.5;
}

.wp-auth-quick-label {
    font-size: 0.6875rem;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 1.25rem 0 0.5rem 0;
}

/* Streamlit Input Styling inside Auth */
div[data-testid="stTextInput"] input {
    height: 46px !important;
    background: #F8FAFC !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    padding: 0 1rem !important;
    font-size: 0.9375rem !important;
    color: #0F172A !important;
    transition: all 140ms ease !important;
}

div[data-testid="stTextInput"] input:focus {
    background: #FFFFFF !important;
    border-color: #168C83 !important;
    box-shadow: 0 0 0 3px rgba(22, 140, 131, 0.16) !important;
}

div[data-testid="stTextInput"] label {
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    margin-bottom: 0.25rem !important;
}

/* Submit Button */
div[data-testid="stFormSubmitButton"] > button {
    height: 48px !important;
    background: linear-gradient(135deg, #102A43 0%, #168C83 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 12px rgba(16, 42, 67, 0.2) !important;
    transition: all 150ms ease !important;
    margin-top: 0.5rem !important;
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #0B1D30 0%, #0E7C7B 100%) !important;
    box-shadow: 0 6px 16px rgba(16, 42, 67, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* Quick Fill Buttons */
div.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.8125rem !important;
    transition: all 140ms ease !important;
}

/* Standalone Center Card for Forgot/Reset Pages */
.wp-auth-center-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 10px 25px -5px rgba(16, 42, 67, 0.08), 0 8px 10px -6px rgba(16, 42, 67, 0.04);
    max-width: 480px;
    margin: 4rem auto;
    box-sizing: border-box;
}

/* Demo Credentials Table */
.wp-auth-demo-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.875rem 1rem;
    margin-top: 1.25rem;
}

.wp-auth-demo-card-head {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.6875rem;
    font-weight: 700;
    color: #168C83;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}

.wp-auth-demo-card-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.35rem 0;
    border-bottom: 1px solid #EDF2F7;
    font-size: 0.75rem;
}

.wp-auth-demo-card-item:last-child {
    border-bottom: none;
}

.wp-auth-demo-role-tag {
    font-weight: 600;
    color: #0F172A;
}

.wp-auth-demo-code {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.72rem;
    color: #475569;
    background: #FFFFFF;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    border: 1px solid #E2E8F0;
}

/* Responsive adjustments */
@media (max-width: 992px) {
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }
    .wp-auth-left-panel {
        min-height: auto !important;
        padding: 2.5rem 1.75rem !important;
    }
    .wp-auth-right-container {
        min-height: auto !important;
        padding: 2rem 1rem !important;
    }
    .wp-auth-card {
        padding: 1.75rem !important;
    }
}
</style>
"""


def _inject_auth_css() -> None:
    """Inject full-screen auth page CSS."""
    st.html(_AUTH_CSS)


# ---------------------------------------------------------------------------
# Login Page
# ---------------------------------------------------------------------------

def render_login_page() -> None:
    """Render the premium split-screen WorkPulse login page."""
    _inject_auth_css()

    if st.session_state.pop("session_expired", False):
        st.warning("Your session expired after 12 hours of inactivity. Please sign in again.")

    left_col, right_col = st.columns([10, 11], gap="medium")

    # ---- Left branding panel ----
    with left_col:
        st.html("""
        <div class="wp-auth-left-panel">
            <div class="wp-auth-brand">
                <div class="wp-auth-brand-mark">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                         stroke="#2DD4BF" stroke-width="2.5"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                </div>
                <div>
                    <span class="wp-auth-brand-name">WorkPulse</span>
                    <span class="wp-auth-brand-pill">Enterprise People Analytics</span>
                </div>
            </div>

            <div class="wp-auth-content-wrap">
                <div class="wp-auth-tag">WORKFORCE INTELLIGENCE PLATFORM</div>
                <h1 class="wp-auth-headline">
                    Understand Performance.<br>
                    <span>Empower Growth.</span>
                </h1>

                <p class="wp-auth-subline">
                    Bring review cycles, weighted KPI rubrics, and explainable ML insights
                    together in one unified, high-integrity executive workspace.
                </p>

                <ul class="wp-auth-features">
                    <li class="wp-auth-feature-item">
                        <div class="wp-auth-check">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                                 stroke="currentColor" stroke-width="3"
                                 stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <div>
                            <strong>Weighted KPI Rubrics</strong>
                            <p>Real-time scoring across core competencies and project metrics.</p>
                        </div>
                    </li>
                    <li class="wp-auth-feature-item">
                        <div class="wp-auth-check">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                                 stroke="currentColor" stroke-width="3"
                                 stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <div>
                            <strong>Transparent ML Forecasting</strong>
                            <p>Decision Tree and Random Forest models with held-out splits.</p>
                        </div>
                    </li>
                    <li class="wp-auth-feature-item">
                        <div class="wp-auth-check">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                                 stroke="currentColor" stroke-width="3"
                                 stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <div>
                            <strong>Role-Based Access Control</strong>
                            <p>Tailored portals and strict permission boundaries for Admin, HR, and Staff.</p>
                        </div>
                    </li>
                </ul>
            </div>

            <div class="wp-auth-left-footer">
                <div class="wp-auth-trust-badges">
                    <span>🔒 bcrypt Encryption</span>
                    <span>⚡ Local SQLite Engine</span>
                    <span>🛡️ Full Audit Logging</span>
                </div>
            </div>
        </div>
        """)

    # ---- Right form panel ----
    with right_col:
        # Check role from query parameters
        query_role = st.query_params.get("role", "").lower().strip()
        role_titles = {
            "admin": ("Admin Portal Sign In", "System administration and configuration access"),
            "hr": ("HR Manager Sign In", "Review workflows, evaluations, and workforce analytics"),
            "employee": ("Employee Portal Sign In", "Access personal dossier, reviews, and KPI scores"),
        }

        # Default credentials initialization if not yet set
        role_demo = {
            "admin": ("admin@workpulse.local", "Admin@WorkPulse2024"),
            "hr": ("hr@workpulse.local", "Hr@WorkPulse2024"),
            "employee": ("employee@workpulse.local", "Emp@WorkPulse2024"),
        }.get(query_role, ("admin@workpulse.local", "Admin@WorkPulse2024"))
        if "login_email_input" not in st.session_state:
            st.session_state["login_email_input"] = role_demo[0]
        if "login_password_input" not in st.session_state:
            st.session_state["login_password_input"] = role_demo[1]
        title_text, sub_text = role_titles.get(
            query_role,
            ("Sign in to WorkPulse", "Enter your credentials to access your organization's workspace."),
        )

        st.html(f"""
        <div class="wp-auth-card-header">
            <div class="wp-auth-top-meta">
                <span class="wp-auth-pill">SECURE WORKSPACE LOGIN</span>
            </div>
            <h1 class="wp-auth-title">{title_text}</h1>
            <p class="wp-auth-sub">{sub_text}</p>
        </div>
        """)

        # 1-Click Demo Profile Switcher
        st.markdown('<div class="wp-auth-quick-label">QUICK EVALUATION PROFILES (1-CLICK FILL)</div>', unsafe_allow_html=True)
        col_adm, col_hr, col_emp = st.columns(3)
        with col_adm:
            st.button(
                "🔑 Admin",
                key="btn_quick_admin",
                use_container_width=True,
                help="Autofill Administrator credentials",
                on_click=_on_quick_fill,
                args=("admin@workpulse.local", "Admin@WorkPulse2024"),
            )
        with col_hr:
            st.button(
                "💼 HR Manager",
                key="btn_quick_hr",
                use_container_width=True,
                help="Autofill HR Manager credentials",
                on_click=_on_quick_fill,
                args=("hr@workpulse.local", "Hr@WorkPulse2024"),
            )
        with col_emp:
            st.button(
                "👤 Employee",
                key="btn_quick_emp",
                use_container_width=True,
                help="Autofill Employee credentials",
                on_click=_on_quick_fill,
                args=("employee@workpulse.local", "Emp@WorkPulse2024"),
            )

        # Streamlit login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Work Email Address",
                placeholder="name@workpulse.local",
                key="login_email_input",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your account password",
                key="login_password_input",
            )
            submitted = st.form_submit_button(
                "Sign In to Workspace →",
                type="primary",
                use_container_width=True,
            )

        # Action links row
        c_fp, c_reg, c_home = st.columns([1.25, 1.15, 1])
        with c_fp:
            if st.button(":material/key: Forgot password?", key="go_forgot_pw", use_container_width=True):
                st.session_state.auth_page = "forgot_password"
                st.rerun()
        with c_reg:
            if st.button(":material/person_add: Create account", key="go_register", use_container_width=True):
                st.session_state.auth_page = "register"
                st.rerun()
        with c_home:
            if st.button(":material/home: Product Home", key="go_home_from_login", use_container_width=True):
                st.session_state.active_page = "Home"
                st.query_params["page"] = "Home"
                st.rerun()

        # Handle form submission
        if submitted:
            if not email.strip() or not password:
                st.error("Please enter both email address and password.")
            elif is_rate_limited(email.strip()):
                mins = get_lockout_remaining_minutes(email.strip())
                st.error(
                    f"⚠️ Account temporarily locked after repeated failed attempts. "
                    f"Please try again in **{mins} minute(s)**."
                )
            else:
                status, user = authenticate_user_with_status(email.strip(), password)
                if status == "pending":
                    st.warning(
                        "Your account is awaiting administrator approval. "
                        "You will be able to sign in once access has been granted."
                    )
                elif status != "success" or user is None:
                    st.error("Invalid credentials. Please verify your email and password.")
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

        # Demo credentials reference card
        st.html("""
        <div class="wp-auth-demo-card">
            <div class="wp-auth-demo-card-head">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                     stroke="#0F766E" stroke-width="2.5"
                     stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                <span>Configured Evaluation Accounts</span>
            </div>
            <div class="wp-auth-demo-card-item">
                <span class="wp-auth-demo-role-tag">Admin:</span>
                <span class="wp-auth-demo-code">admin@workpulse.local · Admin@WorkPulse2024</span>
            </div>
            <div class="wp-auth-demo-card-item">
                <span class="wp-auth-demo-role-tag">HR Manager:</span>
                <span class="wp-auth-demo-code">hr@workpulse.local · Hr@WorkPulse2024</span>
            </div>
            <div class="wp-auth-demo-card-item">
                <span class="wp-auth-demo-role-tag">Employee:</span>
                <span class="wp-auth-demo-code">employee@workpulse.local · Emp@WorkPulse2024</span>
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
        <div class="wp-auth-card" style="margin-top: 2.5rem;">
            <div class="wp-auth-card-header">
                <span class="wp-auth-pill">EMPLOYEE ACCESS REQUEST</span>
                <h1 class="wp-auth-title" style="margin-top:0.5rem;">Create your WorkPulse account</h1>
                <p class="wp-auth-sub">
                    Register with your work email. Your request is reviewed by an administrator
                    before workspace access is enabled.
                </p>
            </div>
        </div>
        """)

        if st.session_state.pop("registration_success", False):
            st.success("Access request submitted. An administrator will review it shortly.")
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
            email = st.text_input("Work Email *", placeholder="name@company.com")
            employee_code = st.text_input(
                "Employee ID (optional)",
                placeholder="e.g. WP-1001",
                help="Link your existing HR profile. Leave blank if you do not have an ID yet.",
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
        <div class="wp-auth-card" style="margin-top: 3rem;">
            <div class="wp-auth-card-header">
                <span class="wp-auth-pill">SECURITY POLICY</span>
                <h1 class="wp-auth-title" style="margin-top:0.5rem;">Set Your New Password</h1>
                <p class="wp-auth-sub">
                    Your account requires a password change before accessing the workspace.
                    Choose a strong password with at least 8 characters.
                </p>
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
                    st.success("✓ Password updated successfully. Taking you to your workspace...")
                    st.rerun()
                else:
                    st.error("Could not update password. Please try again or contact your administrator.")

        # Logout option
        st.markdown("")
        if st.button("Sign Out Instead", key="change_pw_logout", use_container_width=True):
            del st.session_state.user
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Forgot Password Page
# ---------------------------------------------------------------------------

def render_forgot_password_page() -> None:
    """Render the forgot-password page (local token display — no email server)."""
    _inject_auth_css()

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html("""
        <div class="wp-auth-card" style="margin-top: 3rem;">
            <div class="wp-auth-card-header">
                <span class="wp-auth-pill">ACCOUNT RECOVERY</span>
                <h1 class="wp-auth-title" style="margin-top:0.5rem;">Reset Your Password</h1>
                <p class="wp-auth-sub">
                    Enter the email address associated with your account. A one-time reset token
                    will be generated locally for offline workspace recovery.
                </p>
            </div>
        </div>
        """)

        with st.form("forgot_pw_form", clear_on_submit=True):
            email = st.text_input("Email address", placeholder="you@workpulse.local")
            submitted = st.form_submit_button("Generate Reset Token →", type="primary", use_container_width=True)

        if submitted:
            if not email.strip():
                st.error("Please enter your email address.")
            else:
                token = generate_password_reset_token(email.strip())
                if token:
                    st.success("✓ Reset token generated successfully.")
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
        if st.button(":material/arrow_back: Back to Sign In", key="forgot_back", use_container_width=True):
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
        <div class="wp-auth-card" style="margin-top: 3rem;">
            <div class="wp-auth-card-header">
                <span class="wp-auth-pill">TOKEN VERIFICATION</span>
                <h1 class="wp-auth-title" style="margin-top:0.5rem;">Enter Reset Token</h1>
                <p class="wp-auth-sub">
                    Enter the cryptographic reset token you received to set a new password.
                </p>
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

        if st.button(":material/arrow_back: Back to Sign In", key="reset_back", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Logout Confirmation Page
# ---------------------------------------------------------------------------

def render_logout_confirmation_page() -> None:
    """Render logout confirmation before signing out."""
    _inject_auth_css()
    user = st.session_state.get("user", {})
    user_name = user.get("full_name", "User").split()[0]

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.html(f"""
        <div class="wp-auth-card" style="margin-top: 5rem; text-align: center;">
            <div style="width: 3rem; height: 3rem; background: #FFF1F2; border: 1px solid #FECDD3; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto; color: #E11D48;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
            </div>
            <h1 class="wp-auth-title">Sign Out</h1>
            <p class="wp-auth-sub">
                Are you sure you want to sign out of WorkPulse, <strong>{escape(user_name)}</strong>?
            </p>
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
# Navigation Link Helper
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
