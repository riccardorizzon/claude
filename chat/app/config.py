from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAT_DIR = ROOT / "chat"
DATA_DIR = CHAT_DIR / "data"
DB_PATH = DATA_DIR / "sessions.db"
STATIC_DIR = CHAT_DIR / "static"
WORKSPACE = Path(os.environ.get("CHAT_WORKSPACE", str(ROOT)))
AGENT_BIN = os.environ.get("AGENT_BIN", "agent")
HOST = os.environ.get("CHAT_HOST", "0.0.0.0")
PORT = int(os.environ.get("CHAT_PORT", "8765"))
DEFAULT_MODE = os.environ.get("CHAT_MODE", "ask")
USE_MOCK = os.environ.get("CHAT_USE_MOCK", "").lower() in {"1", "true", "yes"}
