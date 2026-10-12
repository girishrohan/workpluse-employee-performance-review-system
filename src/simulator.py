"""
Employee Performance Analytics - What-If Decision Support Simulator
Simulates intervention scenarios by altering key employee attributes and comparing baseline vs simulated predictions.
"""

from src.ml_model import predict_employee_performance


def simulate_what_if_scenario(baseline_dict, modified_dict, model_name='Random Forest', models_dir='models'):
    """
    Executes What-If comparison between baseline employee profile and modified scenario.
    
    Returns:
    - baseline_pred: Category name
    - baseline_probs: Dict of class probabilities
    - modified_pred: Category name
    - modified_probs: Dict of class probabilities
    - deltas: Dict of probability shifts per category
    - recommendations: List of actionable decision-support insights
    """
    baseline_pred, baseline_probs, pipeline = predict_employee_performance(
        baseline_dict, model_name=model_name, models_dir=models_dir
    )

    modified_pred, modified_probs, _ = predict_employee_performance(
        modified_dict, model_name=model_name, models_dir=models_dir
    )

    deltas = {}
    for cls in ['Needs Support', 'Moderate', 'High']:
        b_p = baseline_probs.get(cls, 0.0)
        m_p = modified_probs.get(cls, 0.0)
        deltas[cls] = round(m_p - b_p, 4)

    recommendations = []
    
    # Analyze changes
    t_diff = modified_dict.get('training_hours', 0) - baseline_dict.get('training_hours', 0)
    tc_diff = modified_dict.get('task_completion_rate', 0) - baseline_dict.get('task_completion_rate', 0)
    att_diff = modified_dict.get('attendance_rate', 0) - baseline_dict.get('attendance_rate', 0)
    pr_diff = modified_dict.get('peer_review_score', 0) - baseline_dict.get('peer_review_score', 0)

    if modified_pred != baseline_pred:
        recommendations.append(
            f"🎯 **Category Transition**: Proposed modifications successfully shift predicted performance from "
            f"**{baseline_pred}** to **{modified_pred}**."
        )

    if t_diff > 0:
        high_shift = deltas.get('High', 0) * 100
        recommendations.append(
            f"📚 **Training Support**: Adding +{t_diff:.1f} training hours yields a {high_shift:+.1f}% shift in 'High' performance probability."
        )

    if tc_diff > 0:
        recommendations.append(
            f"✅ **Task Execution**: Improving task completion rate by +{tc_diff:.1f}% strengthens performance stability."
        )

    if att_diff > 0:
        recommendations.append(
            f"📅 **Attendance Alignment**: Increasing attendance by +{att_diff:.1f}% reduces 'Needs Support' risk by {abs(deltas.get('Needs Support', 0)*100):.1f}%."
        )

    if not recommendations:
        recommendations.append("ℹ️ Baseline and simulated scenarios produce similar probability distributions.")

    return {
        'baseline_pred': baseline_pred,
        'baseline_probs': baseline_probs,
        'modified_pred': modified_pred,
        'modified_probs': modified_probs,
        'deltas': deltas,
        'recommendations': recommendations
    }
