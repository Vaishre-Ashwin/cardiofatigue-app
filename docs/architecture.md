# CardioFatigue AI Architecture

## Overview
CardioFatigue AI is a smartphone PPG and symptom-based screening system for early cardiovascular fatigue and autonomic burden assessment.

## Main Layers
1. Mobile / app interface
2. PPG signal acquisition
3. Signal preprocessing
4. Feature extraction
5. AI / risk scoring model
6. History and weekly trend tracking
7. Recommendation / triage layer

## Data Flow
User input -> PPG signal + symptom questionnaire -> signal processing -> feature extraction -> model inference -> risk score -> recommendation -> report history

## Core Files
- backend/app.py -> Streamlit interface
- backend/signal_processing.py -> PPG preprocessing and feature extraction
- backend/model.py -> baseline risk logic / ML model later
- backend/db.py -> report storage
- backend/translations.py -> multilingual support
