"""
WorkPulse — Authentication Views.
Login, Change Password, and Forgot Password pages.
Premium split-screen design matching the WorkPulse SaaS design system.
"""

import streamlit as st
from html import escape

from auth.auth_service import (
    authenticate_user,
    is_rate_limited,
    get_lockout_remaining_minutes,
    change_password,
    generate_password_reset_token,
    validate_reset_token,
    consume_reset_token,
)


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
}

/* Auth layout: use Streamlit columns – style each col */
.wp-auth-left-panel {
    background: #102A43;
    min-height: 100vh;
    padding: 3.5rem 3rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    overflow: hidden;
    font-family: 'Inter', -apple-system, sans-serif;
}

.wp-auth-left-panel::before {
    content: '';
    position: absolute;
    top: -80px;
    right: -80px;
    width: 320px;
    height: 320px;
    background: rgba(22, 140, 131, 0.07);
    border-radius: 50%;
    pointer-events: none;
}

.wp-auth-left-panel::after {
    content: '';
    position: absolute;
    bottom: -40px;
    left: -40px;
    width: 200px;
    height: 200px;
    background: rgba(22, 140, 131, 0.05);
    border-radius: 50%;
    pointer-events: none;
}

.wp-auth-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 3rem;
    position: relative;
    z-index: 1;
}

.wp-auth-brand-mark {
    width: 2.75rem;
    height: 2.75rem;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2DD4BF;
    flex-shrink: 0;
}

.wp-auth-brand-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.025em;
    display: block;
    line-height: 1.1;
}

.wp-auth-brand-pill {
    font-size: 0.6rem;
    font-weight: 700;
    color: #2DD4BF;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    display: block;
}

.wp-auth-headline {
    font-size: 1.9rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.25;
    letter-spacing: -0.03em;
    margin: 0 0 0.875rem 0;
    position: relative;
    z-index: 1;
}

.wp-auth-headline span { color: #2DD4BF; }

.wp-auth-subline {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
    line-height: 1.65;
    margin: 0 0 2.5rem 0;
    position: relative;
    z-index: 1;
}

.wp-auth-features {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    position: relative;
    z-index: 1;
}

.wp-auth-feature-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    color: rgba(255, 255, 255, 0.78);
    font-size: 0.875rem;
    line-height: 1.4;
}

.wp-auth-check {
    width: 1.375rem;
    height: 1.375rem;
    background: rgba(22, 140, 131, 0.25);
    border: 1px solid rgba(45, 212, 191, 0.3);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 0.1rem;
    color: #2DD4BF;
}

.wp-auth-left-footer {
    margin-top: auto;
    padding-top: 2rem;
    position: relative;
    z-index: 1;
}

.wp-auth-left-tagline {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.35);
    letter-spacing: 0.03em;
}

/* Right panel */
.wp-auth-right-panel {
    background: #FAFBFC;
    min-height: 100vh;
    padding: 3.5rem 3rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-family: 'Inter', -apple-system, sans-serif;
}

.wp-auth-form-title {
    font-size: 1.625rem;
    font-weight: 700;
    color: #102A43;
    letter-spacing: -0.025em;
    margin: 0 0 0.375rem 0;
}

.wp-auth-form-sub {
    color: #64748B;
    font-size: 0.875rem;
    margin: 0 0 1.75rem 0;
    line-height: 1.5;
}

.wp-auth-demo-box {
    background: #F0FDFA;
    border: 1px solid #99F6E4;
    border-radius: 10px;
    padding: 1rem 1.125rem;
    margin-top: 1.25rem;
    font-family: 'Inter', sans-serif;
}

.wp-auth-demo-title {
    font-size: 0.6875rem;
    font-weight: 700;
    color: #0F766E;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.625rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.wp-auth-demo-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.3rem 0;
    font-size: 0.8rem;
    color: #134E4A;
    border-bottom: 1px solid rgba(153, 246, 228, 0.35);
}

.wp-auth-demo-row:last-child { border-bottom: none; }

.wp-auth-demo-role {
    font-weight: 600;
    color: #0D9488;
    min-width: 90px;
}

.wp-auth-demo-creds {
    font-size: 0.75rem;
    color: #134E4A;
    text-align: right;
}

