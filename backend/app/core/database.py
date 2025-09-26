import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import threading
from contextlib import contextmanager

class EphemeralDatabase:
    """
    In-memory SQLite database for ephemeral session data.
    All data is stored in RAM and destroyed when the process ends.
    """

    def __init__(self):
        # Use :memory: for true ephemeral storage
        self.connection = sqlite3.connect(':memory:', check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._initialize_schema()

    def _initialize_schema(self):
        """Create database tables for conversations and messages"""
        with self.lock:
            cursor = self.connection.cursor()

            # Conversations table
            cursor.execute('''
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            ''')

            # Messages table
            cursor.execute('''
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX idx_conversations_session ON conversations(session_id)')
            cursor.execute('CREATE INDEX idx_messages_conversation ON messages(conversation_id)')

            self.connection.commit()

    @contextmanager
    def get_cursor(self):
        """Thread-safe cursor context manager"""
        with self.lock:
            cursor = self.connection.cursor()
            try:
                yield cursor
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                raise e
            finally:
                cursor.close()

    def create_conversation(self, conversation_id: str, session_id: str) -> Dict[str, Any]:
        """Create a new conversation"""
        now = datetime.now(timezone.utc).isoformat()

        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO conversations (id, session_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (conversation_id, session_id, now, now, json.dumps({})))

        return {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

    def add_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        """Add a message to a conversation"""
        timestamp = datetime.now(timezone.utc).isoformat()

        with self.get_cursor() as cursor:
            # Add the message
            cursor.execute('''
                INSERT INTO messages (conversation_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (conversation_id, role, content, timestamp, json.dumps({})))

            message_id = cursor.lastrowid

            # Update conversation's updated_at
            cursor.execute('''
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
            ''', (timestamp, conversation_id))

        return {
            "id": message_id,
            "role": role,
            "content": content,
            "timestamp": timestamp
        }

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation with all its messages"""
        with self.get_cursor() as cursor:
            # Get conversation
            cursor.execute('''
                SELECT * FROM conversations WHERE id = ?
            ''', (conversation_id,))

            conv_row = cursor.fetchone()
            if not conv_row:
                return None

            # Get messages
            cursor.execute('''
                SELECT role, content, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC
            ''', (conversation_id,))

            messages = [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]

            return {
                "conversation_id": conv_row["id"],
                "created_at": conv_row["created_at"],
                "updated_at": conv_row["updated_at"],
                "messages": messages
            }

    def get_conversations_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a session"""
        with self.get_cursor() as cursor:
            # Get all conversations
            cursor.execute('''
                SELECT id, created_at, updated_at
                FROM conversations
                WHERE session_id = ?
                ORDER BY updated_at DESC
            ''', (session_id,))

            conversations = []
            for conv_row in cursor.fetchall():
                # Get messages for each conversation
                cursor.execute('''
                    SELECT role, content, timestamp
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY id ASC
                ''', (conv_row["id"],))

                messages = [
                    {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"]
                    }
                    for row in cursor.fetchall()
                ]

                conversations.append({
                    "conversation_id": conv_row["id"],
                    "created_at": conv_row["created_at"],
                    "messages": messages
                })

            return conversations

    def delete_conversation(self, conversation_id: str, session_id: str) -> bool:
        """Delete a conversation and all its messages"""
        with self.get_cursor() as cursor:
            # Check if conversation exists and belongs to session
            cursor.execute('''
                SELECT id FROM conversations
                WHERE id = ? AND session_id = ?
            ''', (conversation_id, session_id))

            if not cursor.fetchone():
                return False

            # Delete conversation (messages will cascade delete)
            cursor.execute('''
                DELETE FROM conversations WHERE id = ?
            ''', (conversation_id,))

            return True

    def clear_session_data(self, session_id: str):
        """Clear all data for a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                DELETE FROM conversations WHERE session_id = ?
            ''', (session_id,))

# Global database instance
ephemeral_db = EphemeralDatabase()
