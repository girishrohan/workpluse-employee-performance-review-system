"""
Test WorkPulse UI Navigation and Sign-in functionality using Streamlit AppTest.
"""

import os
import unittest
from streamlit.testing.v1 import AppTest

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


class TestWorkPulseUINavigation(unittest.TestCase):

    def test_app_loads_home(self):
        """Test that the application boots and loads the Home page initially."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.run()
        self.assertFalse(at.exception)
        # Should have title or content
        self.assertEqual(at.query_params.get("page"), "Home")

    def test_navigate_to_login(self):
        """Test navigating to the sign-in page."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.query_params["page"] = "login"
        at.run()
        self.assertFalse(at.exception)
        # Login form should be present
        self.assertTrue(len(at.text_input) >= 2)
        # Verify email and password input keys exist
        input_keys = [ti.key for ti in at.text_input]
        self.assertIn("login_email_input", input_keys)
        self.assertIn("login_password_input", input_keys)

    def test_admin_login_and_sidebar_navigation(self):
        """Test signing in as Admin and navigating via the sidebar."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.query_params["page"] = "login"
        at.run()
        self.assertFalse(at.exception)

        # Fill admin credentials and submit form
        for ti in at.text_input:
            if ti.key == "login_email_input":
                ti.set_value("admin@workpulse.local")
            elif ti.key == "login_password_input":
                ti.set_value("Admin@WorkPulse2024")

        # Submit form by clicking submit button
        submit_btn = [b for b in at.button if "Sign In" in b.label][0]
        submit_btn.click().run()
        self.assertFalse(at.exception)

        # After login, sidebar radio should exist
        self.assertTrue(len(at.sidebar.radio) > 0)
        radio = at.sidebar.radio[0]
        options_str = " ".join(radio.options)
        self.assertIn("Dashboard", options_str)
        self.assertIn("Employees", options_str)
        self.assertIn("User Management", options_str)

        # Test navigating via query params / sidebar
        at.query_params["page"] = "Employees"
        at.session_state._nav_radio = "Employees"
        at.session_state.active_page = "Employees"
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state.active_page, "Employees")

    def test_hr_role_navigation_restriction(self):
        """Test HR login and role-based navigation restrictions."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.query_params["page"] = "login"
        at.run()

        for ti in at.text_input:
            if ti.key == "login_email_input":
                ti.set_value("hr@workpulse.local")
            elif ti.key == "login_password_input":
                ti.set_value("Hr@WorkPulse2024")

        submit_btn = [b for b in at.button if "Sign In" in b.label][0]
        submit_btn.click().run()
        self.assertFalse(at.exception)

        radio = at.sidebar.radio[0]
        options_str = " ".join(radio.options)
        self.assertIn("Dashboard", options_str)
        self.assertIn("Assessments", options_str)
        # HR should NOT see User Management
        self.assertNotIn("User Management", options_str)

    def test_employee_role_navigation_restriction(self):
        """Test Employee login and role-based navigation restrictions."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.query_params["page"] = "login"
        at.run()

        for ti in at.text_input:
            if ti.key == "login_email_input":
                ti.set_value("employee@workpulse.local")
            elif ti.key == "login_password_input":
                ti.set_value("Emp@WorkPulse2024")

        submit_btn = [b for b in at.button if "Sign In" in b.label][0]
        submit_btn.click().run()
        self.assertFalse(at.exception)

        radio = at.sidebar.radio[0]
        options_str = " ".join(radio.options)
        self.assertIn("Dashboard", options_str)
        self.assertIn("My Profile", options_str)
        # Employee must not see HR/Admin modules
        self.assertNotIn("Employees", options_str)
        self.assertNotIn("KPI Framework", options_str)
        self.assertNotIn("User Management", options_str)
        self.assertNotIn("Settings", options_str)

    def test_registration_and_recovery_routes_render(self):
        """Public access-request and password-recovery routes must be reachable."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.query_params["page"] = "register"
        at.run()
        self.assertFalse(at.exception)
        labels = " ".join(button.label for button in at.button)
        self.assertIn("Submit Access Request", labels)

        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.query_params["page"] = "forgot_password"
        at.run()
        self.assertFalse(at.exception)
        labels = " ".join(button.label for button in at.button)
        self.assertIn("Generate Reset Token", labels)


if __name__ == "__main__":
    unittest.main()
