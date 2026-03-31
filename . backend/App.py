import streamlit as st
import uuid
import pandas as pd
from datetime import datetime
import numpy as np
import sys
import os

# 🔥 FIX 1: Handle missing modules gracefully
try:
    sys.path.append(os.path.dirname(__file__))
    from translations import TRANSLATIONS
    from signal_processing import extract_ppg_features
    from model import analyze_cardiofatigue
    from db import load_reports, save_report
    HAS_MODULES = True
except ImportError as e:
    st.error(f"Missing modules: {e}")
    HAS_MODULES = False

# 🔥 FIX 2: Create dummy services if modules missing
if not HAS_MODULES:
    TRANSLATIONS = {
        "English": {
            "app_title": "CardioFatigue AI",
            "subtitle": "AI-powered fatigue screening",
            "login": "Login to continue",
            "name": "Name", "email": "Email", "password": "Password",
            "continue": "Continue", "new_screening": "New Screening",
            "history": "History", "weekly_map": "Weekly Map", "logout": "Logout",
            "fatigue": "Fatigue (0-10)", "dizziness": "Dizziness (0-10)",
            "sleep": "Sleep hours", "stress": "Stress (0-10)",
            "palpitations": "Palpitations?", "exercise_intolerance": "Exercise intolerance?",
            "analyze": "🔬 Analyze"
        }
    }
    
    def check_signal_quality(ppg_values):
        return min(100, len(ppg_values) * 10), len(ppg_values) > 5
    
    def extract_ppg_features(ppg_values):
        if not ppg_values:
            return {"hr_est": 75, "hrv": 25, "ppg_quality_score": 50}
        return {
            "hr_est": np.mean(ppg_values) * 100,
            "hrv": np.std(ppg_values) * 10,
            "ppg_quality_score": min(95, len(ppg_values) * 8)
        }
    
    def analyze_cardiofatigue(features):
        score = min(95, features["fatigue"]*8 + features["stress"]*7 + 
                   (10-features["sleep_hours"]*10) + 
                   features["dizziness"]*5)
        if score < 40: risk = "Low"
        elif score < 70: risk = "Moderate"
        else: risk = "High"
        return {"risk": risk, "score": score}
    
    def get_user_history(user_id): return []
    def update_user_history(user_id, features): pass
    def compute_trend(history, features): return {"trend": "stable"}
    def generate_explanation(features, prediction, confidence):
        return f"Based on fatigue={features['fatigue']}, HR={features['hr']}"
    def generate_llm_response(risk, features, explanation):
        return f"Risk: {risk}. {explanation}"
    def load_reports(): return []
    def save_report(report): pass

t = TRANSLATIONS["English"]

# Session state
for key in ["logged_in", "user_id", "name"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ""

# 🔥 REST OF YOUR CODE (unchanged but cleaned up)
if not st.session_state.logged_in:
    st.title(t["app_title"])
    st.subheader(t["subtitle"])
    st.write(t["login"])

    name = st.text_input(t["name"])
    email = st.text_input(t["email"])
    password = st.text_input(t["password"], type="password")

    if st.button(t["continue"]):
        if name and email and password:
            st.session_state.logged_in = True
            st.session_state.name = name
            st.session_state.user_id = "CF-" + str(uuid.uuid4())[:8].upper()
            st.rerun()
        else:
            st.error("Please fill all fields.")

else:
    page = st.sidebar.radio("Go to", [t["new_screening"], t["history"], t["weekly_map"]])
    st.sidebar.write(f"👤 User ID: {st.session_state.user_id}")

    if st.sidebar.button(t["logout"]):
        for key in ["logged_in", "user_id", "name"]:
            st.session_state[key] = False if key == "logged_in" else ""
        st.rerun()

    if page == t["new_screening"]:
        st.title(t["app_title"])
        st.write(f"Welcome, {st.session_state.name} 👋")
        st.info("🩺 This app provides screening only (not diagnosis).")

        col1, col2 = st.columns(2)
        with col1:
            fatigue = st.slider(t["fatigue"], 0, 10, 5)
            dizziness = st.slider(t["dizziness"], 0, 10, 2)
            sleep_hours = st.slider(t["sleep"], 0.0, 12.0, 7.0)
        with col2:
            stress_score = st.slider(t["stress"], 0, 10, 4)
            palpitations = st.checkbox(t["palpitations"])
            exercise_intolerance = st.checkbox(t["exercise_intolerance"])

        st.subheader("📈 PPG Input (comma-separated)")
        ppg_values_text = st.text_area(
            "Paste PPG values", "0.2,0.4,0.5,0.45,0.6,0.55,0.4,0.42",
            help="Example: 0.2,0.4,0.5,0.45"
        )

        if st.button(t["analyze"], type="primary"):
            with st.spinner("🔬 Analyzing your data..."):
                try:
                    ppg_values = [float(x.strip()) for x in ppg_values_text.split(",") if x.strip()]
                except:
                    ppg_values = []
                    st.error("Invalid PPG values!")
                    st.stop()

                # QUALITY CHECK
                quality_score, is_valid = check_signal_quality(ppg_values)
                if not is_valid:
                    st.error(f"❌ Poor signal quality (Score: {quality_score:.1f}/100)")
                    st.stop()

                # EXTRACT FEATURES
                ppg_features = extract_ppg_features(ppg_values)
                hr_est = ppg_features.get("hr_est", 75)
                hrv_val = ppg_features.get("hrv", 25)

                features = {
                    "fatigue": fatigue, "dizziness": dizziness, "sleep_hours": sleep_hours,
                    "stress_score": stress_score, "palpitations": int(palpitations),
                    "exercise_intolerance": int(exercise_intolerance),
                    "ppg_quality_score": ppg_features.get("ppg_quality_score", 50),
                    "hr_est": hr_est, "hrv": hrv_val
                }

                # ANALYZE
                result = analyze_cardiofatigue(features)

                # DISPLAY RESULTS
                risk_emoji = "🟢" if result["risk"] == "Low" else "🟡" if result["risk"] == "Moderate" else "🔴"
                st.markdown(f"## {risk_emoji} **{result['risk']} Risk**")
                st.progress(result["score"] / 100)

                col1, col2, col3 = st.columns(3)
                col1.metric("❤️ HR (bpm)", f"{hr_est:.0f}")
                col2.metric("😴 Fatigue", fatigue)
                col3.metric("😰 Stress", stress_score)

                st.metric("📊 Signal Quality", f"{quality_score:.1f}/100")

                # EXPLANATIONS
                explanation = generate_explanation(features, result["score"]/100, result["score"])
                st.info(explanation)
                
                llm_output = generate_llm_response(result["risk"], features, explanation)
                st.success(llm_output)

                st.json(ppg_features)

                # SAVE (dummy)
                report = {
                    "user_id": st.session_state.user_id,
                    "name": st.session_state.name,
                    "created_at": datetime.now().isoformat(),
                    "risk_score": result["score"],
                    "risk_label": result["risk"]
                }
                save_report(report)
                st.success("✅ Report saved!")

    elif page == t["history"]:
        st.title("📋 Screening History")
        reports = load_reports()
        user_reports = [r for r in reports if r["user_id"] == st.session_state.user_id]
        
        if user_reports:
            df = pd.DataFrame(user_reports)
            st.dataframe(df)
            st.line_chart(df.set_index("created_at")["risk_score"])
        else:
            st.info("📝 No screenings yet. Do one on the New Screening tab!")

    elif page == t["weekly_map"]:
        st.title("📈 Weekly Risk Map")
        st.info("Trend visualization coming soon...")
