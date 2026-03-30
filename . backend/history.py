# history.py

# Temporary in-memory storage (replace with DB later)
user_history = {}

def get_user_history(user_id):
    return user_history.get(user_id, [])


def update_user_history(user_id, features):
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append(features)

    # Keep only last 10 records
    user_history[user_id] = user_history[user_id][-10:]


def compute_trend(history, current_features):
    """
    Computes difference between current values and past average
    """

    if not history:
        return {"trend_hrv": 0, "trend_hr": 0}

    avg_hrv = sum(h.get("hrv", 0) for h in history) / len(history)
    avg_hr = sum(h.get("hr", 0) for h in history) / len(history)

    trend = {
        "trend_hrv": current_features.get("hrv", 0) - avg_hrv,
        "trend_hr": current_features.get("hr", 0) - avg_hr
    }

    return trend
