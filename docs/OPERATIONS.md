# Cursor Mini Chat — Piano operativo end-to-end

> Piano completo per far funzionare la chat al 100% in questo ambiente e in locale.

**Goal:** Web chat stile Cursor collegata alla CLI `agent`, con sessioni persistenti, streaming e regole personali.

**Architecture:** FastAPI espone REST + SSE; ogni messaggio invoca `agent --print --stream-partial-output`; SQLite salva sessioni e messaggi; frontend statico consuma SSE.

**Tech Stack:** Python 3, FastAPI, Uvicorn, SQLite, Cursor CLI (`agent`), HTML/CSS/JS.

---

## Fase 0 — Prerequisiti

- [ ] Python 3.11+
- [ ] Cursor CLI installato (`agent` in PATH)
- [ ] Account Cursor attivo
- [ ] API key da [cursor.com/settings](https://cursor.com/settings) **oppure** `agent login` completato

---

## Fase 1 — Installazione ambiente (5 min)

```bash
cd /workspace   # o percorso del repo clonato
chmod +x start-chat.sh setup/install.sh
./setup/install.sh
```

Verifica CLI:

```bash
export PATH="$HOME/.local/bin:$PATH"
agent --version
agent status
```

---

## Fase 2 — Autenticazione Cursor (obbligatoria per risposte reali)

### Opzione A — API key (consigliata per server/CI/cloud)

```bash
export CURSOR_API_KEY="key_..."
# oppure
cp .env.example .env
# modifica .env e carica:
set -a && source .env && set +a
```

### Opzione B — Login browser (macchina locale)

```bash
agent login
agent status   # deve mostrare autenticato
```

### Opzione C — Demo senza auth (solo test UI)

```bash
export CHAT_USE_MOCK=1
```

---

## Fase 3 — Avvio server chat (2 min)

```bash
./start-chat.sh
```

Apri: **http://localhost:8765**

Verifica health:

```bash
curl -s http://localhost:8765/api/health | python3 -m json.tool
```

Output atteso con auth OK:

```json
{
  "status": "ok",
  "auth": {
    "available": true,
    "authenticated": true,
    "message": "Autenticato via CURSOR_API_KEY"
  }
}
```

---

## Fase 4 — Test funzionale chat (5 min)

1. Apri http://localhost:8765
2. Sidebar: verifica badge auth verde/giallo
3. Scrivi: `Spiegami cos'è FastAPI in 2 frasi`
4. Verifica streaming risposta in tempo reale
5. Clic **+** → nuova sessione
6. Cambia modalità:
   - **Ask** — solo Q&A
   - **Plan** — pianificazione read-only
   - **Agent** — coding con tool (file, shell)

Test API manuale:

```bash
SESSION=$(curl -s -X POST http://localhost:8765/api/sessions \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test API","mode":"ask"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -N -X POST "http://localhost:8765/api/sessions/${SESSION}/messages" \
  -H 'Content-Type: application/json' \
  -d '{"content":"Ciao!"}'
```

---

## Fase 5 — Personalizzazione regole (3 min)

Le regole in `.cursor/rules/personal-chat.mdc` vengono lette automaticamente da `agent` quando `--workspace` punta al repo.

Modifica tono, lingua, stack in:

```
.cursor/rules/personal-chat.mdc
```

Riavvia non necessario — le regole sono caricate ad ogni invocazione agent.

---

## Fase 6 — Test automatici

```bash
source .venv/bin/activate
export PYTHONPATH=/workspace
pytest chat/tests -v
```

Atteso: tutti i test PASS.

---

## Fase 7 — Produzione / always-on

### systemd (Linux)

```ini
[Unit]
Description=Cursor Mini Chat
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/workspace
Environment=CURSOR_API_KEY=...
Environment=PYTHONPATH=/workspace
ExecStart=/workspace/.venv/bin/python /workspace/chat/run.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Reverse proxy (opzionale)

Esporre porta 8765 dietro nginx/caddy con TLS se accesso remoto.

---

## Troubleshooting

| Problema | Causa | Soluzione |
|---|---|---|
| `Authentication required` | Nessuna auth Cursor | `export CURSOR_API_KEY=...` o `agent login` |
| `agent non trovato` | PATH | `export PATH="$HOME/.local/bin:$PATH"` |
| UI ok, risposte demo | Mock attivo | Rimuovi `CHAT_USE_MOCK` |
| Streaming vuoto | Agent crash | Controlla `curl /api/health`, logs terminal |
| Sessioni perse | DB | File in `chat/data/sessions.db` |

---

## Checklist “100% funzionante”

- [ ] `agent --version` OK
- [ ] `agent status` o `CURSOR_API_KEY` OK
- [ ] `./start-chat.sh` avvia senza errori
- [ ] `/api/health` → `authenticated: true`
- [ ] Messaggio in UI → streaming risposta
- [ ] Nuova sessione salvata in sidebar
- [ ] `pytest chat/tests` PASS
- [ ] Regole personali attive (risposte in italiano)

---

## Struttura file

```
chat/
  app/main.py           # API + SSE
  app/agent_runner.py   # Wrapper Cursor CLI
  app/session_store.py  # SQLite
  app/stream_parser.py  # Parser stream-json
  static/               # UI chat
  data/sessions.db      # Persistenza (generato)
start-chat.sh           # Avvio one-command
.cursor/rules/          # Personalizzazione
```
