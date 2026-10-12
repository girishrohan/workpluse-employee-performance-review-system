"""
WorkPulse - Initializer Script
Generates sample datasets, initializes SQLite database, and trains baseline models.
"""

import os
import pandas as pd
from utils.sample_data_generator import create_sample_files
from database.db_manager import init_db, import_records_from_df
from models.train_model import train_and_evaluate_all_models


def setup_workpulse():
    print("Setting up WorkPulse...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # 1. Generate sample CSVs
    s_path, t_path = create_sample_files("data")
    print(f"Sample dataset created: {s_path}")
    print(f"Sample template created: {t_path}")

    # 2. Initialize database
    init_db("data/workpulse.db")
    df_sample = pd.read_csv(s_path)
    inserted, skipped = import_records_from_df(df_sample, "data/workpulse.db")
    print(f"Database populated with {inserted} employees (skipped {skipped}).")

    # 3. Train ML Models
    results, pipelines, splits = train_and_evaluate_all_models(df_sample, "models")
    print("Models trained successfully:")
    for name, m in results.items():
        print(f" - [{name}] Accuracy: {m['accuracy']*100:.2f}% | F1: {m['f1_score']:.4f}")

    print("WorkPulse setup completed successfully!")


if __name__ == '__main__':
    setup_workpulse()
