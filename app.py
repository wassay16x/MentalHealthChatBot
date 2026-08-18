import os
import uuid
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from chatbot import create_chat, generate_response
from database import (
    create_conversation,
    save_message,
    get_conversations,
    get_conversation,
    get_messages,
    update_conversation_title,
    delete_conversation,
    delete_all_conversations
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "senticare-development-secret-key-change-this")

gemini_chats = {}

@app.route("/")
def home():
    return render_template("index.html")

def get_session_id():
    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
    return session_id

def get_current_conversation():
    session_id = get_session_id()
    conversation_id = session.get("conversation_id")

    if conversation_id:
        conversation = get_conversation(conversation_id, session_id)
        if conversation:
            return conversation

    conversation_id = create_conversation(session_id, "New Conversation")
    session["conversation_id"] = conversation_id
    return get_conversation(conversation_id, session_id)

def get_chat():
    conversation = get_current_conversation()
    conversation_id = conversation["id"]

    if conversation_id not in gemini_chats:
        gemini_chats[conversation_id] = create_chat()

    return gemini_chats[conversation_id], conversation

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"response": "Invalid request."}), 400

        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"response": "Please enter a message."}), 400

        if len(user_message) > 2000:
            return jsonify({
                "response": "Your message is too long. Please keep it under 2000 characters."
            }), 400

        chat_session, conversation = get_chat()
        conversation_id = conversation["id"]
        session_id = get_session_id()

        user_message_id = save_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )

        result = generate_response(chat_session, user_message)

        ai_response = result.get("response", "")
        emotion = result.get("emotion", "Neutral")
        sentiment = result.get("sentiment", "Neutral")
        intensity = result.get("intensity", "Low")
        topic = result.get("topic", "General")
        confidence = result.get("confidence", 0.0)

        assistant_message_id = save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response,
            emotion=emotion,
            sentiment=sentiment,
            intensity=intensity,
            topic=topic,
            confidence=confidence
        )

        conversation_title = conversation.get("title", "New Conversation")
        if conversation_title == "New Conversation" and topic:
            conversation_title = topic[:35].strip()
            update_conversation_title(conversation_id, session_id, conversation_title)

        return jsonify({
            "response": ai_response,
            "emotion": emotion,
            "sentiment": sentiment,
            "intensity": intensity,
            "topic": topic,
            "confidence": confidence,
            "conversation_id": conversation_id,
            "conversation_title": conversation_title,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id
        }), 200

    except Exception as e:
        error_message = str(e)
        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message or "quota" in error_message.lower():
            return jsonify({"response": "Usage limit reached. Please retry in a minute."}), 429
        return jsonify({"response": "Sorry, I couldn't process your message right now."}), 500

@app.route("/clear", methods=["POST"])
def clear_conversation():
    try:
        session_id = get_session_id()
        conversation_id = create_conversation(session_id, "New Conversation")
        session["conversation_id"] = conversation_id
        gemini_chats[conversation_id] = create_chat()

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "title": "New Conversation"
        }), 200
    except Exception as e:
        return jsonify({"success": False}), 500

@app.route("/conversations", methods=["GET"])
def conversation_list():
    try:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"conversations": []}), 200
        return jsonify({"conversations": get_conversations(session_id)}), 200
    except Exception as e:
        return jsonify({"conversations": []}), 500

@app.route("/conversations/<int:conversation_id>", methods=["GET"])
def load_conversation(conversation_id):
    try:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"error": "Session not found."}), 401

        conversation = get_conversation(conversation_id, session_id)
        if not conversation:
            return jsonify({"error": "Conversation not found."}), 404

        messages = get_messages(conversation_id, session_id)
        session["conversation_id"] = conversation_id

        if conversation_id not in gemini_chats:
            gemini_chats[conversation_id] = create_chat()

        return jsonify({"conversation": conversation, "messages": messages}), 200
    except Exception as e:
        return jsonify({"error": "Unable to load conversation."}), 500

@app.route("/conversations/<int:conversation_id>", methods=["DELETE"])
def remove_conversation(conversation_id):
    try:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"success": False}), 401

        delete_conversation(conversation_id, session_id)
        gemini_chats.pop(conversation_id, None)

        if session.get("conversation_id") == conversation_id:
            new_id = create_conversation(session_id, "New Conversation")
            session["conversation_id"] = new_id
            gemini_chats[new_id] = create_chat()

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False}), 500

if __name__ == "__main__":
    app.run(debug=True)