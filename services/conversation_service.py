from pathlib import Path
import sqlite3
from datetime import datetime, timezone


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

CHECKPOINT_DATABASE_PATH = (
    BASE_DIR / "conversation_checkpoints.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a SQLite connection to the existing
    conversation database.
    """

    connection = sqlite3.connect(
        str(CHECKPOINT_DATABASE_PATH)
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# TABLE INITIALIZATION
# ============================================================

def initialize_conversation_table():
    """
    Create the conversation metadata table if
    it does not already exist.
    """

    connection = get_connection()

    try:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# CREATE CONVERSATION
# ============================================================

def create_conversation(
    thread_id: str,
    title: str
):
    """
    Create a new conversation metadata record.
    """

    if not thread_id or not thread_id.strip():
        raise ValueError(
            "Thread ID cannot be empty."
        )

    if not title or not title.strip():
        raise ValueError(
            "Conversation title cannot be empty."
        )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO conversations (
                thread_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                thread_id,
                title.strip(),
                now,
                now
            )
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

def get_all_conversations():
    """
    Return all conversations ordered by most
    recently updated.
    """

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            SELECT
                thread_id,
                title,
                created_at,
                updated_at
            FROM conversations
            ORDER BY updated_at DESC
            """
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# GET ONE CONVERSATION
# ============================================================

def get_conversation(
    thread_id: str
):
    """
    Return metadata for a single conversation.
    """

    if not thread_id or not thread_id.strip():
        return None

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            SELECT
                thread_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE thread_id = ?
            """,
            (thread_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:

        connection.close()


# ============================================================
# UPDATE CONVERSATION TIMESTAMP
# ============================================================

def update_conversation_timestamp(
    thread_id: str
):
    """
    Update the last activity time of a conversation.
    """

    if not thread_id or not thread_id.strip():
        return

    now = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE thread_id = ?
            """,
            (
                now,
                thread_id
            )
        )

        connection.commit()

    finally:

        connection.close()


def create_conversation_if_not_exists(thread_id: str, title: str):
    existing = get_conversation(thread_id)

    if existing is not None:
        return existing

    create_conversation(
        thread_id=thread_id,
        title=title
    )

    return get_conversation(thread_id)


def update_conversation(thread_id: str, title: str | None = None):
    if not thread_id or not thread_id.strip():
        return

    connection = get_connection()

    try:
        now = datetime.now(timezone.utc).isoformat()

        if title is not None and title.strip():
            connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE thread_id = ?
                """,
                (title.strip(), now, thread_id)
            )
        else:
            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE thread_id = ?
                """,
                (now, thread_id)
            )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_conversation_table()