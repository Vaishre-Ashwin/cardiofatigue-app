# llm_service.py

import google.generativeai as genai

# Set your API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

model = genai.GenerativeModel("gemini-pro")


def generate_llm_response(risk, features, explanation, language="en"):
    """
    Generates AI assistant response using Gemini
    """

    prompt = f"""
    You are a medical assistant (non-diagnostic).

    Risk Level: {risk}
    Explanation: {explanation}
    Features: {features}

    Instructions:
    - Explain result in simple words
    - Give safe health advice
    - DO NOT diagnose any disease
    - Encourage medical consultation if risk is high
    - Respond in {language}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "AI assistant unavailable at the moment."
