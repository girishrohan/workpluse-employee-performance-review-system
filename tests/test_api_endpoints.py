"""
WorkPulse — REST API Automated Test Suite.
Tests all endpoints exposed by the Flask/WSGI serverless layer.
"""

import unittest
from app import app


class TestWorkPulseAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_health_check(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database"]["exists"])

    def test_02_web_portal(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("WorkPulse", response.data.decode("utf-8"))

    def test_03_dashboard_summary(self):
        response = self.client.get('/api/dashboard/summary')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("metrics", data)
        self.assertIn("total_employees", data["metrics"])
        self.assertIn("performance_distribution", data)

    def test_04_auth_login_success(self):
        response = self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'Admin@WorkPulse2024'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["role"], "admin")

    def test_05_auth_login_invalid(self):
        response = self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("error", data)

    def test_06_employees_list(self):
        response = self.client.get('/api/employees')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("employees", data)
        self.assertGreater(data["count"], 0)

    def test_07_employee_details(self):
        response = self.client.get('/api/employees/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["employee_id"], 1)
        self.assertIn("performance_history", data)

    def test_08_periods(self):
        response = self.client.get('/api/periods')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("periods", data)

    def test_09_areas(self):
        response = self.client.get('/api/areas')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("areas", data)

    def test_10_assessments(self):
        response = self.client.get('/api/assessments')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("assessments", data)

    def test_11_workforce_analytics(self):
        response = self.client.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("kpis", data)
        self.assertIn("department_benchmarks", data)

    def test_12_ml_models_benchmark(self):
        response = self.client.get('/api/predictions/models')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("model_evaluations", data)

    def test_13_ml_inference_prediction(self):
        payload = {
            'department': 'Engineering',
            'attendance_rate': 95.0,
            'task_completion_rate': 90.0,
            'training_hours': 40.0,
            'experience_years': 4.5,
            'previous_performance': 4.0,
            'model_type': 'Random Forest'
        }
        response = self.client.post('/api/predictions/predict', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn(data["predicted_category"], ["High", "Moderate", "Needs Support"])
        self.assertIn("probabilities", data)
        self.assertIn("factor_drivers", data)

    def test_14_reports_summary(self):
        response = self.client.get('/api/reports/summary')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("report_title", data)

    def test_15_notifications(self):
        response = self.client.get('/api/notifications')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("notifications", data)


if __name__ == "__main__":
    unittest.main()