/* Streamlit form & button overrides for auth */
[data-testid="stForm"] {
    background: transparent;
    border: none;
    padding: 0;
}

div[data-testid="stFormSubmitButton"] > button {
    background: #102A43 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9375rem !important;
    padding: 0.65rem 1.5rem !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 150ms ease !important;
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background: #1E3A5F !important;
}

/* Auth input styling */
.wp-auth-right-panel input[type="text"],
.wp-auth-right-panel input[type="email"],
.wp-auth-right-panel input[type="password"] {
    border-radius: 8px !important;
    border-color: #E2E8F0 !important;
    font-size: 0.9375rem !important;
}

/* Error / success messages in auth */
.wp-auth-right-panel [data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 0.875rem !important;
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

    left_col, right_col = st.columns([9, 11], gap="small")

    # ---- Left branding panel ----
    with left_col:
        st.html("""
        <div class="wp-auth-left-panel">
            <div class="wp-auth-brand">
                <div class="wp-auth-brand-mark">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2.5"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                </div>
                <div>
                    <span class="wp-auth-brand-name">WorkPulse</span>
                    <span class="wp-auth-brand-pill">People Analytics</span>
                </div>
            </div>

            <h1 class="wp-auth-headline">
                Understand Performance.<br>
                <span>Empower Growth.</span>
            </h1>

            <p class="wp-auth-subline">
                Bring employee reviews, performance analytics, and actionable
                insights together in one clear workspace.
            </p>

            <ul class="wp-auth-features">
                <li class="wp-auth-feature-item">
                    <div class="wp-auth-check">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="3"
                             stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </div>
                    <span>Weighted KPI framework with real-time score calculation</span>
                </li>
                <li class="wp-auth-feature-item">
                    <div class="wp-auth-check">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="3"
                             stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </div>
                    <span>Department analytics with Plotly visualizations</span>
                </li>
                <li class="wp-auth-feature-item">
                    <div class="wp-auth-check">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="3"
                             stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </div>
                    <span>Decision Tree &amp; Random Forest ML predictions</span>
                </li>
                <li class="wp-auth-feature-item">
                    <div class="wp-auth-check">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="3"
                             stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </div>
                    <span>Role-based access for Admin, HR, and Employee</span>
                </li>
            </ul>

            <div class="wp-auth-left-footer">
                <span class="wp-auth-left-tagline">
                    Local SQLite · bcrypt-secured · Zero vendor lock-in
                </span>
            </div>
        </div>
        """)

    # ---- Right form panel ----
    with right_col:
        # Check if a specific role is requested via query params or session state
        query_role = st.query_params.get("role", "").lower().strip()
        role_titles = {
            "admin": ("Admin Portal", "System administration and configuration access"),
            "hr": ("HR Manager Sign In", "Review workflows, evaluations, and workforce analytics"),
            "employee": ("Employee Sign In", "View your performance dossier, reviews, and goals"),
        }
        title_text, sub_text = role_titles.get(
            query_role,
            ("Sign in to WorkPulse", "Enter your credentials to access the workspace."),
        )

        st.html(f"""
        <div class="wp-auth-right-panel" style="padding-bottom:0.5rem; min-height:auto;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <span style="font-size:0.75rem; font-weight:700; color:var(--wp-teal); letter-spacing:0.08em; text-transform:uppercase;">SECURE LOGIN</span>
                <a href="?page=Home" target="_self" style="font-size:0.8125rem; color:#64748B; text-decoration:none; font-weight:500;">← Back to Home</a>
            </div>
            <h1 class="wp-auth-form-title">{title_text}</h1>
            <p class="wp-auth-form-sub">{sub_text}</p>
        </div>
        """)

        # Role switcher tabs
        role_tab = st.radio(
            "Select Login Role",
            options=["All Roles", "Admin Portal", "HR Manager", "Employee"],
            horizontal=True,
            label_visibility="collapsed",
            key="login_role_tab",
        )

        # Quick demo credential autofill helpers
        if "login_email_val" not in st.session_state:
            st.session_state.login_email_val = "admin@workpulse.local"
        if "login_pw_val" not in st.session_state:
            st.session_state.login_pw_val = "Admin@WorkPulse2024"

        # Update defaults based on selected tab if changed
        if role_tab == "Admin Portal" and st.session_state.get("_last_tab") != "Admin Portal":
            st.session_state.login_email_val = "admin@workpulse.local"
            st.session_state.login_pw_val = "Admin@WorkPulse2024"
            st.session_state._last_tab = "Admin Portal"
        elif role_tab == "HR Manager" and st.session_state.get("_last_tab") != "HR Manager":
            st.session_state.login_email_val = "hr@workpulse.local"
            st.session_state.login_pw_val = "Hr@WorkPulse2024"
            st.session_state._last_tab = "HR Manager"
        elif role_tab == "Employee" and st.session_state.get("_last_tab") != "Employee":
            st.session_state.login_email_val = "employee@workpulse.local"
            st.session_state.login_pw_val = "Emp@WorkPulse2024"
            st.session_state._last_tab = "Employee"
        elif role_tab == "All Roles" and st.session_state.get("_last_tab") not in ("All Roles", None):
            st.session_state._last_tab = "All Roles"

        # Streamlit login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("login_email_val", ""),
                placeholder="you@workpulse.local",
                key="login_email_input",
            )
            password = st.text_input(
                "Password",
                type="password",
                value=st.session_state.get("login_pw_val", ""),
                placeholder="Enter your password",
                key="login_password_input",
            )
            remember = st.checkbox("Remember me on this browser", value=True, key="login_remember")
            submitted = st.form_submit_button(
                "Sign In to Workspace",
                type="primary",
                use_container_width=True,
            )

        # Action links row
        c_fp, c_home = st.columns([1.2, 1])
        with c_fp:
            if st.button("Forgot password?", key="go_forgot_pw"):
                st.session_state.auth_page = "forgot_password"
                st.rerun()
        with c_home:
            if st.button("🌐 Product Home", key="go_home_from_login"):
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
                user = authenticate_user(email.strip(), password)
                if user is None:
                    st.error("Invalid credentials. Please verify your email and password.")
                else:
                    st.session_state.user = user
                    st.session_state.auth_page = None
                    if user.get("must_change_password"):
                        st.session_state.auth_page = "change_password"
                    st.rerun()

        # Demo credentials box with 1-click fill buttons
        st.html("""
        <div class="wp-auth-demo-box">
            <div class="wp-auth-demo-title">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                     stroke="#0F766E" stroke-width="2.5"
                     stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                Demo Credentials — Click below or use pre-filled values
            </div>
            <div class="wp-auth-demo-row">
                <span class="wp-auth-demo-role">Admin</span>
                <span class="wp-auth-demo-creds">admin@workpulse.local · <code>Admin@WorkPulse2024</code></span>
            </div>
            <div class="wp-auth-demo-row">
                <span class="wp-auth-demo-role">HR Manager</span>
                <span class="wp-auth-demo-creds">hr@workpulse.local · <code>Hr@WorkPulse2024</code></span>
            </div>
            <div class="wp-auth-demo-row">
                <span class="wp-auth-demo-role">Employee</span>
                <span class="wp-auth-demo-creds">employee@workpulse.local · <code>Emp@WorkPulse2024</code></span>
            </div>
        </div>
        """)


