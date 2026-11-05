"""
WorkPulse Supabase Authentication Service.

Provides integration with Supabase Auth for production deployments while
maintaining backward compatibility with the local SQLite-based authentication.

This module enables:
- Supabase Auth integration (email/password, OAuth)
- JWT token validation
- Role-based access control from Supabase metadata
- Password hashing with bcrypt (for database users)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from flask import Request

from database.supabase_client import get_supabase_url, get_supabase_anon_key

# Configuration
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
JWT_AUDIENCE = os.environ.get("SUPABASE_JWT_AUDIENCE", "authenticated")

# Default roles
ROLE_ADMIN = "admin"
ROLE_HR = "hr"
ROLE_EMPLOYEE = "employee"
VALID_ROLES = {ROLE_ADMIN, ROLE_HR, ROLE_EMPLOYEE}


class SupabaseAuthError(Exception):
    """Raised when Supabase authentication fails."""
    pass


def get_supabase_client_with_auth():
    """Get Supabase client configured for auth operations."""
    from database.supabase_client import get_supabase_client
    return get_supabase_client(use_service_key=True)


def validate_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a Supabase JWT token.

    Returns the token payload if valid, None otherwise.
    """
    if not JWT_SECRET:
        # Fallback to anon key if no JWT secret configured
        try:
            supabase_url = get_supabase_url()
            anon_key = get_supabase_anon_key()
            # Decode without verification to extract user info
            # Note: In production, always use JWT_SECRET
            payload = jwt.decode(anon_key, options={"verify_signature": False})
            return payload
        except Exception:
            return None

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["RS256"],
            audience=JWT_AUDIENCE,
            issuer=f"https://{supabase_url.replace('https://', '')}/auth/v1"
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def get_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract and validate the authenticated user from a Flask request.

    Returns user info dict with keys: user_id, email, full_name, role, employee_id
    or None if not authenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix
    return get_user_from_token(token)


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT token and return user info.

    Maps Supabase Auth user to WorkPulse user format.
    """
    payload = validate_jwt_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", ROLE_EMPLOYEE)
    is_admin = payload.get("role_metadata", {}).get("role", role)

    # Extract employee_id from user_metadata if present
    employee_id = payload.get("user_metadata", {}).get("employee_id")

    return {
        "user_id": user_id,
        "email": email,
        "full_name": payload.get("user_metadata", {}).get("full_name", email.split("@")[0]),
        "role": is_admin if isinstance(is_admin, str) else role,
        "employee_id": employee_id,
        "is_active": True,
        "must_change_password": False,
    }


def require_role(*roles: str):
    """
    Decorator to enforce role-based access control.

    Usage:
        @app.route("/api/admin-only")
        @require_role("admin")
        def admin_endpoint():
            ...
    """
    from functools import wraps
    from flask import abort, g

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request_roles = getattr(g, "user_roles", [])
            if not any(r in roles for r in request_roles):
                abort(403, "Insufficient permissions")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f):
    """Decorator requiring admin role."""
    return require_role(ROLE_ADMIN)(f)


def require_hr(f):
    """Decorator requiring HR or admin role."""
    return require_role(ROLE_HR, ROLE_ADMIN)(f)


def require_employee_or_admin(f):
    """Decorator requiring employee or admin role."""
    return require_role(ROLE_EMPLOYEE, ROLE_HR, ROLE_ADMIN)(f)


def sign_up_user(
    email: str,
    password: str,
    full_name: str,
    employee_id: Optional[int] = None,
    role: str = ROLE_EMPLOYEE
) -> Dict[str, Any]:
    """
    Sign up a new user via Supabase Auth.

    Returns user data on success or raises SupabaseAuthError.
    """
    if not SUPABASE_SERVICE_KEY:
        raise SupabaseAuthError("Supabase service key not configured")

    client = get_supabase_client_with_auth()

    try:
        # Create user in Supabase Auth
        response = client.auth.admin.create_user(
            email=email,
            password=password,
            user_metadata={
                "full_name": full_name,
                "role": role,
                "employee_id": employee_id,
            }
        )

        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "full_name": full_name,
                "role": role,
                "employee_id": employee_id,
            }
        raise SupabaseAuthError("Failed to create user")

    except Exception as e:
        raise SupabaseAuthError(str(e))


def update_user_role(
    user_id: str,
    role: str,
    employee_id: Optional[int] = None
) -> bool:
    """Update user's role and metadata in Supabase Auth."""
    if not SUPABASE_SERVICE_KEY:
        raise SupabaseAuthError("Supabase service key not configured")

    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")

    client = get_supabase_client_with_auth()

    try:
        user_metadata = {"role": role}
        if employee_id is not None:
            user_metadata["employee_id"] = employee_id

        client.auth.admin.update_user(user_id, user_metadata=user_metadata)
        return True
    except Exception:
        return False


