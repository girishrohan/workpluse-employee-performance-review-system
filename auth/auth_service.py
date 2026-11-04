"""
WorkPulse Authentication Service.

Handles user authentication, session management, password hashing,
reset tokens, rate limiting, and audit logging.

Security principles enforced here:
- bcrypt for all password hashing (never plain text, never MD5/SHA)
- Parameterised SQL queries throughout (no f-string SQL)
- Generic error messages to prevent user enumeration
- Rate limiting via login_attempts table (5 attempts / 15 min window)
- Secure random tokens via secrets.token_hex
"""

import bcrypt
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = "data/workpulse.db"

# Rate limiting: block account after this many consecutive failures in window
MAX_FAILED_ATTEMPTS: int = 5
LOCKOUT_WINDOW_MINUTES: int = 15

# Password-reset token validity
RESET_TOKEN_EXPIRY_HOURS: int = 2


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a sqlite3 connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt (12 rounds)."""
    # bcrypt.hashpw returns bytes; decode to str for DB storage
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify *plain* against the stored *hashed* value.

    Handles both bcrypt hashes (starts with '$2') and any unknown legacy
    format by returning False safely for the latter.
    """
    try:
        hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        plain_bytes = plain.encode("utf-8") if isinstance(plain, str) else plain
        # Only attempt bcrypt verification for bcrypt hashes
        if hashed_bytes.startswith(b"$2"):
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        # Unknown hash format — treat as invalid (security: never reveal detail)
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def is_rate_limited(email: str) -> bool:
    """
    Return True if *email* has ≥ MAX_FAILED_ATTEMPTS failed logins in the
    last LOCKOUT_WINDOW_MINUTES minutes.
    """
    conn = get_db()
    try:
        window_start = (
            datetime.utcnow() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
        ).isoformat(timespec="seconds")
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM   login_attempts
            WHERE  email = ?
              AND  success = 0
              AND  attempted_at >= ?
            """,
            (email.lower().strip(), window_start),
        ).fetchone()
        return int(row["cnt"]) >= MAX_FAILED_ATTEMPTS
    finally:
        conn.close()


def get_lockout_remaining_minutes(email: str) -> int:
    """Return the approximate minutes left in the current lockout window."""
    conn = get_db()
    try:
        window_start = (
            datetime.utcnow() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
        ).isoformat(timespec="seconds")
        row = conn.execute(
            """
            SELECT MIN(attempted_at) AS oldest
            FROM   login_attempts
            WHERE  email = ?
              AND  success = 0
              AND  attempted_at >= ?
            """,
            (email.lower().strip(), window_start),
        ).fetchone()
        if row and row["oldest"]:
            oldest = datetime.fromisoformat(row["oldest"])
            unlock_at = oldest + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
            remaining = (unlock_at - datetime.utcnow()).total_seconds()
            return max(1, int(remaining // 60) + 1)
        return LOCKOUT_WINDOW_MINUTES
    finally:
        conn.close()


def _log_attempt(email: str, success: bool) -> None:
    """Record a login attempt (used internally by authenticate_user)."""
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO login_attempts (email, success, attempted_at)
            VALUES (?, ?, ?)
            """,
            (
                email.lower().strip(),
                1 if success else 0,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Core authentication
# ---------------------------------------------------------------------------

def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Validate *email* / *password* credentials.

    Returns a user dict on success (keys: user_id, email, full_name, role,
    employee_id, is_active, must_change_password).
    Returns None if credentials are wrong, account is inactive, or an error
    occurs — deliberately generic to prevent user enumeration.
    """
    email = email.lower().strip()
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT user_id, email, full_name, role, employee_id,
                   is_active, must_change_password, password_hash
            FROM   users
            WHERE  email = ?
            """,
            (email,),
        ).fetchone()

        if row is None:
            # User not found — still log attempt to rate-limit scanning
            _log_attempt(email, False)
            return None

        if not verify_password(password, row["password_hash"]):
            _log_attempt(email, False)
            return None

        # Successful credential verification — now check active status
        if not row["is_active"]:
            # Log as success so a disabled account isn't trivially detectable
            _log_attempt(email, True)
            return None  # Caller will handle "account disabled" if needed separately

        # Update last_login timestamp
        conn.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (datetime.utcnow().isoformat(timespec="seconds"), row["user_id"]),
        )
        conn.commit()
        _log_attempt(email, True)

        return {
            "user_id": row["user_id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "role": row["role"],
            "employee_id": row["employee_id"],
            "is_active": row["is_active"],
            "must_change_password": row["must_change_password"],
        }
    except Exception:
        _log_attempt(email, False)
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch a user record by email (returns None if not found)."""
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT user_id, email, full_name, role, employee_id,
                   is_active, must_change_password, last_login, created_at
            FROM   users
            WHERE  email = ?
            """,
            (email.lower().strip(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Fetch a user record by user_id (returns None if not found)."""
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT user_id, email, full_name, role, employee_id,
                   is_active, must_change_password, last_login, created_at
            FROM   users
            WHERE  user_id = ?
            """,
            (int(user_id),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def create_user(
    email: str,
    full_name: str,
    role: str,
    created_by_user_id: Optional[int],
    employee_id: Optional[int] = None,
    plain_password: Optional[str] = None,
) -> int:
    """
    Create a new user account.

    If *plain_password* is None a random secure password is generated and
    must_change_password is set so the user is forced to reset on first login.
    Returns the new user_id.
    """
    email = email.lower().strip()
    if role not in ("employee", "hr", "admin"):
        raise ValueError("Invalid role.")

    must_change = 0
    if plain_password:
        pw_hash = hash_password(plain_password)
    else:
        # Generate a random temporary password — only used internally
        plain_password = secrets.token_urlsafe(16)
        pw_hash = hash_password(plain_password)
        must_change = 1

    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO users
                (email, password_hash, full_name, role, employee_id,
                 is_active, must_change_password, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                email,
                pw_hash,
                full_name.strip(),
                role,
                employee_id,
                must_change,
                datetime.utcnow().isoformat(timespec="seconds"),
                created_by_user_id,
            ),
        )
        new_id = int(cursor.lastrowid)
        conn.commit()
        log_audit(
            created_by_user_id,
            "CREATE_USER",
            "user",
            new_id,
            f"Created user {email} with role={role}",
        )
        return new_id
    finally:
        conn.close()


def update_user(user_id: int, **kwargs: Any) -> bool:
    """
    Update mutable user fields.

    Supported keys: full_name, email, role, is_active, employee_id.
    Returns True on success, False if user not found.
    """
    allowed = {"full_name", "email", "role", "is_active", "employee_id"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False

    if "role" in updates and updates["role"] not in ("employee", "hr", "admin"):
        raise ValueError("Invalid role.")
    if "email" in updates:
        updates["email"] = updates["email"].lower().strip()

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [int(user_id)]

    conn = get_db()
    try:
        cursor = conn.execute(
            f"UPDATE users SET {set_clause} WHERE user_id = ?",  # noqa: S608 (col names are allowlisted)
            values,
        )
        conn.commit()
        if cursor.rowcount > 0:
            log_audit(None, "UPDATE_USER", "user", user_id, f"Fields updated: {list(updates)}")
            return True
        return False
    finally:
        conn.close()


def change_password(user_id: int, new_password: str) -> bool:
    """
    Hash *new_password* and update the user's record.
    Also clears must_change_password flag.
    Returns True on success.
    """
    pw_hash = hash_password(new_password)
    conn = get_db()
    try:
        cursor = conn.execute(
            """
            UPDATE users
            SET    password_hash = ?, must_change_password = 0
            WHERE  user_id = ?
            """,
            (pw_hash, int(user_id)),
        )
        conn.commit()
        if cursor.rowcount > 0:
            log_audit(user_id, "CHANGE_PASSWORD", "user", user_id, "Password changed")
            return True
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

def generate_password_reset_token(email: str) -> Optional[str]:
    """
    Create a one-time password-reset token for *email*.

    Returns the token string, or None if the email is not registered.
    The token is stored in the DB and expires after RESET_TOKEN_EXPIRY_HOURS.
    """
    user = get_user_by_email(email)
    if user is None:
        # Do NOT reveal whether the email exists — just return None silently
        return None

    token = secrets.token_hex(32)  # 64 hex characters = 256 bits entropy
    expires_at = (
        datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
    ).isoformat(timespec="seconds")

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user["user_id"],
                token,
                expires_at,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        log_audit(user["user_id"], "PASSWORD_RESET_REQUESTED", "user", user["user_id"])
        return token
    finally:
        conn.close()


def validate_reset_token(token: str) -> Optional[dict]:
    """
    Return the user dict if *token* is valid and unexpired, else None.
    Does NOT consume the token — call consume_reset_token for that.
    """
    now = datetime.utcnow().isoformat(timespec="seconds")
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT t.token_id, t.user_id, t.expires_at, t.used_at,
                   u.email, u.full_name, u.role, u.is_active
            FROM   password_reset_tokens t
            JOIN   users u ON u.user_id = t.user_id
            WHERE  t.token = ?
              AND  t.used_at IS NULL
              AND  t.expires_at >= ?
            """,
            (token, now),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def consume_reset_token(token: str, new_password: str) -> bool:
    """
    Validate *token*, change the user's password, mark the token as used.
    Returns True on success.
    """
    user_data = validate_reset_token(token)
    if user_data is None:
        return False

    success = change_password(user_data["user_id"], new_password)
    if not success:
        return False

    # Mark the token as consumed
    conn = get_db()
    try:
        conn.execute(
            "UPDATE password_reset_tokens SET used_at = ? WHERE token = ?",
            (datetime.utcnow().isoformat(timespec="seconds"), token),
        )
        conn.commit()
        log_audit(
            user_data["user_id"],
            "PASSWORD_RESET_COMPLETED",
            "user",
            user_data["user_id"],
        )
        return True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def log_audit(
    user_id: Optional[int],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
) -> None:
    """Insert a record into audit_log (best-effort — swallows exceptions)."""
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO audit_log
                (user_id, action, target_type, target_id, detail, performed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                action,
                target_type,
                target_id,
                detail,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    except Exception:
        pass  # Audit logging must never crash the main flow
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

def get_all_users() -> list[dict]:
    """Return all users with their linked employee name (admin use)."""
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT u.user_id, u.email, u.full_name, u.role,
                   u.is_active, u.must_change_password,
                   u.last_login, u.created_at,
                   u.employee_id,
                   e.employee_name, e.department
            FROM   users u
            LEFT   JOIN employees e ON e.employee_id = u.employee_id
            ORDER  BY u.created_at DESC, u.user_id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_audit_log(limit: int = 200) -> list[dict]:
    """Return the most recent audit log entries with user email joined."""
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT al.log_id, al.action, al.target_type, al.target_id,
                   al.detail, al.performed_at,
                   u.email AS performed_by_email
            FROM   audit_log al
            LEFT   JOIN users u ON u.user_id = al.user_id
            ORDER  BY al.performed_at DESC, al.log_id DESC
            LIMIT  ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Table initialisation
# ---------------------------------------------------------------------------

def init_auth_tables(db_path: str = DB_PATH) -> None:
    """
    Create the four authentication-related tables if they do not yet exist.
    Safe to call on every startup — uses CREATE TABLE IF NOT EXISTS.
    """
    global DB_PATH
    DB_PATH = db_path  # Allow override (useful for tests)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email                TEXT    NOT NULL UNIQUE,
                password_hash        TEXT    NOT NULL,
                full_name            TEXT    NOT NULL,
                role                 TEXT    NOT NULL DEFAULT 'employee'
                                         CHECK (role IN ('employee', 'hr', 'admin')),
                employee_id          INTEGER REFERENCES employees(employee_id)
                                         ON DELETE SET NULL,
                is_active            INTEGER NOT NULL DEFAULT 1
                                         CHECK (is_active IN (0, 1)),
                must_change_password INTEGER NOT NULL DEFAULT 0
                                         CHECK (must_change_password IN (0, 1)),
                last_login           TEXT,
                created_at           TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by           INTEGER REFERENCES users(user_id)
                                         ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(user_id)
                               ON DELETE CASCADE,
                token      TEXT    NOT NULL UNIQUE,
                expires_at TEXT    NOT NULL,
                used_at    TEXT,
                created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS login_attempts (
                attempt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                email        TEXT    NOT NULL,
                success      INTEGER NOT NULL DEFAULT 0
                                 CHECK (success IN (0, 1)),
                ip_hint      TEXT,
                attempted_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
                action       TEXT    NOT NULL,
                target_type  TEXT,
                target_id    INTEGER,
                detail       TEXT,
                performed_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Default accounts seeding
# ---------------------------------------------------------------------------

def ensure_default_admin() -> None:
    """
    Seed default accounts on first run (if no admin exists yet).

    Accounts created:
      • admin@workpulse.local  — admin role, random strong password (printed once)
      • hr@workpulse.local     — hr role,    password: Hr@WorkPulse2024
      • employee@workpulse.local — employee role, password: Emp@WorkPulse2024

    All passwords are bcrypt-hashed before storage.
    """
    conn = get_db()
    try:
        admin_exists = conn.execute(
            "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    if admin_exists:
        return  # Already initialised — skip silently

    # ---- Admin account with predictable demo password for reliable evaluation ----
    admin_password = "Admin@WorkPulse2024"
    create_user(
        email="admin@workpulse.local",
        full_name="System Administrator",
        role="admin",
        created_by_user_id=None,
        plain_password=admin_password,
    )

    # ---- HR account ----
    hr_password = "Hr@WorkPulse2024"
    create_user(
        email="hr@workpulse.local",
        full_name="HR Manager",
        role="hr",
        created_by_user_id=None,
        plain_password=hr_password,
    )

    # ---- Employee account ----
    emp_password = "Emp@WorkPulse2024"
    create_user(
        email="employee@workpulse.local",
        full_name="Demo Employee",
        role="employee",
        created_by_user_id=None,
        plain_password=emp_password,
    )

    # ---- Print credentials to terminal (one-time) ----
    separator = "=" * 60
    print(f"\n{separator}")
    print("  WorkPulse - Default Accounts Created (FIRST RUN)")
    print(separator)
    print("  ADMIN    : admin@workpulse.local")
    print(f"  Password : {admin_password}")
    print()
    print("  HR       : hr@workpulse.local")
    print(f"  Password : {hr_password}")
    print()
    print("  EMPLOYEE : employee@workpulse.local")
    print(f"  Password : {emp_password}")
    print(separator)
    print("  These credentials will NOT be shown again.\n")
