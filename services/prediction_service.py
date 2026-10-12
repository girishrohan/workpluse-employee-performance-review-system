"""
WorkPulse - Prediction Service
Handles real-time machine learning inference, confidence scoring, explainability, and database logging.
"""

import pandas as pd
from models.train_model import explain_prediction
from database.db_manager import log_prediction


def run_employee_prediction(pipeline, input_dict, model_id=1, employee_id=None, population_df=None, db_path="data/workpulse.db"):
    """
    Executes an actual prediction using the trained pipeline.
    Never hardcodes or fabricates random predictions.
    
    Returns:
    - predicted_category: str
    - prob_dict: dict of {category: float}
    - contrib_df: pd.DataFrame of feature contributions
    - summary_text: str
    - disclaimer: str
    """
    df_single = pd.DataFrame([input_dict])

    # Run inference
    pred_cat = str(pipeline.predict(df_single)[0])
    probas = pipeline.predict_proba(df_single)[0]

    prob_dict = {
        cls_name: round(float(prob), 4)
        for cls_name, prob in zip(pipeline.classes_, probas)
    }

    # Extract local explanations
    contrib_df, summary_text = explain_prediction(pipeline, input_dict, population_df=population_df)

    disclaimer = (
        "⚠️ Decision-Support Notice: Machine learning predictions are experimental estimates based on historical statistical patterns. "
        "They must never be used as the sole basis for hiring, firing, promotion, or ranking. Human review and contextual judgment are strictly required."
    )

    # Log prediction to SQLite
    try:
        log_prediction(
            model_id=model_id,
            predicted_category=pred_cat,
            feature_snapshot=input_dict,
            explanation_summary=summary_text,
            employee_id=employee_id,
            db_path=db_path
        )
    except Exception as e:
        print("Note: Could not log prediction to database:", e)

    return {
        'predicted_category': pred_cat,
        'probabilities': prob_dict,
        'contributions': contrib_df,
        'summary': summary_text,
        'disclaimer': disclaimer
    }
