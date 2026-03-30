# explainability.py

def generate_explanation(features, prediction, confidence=0.0):
    """
    Advanced explainability with severity, context, and confidence
    """

    reasons = []
    context_notes = []

    hrv = features.get("hrv", 100)
    hr = features.get("hr", 0)
    fatigue = features.get("fatigue", 0)
    stress = features.get("stress", 0)

    # 🔹 HRV analysis
    if hrv < 15:
        reasons.append("Severely low HRV")
    elif hrv < 30:
        reasons.append("Moderately low HRV")

    # 🔹 Heart rate analysis
    if hr > 110:
        reasons.append("Significantly elevated heart rate")
    elif hr > 90:
        reasons.append("Mildly elevated heart rate")

    # 🔹 Fatigue
    if fatigue > 8:
        reasons.append("Severe fatigue")
    elif fatigue > 5:
        reasons.append("Moderate fatigue")

    # 🔹 Stress
    if stress > 8:
        reasons.append("High stress levels")
    elif stress > 5:
        reasons.append("Moderate stress levels")

    # 🔹 Context reasoning
    if fatigue > 7 and stress > 7:
        context_notes.append("Combined effect of stress and fatigue may be influencing autonomic balance")

    if hrv < 20 and hr > 100:
        context_notes.append("Possible autonomic imbalance detected")

    # 🔹 Default condition
    if not reasons:
        reasons.append("Stable physiological patterns")

    # 🔹 Build explanation
    explanation = ""

    if prediction == 1:
        explanation += "Higher risk pattern detected. "
    else:
        explanation += "Low risk pattern observed. "

    explanation += "Key observations: " + ", ".join(reasons) + ". "

    if context_notes:
        explanation += "Additional insights: " + ". ".join(context_notes) + ". "

    explanation += f"Model confidence: {round(confidence * 100, 2)}%."

    return explanation
