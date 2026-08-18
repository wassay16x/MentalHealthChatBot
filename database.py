import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "senticare.db")

os.makedirs(DATA_DIR, exist_ok=True)

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'New Conversation',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            emotion TEXT,
            sentiment TEXT,
            intensity TEXT,
            topic TEXT,
            confidence REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")

    connection.commit()
    connection.close()

def create_conversation(session_id, title="New Conversation"):
    connection = get_connection()
    cursor = connection.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    cursor.execute(
        """
        INSERT INTO conversations (session_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, title, now, now)
    )

    conversation_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return conversation_id

def save_message(
    conversation_id,
    role,
    content,
    emotion=None,
    sentiment=None,
    intensity=None,
    topic=None,
    confidence=None
):
    connection = get_connection()
    cursor = connection.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    cursor.execute(
        """
        INSERT INTO messages (
            conversation_id,
            role,
            content,
            emotion,
            sentiment,
            intensity,
            topic,
            confidence,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            emotion,
            sentiment,
            intensity,
            topic,
            confidence,
            now
        )
    )

    cursor.execute(
        """
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
        """,
        (now, conversation_id)
    )

    connection.commit()
    message_id = cursor.lastrowid
    connection.close()
    return message_id

def get_conversations(session_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, session_id, title, created_at, updated_at
        FROM conversations
        WHERE session_id = ?
        ORDER BY updated_at DESC
        """,
        (session_id,)
    )

    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]

def get_conversation(conversation_id, session_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, session_id, title, created_at, updated_at
        FROM conversations
        WHERE id = ? AND session_id = ?
        """,
        (conversation_id, session_id)
    )

    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None

def get_messages(conversation_id, session_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.role,
            m.content,
            m.emotion,
            m.sentiment,
            m.intensity,
            m.topic,
            m.confidence,
            m.created_at
        FROM messages m
        INNER JOIN conversations c ON m.conversation_id = c.id
        WHERE m.conversation_id = ? AND c.session_id = ?
        ORDER BY m.id ASC
        """,
        (conversation_id, session_id)
    )

    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]

def update_conversation_title(conversation_id, session_id, title):
    connection = get_connection()
    cursor = connection.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    cursor.execute(
        """
        UPDATE conversations
        SET title = ?, updated_at = ?
        WHERE id = ? AND session_id = ?
        """,
        (title, now, conversation_id, session_id)
    )

    connection.commit()
    updated = cursor.rowcount > 0
    connection.close()
    return updated

def delete_conversation(conversation_id, session_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM conversations
        WHERE id = ? AND session_id = ?
        """,
        (conversation_id, session_id)
    )

    connection.commit()
    deleted = cursor.rowcount > 0
    connection.close()
    return deleted

def generate_conversation_title(conversation_id, session_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT content
        FROM messages
        WHERE conversation_id = ? AND role = 'user'
        ORDER BY id ASC
        LIMIT 1
        """,
        (conversation_id,)
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return "New Conversation"

    text = " ".join(row["content"].strip().split())
    max_length = 45

    title = text[:max_length].rstrip() + "..." if len(text) > max_length else text

    update_conversation_title(conversation_id, session_id, title)
    return title

def get_latest_conversation(session_id):
    conversations = get_conversations(session_id)
    return conversations[0] if conversations else None

def delete_all_conversations(session_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM conversations
        WHERE session_id = ?
        """,
        (session_id,)
    )

    connection.commit()
    deleted_count = cursor.rowcount
    connection.close()
    return deleted_count

init_database()

if __name__ == "__main__":
    print("========================================")
    print("SentiCare AI Database")
    print("========================================")
    print(f"Database: {DATABASE_PATH}")
    print("Database initialized successfully.")
    print("========================================")