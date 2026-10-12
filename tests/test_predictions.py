"""
WorkPulse - Automated Prediction & Machine Learning Unit Tests
Verifies model training, inference, classification metrics, feature importances, and explainability.
"""

import unittest
import pandas as pd
from utils.sample_data_generator import generate_sample_employees
from models.train_model import (
    train_and_evaluate_all_models, get_feature_importances
)
from services.prediction_service import run_employee_prediction


class TestPredictions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = generate_sample_employees(n_samples=150, random_seed=42)
        cls.results, cls.pipelines, cls.splits = train_and_evaluate_all_models(cls.df, models_dir="models_test")

    def test_models_trained_and_evaluated(self):
        """Verifies both Decision Tree and Random Forest trained with real metrics."""
        self.assertIn("Random Forest", self.results)
        self.assertIn("Decision Tree", self.results)

        rf_res = self.results["Random Forest"]
        self.assertGreater(rf_res['accuracy'], 0.5)
        self.assertIn("confusion_matrix", rf_res)
        self.assertEqual(len(rf_res['confusion_matrix']), 3)

    def test_prediction_inference(self):
        """Verifies real prediction inference and probability outputs."""
        pipeline = self.pipelines["Random Forest"]
        test_input = {
            'attendance_rate': 94.0,
            'task_completion_rate': 91.0,
            'training_hours': 40.0,
            'experience_years': 5.0,
            'previous_performance': 4.5,
            'department': 'Engineering'
        }
        res = run_employee_prediction(
            pipeline=pipeline,
            input_dict=test_input,
            model_id=1,
            population_df=self.df,
            db_path="data/test_workpulse.db"
        )
        self.assertIn(res['predicted_category'], ['Needs Support', 'Moderate', 'High'])
        self.assertAlmostEqual(sum(res['probabilities'].values()), 1.0, places=2)
        self.assertGreater(len(res['contributions']), 0)
        self.assertTrue(len(res['summary']) > 0)

    def test_feature_importances(self):
        """Verifies feature importance extraction."""
        pipeline = self.pipelines["Random Forest"]
        df_imp = get_feature_importances(pipeline)
        self.assertGreater(len(df_imp), 0)
        self.assertIn("Importance_Pct", df_imp.columns)


if __name__ == '__main__':
    unittest.main()
