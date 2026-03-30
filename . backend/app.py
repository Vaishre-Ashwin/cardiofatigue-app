import streamlit as st
import uuid
import pandas as pd
from datetime import datetime

from translations import TRANSLATIONS
from signal_processing import extract_ppg_features
from model import analyze_cardiofatigue
from db import load_reports, save_report

from services.quality import check_signal_quality
from services.history import get_user_history, update_user_history, compute_trend
from services.explainability import generate_explanation
from services.llm_service import generate_llm_response

st.set_page_config(page_title="CardioFatigue AI", layout="wide")

t = TRANSLATIONS["English"]

# Session state
for key in ["logged_in", "user_id", "name"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ""

# LOGIN
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

# MAIN APP
else:
    page = st.sidebar.radio("Go to", [t["new_screening"], t["history"], t["weekly_map"]])
    st.sidebar.write(f"User ID: {st.session_state.user_id}")

    if st.sidebar.button(t["logout"]):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.name = ""
        st.rerun()

    # =========================
    # NEW SCREENING PAGE
    # =========================
    if page == t["new_screening"]:
        st.title(t["app_title"])
        st.write(f"Welcome, {st.session_state.name}")
        st.info("This app provides early screening support only. It does not diagnose disease.")

        # Inputs
        col1, col2 = st.columns(2)

        with col1:
            fatigue = st.slider(t["fatigue"], 0, 10, 5)
            dizziness = st.slider(t["dizziness"], 0, 10, 2)
            sleep_hours = st.slider(t["sleep"], 0.0, 12.0, 7.0)

        with col2:
            stress_score = st.slider(t["stress"], 0, 10, 4)
            palpitations = st.checkbox(t["palpitations"])
            exercise_intolerance = st.checkbox(t["exercise_intolerance"])

        st.subheader("PPG Input")
        ppg_values_text = st.text_area(
            "Paste PPG values (comma separated)",
            "0.2,0.4,0.5,0.45,0.6,0.55,0.4,0.42,0.50,0.47,0.58,0.53"
        )

        if st.button(t["analyze"]):

            with st.spinner("Analyzing your data..."):

                try:
                    ppg_values = [float(x.strip()) for x in ppg_values_text.split(",") if x.strip()]
                except:
                    ppg_values = []

                # QUALITY CHECK
                quality_score, is_valid = check_signal_quality(ppg_values)

                if not is_valid:
                    st.error(f"Poor signal quality (Score: {quality_score})")
                    st.stop()

                # SIGNAL PROCESSING
                ppg_features = extract_ppg_features(ppg_values)

                hr_est = ppg_features.get("hr_est", 0)
                hrv_val = ppg_features.get("hrv", 25)

                features = {
                    "fatigue": fatigue,
                    "dizziness": dizziness,
                    "sleep_hours": sleep_hours,
                    "stress_score": stress_score,
                    "palpitations": palpitations,
                    "exercise_intolerance": exercise_intolerance,
                    "ppg_quality_score": ppg_features.get("ppg_quality_score", 0),
                    "hr_est": hr_est,

                    # For explainability
                    "hr": hr_est,
                    "stress": stress_score,
                    "hrv": hrv_val
                }

                result = analyze_cardiofatigue(features)

                # TREND
                history = get_user_history(st.session_state.user_id)
                trend = compute_trend(history, features)
                features.update(trend)

                # EXPLANATION
                explanation = generate_explanation(
                    features,
                    prediction=1 if result["risk"] != "Low" else 0,
                    confidence=result.get("score", 0) / 100
                )

                # LLM SAFE CALL
                try:
                    llm_output = generate_llm_response(result["risk"], features, explanation)
                except:
                    llm_output = "AI assistant unavailable."

                update_user_history(st.session_state.user_id, features)

                # SAVE
                report = {
                    "user_id": st.session_state.user_id,
                    "name": st.session_state.name,
                    "created_at": datetime.now().isoformat(),
                    "fatigue": fatigue,
                    "dizziness": dizziness,
                    "sleep_hours": sleep_hours,
                    "stress_score": stress_score,
                    "palpitations": palpitations,
                    "exercise_intolerance": exercise_intolerance,
                    "ppg_quality_score": ppg_features.get("ppg_quality_score", 0),
                    "hr_est": hr_est,
                    "risk_score": result["score"],
                    "risk_label": result["risk"]
                }
                save_report(report)

            # ================= UI OUTPUT =================

            st.subheader("Results")

            # COLOR RESULT
            if result["risk"] == "Low":
                st.success("🟢 Low Risk")
            elif result["risk"] == "Moderate":
                st.warning("🟡 Moderate Risk")
            else:
                st.error("🔴 High Risk")

            st.progress(result["score"] / 100)

            # METRICS
            col1, col2, col3 = st.columns(3)
            col1.metric("Heart Rate", hr_est)
            col2.metric("Fatigue", fatigue)
            col3.metric("Stress", stress_score)

            st.write(f"Risk Score: {result['score']}")

            st.subheader("Signal Quality")
            st.metric("Quality Score", f"{quality_score}/100")

            st.subheader("Explanation")
            st.info(explanation)

            st.subheader("AI Assistant")
            st.info(llm_output)

            st.subheader("Doctor Suggestion")
            st.write(result["doctor_suggestion"])

            st.subheader("Signal Features")
            st.write(ppg_features)

    # ================= HISTORY =================
    elif page == t["history"]:
        st.title("History")
        reports = load_reports()
        user_reports = [r for r in reports if r["user_id"] == st.session_state.user_id]

        if user_reports:
            st.dataframe(pd.DataFrame(user_reports), use_container_width=True)
        else:
            st.warning("No reports yet.")

    # ================= WEEKLY MAP =================
    elif page == t["weekly_map"]:
        st.title("Weekly Map")
        reports = load_reports()
        user_reports = [r for r in reports if r["user_id"] == st.session_state.user_id]

        if user_reports:
            df = pd.DataFrame(user_reports)
            df["created_at"] = pd.to_datetime(df["created_at"])
            df = df.sort_values("created_at")

            st.line_chart(df.set_index("created_at")["risk_score"])
        else:
            st.warning("No reports yet.")
