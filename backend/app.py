# app.py
import importlib, sys, types, pkgutil

# temporary compatibility patch for Python 3.14
if not hasattr(pkgutil, "get_loader"):
    pkgutil.get_loader = importlib.util.find_spec
if not hasattr(sys, "importlib"):
    sys.importlib = importlib

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import openai
from utils.sentiment import analyze_sentiment
from utils.prompt import THERAPIST_SYSTEM_PROMPT
import time

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "mindmate")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "mindmate")
PORT = int(os.getenv("PORT", 5000))

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
CORS(app)

# SIMPLE health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": time.time()})

# ADMIN login (very basic - replace later with secure auth or JWT)
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    user = data.get("username")
    pwd = data.get("password")
    if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
        return jsonify({"ok": True, "admin": True})
    return jsonify({"ok": False, "admin": False}), 401

# CHAT endpoint - main
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    user_id = data.get("user_id", "anonymous")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # 1) Sentiment / mood analysis
    mood = analyze_sentiment(message)

    # 2) Construct prompt for OpenAI (we send system prompt + user message)
    # We'll ask the model to be empathic and also return a short summary (for storage)
    system_prompt = THERAPIST_SYSTEM_PROMPT
    # Provide a little instruction to keep replies short and helpful
    user_prompt = (
        f"User: {message}\n\n"
        "You are MindMate, respond as an empathetic mental health companion. "
        "Keep it calm, short (2-5 sentences), validating, and supportive. "
        "If the message indicates crisis/self-harm, acknowledge and encourage seeking immediate help."
    )

    # 3) Call OpenAI chat completion
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # recommended if available. If not, use "gpt-4o" or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.7,
            top_p=0.9,
            n=1,
        )
        assistant_text = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Robust fallback: try a simpler model or return a generic empathetic reply
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            assistant_text = resp["choices"][0]["message"]["content"].strip()
        except Exception as e2:
            assistant_text = (
                "I'm sorry — I'm having trouble connecting to the chat service right now. "
                "Please try again in a moment."
            )

    # 4) Optional: create a short anonymized summary (very short)
    # We'll just take first 120 chars as a naive summary placeholder. You can later use model to summarize.
    summary = (message[:120] + "...") if len(message) > 120 else message

    # 5) Response payload
    result = {
        "reply": assistant_text,
        "mood": mood,
        "summary": summary,
        "user_id": user_id
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=8000)

