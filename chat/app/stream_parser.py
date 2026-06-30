from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class StreamEvent:
    text_delta: str = ""
    session_id: str | None = None
    done: bool = False
    error: str | None = None
    tool_name: str | None = None


@dataclass
class StreamParser:
    last_assistant_text: str = ""
    session_id: str | None = None
    seen_deltas: set[str] = field(default_factory=set)

    def feed_line(self, line: str) -> StreamEvent:
        line = line.strip()
        if not line:
            return StreamEvent()

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            if line.startswith("Error:"):
                return StreamEvent(error=line)
            return StreamEvent(text_delta=line)

        event_type = event.get("type")

        if event_type == "system" and event.get("subtype") == "init":
            self.session_id = event.get("session_id")
            return StreamEvent(session_id=self.session_id)

        if event_type == "result":
            if event.get("is_error"):
                return StreamEvent(error=str(event.get("result", "Unknown error")), done=True)
            return StreamEvent(done=True, session_id=self.session_id)

        if event_type == "assistant":
            message = event.get("message", {})
            content = message.get("content", [])
            text_parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            full_text = "".join(text_parts)
            if not full_text:
                return StreamEvent(session_id=self.session_id)

            if "timestamp_ms" in event:
                if full_text.startswith(self.last_assistant_text):
                    delta = full_text[len(self.last_assistant_text) :]
                else:
                    delta = full_text
                if delta:
                    self.last_assistant_text = full_text
                    return StreamEvent(text_delta=delta, session_id=self.session_id)
                return StreamEvent(session_id=self.session_id)

            if full_text != self.last_assistant_text:
                delta = full_text[len(self.last_assistant_text) :] if full_text.startswith(self.last_assistant_text) else full_text
                self.last_assistant_text = full_text
                return StreamEvent(text_delta=delta, session_id=self.session_id)
            return StreamEvent(session_id=self.session_id)

        if event_type == "tool_call":
            subtype = event.get("subtype")
            tool = event.get("tool_call", {})
            name = _tool_name(tool)
            if subtype == "started" and name:
                return StreamEvent(tool_name=name, session_id=self.session_id)
            return StreamEvent(session_id=self.session_id)

        return StreamEvent(session_id=self.session_id)

    def parse_stream(self, lines: Iterator[str]) -> Iterator[StreamEvent]:
        for line in lines:
            parsed = self.feed_line(line)
            if parsed.text_delta or parsed.done or parsed.error or parsed.tool_name or parsed.session_id:
                yield parsed


def _tool_name(tool: dict) -> str | None:
    for key in ("readToolCall", "editToolCall", "shellToolCall", "grepToolCall", "lsToolCall"):
        if key in tool:
            return key.replace("ToolCall", "")
    return None
