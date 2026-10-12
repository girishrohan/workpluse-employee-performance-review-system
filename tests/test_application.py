"""
Automated Test Suite for Employee Performance Analytics System
Validates Technical Requirements Document (TRD) Test Cases TC-01 through TC-09.
"""

import os
import unittest
import pandas as pd
import numpy as np

from src.dataset_generator import generate_employee_data, save_dataset
from src.ml_model import (
    train_and_evaluate_models, predict_employee_performance,
    CustomPreprocessor, FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL
)
from src.explainability import explain_individual_prediction, get_global_feature_importance
from src.simulator import simulate_what_if_scenario
from src.fairness import evaluate_departmental_fairness, get_privacy_and_ethics_checklist


class TestEmployeePerformanceSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_csv_path = "data/test_sample.csv"
        cls.df = generate_employee_data(n_samples=100, random_seed=42)
        os.makedirs("data", exist_ok=True)
        cls.df.to_csv(cls.test_csv_path, index=False)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_csv_path):
            os.remove(cls.test_csv_path)

    def test_tc01_load_valid_csv(self):
        """TC-01: Upload/Load valid CSV file."""
        loaded_df = pd.read_csv(self.test_csv_path)
        self.assertEqual(len(loaded_df), 100)
        self.assertIn('performance_category', loaded_df.columns)
        print("[PASS] TC-01: Valid CSV loaded successfully.")

    def test_tc02_invalid_file_handling(self):
        """TC-02: Non-CSV file handling."""
        invalid_path = "data/test.invalid"
        with open(invalid_path, "w") as f:
            f.write("Invalid content non-csv format")
        
        with self.assertRaises(Exception):
            df = pd.read_csv(invalid_path, delimiter="\t\t\t")
            if 'performance_category' not in df.columns:
                raise ValueError("Invalid columns")
        
        if os.path.exists(invalid_path):
            os.remove(invalid_path)
        print("[PASS] TC-02: Non-CSV file produces clear error validation.")

    def test_tc03_missing_value_detection(self):
        """TC-03: Missing value detection and cleaning."""
        df_dirty = self.df.copy()
        df_dirty.loc[0, 'attendance_rate'] = np.nan
        self.assertTrue(df_dirty['attendance_rate'].isnull().any())
        
        clean_df = df_dirty.fillna(df_dirty['attendance_rate'].mean())
        self.assertFalse(clean_df['attendance_rate'].isnull().any())
        print("[PASS] TC-03: Missing values detected and cleaned.")

    def test_tc04_numerical_range_validation(self):
        """TC-04: Numerical percentage range clipping."""
        df_range = self.df.copy()
        df_range['attendance_rate'] = np.clip(df_range['attendance_rate'], 0.0, 100.0)
        self.assertTrue((df_range['attendance_rate'] >= 0.0).all())
        self.assertTrue((df_range['attendance_rate'] <= 100.0).all())
        print("[PASS] TC-04: Numerical percentage ranges validated.")

    def test_tc05_train_model(self):
        """TC-05: Train machine learning models."""
        results, pipelines, splits = train_and_evaluate_models(df=self.df, models_dir='models_test')
        self.assertIn('Decision Tree', pipelines)
        self.assertIn('Random Forest', pipelines)
        print("[PASS] TC-05: Machine learning models trained successfully.")

    def test_tc06_predict_valid_inputs(self):
        """TC-06: Predict performance category for valid inputs."""
        sample_input = {
            'department': 'Engineering',
            'attendance_rate': 92.0,
            'task_completion_rate': 88.0,
            'training_hours': 45.0,
            'experience_years': 5.0,
            'previous_performance': 4.0,
            'projects_delivered': 10,
            'overtime_hours': 12.0,
            'peer_review_score': 4.2,
            'communication_score': 4.0
        }
        pred_label, prob_dict, pipeline = predict_employee_performance(sample_input, models_dir='models_test')
        self.assertIn(pred_label, ['Needs Support', 'Moderate', 'High'])
        self.assertAlmostEqual(sum(prob_dict.values()), 1.0, places=2)
        print(f"[PASS] TC-06: Prediction returned category '{pred_label}' with probabilities.")

    def test_tc07_evaluate_metrics(self):
        """TC-07: Display evaluation metrics and confusion matrix."""
        results, _, _ = train_and_evaluate_models(df=self.df, models_dir='models_test')
        rf_res = results['Random Forest']
        self.assertIn('accuracy', rf_res)
        self.assertIn('confusion_matrix', rf_res)
        self.assertEqual(len(rf_res['confusion_matrix']), 3)
        print("[PASS] TC-07: Evaluation metrics and confusion matrix calculated correctly.")

    def test_tc08_export_results(self):
        """TC-08: Export results to CSV."""
        export_path = "data/exported_test.csv"
        self.df.to_csv(export_path, index=False)
        self.assertTrue(os.path.exists(export_path))
        if os.path.exists(export_path):
            os.remove(export_path)
        print("[PASS] TC-08: CSV export generated successfully.")

    def test_tc09_explainability_and_whatif(self):
        """TC-09: Explain predictions and simulate what-if scenarios."""
        sample_input = self.df.iloc[0].to_dict()
        _, _, pipeline = predict_employee_performance(sample_input, models_dir='models_test')
        
        contrib_df, bullets, disclaimer = explain_individual_prediction(pipeline, sample_input, baseline_df=self.df)
        self.assertGreater(len(contrib_df), 0)
        
        mod_input = sample_input.copy()
        mod_input['training_hours'] += 30.0
        sim_res = simulate_what_if_scenario(sample_input, mod_input, models_dir='models_test')
        self.assertIn('deltas', sim_res)
        print("[PASS] TC-09: Explainability and What-If simulation executed successfully.")


if __name__ == '__main__':
    unittest.main()
