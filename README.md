# SentiCare AI — Empathetic Mental Wellness Companion

SentiCare AI is an AI-powered conversational wellness companion designed to provide supportive, empathetic dialogue alongside real-time emotional tone analysis. Built with Flask, SQLite, and the Google Gemini API, SentiCare AI extracts sentiment, emotional intensity, and conversation topics in a single API call to minimize latency and manage rate limits.

---

## Key Features

* **Empathetic Dialogue**: Supportive, non-judgmental conversational assistant calibrated for mental clarity and mindfulness.
* **Unified API Architecture**: Performs both full-response generation and emotional metadata extraction (emotion, sentiment, intensity, topic, confidence) in a single Gemini request to optimize token and quota usage.
* **Real-Time Tone Tracking**: Dynamic emotional metrics panel displaying detected mood, intensity level, sentiment polarity, and topic categorization for every turn.
* **Conversation Persistence**: SQLite database back-end managing multi-session history, automatic conversation titling based on topic, message logs, and session deletion.
* **Modern Dark UI**: SaaS-grade responsive interface featuring:
  * Minimal hero greeting screen with starter prompt chips.
  * Markdown and inline code rendering with DOMPurify sanitization.
  * Gemini-style message action toolbar (clipboard copy feedback, rating states, timestamps).
  * Continuous glowing circular send button with launch animation.

---

## Tech Stack

* **Back-End**: Python, Flask, SQLite3
* **AI Engine**: Google GenAI SDK (`gemini-3.6-flash`)
* **Front-End**: Vanilla JavaScript (ES6+), CSS3 (Modern Flex/Grid, Custom Properties), HTML5
* **Libraries**: Marked.js (Markdown parsing), DOMPurify (XSS protection), Plus Jakarta Sans font

---

## Project Structure

```text
senticare-ai/
├── app.py                  # Flask server, routing, and session management
├── chatbot.py              # Gemini client, system instructions, and JSON parser
├── database.py             # SQLite schemas, conversation and message persistence
├── .env                    # Environment variables (API keys, secrets)
├── requirements.txt        # Python package dependencies
├── data/
│   └── senticare.db        # SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css       # Complete dark-mode interface styling
│   ├── js/
│   │   └── chat.js         # Chat handling, message actions, and API events
│   └── images/
│       └── logo.png        # Brand logo asset
└── templates/
    └── index.html          # Main application markup
