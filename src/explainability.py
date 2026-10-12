"""
Employee Performance Analytics - Explainability Engine
Extracts global feature importances and computes local feature contributions for individual predictions.
"""

import numpy as np
import pandas as pd
from src.ml_model import FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL


def get_global_feature_importance(pipeline):
    """Returns sorted DataFrame of global feature importances for a trained pipeline."""
    preprocessor = pipeline.preprocessor
    classifier = pipeline.classifier

    feature_names = preprocessor.feature_names_

    if hasattr(classifier, 'feature_importances_') and classifier.feature_importances_ is not None:
        importances = classifier.feature_importances_
    else:
        importances = np.ones(len(feature_names)) / len(feature_names)

    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False).reset_index(drop=True)

    importance_df['Importance_Pct'] = (importance_df['Importance'] * 100).round(2)
    return importance_df


def explain_individual_prediction(pipeline, input_dict, baseline_df=None):
    """
    Computes local feature contributions for an individual employee prediction.
    Calculates impact of each feature relative to population benchmarks.
    """
    preprocessor = pipeline.preprocessor
    feature_names = preprocessor.feature_names_
    importance_df = get_global_feature_importance(pipeline)
    importance_map = dict(zip(importance_df['Feature'], importance_df['Importance']))

    input_df = pd.DataFrame([input_dict])

    # Reference benchmarks for numeric features
    benchmarks = {
        'attendance_rate': 85.0,
        'task_completion_rate': 80.0,
        'training_hours': 35.0,
        'experience_years': 4.0,
        'previous_performance': 3.5,
        'projects_delivered': 8.0,
        'overtime_hours': 15.0,
        'peer_review_score': 3.5,
        'communication_score': 3.5
    }

    if baseline_df is not None:
        for col in FEATURE_COLS_NUMERIC:
            if col in baseline_df.columns:
                benchmarks[col] = float(baseline_df[col].mean())

    contributions = []

    for fname in FEATURE_COLS_NUMERIC:
        weight = importance_map.get(fname, 0.08)
        val = float(input_dict.get(fname, benchmarks[fname]))
        bm = float(benchmarks[fname])

        delta_ratio = (val - bm) / (bm if bm != 0 else 1.0)
        impact = delta_ratio * weight * 100

        friendly_name = fname.replace('_', ' ').title()
        contributions.append({
            'Feature': friendly_name,
            'Raw_Value': f"{val:.1f}",
            'Benchmark': f"{bm:.1f}",
            'Impact_Score': round(impact, 2),
            'Direction': 'Positive' if impact >= 0 else 'Negative'
        })

    contrib_df = pd.DataFrame(contributions).sort_values(by='Impact_Score', key=abs, ascending=False).reset_index(drop=True)

    positives = contrib_df[contrib_df['Impact_Score'] > 0].head(3)
    negatives = contrib_df[contrib_df['Impact_Score'] < 0].head(3)

    summary_bullets = []
    for _, row in positives.iterrows():
        summary_bullets.append(f"🟢 **{row['Feature']}** ({row['Raw_Value']}) is above population average ({row['Benchmark']}), positively strengthening performance score.")

    for _, row in negatives.iterrows():
        summary_bullets.append(f"🔴 **{row['Feature']}** ({row['Raw_Value']}) is below benchmark ({row['Benchmark']}), indicating potential area for targeted support.")

    if not summary_bullets:
        summary_bullets.append("ℹ️ Employee metrics closely align with population benchmarks.")

    disclaimer = (
        "⚠️ **Decision Support Disclaimer**: Feature impact scores reflect statistical associations in historical performance data "
        "and do not constitute proof of individual causality. Use these insights to guide training and developmental support."
    )

    return contrib_df, summary_bullets, disclaimer
