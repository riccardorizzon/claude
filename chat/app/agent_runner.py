from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from chat.app.config import AGENT_BIN, USE_MOCK, WORKSPACE
from chat.app.stream_parser import StreamEvent, StreamParser


@dataclass
class AuthStatus:
    available: bool
    authenticated: bool
    message: str
    agent_path: str | None


class AgentRunner:
    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or WORKSPACE
        self.agent_path = shutil.which(AGENT_BIN)

    def auth_status(self) -> AuthStatus:
        if USE_MOCK:
            return AuthStatus(
                available=True,
                authenticated=True,
                message="Modalità mock attiva (CHAT_USE_MOCK=1)",
                agent_path=self.agent_path,
            )
        if not self.agent_path:
            return AuthStatus(
                available=False,
                authenticated=False,
                message=f"CLI '{AGENT_BIN}' non trovato. Esegui setup/install.sh",
                agent_path=None,
            )
        if os.environ.get("CURSOR_API_KEY"):
            return AuthStatus(
                available=True,
                authenticated=True,
                message="Autenticato via CURSOR_API_KEY",
                agent_path=self.agent_path,
            )
        try:
            result = subprocess.run(
                [self.agent_path, "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = (result.stdout + result.stderr).lower()
            if "logged in" in output or "authenticated" in output:
                return AuthStatus(
                    available=True,
                    authenticated=True,
                    message="Autenticato via agent login",
                    agent_path=self.agent_path,
                )
        except (subprocess.TimeoutExpired, OSError):
            pass
        return AuthStatus(
            available=True,
            authenticated=False,
            message="Autenticazione richiesta: imposta CURSOR_API_KEY o esegui agent login",
            agent_path=self.agent_path,
        )

    async def create_agent_session(self) -> str | None:
        if USE_MOCK:
            return "mock-session"
        if not self.agent_path:
            return None
        proc = await asyncio.create_subprocess_exec(
            self.agent_path,
            "create-chat",
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode().strip() or "create-chat fallito")
        chat_id = stdout.decode().strip()
        return chat_id or None

    async def stream_prompt(
        self,
        prompt: str,
        mode: str = "ask",
        agent_session_id: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        status = self.auth_status()
        if not status.authenticated:
            yield StreamEvent(error=status.message, done=True)
            return

        if USE_MOCK:
            async for event in self._mock_stream(prompt):
                yield event
            return

        assert self.agent_path is not None
        args = [
            self.agent_path,
            "--print",
            "--output-format",
            "stream-json",
            "--stream-partial-output",
            "--trust",
            "--workspace",
            str(self.workspace),
        ]
        if mode in {"ask", "plan"}:
            args.extend(["--mode", mode])
        if mode == "agent":
            args.extend(["--force", "--approve-mcps"])
        if agent_session_id:
            args.extend(["--resume", agent_session_id])
        args.append(prompt)

        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )
        assert proc.stdout is not None
        parser = StreamParser()

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            for event in parser.parse_stream([line.decode().rstrip("\n")]):
                yield event

        stderr_data = b""
        if proc.stderr is not None:
            stderr_data = await proc.stderr.read()
        await proc.wait()

        if proc.returncode != 0:
            err = stderr_data.decode().strip() or f"agent terminato con codice {proc.returncode}"
            yield StreamEvent(error=err, done=True)
            return

        yield StreamEvent(done=True, session_id=parser.session_id or agent_session_id)

    async def _mock_stream(self, prompt: str) -> AsyncIterator[StreamEvent]:
        reply = (
            f"Ciao! Sono la tua mini chat Cursor (modalità demo).\n\n"
            f"Hai scritto: **{prompt}**\n\n"
            "Per risposte reali, imposta `CURSOR_API_KEY` e riavvia il server."
        )
        words = reply.split(" ")
        buffer = ""
        for word in words:
            buffer += word + " "
            yield StreamEvent(text_delta=word + " ")
            await asyncio.sleep(0.03)
        yield StreamEvent(done=True, session_id="mock-session")
