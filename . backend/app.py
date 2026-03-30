import streamlit as st
import uuid
import pandas as pd
from datetime import datetime

from translations import TRANSLATIONS
from signal_processing import extract_ppg_features
from model import analyze_cardiofatigue
from db import load_reports, save_report

# 🔵 NEW IMPORTS
from services.quality import check_signal_quality
from services.history import get_user_history, update_user_history, compute_trend
from services.explainability import generate_explanation
from services.llm_service import generate_llm_response

st.set_page_config(page_title="CardioFatigue AI", layout="wide")

t = TRANSLATIONS["English"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "name" not in st.session_state:
    st.session_state.name = ""

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
    st.sidebar.write(f"User ID: {st.session_state.user_id}")

    if st.sidebar.button(t["logout"]):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.name = ""
        st.rerun()

    if page == t["new_screening"]:
        st.title(t["app_title"])
        st.write(f"Welcome, {st.session_state.name}")
        st.info("This app provides early screening support only. It does not diagnose disease.")

        fatigue = st.slider(t["fatigue"], 0, 10, 5)
        dizziness = st.slider(t["dizziness"], 0, 10, 2)
        sleep_hours = st.slider(t["sleep"], 0.0, 12.0, 7.0)
        stress_score = st.slider(t["stress"], 0, 10, 4)
        palpitations = st.checkbox(t["palpitations"])
        exercise_intolerance = st.checkbox(t["exercise_intolerance"])

        st.subheader("Prototype PPG Input")
        ppg_values_text = st.text_area(
            "Paste sample PPG values separated by commas",
            "0.2,0.4,0.5,0.45,0.6,0.55,0.4,0.42,0.50,0.47,0.58,0.53"
        )

        if st.button(t["analyze"]):
            try:
                ppg_values = [float(x.strip()) for x in ppg_values_text.split(",") if x.strip()]
            except:
                ppg_values = []

            # 🔵 NEW: SIGNAL QUALITY CHECK
            quality_score, is_valid = check_signal_quality(ppg_values)

            if not is_valid:
                st.error(f"Poor signal quality (Score: {quality_score}). Please retry.")
                st.stop()

            # EXISTING
            ppg_features = extract_ppg_features(ppg_values)

            features = {
                "fatigue": fatigue,
                "dizziness": dizziness,
                "sleep_hours": sleep_hours,
                "stress_score": stress_score,
                "palpitations": palpitations,
                "exercise_intolerance": exercise_intolerance,
                "ppg_quality_score": ppg_features["ppg_quality_score"],
                "hr_est": ppg_features["hr_est"],

                # 🔵 NEW (for explainability)
                "hr": ppg_features["hr_est"],
                "stress": stress_score,
                "fatigue": fatigue,
                "hrv": ppg_features.get("hrv", 25)
            }

            result = analyze_cardiofatigue(features)

            # 🔵 NEW: TREND ANALYSIS
            history = get_user_history(st.session_state.user_id)
            trend = compute_trend(history, features)
            features.update(trend)

            # 🔵 NEW: EXPLAINABILITY
            explanation = generate_explanation(
                features,
                prediction=1 if result["risk"] != "Low" else 0,
                confidence=result.get("score", 0) / 100
            )

            # 🔵 NEW: LLM (Gemini)
            llm_output = generate_llm_response(
                result["risk"],
                features,
                explanation
            )

            # 🔵 NEW: UPDATE HISTORY
            update_user_history(st.session_state.user_id, features)

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
                "ppg_quality_score": ppg_features["ppg_quality_score"],
                "hr_est": ppg_features["hr_est"],
                "risk_score": result["score"],
                "risk_label": result["risk"]
            }
            save_report(report)

            st.subheader("Screening Output")
            st.success(result["risk"])
            st.write(f"Risk Score: {result['score']}")
            st.write(result["message"])
            st.write(result["doctor_suggestion"])

            # 🔵 NEW DISPLAY
            st.subheader("Signal Quality")
            st.write(f"Quality Score: {quality_score}")

            st.subheader("Advanced Explanation")
            st.write(explanation)

            st.subheader("AI Assistant")
            st.info(llm_output)

            st.subheader("Signal Features")
            st.write(ppg_features)

            st.subheader("Why this result")
            for reason in result["reasons"]:
                st.write(f"- {reason}")

    elif page == t["history"]:
        st.title("History")
        reports = load_reports()
        user_reports = [r for r in reports if r["user_id"] == st.session_state.user_id]
        if user_reports:
            st.dataframe(pd.DataFrame(user_reports), use_container_width=True)
        else:
            st.warning("No reports yet.")

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
