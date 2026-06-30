const state = {
  sessions: [],
  currentSessionId: null,
  streaming: false,
};

const els = {
  sessionList: document.getElementById("session-list"),
  messages: document.getElementById("messages"),
  composer: document.getElementById("composer"),
  promptInput: document.getElementById("prompt-input"),
  sendBtn: document.getElementById("send-btn"),
  newChatBtn: document.getElementById("new-chat-btn"),
  chatTitle: document.getElementById("chat-title"),
  modeSelect: document.getElementById("mode-select"),
  authStatus: document.getElementById("auth-status"),
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  if (res.headers.get("content-type")?.includes("text/event-stream")) {
    return res;
  }
  return res.json();
}

function renderAuth(status) {
  const auth = status.auth;
  els.authStatus.className = "auth-status";
  if (auth.authenticated) {
    els.authStatus.classList.add("ok");
    els.authStatus.textContent = auth.message;
  } else if (auth.available) {
    els.authStatus.classList.add("warn");
    els.authStatus.textContent = auth.message;
  } else {
    els.authStatus.classList.add("error");
    els.authStatus.textContent = auth.message;
  }
}

function renderSessions() {
  els.sessionList.innerHTML = "";
  for (const session of state.sessions) {
    const btn = document.createElement("button");
    btn.className = "session-item" + (session.id === state.currentSessionId ? " active" : "");
    btn.textContent = session.title;
    btn.onclick = () => loadSession(session.id);
    els.sessionList.appendChild(btn);
  }
}

function appendMessage(role, content, extraClass = "") {
  const div = document.createElement("div");
  div.className = `message ${role} ${extraClass}`.trim();
  div.textContent = content;
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
  return div;
}

function renderMessages(messages) {
  els.messages.innerHTML = "";
  if (!messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = "<p>Chat pronta.</p><p>Scrivi un messaggio per iniziare.</p>";
    els.messages.appendChild(empty);
    return;
  }
  for (const msg of messages) {
    appendMessage(msg.role, msg.content);
  }
}

async function refreshHealth() {
  const health = await api("/api/health");
  renderAuth(health);
}

async function refreshSessions() {
  state.sessions = await api("/api/sessions");
  renderSessions();
}

async function createSession() {
  const mode = els.modeSelect.value;
  const session = await api("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ title: "Nuova chat", mode }),
  });
  state.currentSessionId = session.id;
  els.chatTitle.textContent = session.title;
  els.modeSelect.value = session.mode;
  await refreshSessions();
  renderMessages([]);
}

async function loadSession(sessionId) {
  const data = await api(`/api/sessions/${sessionId}`);
  state.currentSessionId = sessionId;
  els.chatTitle.textContent = data.session.title;
  els.modeSelect.value = data.session.mode;
  renderSessions();
  renderMessages(data.messages);
}

async function sendMessage(text) {
  if (!state.currentSessionId) {
    await createSession();
  }
  if (state.streaming) return;

  state.streaming = true;
  els.sendBtn.disabled = true;
  appendMessage("user", text);
  els.promptInput.value = "";

  const assistantEl = appendMessage("assistant", "");
  let buffer = "";

  try {
    const res = await api(`/api/sessions/${state.currentSessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content: text, mode: els.modeSelect.value }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let partial = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      partial += decoder.decode(value, { stream: true });
      const chunks = partial.split("\n\n");
      partial = chunks.pop() || "";

      for (const chunk of chunks) {
        const line = chunk.trim();
        if (!line.startsWith("data:")) continue;
        const payload = JSON.parse(line.slice(5).trim());
        if (payload.type === "delta") {
          buffer += payload.text;
          assistantEl.textContent = buffer;
          els.messages.scrollTop = els.messages.scrollHeight;
        } else if (payload.type === "tool") {
          const badge = document.createElement("div");
          badge.className = "tool-badge";
          badge.textContent = `Tool: ${payload.name}`;
          assistantEl.prepend(badge);
        } else if (payload.type === "error") {
          appendMessage("system", payload.message, "error");
        }
      }
    }
  } catch (err) {
    appendMessage("system", String(err.message || err), "error");
  } finally {
    state.streaming = false;
    els.sendBtn.disabled = false;
    await refreshSessions();
  }
}

els.composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = els.promptInput.value.trim();
  if (text) sendMessage(text);
});

els.promptInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    els.composer.requestSubmit();
  }
});

els.newChatBtn.addEventListener("click", createSession);

els.modeSelect.addEventListener("change", async () => {
  if (!state.currentSessionId) return;
  await api(`/api/sessions/${state.currentSessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ mode: els.modeSelect.value }),
  });
});

async function boot() {
  await refreshHealth();
  await refreshSessions();
  if (state.sessions.length) {
    await loadSession(state.sessions[0].id);
  } else {
    await createSession();
  }
}

boot();
