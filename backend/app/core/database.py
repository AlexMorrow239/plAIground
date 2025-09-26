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
                    document_ids TEXT,
                    document_contents TEXT,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            ''')

            # Documents table
            cursor.execute('''
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    processed_content TEXT,
                    processing_error TEXT,
                    page_count INTEGER,
                    word_count INTEGER,
                    uploaded_at TEXT NOT NULL,
                    processed_at TEXT
                )
            ''')

            # Document-Message associations table
            cursor.execute('''
                CREATE TABLE message_documents (
                    message_id INTEGER NOT NULL,
                    document_id TEXT NOT NULL,
                    PRIMARY KEY (message_id, document_id),
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX idx_conversations_session ON conversations(session_id)')
            cursor.execute('CREATE INDEX idx_messages_conversation ON messages(conversation_id)')
            cursor.execute('CREATE INDEX idx_documents_session ON documents(session_id)')
            cursor.execute('CREATE INDEX idx_message_documents_message ON message_documents(message_id)')
            cursor.execute('CREATE INDEX idx_message_documents_document ON message_documents(document_id)')

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

    def add_message(self, conversation_id: str, role: str, content: str,
                   document_ids: Optional[List[str]] = None,
                   document_contents: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Add a message to a conversation with optional document associations and contents"""
        timestamp = datetime.now(timezone.utc).isoformat()

        with self.get_cursor() as cursor:
            # Add the message
            cursor.execute('''
                INSERT INTO messages (conversation_id, role, content, timestamp, document_ids, document_contents, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (conversation_id, role, content, timestamp,
                  json.dumps(document_ids) if document_ids else None,
                  json.dumps(document_contents) if document_contents else None,
                  json.dumps({})))

            message_id = cursor.lastrowid

            # Add document associations (keeping for backward compatibility)
            if document_ids:
                for doc_id in document_ids:
                    cursor.execute('''
                        INSERT OR IGNORE INTO message_documents (message_id, document_id)
                        VALUES (?, ?)
                    ''', (message_id, doc_id))

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
            "timestamp": timestamp,
            "document_ids": document_ids or [],
            "document_contents": document_contents or {}
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

            # Get messages with document associations and contents
            cursor.execute('''
                SELECT m.id, m.role, m.content, m.timestamp, m.document_ids, m.document_contents
                FROM messages m
                WHERE m.conversation_id = ?
                ORDER BY m.id ASC
            ''', (conversation_id,))

            messages = []
            for row in cursor.fetchall():
                msg = {
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "document_ids": json.loads(row["document_ids"]) if row["document_ids"] else [],
                    "document_contents": json.loads(row["document_contents"]) if row["document_contents"] else {}
                }
                messages.append(msg)

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
                # Get messages for each conversation with document associations and contents
                cursor.execute('''
                    SELECT m.id, m.role, m.content, m.timestamp, m.document_ids, m.document_contents
                    FROM messages m
                    WHERE m.conversation_id = ?
                    ORDER BY m.id ASC
                ''', (conv_row["id"],))

                messages = []
                for row in cursor.fetchall():
                    msg = {
                        "id": row["id"],
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "document_ids": json.loads(row["document_ids"]) if row["document_ids"] else [],
                        "document_contents": json.loads(row["document_contents"]) if row["document_contents"] else {}
                    }
                    messages.append(msg)

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
            cursor.execute('''
                DELETE FROM documents WHERE session_id = ?
            ''', (session_id,))

    def add_document(self, document_id: str, session_id: str, filename: str,
                    file_path: str, file_size: int, file_type: str) -> Dict[str, Any]:
        """Add a document to the database"""
        uploaded_at = datetime.now(timezone.utc).isoformat()

        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO documents (id, session_id, filename, file_path, file_size,
                                     file_type, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (document_id, session_id, filename, file_path, file_size, file_type, uploaded_at))

        return {
            "document_id": document_id,
            "filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "uploaded_at": uploaded_at
        }

    def update_document_processing(self, document_id: str, processed_content: Optional[str],
                                  processing_error: Optional[str], page_count: Optional[int],
                                  word_count: Optional[int]):
        """Update document processing results"""
        processed_at = datetime.now(timezone.utc).isoformat()

        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE documents
                SET processed_content = ?, processing_error = ?, page_count = ?,
                    word_count = ?, processed_at = ?
                WHERE id = ?
            ''', (processed_content, processing_error, page_count, word_count,
                 processed_at, document_id))

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM documents WHERE id = ?
            ''', (document_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return dict(row)

    def get_documents_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a session"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT id, filename, file_size, file_type, uploaded_at, processed_at,
                       page_count, word_count, processing_error
                FROM documents
                WHERE session_id = ?
                ORDER BY uploaded_at DESC
            ''', (session_id,))

            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, document_id: str, session_id: str) -> bool:
        """Delete a document"""
        with self.get_cursor() as cursor:
            # Check if document exists and belongs to session
            cursor.execute('''
                SELECT id FROM documents
                WHERE id = ? AND session_id = ?
            ''', (document_id, session_id))

            if not cursor.fetchone():
                return False

            # Delete document (message associations will cascade delete)
            cursor.execute('''
                DELETE FROM documents WHERE id = ?
            ''', (document_id,))

            return True

    def get_documents_by_ids(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple documents by their IDs"""
        if not document_ids:
            return []

        with self.get_cursor() as cursor:
            placeholders = ','.join('?' * len(document_ids))
            cursor.execute(f'''
                SELECT id, filename, processed_content, page_count, word_count
                FROM documents
                WHERE id IN ({placeholders})
            ''', document_ids)

            return [dict(row) for row in cursor.fetchall()]

# Global database instance
ephemeral_db = EphemeralDatabase()
