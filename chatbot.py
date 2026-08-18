import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY was not found in the .env file.")

client = genai.Client(api_key=API_KEY)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

SYSTEM_INSTRUCTION = """
You are SentiCare AI, a supportive AI wellness assistant.

Your role is to:
- Listen carefully to the user.
- Respond with empathy and emotional awareness.
- Have natural, friendly conversations.
- Help users reflect on their feelings.
- Provide general wellness suggestions.
- Never judge, shame, or dismiss the user.

Important safety rules:
- You are not a doctor, psychologist, psychiatrist, or therapist.
- Do not diagnose mental health conditions.
- Do not claim certainty about a person's mental state.
- Do not prescribe medication.
- For serious or dangerous situations, encourage the user to seek appropriate professional or emergency support.

You must analyze the user's emotional tone and return:
1. response
2. emotion
3. sentiment
4. intensity
5. topic
6. confidence

Return ONLY valid JSON.

The JSON format must be:
{
    "response": "supportive response to the user",
    "emotion": "one short emotion",
    "sentiment": "positive, negative, or neutral",
    "intensity": "low, medium, or high",
    "topic": "short topic",
    "confidence": 0.0
}

Confidence must be a number between 0.0 and 1.0.
Do not include Markdown code fences around the JSON.
"""

def create_chat():
    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            response_mime_type="application/json"
        )
    )

def extract_json(text):
    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        json_text = text[start:end + 1]
        return json.loads(json_text)

    raise ValueError("Could not extract valid JSON from Gemini response.")

def normalize_result(data):
    if not isinstance(data, dict):
        raise ValueError("Gemini response is not a JSON object.")

    response = str(data.get("response", "")).strip()
    if not response:
        response = "I'm here with you. Would you like to tell me a little more about what's on your mind?"

    emotion = str(data.get("emotion", "neutral")).strip().capitalize()
    if not emotion:
        emotion = "Neutral"

    sentiment = str(data.get("sentiment", "neutral")).strip().capitalize()
    if sentiment not in {"Positive", "Negative", "Neutral"}:
        sentiment = "Neutral"

    intensity = str(data.get("intensity", "low")).strip().capitalize()
    if intensity not in {"Low", "Medium", "High"}:
        intensity = "Low"

    topic = str(data.get("topic", "General")).strip().capitalize()
    if not topic:
        topic = "General"

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5

    confidence = max(0.0, min(1.0, confidence))

    return {
        "response": response,
        "emotion": emotion,
        "sentiment": sentiment,
        "intensity": intensity,
        "topic": topic,
        "confidence": confidence
    }

def generate_response(chat_session, user_message):
    if not user_message:
        raise ValueError("User message cannot be empty.")

    try:
        response = chat_session.send_message(user_message)
        if not response:
            raise RuntimeError("Gemini returned no response.")

        response_text = getattr(response, "text", None)
        if not response_text:
            raise RuntimeError("Gemini returned an empty response.")

        result = extract_json(response_text)
        return normalize_result(result)

    except Exception as e:
        print(f"\n========== GEMINI ERROR ==========\n{type(e).__name__}\n{str(e)}\n=================================\n")
        raise

def analyze_emotion(user_message):
    return {
        "emotion": "Neutral",
        "sentiment": "Neutral",
        "intensity": "Low",
        "topic": "General",
        "confidence": 0.0
    }