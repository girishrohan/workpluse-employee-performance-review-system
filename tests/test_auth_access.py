"""Authentication, registration approval, and role-permission tests."""

import os
import tempfile
import unittest
from datetime import date

from auth.auth_service import (
    authenticate_user,
    authenticate_user_with_status,
    approve_user,
    create_user,
    delete_user,
    ensure_default_admin,
    find_employee_by_code,
    get_all_users,
    init_auth_tables,
    register_pending_user,
    update_user,
)
from services.workpulse_service import create_employee, initialize_database
from workpulse_ui import can_access_page


class AuthenticationAndAccessTests(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(handle)
        initialize_database(self.db_path)
        init_auth_tables(self.db_path)
        ensure_default_admin()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_default_accounts_authenticate_with_expected_roles(self):
        expected = {
            "admin@workpulse.local": ("Admin@WorkPulse2024", "admin"),
            "hr@workpulse.local": ("Hr@WorkPulse2024", "hr"),
            "employee@workpulse.local": ("Emp@WorkPulse2024", "employee"),
        }
        for email, (password, role) in expected.items():
            user = authenticate_user(email, password)
            self.assertIsNotNone(user)
            self.assertEqual(user["role"], role)

    def test_wrong_password_is_rejected(self):
        self.assertIsNone(authenticate_user("admin@workpulse.local", "not-the-password"))

    def test_registration_is_inactive_until_admin_approval(self):
        user_id = register_pending_user(
            email="new.staff@workpulse.local",
            full_name="New Staff",
            password="StrongPass123",
        )
        self.assertIsNone(authenticate_user("new.staff@workpulse.local", "StrongPass123"))
        status, user = authenticate_user_with_status(
            "new.staff@workpulse.local", "StrongPass123"
        )
        self.assertEqual(status, "pending")
        self.assertIsNone(user)

        self.assertTrue(approve_user(user_id))
        status, user = authenticate_user_with_status(
            "new.staff@workpulse.local", "StrongPass123"
        )
        self.assertEqual(status, "success")
        self.assertEqual(user["role"], "employee")

    def test_registration_cannot_reuse_email_or_link_taken_profile(self):
        register_pending_user("first@workpulse.local", "First Person", "StrongPass123")
        with self.assertRaises(ValueError):
            register_pending_user("first@workpulse.local", "Second Person", "StrongPass123")

        employee_id = create_employee(
            "WP-9001", "Linked Employee", "Engineering", "Analyst",
            date.today(), "Active", 3.0, self.db_path,
        )
        register_pending_user(
            "linked@workpulse.local", "Linked Employee", "StrongPass123", "WP-9001"
        )
        with self.assertRaises(ValueError):
            register_pending_user(
                "another@workpulse.local", "Another Person", "StrongPass123", "WP-9001"
            )
        self.assertIsNotNone(find_employee_by_code("wp-9001"))
        self.assertEqual(int(find_employee_by_code("WP-9001")["employee_id"]), employee_id)

    def test_admin_can_update_and_delete_accounts(self):
        user_id = create_user(
            email="temp.user@workpulse.local",
            full_name="Temp User",
            role="employee",
            created_by_user_id=None,
            plain_password="TempPass123",
        )
        self.assertTrue(update_user(user_id, full_name="Updated User", role="hr"))
        record = next(user for user in get_all_users() if user["user_id"] == user_id)
        self.assertEqual(record["full_name"], "Updated User")
        self.assertEqual(record["role"], "hr")
        self.assertTrue(delete_user(user_id))
        self.assertFalse(any(user["user_id"] == user_id for user in get_all_users()))

    def test_route_permissions_enforce_role_boundaries(self):
        self.assertTrue(can_access_page("Employees", "hr"))
        self.assertTrue(can_access_page("Employees", "admin"))
        self.assertFalse(can_access_page("Employees", "employee"))
        self.assertFalse(can_access_page("User Management", "hr"))
        self.assertFalse(can_access_page("Settings", "employee"))
        self.assertTrue(can_access_page("My Profile", "employee"))
        self.assertTrue(can_access_page("Notifications", "employee"))


if __name__ == "__main__":
    unittest.main()
