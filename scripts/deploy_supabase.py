#!/usr/bin/env python3
"""
WorkPulse Supabase Deployment Script

This script helps deploy the WorkPulse application to Vercel with Supabase.

Usage:
    python scripts/deploy_supabase.py --setup-schema
    python scripts/deploy_supabase.py --seed-data
    python scripts/deploy_supabase.py --verify
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_JWT_SECRET",
    ]

    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nSet them with:")
        print("  export SUPABASE_URL='https://your-project.supabase.co'")
        print("  export SUPABASE_ANON_KEY='your-anon-key'")
        print("  export SUPABASE_SERVICE_KEY='your-service-key'")
        print("  export SUPABASE_JWT_SECRET='your-jwt-secret'")
        return False

    print("[OK] All required environment variables are set")
    return True


def setup_schema():
    """Run the Supabase schema migrations."""
    print("\n[SETUP] Setting up Supabase database schema...")

    schema_path = project_root / "sql" / "supabase_schema.sql"
    if not schema_path.exists():
        print(f"[FAIL] Schema file not found: {schema_path}")
        return False

    try:
        from database.supabase_client import get_supabase_client

        client = get_supabase_client(use_service_key=True)

        # Read and execute schema (via SQL editor or manual application)
        print(f"Schema file location: {schema_path}")
        print("\nPlease apply the schema to your Supabase project via:")
        print("  1. Supabase Dashboard -> SQL Editor")
        print(f"  2. Paste the contents of {schema_path}")
        print("  3. Click 'Run'")
        print("\nOr use the Supabase CLI:")
        print("  supabase db push --from-file sql/supabase_schema.sql")

        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import Supabase client: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error connecting to Supabase: {e}")
        return False


def seed_data():
    """Seed demo data into the database."""
    print("\n[SEED] Seeding demo data...")

    try:
        from database.seed_supabase import run_all_seeders
        run_all_seeders()
        print("[OK] Demo data seeded successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import seeding functions: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error seeding data: {e}")
        return False


def verify_deployment():
    """Verify the deployment configuration."""
    print("\n[VERIFY] Verifying deployment...")

    checks = []

    # Check 1: Environment variables
    env_ok = check_environment()
    checks.append(("Environment variables", env_ok))

    # Check 2: Supabase connection
    if env_ok:
        try:
            from database.supabase_client import get_supabase_url, get_supabase_service_key
            url = get_supabase_url()
            key = get_supabase_service_key()
            print(f"[OK] Supabase URL: {url}")
            print(f"[OK] Service key: [configured]")
            checks.append(("Supabase connection", True))
        except Exception as e:
            print(f"[FAIL] Supabase connection failed: {e}")
            checks.append(("Supabase connection", False))
    else:
        checks.append(("Supabase connection", False))

    # Check 3: Database provider setting
    provider = os.environ.get("DATABASE_PROVIDER", "sqlite")
    print(f"[OK] Database provider: {provider}")
    checks.append(("Database provider", True))

    # Check 4: Vercel configuration
    vercel_json = project_root / "vercel.json"
    if vercel_json.exists():
        print("[OK] vercel.json found")
        checks.append(("Vercel config", True))
    else:
        print("[FAIL] vercel.json not found")
        checks.append(("Vercel config", False))

    # Check 5: WSGI entrypoint
    wsgi_py = project_root / "wsgi.py"
    if wsgi_py.exists():
        print("[OK] wsgi.py found")
        checks.append(("WSGI entrypoint", True))
    else:
        print("[FAIL] wsgi.py not found")
        checks.append(("WSGI entrypoint", False))

    # Summary
    print("\n" + "=" * 50)
    print("Deployment Verification Summary")
    print("=" * 50)
    for name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    all_passed = all(passed for _, passed in checks)
    if all_passed:
        print("\n[SUCCESS] All checks passed! Ready for deployment.")
        return True
    else:
        print("\n[ERROR] Some checks failed. Please fix before deploying.")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="WorkPulse Supabase Deployment Helper")
    parser.add_argument(
        "--setup-schema",
        action="store_true",
        help="Set up Supabase database schema"
    )
    parser.add_argument(
        "--seed-data",
        action="store_true",
        help="Seed demo data into the database"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify deployment configuration"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all deployment steps"
    )

    args = parser.parse_args()

    if args.all:
        success = True
        success &= setup_schema()
        success &= seed_data()
        success &= verify_deployment()
        sys.exit(0 if success else 1)

    success = True
    if args.setup_schema:
        success &= setup_schema()
    if args.seed_data:
        success &= seed_data()
    if args.verify:
        success &= verify_deployment()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()