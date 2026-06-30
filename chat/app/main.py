from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chat.app.agent_runner import AgentRunner
from chat.app.config import DB_PATH, STATIC_DIR
from chat.app.session_store import SessionStore

app = FastAPI(title="Cursor Mini Chat", version="1.0.0")
store = SessionStore(DB_PATH)
runner = AgentRunner()


class CreateSessionRequest(BaseModel):
    title: str = "Nuova chat"
    mode: str = Field(default="ask", pattern="^(ask|plan|agent)$")


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=32000)
    mode: str | None = None


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    mode: str | None = Field(default=None, pattern="^(ask|plan|agent)$")


@app.get("/api/health")
def health() -> dict[str, Any]:
    auth = runner.auth_status()
    return {
        "status": "ok",
        "auth": auth.__dict__,
        "sessions": len(store.list_sessions()),
    }


@app.get("/api/sessions")
def list_sessions() -> list[dict[str, Any]]:
    return [s.__dict__ for s in store.list_sessions()]


@app.post("/api/sessions")
def create_session(body: CreateSessionRequest) -> dict[str, Any]:
    session = store.create_session(title=body.title, mode=body.mode)
    return session.__dict__


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    messages = store.list_messages(session_id)
    return {"session": session.__dict__, "messages": [m.__dict__ for m in messages]}


@app.patch("/api/sessions/{session_id}")
def patch_session(session_id: str, body: UpdateSessionRequest) -> dict[str, Any]:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    updates: dict[str, Any] = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.mode is not None:
        updates["mode"] = body.mode
    updated = store.update_session(session_id, **updates)
    assert updated is not None
    return updated.__dict__


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    with store._connect() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    return {"status": "deleted"}


@app.post("/api/sessions/{session_id}/messages")
async def send_message(session_id: str, body: SendMessageRequest) -> StreamingResponse:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")

    mode = body.mode or session.mode
    store.add_message(session_id, "user", body.content)

    if session.title == "Nuova chat":
        title = body.content.strip().splitlines()[0][:60]
        store.update_session(session_id, title=title or "Nuova chat")

    agent_session_id = session.agent_session_id
    if not agent_session_id:
        try:
            agent_session_id = await runner.create_agent_session()
            if agent_session_id:
                store.update_session(session_id, agent_session_id=agent_session_id)
        except RuntimeError as exc:
            async def error_stream():
                payload = {"type": "error", "message": str(exc)}
                yield f"data: {json.dumps(payload)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            return StreamingResponse(error_stream(), media_type="text/event-stream")

    current_agent_session = agent_session_id

    async def event_stream():
        assistant_text = ""
        active_agent_session = current_agent_session
        try:
            async for event in runner.stream_prompt(
                body.content, mode=mode, agent_session_id=active_agent_session
            ):
                if event.session_id and event.session_id != active_agent_session:
                    store.update_session(session_id, agent_session_id=event.session_id)
                    active_agent_session = event.session_id
                if event.tool_name:
                    payload = {"type": "tool", "name": event.tool_name}
                    yield f"data: {json.dumps(payload)}\n\n"
                if event.text_delta:
                    assistant_text += event.text_delta
                    payload = {"type": "delta", "text": event.text_delta}
                    yield f"data: {json.dumps(payload)}\n\n"
                if event.error:
                    payload = {"type": "error", "message": event.error}
                    yield f"data: {json.dumps(payload)}\n\n"
                    break
                if event.done:
                    break
        finally:
            if assistant_text.strip():
                store.add_message(session_id, "assistant", assistant_text.strip())
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


static_path = Path(STATIC_DIR)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_path / "index.html")
