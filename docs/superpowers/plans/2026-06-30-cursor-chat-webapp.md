# Cursor Mini Chat Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web chat (Cursor-like UX) powered by Cursor CLI with streaming, sessions, and personal rules.

**Architecture:** FastAPI backend wraps `agent --print --stream-json`; SQLite stores sessions; vanilla JS frontend uses SSE for streaming.

**Tech Stack:** Python 3, FastAPI, Uvicorn, SQLite, Cursor CLI, HTML/CSS/JS.

---

### Task 1: Backend core

**Files:**
- Create: `chat/app/config.py`, `chat/app/stream_parser.py`, `chat/app/session_store.py`, `chat/app/agent_runner.py`
- Test: `chat/tests/test_stream_parser.py`, `chat/tests/test_session_store.py`

- [x] Implement stream parser for agent JSONL output
- [x] Implement SQLite session/message store
- [x] Implement agent runner with auth detection and mock fallback

### Task 2: API layer

**Files:**
- Create: `chat/app/main.py`, `chat/run.py`

- [x] REST endpoints for sessions CRUD
- [x] SSE endpoint for message streaming
- [x] Health endpoint with auth status

### Task 3: Frontend

**Files:**
- Create: `chat/static/index.html`, `style.css`, `app.js`

- [x] Sidebar with session list
- [x] Message panel with streaming
- [x] Mode selector (ask/plan/agent)
- [x] Auth status indicator

### Task 4: Operations

**Files:**
- Create: `start-chat.sh`, `docs/OPERATIONS.md`, `.env.example`

- [x] One-command startup script
- [x] End-to-end operational guide
- [x] Environment variable documentation

### Task 5: Verification

- [ ] Run `pytest chat/tests -v`
- [ ] Start server with `CHAT_USE_MOCK=1`
- [ ] Verify `/api/health` and UI streaming
- [ ] With `CURSOR_API_KEY`, verify real agent responses
