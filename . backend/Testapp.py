import streamlit as st
import uuid
import pandas as pd
from datetime import datetime
import sys
import os

# 🔥 FIX IMPORT PATH
sys.path.append(os.path.dirname(__file__))

# IMPORTS
from translations import TRANSLATIONS
from signal_processing import extract_ppg_features
from model import analyze_cardiofatigue
from db import load_reports, save_report

from quality import check_signal_quality
from history import get_user_history, update_user_history, compute_trend
from explainability import generate_explanation
from llm_service import generate_llm_response

st.set_page_config(page_title="CardioFatigue AI", layout="wide")

t = TRANSLATIONS["English"]

# SESSION
for key in ["logged_in", "user_id", "name"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ""

# LOGIN
if not st.session_state.logged_in:
    st.title(t["app_title"])
    st.subheader(t["subtitle"])

    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Continue"):
        if name and email and password:
            st.session_state.logged_in = True
            st.session_state.name = name
            st.session_state.user_id = "CF-" + str(uuid.uuid4())[:8].upper()
            st.rerun()
        else:
            st.error("Fill all fields")

else:
    st.sidebar.write(f"User ID: {st.session_state.user_id}")
    page = st.sidebar.radio("Menu", ["Screening", "History"])

    # ================= SCREENING =================
    if page == "Screening":
        st.title("CardioFatigue AI")
        st.info("Screening tool (not diagnosis)")

        # 🔥 INPUTS (NO SLIDERS)
        col1, col2 = st.columns(2)

        with col1:
            fatigue = st.number_input("Fatigue Level (0–10)", 0, 10, 5)
            dizziness = st.number_input("Dizziness Level (0–10)", 0, 10, 2)
            sleep_hours = st.number_input("Sleep Hours", 0.0, 12.0, 7.0)

        with col2:
            stress_score = st.number_input("Stress Level (0–10)", 0, 10, 4)
            palpitations = st.checkbox("Palpitations")
            exercise_intolerance = st.checkbox("Exercise Intolerance")

        # 🔥 PPG INPUT OPTIONS
        st.subheader("PPG Input Source")

        input_mode = st.radio(
            "Select Input Method",
            ["Upload File", "Simulated Wearable"]
        )

        ppg_values = []

        # -------- FILE UPLOAD --------
        if input_mode == "Upload File":
            file = st.file_uploader("Upload PPG CSV file", type=["csv"])

            if file is not None:
                df = pd.read_csv(file)
                ppg_values = df.iloc[:, 0].tolist()
                st.success("PPG data loaded")

        # -------- SIMULATED WEARABLE --------
        else:
            st.info("Simulated wearable sensor generating PPG")

            import numpy as np
            ppg_values = list(0.5 + 0.1 * np.sin(np.linspace(0, 10, 100)))

        # -------- ANALYZE --------
        if st.button("Analyze"):

            if len(ppg_values) == 0:
                st.error("No PPG data available")
                st.stop()

            # QUALITY CHECK
            quality_score, is_valid = check_signal_quality(ppg_values)

            if not is_valid:
                st.error(f"Poor signal quality: {quality_score}")
                st.stop()

            # FEATURES
            ppg_features = extract_ppg_features(ppg_values)

            features = {
                "fatigue": fatigue,
                "dizziness": dizziness,
                "sleep_hours": sleep_hours,
                "stress_score": stress_score,
                "palpitations": palpitations,
                "exercise_intolerance": exercise_intolerance,
                "hr": ppg_features.get("hr_est", 0),
                "hrv": ppg_features.get("hrv", 25)
            }

            # MODEL
            result = analyze_cardiofatigue(features)

            # TREND
            history = get_user_history(st.session_state.user_id)
            trend = compute_trend(history, features)
            features.update(trend)

            # EXPLAIN
            explanation = generate_explanation(
                features,
                prediction=1 if result["risk"] != "Low" else 0,
                confidence=result.get("score", 0)
            )

            # LLM
            try:
                llm_output = generate_llm_response(result["risk"], features, explanation)
            except:
                llm_output = "AI unavailable"

            # SAVE
            save_report({
                "user_id": st.session_state.user_id,
                "created_at": datetime.now().isoformat(),
                "risk_score": result["score"],
                "risk_label": result["risk"]
            })

            # OUTPUT
            st.subheader("Result")

            if result["risk"] == "Low":
                st.success("🟢 Low Risk")
            elif result["risk"] == "Moderate":
                st.warning("🟡 Moderate Risk")
            else:
                st.error("🔴 High Risk")

            st.write(f"Score: {result['score']}")
            st.write(f"Signal Quality: {quality_score}")

            st.subheader("Explanation")
            st.info(explanation)

            st.subheader("AI Assistant")
            st.info(llm_output)

    # ================= HISTORY =================
    elif page == "History":
        reports = load_reports()
        st.dataframe(pd.DataFrame(reports))
