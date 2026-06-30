from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChatSession:
    id: str
    title: str
    mode: str
    agent_session_id: str | None
    created_at: str
    updated_at: str


@dataclass
class ChatMessage:
    id: str
    session_id: str
    role: str
    content: str
    created_at: str


class SessionStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'ask',
                    agent_session_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
                """
            )

    def create_session(self, title: str = "Nuova chat", mode: str = "ask") -> ChatSession:
        session_id = str(uuid.uuid4())
        now = _utc_now()
        session = ChatSession(
            id=session_id,
            title=title,
            mode=mode,
            agent_session_id=None,
            created_at=now,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, title, mode, agent_session_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session.id, session.title, session.mode, session.agent_session_id, session.created_at, session.updated_at),
            )
        return session

    def list_sessions(self) -> list[ChatSession]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [self._row_to_session(row) for row in rows]

    def get_session(self, session_id: str) -> ChatSession | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return self._row_to_session(row) if row else None

    def update_session(self, session_id: str, **fields: Any) -> ChatSession | None:
        session = self.get_session(session_id)
        if not session:
            return None
        data = session.__dict__.copy()
        data.update(fields)
        data["updated_at"] = _utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET title = ?, mode = ?, agent_session_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (data["title"], data["mode"], data["agent_session_id"], data["updated_at"], session_id),
            )
        return self.get_session(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            created_at=_utc_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message.id, message.session_id, message.role, message.content, message.created_at),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (message.created_at, session_id),
            )
        return message

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [self._row_to_message(row) for row in rows]

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> ChatSession:
        return ChatSession(
            id=row["id"],
            title=row["title"],
            mode=row["mode"],
            agent_session_id=row["agent_session_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_message(row: sqlite3.Row) -> ChatMessage:
        return ChatMessage(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
        )

    def export_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {}
        messages = self.list_messages(session_id)
        return {
            "session": session.__dict__,
            "messages": [m.__dict__ for m in messages],
        }

    def import_json(self, payload: dict[str, Any]) -> ChatSession:
        session_data = payload["session"]
        session = self.create_session(title=session_data.get("title", "Importata"), mode=session_data.get("mode", "ask"))
        if session_data.get("agent_session_id"):
            self.update_session(session.id, agent_session_id=session_data["agent_session_id"])
        for msg in payload.get("messages", []):
            self.add_message(session.id, msg["role"], msg["content"])
        updated = self.get_session(session.id)
        assert updated is not None
        return updated