# ---------------------------------------------------------------------------
# Change Password Page (forced on first login)
# ---------------------------------------------------------------------------

def render_change_password_page(user: dict) -> None:
    """Render the forced password-change page for new accounts."""
    _inject_auth_css()

    st.html("""
    <div class="wp-auth-right-panel" style="min-height:auto; padding:2rem 0 1rem 0;">
        <h1 class="wp-auth-form-title">Set Your New Password</h1>
        <p class="wp-auth-form-sub">
            Your account requires a password change before you can access the workspace.
            Choose a strong password of at least 8 characters.
        </p>
    </div>
    """)

    with st.form("change_pw_form", clear_on_submit=True):
        new_pw = st.text_input("New Password", type="password", placeholder="Minimum 8 characters")
        confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Repeat your new password")
        submitted = st.form_submit_button("Update Password & Continue", type="primary", use_container_width=True)

    if submitted:
        if len(new_pw) < 8:
            st.error("Password must be at least 8 characters long.")
        elif new_pw != confirm_pw:
            st.error("Passwords do not match. Please try again.")
        else:
            if change_password(user["user_id"], new_pw):
                # Clear the flag in session state
                st.session_state.user["must_change_password"] = False
                st.session_state.auth_page = None
                st.success("✓ Password updated successfully. Taking you to your workspace...")
                st.rerun()
            else:
                st.error("Could not update password. Please try again or contact your administrator.")

    # Logout option
    st.markdown("")
    if st.button("Sign Out Instead", key="change_pw_logout"):
        del st.session_state.user
        st.session_state.auth_page = "login"
        st.rerun()


