def analyze_cardiofatigue(features):
    score = 0
    reasons = []

    fatigue = features["fatigue"]
    dizziness = features["dizziness"]
    sleep_hours = features["sleep_hours"]
    stress_score = features["stress_score"]
    palpitations = features["palpitations"]
    exercise_intolerance = features["exercise_intolerance"]
    ppg_quality_score = features["ppg_quality_score"]
    hr_est = features["hr_est"]

    if fatigue >= 7:
        score += 3
        reasons.append("High fatigue")
    elif fatigue >= 4:
        score += 2
        reasons.append("Moderate fatigue")

    if dizziness >= 6:
        score += 2
        reasons.append("Frequent dizziness")

    if sleep_hours < 6:
        score += 2
        reasons.append("Poor sleep duration")

    if stress_score >= 7:
        score += 2
        reasons.append("High stress burden")

    if palpitations:
        score += 2
        reasons.append("Palpitations present")

    if exercise_intolerance:
        score += 2
        reasons.append("Exercise intolerance present")

    if ppg_quality_score < 0.4:
        reasons.append("Low signal quality")

    if hr_est > 100:
        score += 1
        reasons.append("Elevated pulse pattern")

    if score <= 3:
        risk = "Low"
        message = "Low cardiovascular fatigue / autonomic burden pattern."
        doctor = "General wellness monitoring is enough for now."
    elif score <= 7:
        risk = "Moderate"
        message = "Moderate cardiovascular fatigue / autonomic burden pattern."
        doctor = "Consider consulting a physician if symptoms persist."
    else:
        risk = "High"
        message = "High cardiovascular fatigue / autonomic burden pattern."
        doctor = "Medical consultation is recommended if symptoms continue."

    return {
        "score": score,
        "risk": risk,
        "message": message,
        "doctor_suggestion": doctor,
        "reasons": reasons[:4]
    }