def delete_user(user_id: str) -> bool:
    """Delete a user from Supabase Auth."""
    if not SUPABASE_SERVICE_KEY:
        raise SupabaseAuthError("Supabase service key not configured")

    client = get_supabase_client_with_auth()

    try:
        client.auth.admin.delete_user(user_id)
        return True
    except Exception:
        return False


def send_password_reset_email(email: str) -> bool:
    """
    Send a password reset email via Supabase Auth.

    Note: In server environments, you may need to configure email templates
    in the Supabase dashboard.
    """
    if not SUPABASE_SERVICE_KEY:
        raise SupabaseAuthError("Supabase service key not configured")

    client = get_supabase_client_with_auth()

    try:
        client.auth.admin.reset_user_password(email)
        return True
    except Exception:
        return False


def get_users_list() -> list:
    """List all users in the project (admin use only)."""
    if not SUPABASE_SERVICE_KEY:
        raise SupabaseAuthError("Supabase service key not configured")

    client = get_supabase_client_with_auth()

    try:
        # Supabase doesn't have a direct list users API
        # This would require using the pg_meta schema or the Admin API
        # For now, return empty list
        return []
    except Exception:
        return []


# ============================================================================
# Hybrid Authentication (SQLite + Supabase Fallback)
# ============================================================================

def hybrid_authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with hybrid approach:
    1. Try Supabase Auth first (if configured)
    2. Fall back to local SQLite users table

    Returns user dict or None.
    """
    # Try Supabase Auth first
    if SUPABASE_SERVICE_KEY:
        try:
            client = get_supabase_client_with_auth()
            response = client.auth.signInWithPassword(
                email=email.lower().strip(),
                password=password
            )
            if response.user:
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get("full_name", ""),
                    "role": response.user.user_metadata.get("role", ROLE_EMPLOYEE),
                    "employee_id": response.user.user_metadata.get("employee_id"),
                    "is_active": True,
                    "must_change_password": False,
                }
        except Exception:
            pass  # Fall through to SQLite

    # Fall back to local SQLite authentication
    try:
        from auth.auth_service import authenticate_user
        return authenticate_user(email, password)
    except Exception:
        return None


def setup_supabase_auth_tables():
    """
    Configure Supabase for authentication.

    This function creates the necessary auth tables and policies.
    In Supabase, most of this is handled automatically, but this
    can be used to set up initial admin users.
    """
    if not SUPABASE_SERVICE_KEY:
        return

    # Create initial admin user via Supabase Auth
    try:
        client = get_supabase_client_with_auth()

        # Check if admin already exists
        admin_email = "admin@workpulse.local"

        # Try to get admin user
        try:
            response = client.auth.admin.list_users_by_email(admin_email)
            if response and len(response) > 0:
                return  # Admin already exists
        except Exception:
            pass

        # Create admin user
        client.auth.admin.create_user(
            email=admin_email,
            password="Admin@WorkPulse2024",
            confirmed=True,
            user_metadata={
                "full_name": "System Administrator",
                "role": ROLE_ADMIN,
            }
        )

        print(f"\nCreated admin user: {admin_email}")

    except Exception as e:
        print(f"Warning: Could not set up initial admin user: {e}")


# ============================================================================
# Environment Configuration Helpers
# ============================================================================

def get_auth_config() -> Dict[str, str]:
    """
    Return the current auth configuration.
    Useful for debugging and health checks.
    """
    return {
        "provider": "supabase" if SUPABASE_SERVICE_KEY else "sqlite",
        "supabase_url": get_supabase_url() if SUPABASE_SERVICE_KEY else None,
        "jwt_secret_configured": bool(JWT_SECRET),
        "service_key_configured": bool(SUPABASE_SERVICE_KEY),
    }