# ---------------------------------------------------------------------------
# Forgot Password Page
# ---------------------------------------------------------------------------

def render_forgot_password_page() -> None:
    """Render the forgot-password page (local token display — no email server)."""
    _inject_auth_css()

    st.html("""
    <div class="wp-auth-right-panel" style="min-height:auto; padding:2rem 0 1rem 0;">
        <h1 class="wp-auth-form-title">Reset Your Password</h1>
        <p class="wp-auth-form-sub">
            Enter the email address associated with your account. A one-time reset token
            will be generated and displayed below (this application runs locally without
            an email server).
        </p>
    </div>
    """)

    with st.form("forgot_pw_form", clear_on_submit=True):
        email = st.text_input("Email address", placeholder="you@workpulse.local")
        submitted = st.form_submit_button("Generate Reset Token", type="primary", use_container_width=True)

    if submitted:
        if not email.strip():
            st.error("Please enter your email address.")
        else:
            token = generate_password_reset_token(email.strip())
            if token:
                st.success("✓ Reset token generated successfully.")
                st.info(
                    f"**Your password reset token:**\n\n"
                    f"```\n{token}\n```\n\n"
                    f"This token expires in **2 hours**. "
                    f"Share it with your administrator to complete the password reset, "
                    f"or use the admin panel to apply it directly."
                )
            else:
                # Generic message to prevent email enumeration
                st.info(
                    "If that email address is registered, a reset token has been generated. "
                    "Contact your system administrator to retrieve it."
                )

    st.markdown("")
    if st.button("← Back to Sign In", key="forgot_back"):
        st.session_state.auth_page = "login"
        st.rerun()


# ---------------------------------------------------------------------------
# Password Reset Token Entry Page
# ---------------------------------------------------------------------------

def render_password_reset_page() -> None:
    """Render the page where user enters a reset token to set a new password."""
    _inject_auth_css()

    st.html("""
    <div class="wp-auth-right-panel" style="min-height:auto; padding:2rem 0 1rem 0;">
        <h1 class="wp-auth-form-title">Reset Your Password</h1>
        <p class="wp-auth-form-sub">
            Enter the password reset token you received to set a new password.
        </p>
    </div>
    """)

    with st.form("reset_token_form", clear_on_submit=False):
        token = st.text_input(
            "Password Reset Token",
            type="password",
            placeholder="64-character hex token",
        )
        new_pw = st.text_input("New Password", type="password", placeholder="Minimum 8 characters")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Reset Password", type="primary", use_container_width=True)

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
            st.success("✓ Password reset successfully!")
            st.info("You can now sign in with your new password.")
            if st.button("Go to Login", key="reset_done_login"):
                st.session_state.auth_page = "login"
                st.rerun()

    if st.button("← Back to Sign In", key="reset_back"):
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

    st.html(f"""
    <div class="wp-auth-right-panel" style="min-height:auto; padding:2rem 0 1rem 0;">
        <h1 class="wp-auth-form-title">Sign Out</h1>
        <p class="wp-auth-form-sub">
            Are you sure you want to sign out, {user_name}?
        </p>
    </div>
    """)

    c_confirm, c_cancel = st.columns([1.2, 1])
    with c_confirm:
        if st.button("Yes, Sign Out", type="primary", use_container_width=True, key="confirm_signout"):
            if "user" in st.session_state:
                u_id = st.session_state.user.get("user_id")
                log_audit(u_id, "LOGOUT", "user", u_id, f"User {st.session_state.user.get('email')} signed out")
                del st.session_state.user
            st.session_state.auth_page = "login"
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
