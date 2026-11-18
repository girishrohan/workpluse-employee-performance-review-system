#!/usr/bin/env python3
"""
WorkPulse - Supabase Auth User Seeding Script

Seeds default admin, HR, and employee accounts into Supabase Auth.
Run this after setting up Supabase schema and configuring environment variables.

Usage:
    python scripts/seed_supabase_auth.py

Environment variables required:
    SUPABASE_URL - Your Supabase project URL (e.g., https://xyz.supabase.co)
    SUPABASE_SERVICE_KEY - Service role key (NOT the anon key)

Optional:
    SUPABASE_ANON_KEY - Anon key (for client-side operations)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass  # dotenv not installed, rely on system env vars

try:
    from supabase import create_client
except ImportError:
    print("[ERROR] supabase package not installed. Run: pip install supabase")
    sys.exit(1)

# Default accounts to seed (matching SQLite defaults from auth/auth_service.py)
DEFAULT_ACCOUNTS = [
    {
        "email": "admin@workpulse.local",
        "password": "Admin@WorkPulse2024",
        "user_metadata": {"role": "admin", "full_name": "System Administrator"}
    },
    {
        "email": "hr@workpulse.local",
        "password": "Hr@WorkPulse2024",
        "user_metadata": {"role": "hr", "full_name": "HR Manager"}
    },
    {
        "email": "employee@workpulse.local",
        "password": "Emp@WorkPulse2024",
        "user_metadata": {"role": "employee", "full_name": "Demo Employee"}
    }
]


def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
    ]

    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nSet them in .env file or export them:")
        print("  SUPABASE_URL='https://your-project.supabase.co'")
        print("  SUPABASE_SERVICE_KEY='your-service-role-key'")
        print("\nGet these from your Supabase Dashboard: Settings > API")
        return False

    print("[OK] Required environment variables are set")
    return True


def seed_auth_users():
    """Create default users in Supabase Auth."""
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    # Create client with service key for admin operations
    client = create_client(url, service_key)

    created_count = 0
    skipped_count = 0
    failed_count = 0

    for account in DEFAULT_ACCOUNTS:
        email = account["email"]
        password = account["password"]
        user_metadata = account["user_metadata"]

        try:
            # Check if user already exists
            response = client.auth.admin.list_users()
            existing = next((u for u in response if u.email == email), None)

            if existing:
                print(f"[SKIP] User already exists: {email} (ID: {existing.id})")
                skipped_count += 1
                continue

            # Create user
            result = client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": user_metadata
            })

            if result.user:
                print(f"[OK] Created user: {email} (ID: {result.user.id})")
                created_count += 1
            else:
                print(f"[FAIL] Failed to create user: {email}")
                failed_count += 1

        except Exception as e:
            print(f"[ERROR] Failed to create user {email}: {e}")
            failed_count += 1

    print(f"\nSummary: {created_count} created, {skipped_count} skipped, {failed_count} failed")
    return failed_count == 0


def main():
    """Main entry point."""
    print("WorkPulse Supabase Auth User Seeding")
    print("=" * 50)

    if not check_environment():
        print("\n[TIP] If you don't have a Supabase project yet:")
        print("  1. Create one at https://supabase.com")
        print("  2. Run the schema from sql/supabase_schema.sql in the SQL Editor")
        print("  3. Copy the URL and Service Role Key to your .env file")
        sys.exit(1)

    success = seed_auth_users()

    if success:
        print("\n[SUCCESS] Auth users seeded successfully!")
        print("\nYou can now log in with:")
        for acc in DEFAULT_ACCOUNTS:
            print(f"  {acc['email']} / {acc['password']}")
    else:
        print("\n[ERROR] Some users failed to seed")
        sys.exit(1)


if __name__ == "__main__":
    main()